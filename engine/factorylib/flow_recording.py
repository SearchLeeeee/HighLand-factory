"""Portable workflow evidence written by factory clients, independent of chat runtimes."""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import tempfile
import time

from . import flow_scopes, util


SCHEMA = """
CREATE TABLE IF NOT EXISTS flow(name TEXT PRIMARY KEY, started TEXT NOT NULL, sealed TEXT);
CREATE TABLE IF NOT EXISTS event(
 seq INTEGER PRIMARY KEY, utc TEXT NOT NULL, phase TEXT NOT NULL, agent TEXT NOT NULL,
 kind TEXT NOT NULL, parent INTEGER REFERENCES event(seq), body TEXT NOT NULL);
CREATE UNIQUE INDEX IF NOT EXISTS one_end_per_step ON event(parent) WHERE kind='end';
"""
OUTCOMES = ("passed", "failed", "blocked", "interrupted", "completed")
NOTES = ("observation", "decision", "handoff", "blocked", "retry", "delivery")


def utc():
    return datetime.now(timezone.utc).isoformat()


def emit(value):
    # JSON stays portable even on a Windows pipe using a legacy code page.
    print(json.dumps(value, indent=2, ensure_ascii=(sys.stdout.encoding or "").lower() != "utf-8"))


def record_dir(args):
    if (not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}", args.flow) or args.flow.endswith(".")
            or (os.name == "nt" and Path(args.flow).is_reserved())):
        raise util.FactoryError("use a filesystem-safe flow name starting with a letter or digit")
    root = args.records or args.work / ".factory" / "analysis" / "flows"
    return root.resolve() / args.flow


def handoff(args, destination, parent=None, scope=None):
    lines = [f"factory-flow {args.flow} {destination}", f"WORK_ROOT = {args.work.resolve()}",
             f"RECORDS = {record_dir(args).parent}"]
    if scope:
        lines.append(f"Recording scope = {scope}. Keep recording until that scope's workflow ends.")
    if parent is not None:
        lines.append(f"Read upstream event {parent} with factory debug flow report --event {parent}. "
                     f"Link the first action with --parent {parent}.")
    lines.append("Use factory debug flow with these coordinates only for work continuing this workflow. "
                 "Record your own role and carry the marker in same-workflow handoffs. "
                 "At final closure the coordinator seals this flow. Every independent workflow starts "
                 "with recording off unless the user explicitly requests it at that workflow's start.")
    return "\n".join(lines)


@contextmanager
def ledger(args, *, create=False, read=False, bind_scope=False):
    directory = record_dir(args)
    if create:
        if not args.work.is_dir():
            raise util.FactoryError("workspace does not exist")
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = directory / "flow.sqlite3"
    if not create and not path.is_file():
        raise util.FactoryError("flow not found; check --work or the shared --records directory")
    mode = "rwc" if create else "ro" if read else "rw"
    db = sqlite3.connect(path.as_uri() + "?mode=" + mode, uri=True, timeout=20)
    db.row_factory = sqlite3.Row
    try:
        if create:
            db.executescript(SCHEMA)
        if bind_scope:
            flow_scopes.attach_index(db, args.work)
        with db:
            db.execute("BEGIN" if read else "BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM flow").fetchone()
            if row is None and create:
                db.execute("INSERT INTO flow(name,started) VALUES(?,?)", (args.flow, utc()))
            elif row is None or row["name"] != args.flow:
                raise util.FactoryError("flow identity does not match this record directory")
            elif row["sealed"] and not read and args.action != "seal":
                raise util.FactoryError("flow is sealed")
            elif create:
                raise util.FactoryError("flow already started; use the existing handoff to continue it "
                                        "or choose a fresh ID for a new recording")
            yield db
    finally:
        db.close()


def save_stream(directory, relative, source, echo=None):
    """Publish the finished file at its event-relative location."""
    destination = directory / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = tempfile.NamedTemporaryFile(dir=destination.parent, delete=False)
    path = Path(temp.name)
    try:
        with temp:
            read = getattr(source, "read1", source.read)
            while chunk := read(65536):
                temp.write(chunk)
                if echo is not None:
                    try:
                        echo.write(chunk)
                        echo.flush()
                    except BrokenPipeError:
                        echo = None
            count = temp.tell()
        os.replace(path, destination)
        return {"bytes": count, "object": relative.as_posix()}
    finally:
        path.unlink(missing_ok=True)


