"""Exercise enrollment, host hook output and grader reads via the public CLI."""

import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

from factorylib.measurement import LIMIT


ENGINE = Path(__file__).resolve().parents[1] / "factory.py"


def cli(*args, payload=None):
    run = subprocess.run(
        [sys.executable, str(ENGINE), "debug", *map(str, args)],
        input=json.dumps(payload) if payload else None,
        capture_output=True, text=True, timeout=20, check=True,
    )
    return json.loads(run.stdout) if run.stdout else None


class Probe:
    def __init__(self, tmp_path):
        self.work = tmp_path / "exam"
        self.work.mkdir()
        self.group = tmp_path / "outside" / "A"
        self.switch = tmp_path / "operator"
        self.rollout = tmp_path / "synthetic.jsonl"
        self.row("session_meta", {"id": "parent"})
        cli("arm", "--group-dir", self.group, "--stage", "writer", "--work", self.work,
            "--marker", "begin probe")

    def hook(self, kind, **fields):
        base = dict(session_id="parent", cwd=str(self.work), transcript_path=str(self.rollout),
                    hook_event_name=kind)
        return cli("hook", "--group-dir", self.group, "--switch", self.switch,
                   payload={**base, **fields})

    def row(self, kind, body, path=None, timestamp=None):
        with (path or self.rollout).open("a", encoding="utf-8") as out:
            entry = {"timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
                     "type": kind, "payload": body}
            out.write(json.dumps(entry) + "\n")

    def report(self):
        return cli("report", "--group-dir", self.group, "--stage", "writer", "--events")

    def enable(self):
        cli("on", "--switch", self.switch)
        self.hook("UserPromptSubmit", prompt="begin probe\nactual task")

    def seal(self):
        cli("seal", "--stage", "writer", "--group-dir", self.group, "--switch", self.switch)


def test_named_session_only_and_no_backfill_after_disable(tmp_path):
    probe = Probe(tmp_path)
    probe.hook("UserPromptSubmit", prompt="begin probe")
    assert not probe.report()["events"]
    cli("on", "--switch", probe.switch)
    probe.hook("UserPromptSubmit", prompt="ordinary", session_id="outsider")
    probe.hook("UserPromptSubmit", prompt="begin probe", cwd=str(tmp_path))
    assert not probe.report()["actors"]
    probe.enable()
    probe.hook("UserPromptSubmit", prompt="later visible input")
    probe.hook("PostToolUse", session_id="outsider", tool_response="unrelated")
    cli("off", "--switch", probe.switch)
    probe.row("response_item", {"type": "message", "role": "assistant",
                               "content": [{"type": "output_text", "text": "off record"}]})
    cli("on", "--switch", probe.switch)
    probe.hook("Stop", last_assistant_message="off record")
    probe.seal()
    result = probe.report()
    assert "later visible input" in str(result)
    assert "off record" not in str(result) and "unrelated" not in str(result)
    assert result["known_total_tokens"] is None and result["sealed"]


def test_children_exact_content_visibility_and_late_cost(tmp_path):
    probe = Probe(tmp_path)
    probe.row("response_item", {"type": "message", "role": "assistant",
              "content": [{"type": "output_text", "text": "earlier chat"}]})
    probe.row("event_msg", {"type": "token_count", "info": {"total_token_usage": {"total_tokens": 5}}})
    probe.enable()
    for channel in ("analysis", "final"):
        probe.row("response_item", {"type": "message", "role": "assistant", "channel": channel,
                  "content": [{"type": "output_text", "text": "text-" + channel}]})
    probe.row("response_item", {"type": "message", "role": "developer",
                               "content": [{"type": "output_text", "text": "hidden instructions"}]})
    probe.hook("SubagentStart", agent_id="child", agent_type="review")
    child = tmp_path / "child.jsonl"
    probe.row("session_meta", {"id": "child"}, child)
    probe.row("response_item", {"type": "function_call_output", "call_id": "c",
                               "output": "z" * LIMIT}, child)
    probe.hook("SubagentStop", agent_id="child", agent_transcript_path=str(child))
    probe.hook("PostToolUse", tool_response={"exit_code": 7, "stdout": "out", "stderr": "err"})
    probe.hook("PostToolUse", tool_response="combined")
    probe.hook("Stop", last_assistant_message="text-final")
    probe.row("event_msg", {"type": "token_count", "info": {"total_token_usage": {"total_tokens": 17}}})
    probe.seal()
    probe.seal()
    result = probe.report()
    assert {a["id"] for a in result["actors"]} == {"child", "parent"}
    assert result["actors_without_usage"] == ["child"]
    assert result["known_total_tokens"] == 12
    assert "earlier chat" not in str(result) and "text-analysis" not in str(result)
    assert "hidden instructions" not in str(result) and "text-final" in str(result)
    refs = [e for e in result["events"] if e["kind"] == "tool_return"]
    assert len(refs) == 1 and refs[0]["actor"] == "child"
    digest = refs[0]["body"]["result"]["sha256"]
    assert cli("content", "--group-dir", probe.group, "--sha256", digest) == "z" * LIMIT
    tools = [e["body"] for e in result["events"] if e["kind"] == "PostToolUse"]
    assert [e["streams"] for e in tools] == ["separate", "combined_or_unavailable"]
    assert tools[0]["stderr"]["value"] == "err" and "stderr" not in tools[1]
    probe.hook("UserPromptSubmit", prompt="after seal")
    assert "after seal" not in str(probe.report())


def test_foreign_transcript_and_missing_child_are_reported(tmp_path):
    probe = Probe(tmp_path)
    probe.enable()
    probe.hook("SubagentStop", agent_id="child", agent_transcript_path=str(probe.rollout))
    report = probe.report()
    assert "subagent start missing" in str(report)
    assert "unverified transcript identity" in str(report)
    assert report["known_total_tokens"] is None
