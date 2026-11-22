"""Opt-in workflow recording. One private SQLite ledger per experimental group."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shlex
import sqlite3
import sys
from base64 import b64encode
from contextlib import contextmanager
from uuid import uuid4
import zlib
from datetime import datetime, timezone

from . import util

EVENTS = ("UserPromptSubmit", "PostToolUse", "SubagentStart", "SubagentStop", "Stop",
          "Interrupt", "SessionEnd")
SCHEMA = """
CREATE TABLE IF NOT EXISTS stage(
 name TEXT PRIMARY KEY, work TEXT NOT NULL, marker TEXT NOT NULL, session TEXT UNIQUE,
 epoch TEXT, sealed TEXT,
 UNIQUE(work, marker));
CREATE TABLE IF NOT EXISTS actor(
 id TEXT PRIMARY KEY, stage TEXT NOT NULL REFERENCES stage(name), parent TEXT,
 offset INTEGER NOT NULL DEFAULT 0, usage TEXT, path TEXT, started TEXT, ended TEXT,
 baseline INTEGER);
CREATE TABLE IF NOT EXISTS event(
 seq INTEGER PRIMARY KEY, stage TEXT, actor TEXT, utc TEXT, kind TEXT, body TEXT);
CREATE TABLE IF NOT EXISTS content(sha256 TEXT PRIMARY KEY, compressed BLOB NOT NULL);
"""
LIMIT = 64000


def now():
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def ledger(directory, create=False, readonly=False):
    path = Path(directory).resolve() / "events.sqlite3"
    if create:
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    elif not path.is_file():
        raise util.FactoryError("missing enrolled group ledger")
    mode = "rwc" if create else ("ro" if readonly else "rw")
    conn = sqlite3.connect(path.as_uri() + "?mode=" + mode, uri=True, timeout=20)
    try:
        conn.row_factory = sqlite3.Row
        if create:
            conn.executescript(SCHEMA)
        with conn:
            yield conn
    finally:
        conn.close()


def event(db, stage, actor, kind, body):
    db.execute("INSERT INTO event(stage,actor,utc,kind,body) VALUES(?,?,?,?,?)",
               (stage, actor, now(), kind, json.dumps(body, ensure_ascii=False)))


def observed(db, value):
    raw = json.dumps(value, ensure_ascii=False)
    if len(raw) <= LIMIT:
        return {"value": value, "coverage": "as_returned"}
    data = raw.encode()
    digest = hashlib.sha256(data).hexdigest()
    db.execute("INSERT OR IGNORE INTO content VALUES(?,?)", (digest, zlib.compress(data)))
    return {"coverage": "exact_reference", "bytes": len(data), "sha256": digest}


def read_transcript(db, stage, actor, path, cutoff=None):
    """Read only the enrolled actor's append-only rollout, never reasoning items."""
    if not path:
        event(db, stage, actor, "coverage", "transcript unavailable")
        return
    state = db.execute("SELECT offset,started,baseline FROM actor WHERE id=?", (actor,)).fetchone()
    pos = state["offset"]
    try:
        with Path(path).open("rb") as stream:
            meta = json.loads(stream.readline())
            if meta.get("type") != "session_meta" or meta.get("payload", {}).get("id") != actor:
                event(db, stage, actor, "coverage", "unverified transcript identity")
                return
            db.execute("UPDATE actor SET path=? WHERE id=?", (str(Path(path).resolve()), actor))
            if pos > stream.seek(0, os.SEEK_END):
                event(db, stage, actor, "coverage", "transcript shortened")
                return
            stream.seek(pos)
            for line in stream:
                if not line.endswith(b"\n"):
                    break
                pos += len(line)
                try:
                    item = json.loads(line)
                except ValueError:
                    event(db, stage, actor, "coverage", "unreadable transcript row")
                    continue
                if not isinstance(item, dict) or not isinstance(item.get("payload"), dict):
                    event(db, stage, actor, "coverage", "unknown transcript row")
                    continue
                body = item["payload"]
                kind = body.get("type")
                # Forks can contain the parent's earlier context. Read only new,
                # timestamped activity; turn other/older shapes into coverage gaps.
                try:
                    timestamp = datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00"))
                    before = timestamp < datetime.fromisoformat(state["started"])
                    if cutoff and timestamp > datetime.fromisoformat(cutoff):
                        continue
                except (KeyError, TypeError, ValueError, AttributeError):
                    event(db, stage, actor, "coverage", "row has no comparable timestamp")
                    continue
                if before:
                    if item["type"] == "event_msg" and kind == "token_count":
                        totals = (body.get("info") or {}).get("total_token_usage") or {}
                        if isinstance(totals.get("total_tokens"), int):
                            db.execute("UPDATE actor SET baseline=? WHERE id=?", (totals["total_tokens"], actor))
                    continue
                if item.get("type") == "response_item":
                    if kind == "message" and body.get("role") == "assistant":
                        if body.get("channel") not in (None, "commentary", "final"):
                            continue
                        for block in body.get("content", []):
                            if block.get("type") == "output_text":
                                event(db, stage, actor, "assistant", block.get("text"))
                    elif kind in ("function_call_output", "custom_tool_call_output"):
                        event(db, stage, actor, "tool_return", {
                            "call_id": body.get("call_id"), "result": observed(db, body.get("output")),
                            "streams": "as_exposed_by_runtime"})
                    elif kind in ("function_call", "custom_tool_call"):
                        event(db, stage, actor, "tool_call", {
                            "name": body.get("name"), "call_id": body.get("call_id"),
                            "arguments": observed(db, body.get("arguments", body.get("input")))})
                elif item.get("type") == "event_msg" and kind == "token_count":
                    totals = (body.get("info") or {}).get("total_token_usage")
                    if isinstance(totals, dict) and isinstance(totals.get("total_tokens"), int):
                        db.execute("UPDATE actor SET usage=? WHERE id=?", (json.dumps(totals), actor))
            db.execute("UPDATE actor SET offset=? WHERE id=?", (pos, actor))
    except (OSError, ValueError, AttributeError) as exc:
        event(db, stage, actor, "coverage", "transcript unavailable: " + type(exc).__name__)