def artifact_targets(args):
    work = args.work.resolve()
    directory = record_dir(args)
    for relative in dict.fromkeys(map(Path, args.artifact)):
        path = (work / relative).resolve()
        if relative.anchor or ".." in relative.parts or not path.is_relative_to(work) or path.is_relative_to(directory):
            raise util.FactoryError("artifact must be a workspace-relative file outside this recording")
        yield relative, path


def artifacts(args, seq):
    work = args.work.resolve()
    directory = record_dir(args)
    result = []
    for relative, path in list(artifact_targets(args)):
        item = {"path": relative.as_posix(), "work": str(work)}
        try:
            if not path.exists():
                item["status"] = "missing"
            elif not path.is_file():
                item["status"] = "not_a_file"
            else:
                with path.open("rb") as source:
                    before = os.fstat(source.fileno())
                    saved = save_stream(directory, Path("events", str(seq), "artifacts") / relative, source)
                    after = os.fstat(source.fileno())
                if before.st_mtime_ns != after.st_mtime_ns or saved["bytes"] != after.st_size:
                    item["status"] = "changed_during_capture"
                else:
                    item.update(saved, status="captured")
        except OSError as exc:
            item.update(status="unreadable", error=type(exc).__name__)
        result.append(item)
    return result


def capture_output(directory, relative, stream, echo):
    try:
        return save_stream(directory, relative, stream, echo)
    except OSError as exc:
        # Keep draining the child pipe if evidence storage fails mid-command.
        while stream.read(65536):
            pass
        return {"status": "unavailable", "error": str(exc)}


def read_event(db, seq):
    row = db.execute("SELECT * FROM event WHERE seq=?", (seq,)).fetchone()
    if not row:
        raise util.FactoryError(f"event {seq} does not exist in this flow")
    return {**dict(row), "body": json.loads(row["body"])}


def append(db, phase, agent, kind, parent, body, *, capture=None):
    if not phase.strip() or not agent.strip():
        raise util.FactoryError("provide a phase and an agent role or name")
    if parent is not None:
        read_event(db, parent)
    if capture is not None:
        body["artifacts"] = []
    seq = db.execute("INSERT INTO event(utc,phase,agent,kind,parent,body) VALUES(?,?,?,?,?,?)",
                     (utc(), phase, agent, kind, parent, json.dumps(body, ensure_ascii=False))).lastrowid
    if capture is not None and capture.artifact:
        body["artifacts"] = artifacts(capture, seq)
        db.execute("UPDATE event SET body=? WHERE seq=?", (json.dumps(body, ensure_ascii=False), seq))
    return seq


def start_step(args, body):
    with ledger(args) as db:
        return append(db, args.phase, args.agent, "begin", args.parent, body)


def end_step(args, seq, outcome, body):
    with ledger(args) as db:
        start = read_event(db, seq)
        if start["kind"] != "begin":
            raise util.FactoryError("--step must name a begin event")
        if db.execute("SELECT 1 FROM event WHERE kind='end' AND parent=?", (seq,)).fetchone():
            raise util.FactoryError("step already finished")
        if "seconds" not in body:
            duration = (datetime.now(timezone.utc) - datetime.fromisoformat(start["utc"])).total_seconds()
            body.update(seconds=duration if duration >= 0 else None, timing="between_records")
        body.update(outcome=outcome)
        return append(db, start["phase"], args.agent or start["agent"], "end", seq, body, capture=args)


def run_command(args):
    argv = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not argv:
        raise util.FactoryError("supply an executable and arguments after --")
    list(artifact_targets(args))  # Validate selected paths before launching the command.
    seq = start_step(args, {"action": args.label or argv[0], "argv": argv, "cwd": str(Path.cwd()), "source": "command"})
    started = time.monotonic()
    body = {"timing": "command_wall"}
    directory = record_dir(args)
    step_dir = Path("events", str(seq))
    try:
        with subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
            with ThreadPoolExecutor(max_workers=2) as pool:
                out = pool.submit(capture_output, directory, step_dir / "stdout.log", proc.stdout, sys.stdout.buffer)
                err = pool.submit(capture_output, directory, step_dir / "stderr.log", proc.stderr, sys.stderr.buffer)
                try:
                    code = proc.wait()
                    outcome = "passed" if code == 0 else "failed"
                except KeyboardInterrupt:
                    proc.kill()
                    proc.wait()
                    code, outcome = 130, "interrupted"
                body["seconds"] = time.monotonic() - started
                body.update(stdout=out.result(), stderr=err.result())
    except OSError as exc:
        code, outcome = 127, "failed"
        body.update(error=str(exc), seconds=time.monotonic() - started)
        print(str(exc), file=sys.stderr)
    body["exit_code"] = code
    try:
        end_step(args, seq, outcome, body)
    except (util.FactoryError, OSError, sqlite3.Error) as exc:
        print(f"Recording incomplete for step {seq}: {exc}", file=sys.stderr)
    return code if code >= 0 else 128 - code


def open_steps(db):
    return [r[0] for r in db.execute("SELECT b.seq FROM event b WHERE b.kind='begin' AND NOT EXISTS "
                                     "(SELECT 1 FROM event e WHERE e.kind='end' AND e.parent=b.seq) ORDER BY b.seq")]


def report(db, args):
    if args.event:
        return {"flow": args.flow, "events": [read_event(db, n) for n in dict.fromkeys(args.event)]}
    rows = [{**dict(r), "body": json.loads(r["body"])} for r in db.execute("SELECT * FROM event ORDER BY seq")]
    by_seq = {r["seq"]: r for r in rows}
    phases = {}
    steps, issues, files, gaps, usage = [], [], [], [], []
    for i, row in enumerate(rows):
        phase, agent, body = row["phase"], row["agent"], row["body"]
        summary = phases.setdefault(phase, {"agents": [], "event_counts": Counter(), "first_event": row["seq"]})
        summary["last_event"] = row["seq"]
        if agent not in summary["agents"]:
            summary["agents"].append(agent)
        summary["event_counts"][row["kind"]] += 1
        ref = {"event": row["seq"], "phase": phase, "agent": agent}
        files.extend({**ref, **f} for f in body.get("artifacts", []))
        if row["kind"] == "end":
            start = by_seq[row["parent"]]
            step = {**ref, "begin": start["seq"], "action": start["body"]["action"],
                    "outcome": body["outcome"], "seconds": body["seconds"], "timing": body["timing"]}
            if step["seconds"] is not None:
                steps.append(step)
            if body["outcome"] in ("failed", "blocked", "interrupted"):
                issues.append(step)
            if body.get("tokens") is not None:
                usage.append({**ref, "tokens": body["tokens"]})
        elif row["kind"] in ("blocked", "retry", "handoff"):
            issues.append({**ref, "kind": row["kind"], "message": body["message"]})
        if i:
            previous = rows[i - 1]
            seconds = (datetime.fromisoformat(row["utc"]) - datetime.fromisoformat(previous["utc"])).total_seconds()
            if seconds >= 0:
                gaps.append({"from_event": previous["seq"], "to_event": row["seq"], "seconds": seconds})
    result = {**dict(db.execute("SELECT name AS flow,started,sealed FROM flow").fetchone()),
              "record_dir": str(record_dir(args)), "phases": phases,
              "open_steps": [{"event": n, "action": by_seq[n]["body"]["action"]} for n in open_steps(db)],
              "slowest_steps": sorted(steps, key=lambda s: -s["seconds"])[:10], "review_events": issues,
              "longest_observed_gaps": sorted(gaps, key=lambda s: -s["seconds"])[:10],
              "artifacts": files, "reported_usage": usage}
    enrollment = flow_scopes.enrollment(db)
    if enrollment:
        result["enrollment"] = dict(enrollment)
    if args.events:
        result["events"] = rows
    return result