def active_epoch(switch):
    try:
        return (Path(switch) / "enabled").read_text(encoding="ascii").strip()
    except FileNotFoundError:
        return None


def ingest(directory, switch, payload):
    epoch = active_epoch(switch)
    if not epoch:
        return
    parent = payload.get("session_id")
    kind = payload.get("hook_event_name")
    if not isinstance(parent, str) or not parent or kind not in EVENTS:
        return
    with ledger(directory) as db:
        db.execute("BEGIN IMMEDIATE")
        match = db.execute("SELECT stage FROM actor JOIN stage ON name=actor.stage "
                           "WHERE id=? AND epoch=? AND sealed IS NULL", (parent, epoch)).fetchone()
        if not match and kind == "UserPromptSubmit":
            prompt = payload.get("prompt", "")
            first = prompt.splitlines()[:1]
            if not first or not payload.get("cwd"):
                return
            work = os.path.normcase(str(Path(payload["cwd"]).resolve()))
            slot = db.execute("SELECT name FROM stage WHERE work=? AND marker=? AND session IS NULL",
                              (work, first[0])).fetchone()
            if slot:
                if db.execute("SELECT 1 FROM actor WHERE id=?", (parent,)).fetchone():
                    return
                db.execute("UPDATE stage SET session=?, epoch=? WHERE name=?", (parent, epoch, slot[0]))
                db.execute("INSERT INTO actor(id,stage,started) VALUES(?,?,?)", (parent, slot[0], now()))
                match = slot
        if not match:
            return
        stage = match[0]
        actor = parent
        child = payload.get("agent_id")
        if kind in ("SubagentStart", "SubagentStop") and isinstance(child, str) and child:
            if kind == "SubagentStop" and not db.execute("SELECT 1 FROM actor WHERE id=?", (child,)).fetchone():
                event(db, stage, parent, "coverage", "subagent start missing")
            db.execute("INSERT OR IGNORE INTO actor(id,stage,parent,started) VALUES(?,?,?,?)",
                       (child, stage, parent, now()))
            owner = db.execute("SELECT stage FROM actor WHERE id=?", (child,)).fetchone()[0]
            if owner != stage:
                return
            actor = child
        details = {key: payload[key] for key in ("turn_id", "model", "agent_type", "reason",
                                                  "tool_name", "tool_use_id", "status") if key in payload}
        if kind == "UserPromptSubmit":
            details["prompt"] = payload.get("prompt")
        elif kind == "PostToolUse":
            for key in ("tool_input", "tool_response"):
                if key in payload:
                    details[key] = observed(db, payload[key])
            response = payload.get("tool_response")
            if isinstance(response, dict):
                for key in ("exit_code", "stdout", "stderr"):
                    if key in response:
                        details[key] = observed(db, response[key])
            details["streams"] = ("separate" if "stdout" in details and "stderr" in details
                                  else "combined_or_unavailable")
            details["coverage"] = "hook_payload; consult tool_return for model-visible result"
        if kind in ("Stop", "SubagentStop"):
            details["last_assistant_message"] = payload.get("last_assistant_message")
        event(db, stage, actor, kind, details)
        if kind in ("SessionEnd", "SubagentStop"):
            db.execute("UPDATE actor SET ended=? WHERE id=?", (now(), actor))
        if kind in ("Stop", "SessionEnd", "Interrupt", "SubagentStop"):
            key = "agent_transcript_path" if kind == "SubagentStop" else "transcript_path"
            read_transcript(db, stage, actor, payload.get(key))


def add_parser(commands):
    parser = commands.add_parser("debug", help="enroll, record and evaluate named flows")
    sub = parser.add_subparsers(dest="debug_action", required=True)
    for action in ("on", "off", "arm", "hook", "hook-config", "report", "content", "seal"):
        p = sub.add_parser(action)
        if action in ("on", "off", "hook", "hook-config", "seal"):
            p.add_argument("--switch", required=True, type=Path)
        if action not in ("on", "off"):
            p.add_argument("--group-dir", required=True, type=Path)
        if action == "arm":
            p.add_argument("--stage", required=True)
            p.add_argument("--work", required=True, type=Path)
            p.add_argument("--marker", required=True)
        if action in ("seal", "report"):
            p.add_argument("--stage", required=True)
        if action == "report":
            p.add_argument("--events", action="store_true")
        if action == "content":
            p.add_argument("--sha256", required=True)
        p.set_defaults(func=run)


def run(args):
    action = args.debug_action
    if action in ("on", "off"):
        flag = args.switch / "enabled"
        if action == "on":
            flag.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            try:
                with flag.open("x", encoding="ascii") as out:
                    out.write(uuid4().hex)
            except FileExistsError:
                pass
        else:
            flag.unlink(missing_ok=True)
    elif action == "arm":
        if not args.work.is_dir() or not args.marker or not args.stage:
            raise util.FactoryError("provide an existing workspace, stage and exact opening line")
        if args.group_dir.resolve().is_relative_to(args.work.resolve()):
            raise util.FactoryError("the recording directory must be outside the execution workspace")
        with ledger(args.group_dir, create=True) as db:
            key = (args.stage, os.path.normcase(str(args.work.resolve())), args.marker)
            try:
                db.execute("INSERT INTO stage(name,work,marker) VALUES(?,?,?)", key)
            except sqlite3.IntegrityError:
                if not db.execute("SELECT 1 FROM stage WHERE name=? AND work=? AND marker=?", key).fetchone():
                    raise util.FactoryError("stage name or enrollment marker already assigned")
    elif action == "hook":
        ingest(args.group_dir, args.switch, json.load(sys.stdin.buffer))
        print("{}")
    elif action == "hook-config":
        argv = [sys.executable, str(util.ENGINE_ROOT / "factory.py"), "debug", "hook",
                "--switch", str(args.switch.resolve()), "--group-dir", str(args.group_dir.resolve())]
        command = shlex.join(argv)
        handler = {"type": "command", "command": command}
        if os.name == "nt":
            # EncodedCommand carries paths literally through either cmd or PowerShell.
            script = "& " + " ".join("'" + arg.replace("'", "''") + "'" for arg in argv) + "; exit $LASTEXITCODE"
            encoded = b64encode(script.encode("utf-16-le")).decode("ascii")
            handler["command"] = "powershell.exe -NoProfile -NonInteractive -EncodedCommand " + encoded
        print(json.dumps({"hooks": {name: [{"hooks": [dict(handler, timeout=3 if name in ("SessionEnd", "Interrupt") else 30)]}]
                                    for name in EVENTS}}, indent=2))
    elif action == "seal":
        with ledger(args.group_dir) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT epoch,sealed FROM stage WHERE name=? AND session IS NOT NULL",
                             (args.stage,)).fetchone()
            if not row:
                raise util.FactoryError("no enrolled session")
            if row["sealed"]:
                return 0
            when = now()
            for actor in db.execute("SELECT id,path FROM actor WHERE stage=?", (args.stage,)).fetchall():
                if active_epoch(args.switch) == row["epoch"]:
                    read_transcript(db, args.stage, actor["id"], actor["path"], cutoff=when)
                else:
                    event(db, args.stage, actor["id"], "coverage", "switch disabled before seal")
            db.execute("UPDATE stage SET sealed=? WHERE name=?", (when, args.stage))
    elif action == "content":
        with ledger(args.group_dir, readonly=True) as db:
            row = db.execute("SELECT compressed FROM content WHERE sha256=?", (args.sha256,)).fetchone()
            if not row:
                raise util.FactoryError("content reference not found in this group")
            print(zlib.decompress(row[0]).decode())
    else:
        with ledger(args.group_dir, readonly=True) as db:
            stage = db.execute("SELECT sealed FROM stage WHERE name=?", (args.stage,)).fetchone()
            if not stage:
                raise util.FactoryError("unknown stage")
            actors = [dict(row) for row in db.execute("SELECT id,parent,usage,baseline,ended FROM actor WHERE stage=?",
                                                       (args.stage,))]
            for actor in actors:
                actor["usage"] = json.loads(actor["usage"]) if actor["usage"] else None
                actor["enrolled_tokens"] = None
                if actor["usage"]:
                    difference = actor["usage"]["total_tokens"] - (actor["baseline"] or 0)
                    if difference >= 0:
                        actor["enrolled_tokens"] = difference
            bounds = db.execute("SELECT min(utc), max(utc) FROM event WHERE stage=?",
                                (args.stage,)).fetchone()
            duration = None
            if bounds[0] and bounds[1]:
                duration = (datetime.fromisoformat(bounds[1]) - datetime.fromisoformat(bounds[0])).total_seconds()
            counts = [a["enrolled_tokens"] for a in actors if a["enrolled_tokens"] is not None]
            coverage = db.execute("SELECT count(*) FROM event WHERE stage=? AND kind='coverage'",
                                  (args.stage,)).fetchone()[0]
            usage_coverage = "unknown"
            if (actors and len(counts) == len(actors) and stage["sealed"] and not coverage
                    and all(a["ended"] for a in actors)):
                usage_coverage = "reported_for_all_observed_actors"
            result = {"stage": args.stage, "actors": actors, "first_event": bounds[0],
                      "last_event": bounds[1], "observed_span_seconds": duration,
                      "sealed": stage["sealed"], "usage_completeness": usage_coverage,
                      "coverage_gaps": coverage, "known_total_tokens": sum(counts) if counts else None,
                      "actors_without_usage": [a["id"] for a in actors if a["enrolled_tokens"] is None]}
            if args.events:
                result["events"] = [dict(row) for row in db.execute(
                    "SELECT * FROM event WHERE stage=? ORDER BY seq", (args.stage,))]
                for record in result["events"]:
                    record["body"] = json.loads(record["body"])
            print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0