def execute(args):
    if args.action == "run":
        return run_command(args)
    if args.action == "lookup":
        result = flow_scopes.lookup(args)
    elif args.action in ("start", "bind"):
        binding = flow_scopes.target(args) if args.scope else None
        with ledger(args, create=args.action == "start", bind_scope=bool(binding)) as db:
            if binding:
                flow_scopes.bind(db, args, record_dir(args).parent, *binding)
            elif args.pending_scope:
                registry = os.path.normcase(str(flow_scopes.registry_path(args)))
                flow_scopes.declare(db, args.pending_scope, registry)
        result = {"flow": args.flow, "record_dir": str(record_dir(args)),
                  "handoff": handoff(args, args.phase, scope=args.scope)}
        if args.scope:
            result["scope"] = args.scope
    elif args.action == "begin":
        result = {"step": start_step(args, {"action": args.label, "source": "agent"})}
    elif args.action == "end":
        if args.tokens is not None and args.tokens < 0:
            raise util.FactoryError("reported token count must be nonnegative")
        result = {"event": end_step(args, args.step, args.outcome, {"message": args.message, "tokens": args.tokens})}
    elif args.action == "note":
        if args.to_phase and args.kind != "handoff":
            raise util.FactoryError("--to-phase belongs to a handoff")
        with ledger(args) as db:
            body = {"message": args.message}
            if args.to_phase:
                body["to_phase"] = args.to_phase
            seq = append(db, args.phase, args.agent, args.kind, args.parent, body, capture=args)
            result = {"event": seq}
            if args.kind == "handoff":
                enrollment = flow_scopes.enrollment(db)
                result["handoff"] = handoff(args, args.to_phase or "<next-phase>", seq,
                                            scope=enrollment["scope"] if enrollment else None)
    elif args.action == "seal":
        with ledger(args) as db:
            pending = open_steps(db)
            if pending and not args.incomplete and not db.execute("SELECT sealed FROM flow").fetchone()[0]:
                raise util.FactoryError(f"open steps {pending}; finish them or use --incomplete to preserve the gap")
            db.execute("UPDATE flow SET sealed=COALESCE(sealed,?)", (utc(),))
            result = {"flow": args.flow, "sealed": db.execute("SELECT sealed FROM flow").fetchone()[0],
                      "open_steps": pending}
    else:
        with ledger(args, read=True) as db:
            result = report(db, args)
    emit(result)
    return 0


def add_parser(commands):
    parser = commands.add_parser("flow", help="record and review workflow actions from any agent or CLI")
    actions = parser.add_subparsers(dest="action", required=True)
    for action in ("start", "bind", "lookup", "begin", "end", "note", "run", "report", "seal"):
        p = actions.add_parser(action)
        if action != "lookup":
            p.add_argument("--flow", required=True, help="user-chosen workflow identifier")
            p.add_argument("--records", type=Path, help="shared records root (default: WORK/.factory/analysis/flows)")
        p.add_argument("--work", type=Path, default=Path.cwd(), help="common work root (default: current directory)")
        if action in ("start", "bind", "lookup"):
            p.add_argument("--registry", type=Path, help="feature registry (default: configured active registry)")
        if action == "start":
            scope = p.add_mutually_exclusive_group()
            scope.add_argument("--scope", help="authorized registered Initiative or full Leaf ID")
            scope.add_argument("--pending-scope", choices=("initiative", "feature"),
                               help="declare the authorized scope when its formal ID has not been assigned")
        if action in ("bind", "lookup"):
            p.add_argument("--scope", required=True, help="full registered Initiative or Leaf ID")
        if action in ("start", "bind"):
            p.add_argument("--phase", default="intake", help="first phase in the copyable prompt")
        if action in ("begin", "note", "run"):
            p.add_argument("--phase", required=True)
            p.add_argument("--agent", required=True, help="role or client label")
            p.add_argument("--parent", type=int, help="related event number within this flow")
        if action in ("note", "run", "end"):
            p.add_argument("--artifact", action="append", default=[], help="freeze a file relative to --work (repeatable)")
        if action in ("begin", "run"):
            p.add_argument("--label", required=action == "begin")
        if action == "run":
            p.add_argument("command", nargs=argparse.REMAINDER)
        if action == "note":
            p.add_argument("--kind", choices=NOTES, default="observation")
            p.add_argument("--to-phase", help="destination phase for the generated handoff prompt")
            p.add_argument("--message", required=True)
        if action == "end":
            p.add_argument("--step", required=True, type=int)
            p.add_argument("--agent", help="finishing role (default: starting role)")
            p.add_argument("--outcome", choices=OUTCOMES, required=True)
            p.add_argument("--message")
            p.add_argument("--tokens", type=int, help="known usage for this step")
        if action == "report":
            detail = p.add_mutually_exclusive_group()
            detail.add_argument("--events", action="store_true")
            detail.add_argument("--event", type=int, action="append")
        if action == "seal":
            p.add_argument("--incomplete", action="store_true", help="freeze a trace with unfinished steps")
        p.set_defaults(func=execute)
