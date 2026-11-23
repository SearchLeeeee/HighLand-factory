"""Exercise portable recording only through the CLI. No hook or chat host is present."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys

from factory import main

ENGINE = Path(__file__).resolve().parents[1] / "factory.py"


def call(work, action, *args, flow="delivery", check=True):
    selector = [] if action == "lookup" else ["--flow", flow]
    return subprocess.run([sys.executable, str(ENGINE), "debug", "flow", action, *selector, *map(str, args)],
                          cwd=work, capture_output=True, check=check, timeout=20)


def data(work, action, *args, **kwargs):
    return json.loads(call(work, action, *args, **kwargs).stdout)


def test_recording_is_opt_in_per_workflow_in_the_same_process(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    gate = ["gate", "workspace", "--work", str(tmp_path)]
    records = tmp_path / ".factory" / "analysis" / "flows"
    debug = ["debug", "flow"]
    first = ["--flow", "first"]
    note = ["--phase", "verification", "--agent", "owner", "--message", "verified"]

    assert main(["init", "--work", str(tmp_path)]) == 0
    assert main(gate) == 0
    assert not records.exists()

    assert main([*debug, "start", *first]) == 0
    assert main([*debug, "note", *first, *note]) == 0
    assert main([*debug, "start", *first]) == 2
    assert main(gate) == 0  # Ordinary work never discovers an open recording.
    assert main([*debug, "seal", *first]) == 0

    # The next independent workflow runs in the same cwd and process with no opt-in.
    assert main(gate) == 0
    assert main([*debug, "note", "--flow", "second", *note]) == 2
    assert main([*debug, "note", *first, *note]) == 2
    assert main([*debug, "start", *first]) == 2
    assert [path.name for path in records.iterdir()] == ["first"]
    assert [e["kind"] for e in data(tmp_path, "report", "--events", flow="first")["events"]] == ["observation"]

    assert main([*debug, "start", "--flow", "third"]) == 0
    assert data(tmp_path, "report", "--events", flow="third")["events"] == []


def test_three_clients_share_only_workflow_context(tmp_path):
    design = tmp_path / "design"
    code = tmp_path / "code"
    design.mkdir()
    code.mkdir()
    records = ("--records", tmp_path / "shared records")
    root = data(design, "start", *records)
    first = Path(root["record_dir"])
    data(code, "start", *records, flow="unrelated")
    spec = design / "acceptance.md"
    spec.write_bytes("首版\r\n".encode())
    issued = data(design, "note", *records, "--phase", "discussion", "--agent", "Claude designer",
                  "--kind", "handoff", "--to-phase", "implementation", "--message", "验收空输入", "--artifact", spec.name)
    handoff = issued["event"]
    assert issued["handoff"].splitlines()[0] == "factory-flow delivery implementation"
    assert f"--parent {handoff}" in issued["handoff"] and str(tmp_path / "shared records") in issued["handoff"]
    impl = data(code, "begin", *records, "--phase", "implementation", "--agent", "Codex worker",
                "--label", "implement empty input", "--parent", handoff)["step"]
    result = call(code, "run", *records, "--phase", "verification", "--agent", "CI", "--parent", impl,
                  "--label", "first delivery", "--artifact", "result.bin", "--", sys.executable, "-c",
                  "import sys; from pathlib import Path; Path('result.bin').write_bytes(b'\\xff'); "
                  "sys.stdout.buffer.write(b'tested'); sys.stderr.buffer.write(b'failure'); sys.exit(7)", check=False)
    assert (result.returncode, result.stdout, result.stderr) == (7, b"tested", b"failure")
    spec.write_text("revised")
    data(design, "note", *records, "--phase", "discussion", "--agent", "Claude designer", "--kind", "decision",
         "--message", "revised spec", "--artifact", spec.name)
    data(code, "end", *records, "--step", impl, "--agent", "second worker", "--outcome", "completed", "--tokens", 20)
    data(code, "seal", *records)
    report = data(code, "report", *records, "--events")
    assert report["sealed"] and report["open_steps"] == []
    assert report["phases"]["implementation"]["agents"] == ["Codex worker", "second worker"]
    assert [r["kind"] for r in report["events"]] == ["handoff", "begin", "begin", "end", "decision", "end"]
    assert [r["parent"] for r in report["events"]] == [None, handoff, impl, 3, None, impl]
    assert report["reported_usage"][0]["tokens"] == 20
    assert {"command_wall", "between_records"} == {s["timing"] for s in report["slowest_steps"]}
    end = data(code, "report", *records, "--event", 4)["events"][0]["body"]
    assert end["stdout"]["object"] == "events/3/stdout.log"
    assert end["stderr"]["object"] == "events/3/stderr.log"
    assert end["exit_code"] == 7 and (first / end["stdout"]["object"]).read_bytes() == b"tested"
    assert (first / end["stderr"]["object"]).read_bytes() == b"failure"
    saved = [(first / a["object"]).read_bytes() for a in report["artifacts"]]
    assert saved == ["首版\r\n".encode(), b"\xff", b"revised"]
    assert [a["object"] for a in report["artifacts"]] == [
        "events/1/artifacts/acceptance.md", "events/4/artifacts/result.bin", "events/5/artifacts/acceptance.md"]
    assert "sha256" not in json.dumps(report) and not (first / "objects").exists()
    assert "session_id" not in json.dumps(report)
    assert not data(design, "report", *records, "--events", flow="unrelated")["events"]
    assert call(code, "note", *records, "--phase", "late", "--agent", "writer", "--message", "late",
                check=False).returncode == 2


def test_partial_flow_parallel_writers_and_retries(tmp_path):
    phase = ("--phase", "review", "--agent", "reviewer")
    data(tmp_path, "start")
    with ThreadPoolExecutor(max_workers=4) as pool:
        ids = list(pool.map(lambda n: data(tmp_path, "begin", *phase, "--label", str(n))["step"], range(4)))
    assert len(set(ids)) == 4
    completed = data(tmp_path, "end", "--step", ids[0], "--outcome", "blocked", "--artifact", "missing.txt")
    assert call(tmp_path, "end", "--step", ids[0], "--outcome", "completed", check=False).returncode == 2
    assert call(tmp_path, "note", *phase, "--parent", 9999, "--message", "invalid", check=False).returncode == 2
    assert call(tmp_path, "note", *phase, "--message", "invalid", "--artifact", "../outside", check=False).returncode == 2
    assert call(tmp_path, "seal", check=False).returncode == 2
    data(tmp_path, "seal", "--incomplete")
    assert data(tmp_path, "seal")["open_steps"] == sorted(ids[1:])
    result = data(tmp_path, "report")
    assert result["review_events"][0]["event"] == completed["event"]
    assert result["artifacts"][0]["status"] == "missing"
    assert len(result["open_steps"]) == 3
    assert "events" not in result


def test_launch_failure_large_streams_and_unknown_flow(tmp_path):
    phase = ("--phase", "verify", "--agent", "external runner")
    assert call(tmp_path, "report", check=False).returncode == 2
    assert not (tmp_path / ".factory").exists()
    data(tmp_path, "start")
    assert call(tmp_path, "run", *phase, "--", str(tmp_path / "missing-program"), check=False).returncode == 127
    script = "import sys; sys.stderr.buffer.write(b'X' * 200000); sys.stdout.buffer.write(b'Y' * 200000)"
    actual = call(tmp_path, "run", *phase, "--", sys.executable, "-c", script)
    assert actual.stdout == b"Y" * 200000 and actual.stderr == b"X" * 200000
    report = data(tmp_path, "report", "--events")
    assert len(report["slowest_steps"]) == 2
    assert report["events"][1]["body"]["outcome"] == "failed" and report["events"][1]["body"]["error"]
    assert report["events"][-1]["body"]["stdout"]["bytes"] == 200000
    assert not report["open_steps"]


def test_same_filename_in_two_folders_at_one_event(tmp_path):
    directory = Path(data(tmp_path, "start")["record_dir"])
    for folder in ("design", "review"):
        (tmp_path / folder).mkdir()
        (tmp_path / folder / "notes.md").write_text(folder)
    event = data(tmp_path, "note", "--phase", "review", "--agent", "reviewer", "--message", "both drafts",
                 "--artifact", "design/notes.md", "--artifact", "review/notes.md")["event"]
    files = data(tmp_path, "report", "--event", event)["events"][0]["body"]["artifacts"]
    assert [(directory / f["object"]).read_text() for f in files] == ["design", "review"]


def register_tasks(registry):
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text(json.dumps({"schema_version": "1.0", "initiatives": [
        {"id": owner, "manifest": f"{owner}/initiative.yaml"} for owner in ("I005", "I006")]}))
    for owner in ("I005", "I006"):
        root = registry.parent / owner
        root.mkdir()
        ids = [owner + suffix for suffix in ("-F01", "-F02")]
        (root / "initiative.yaml").write_text(json.dumps({
            "id": owner, "state": "in-progress", "next_feature_number": 3,
            "initial_decomposition": {"status": "completed", "feature_ids": ids},
            "features": [{"id": ident, "manifest": ident + ".yaml"} for ident in ids]}))
        for ident in ids:
            (root / (ident + ".yaml")).write_text(json.dumps({
                "id": ident, "leaf": True, "phase": "discussion", "wave": 1,
                "state": "completed" if ident == ids[0] else "in-progress",
                "depends_on": [] if ident == ids[0] else [ids[0]], "next_action": {"skill": "hl-feature-discuss"},
                "scope_gate": {"scores": [1] * 8, "hard_gates": [], "verdict": "leaf"}}))


def test_fresh_feature_discussion_recovers_registered_initiative_read_only(tmp_path):
    work = tmp_path / "project"
    work.mkdir()
    assert main(["init", "--work", str(work)]) == 0
    resolved = subprocess.check_output([sys.executable, str(ENGINE), "resolve", "--work", str(work), "--json"])
    register_tasks(Path(json.loads(resolved)["registry"]))
    subprocess.run([sys.executable, str(ENGINE), "gate", "workspace", "--work", str(work)], check=True)
    assert data(work, "lookup", "--scope", "I005-F02")["flow"] is None
    assert not (work / ".factory" / "analysis" / "flow-scopes.sqlite3").exists()
    records = ("--records", tmp_path / "custom records")
    data(work, "start", *records, "--scope", "I005")
    step = data(work, "begin", *records, "--phase", "F01", "--agent", "owner", "--label", "F01")["step"]
    data(work, "end", *records, "--step", step, "--outcome", "completed")
    before = data(work, "report", *records, "--events")
    # A separate process has only the project root and the target selected from the registry.
    found = data(tmp_path, "lookup", "--work", work, "--scope", "I005-F02")
    assert found == {"target": "I005-F02", "flow": "delivery", "scope": "I005", "records": str(records[1])}
    assert data(work, "report", *records, "--events") == before
    assert data(work, "lookup", "--scope", "I006-F02")["flow"] is None
    for unknown in ("F02", "I005-F03"):
        assert call(work, "lookup", "--scope", unknown, check=False).returncode == 2
    assert call(work, "start", "--scope", "I005-F02", flow="overlap", check=False).returncode == 2
    data(work, "note", "--records", found["records"], "--phase", "F02", "--agent", "discuss",
         "--message", "resumed", flow=found["flow"])
    data(work, "seal", *records)
    assert data(work, "lookup", "--scope", "I005-F02")["flow"] is None


def test_leaf_scope_deferred_binding_and_registry_isolation(tmp_path):
    registry = tmp_path / "registry.yaml"
    registry.write_text('{"initiatives":[]}')
    source = ("--registry", registry)
    data(tmp_path, "start", *source, "--pending-scope", "feature")
    register_tasks(registry)
    assert call(tmp_path, "bind", *source, "--scope", "I005", check=False).returncode == 2
    data(tmp_path, "bind", *source, "--scope", "I005-F01")
    data(tmp_path, "bind", *source, "--scope", "I005-F01")
    assert data(tmp_path, "lookup", *source, "--scope", "I005-F01")["flow"] == "delivery"
    assert data(tmp_path, "lookup", *source, "--scope", "I005-F02")["flow"] is None
    assert data(tmp_path, "lookup", *source, "--scope", "I005")["flow"] is None
    assert call(tmp_path, "bind", *source, "--scope", "I005-F02", check=False).returncode == 2
    assert call(tmp_path, "start", *source, "--scope", "I005", flow="parent", check=False).returncode == 2
    other = tmp_path / "other" / "registry.yaml"
    register_tasks(other)
    assert data(tmp_path, "lookup", "--registry", other, "--scope", "I005-F01")["flow"] is None
    data(tmp_path, "start", flow="unscoped")
    assert call(tmp_path, "bind", *source, "--scope", "I005-F02", flow="unscoped", check=False).returncode == 2
    data(tmp_path, "start", *source, "--scope", "I005-F02", flow="sibling")
    assert data(tmp_path, "lookup", *source, "--scope", "I005-F02")["flow"] == "sibling"


def test_concurrent_overlapping_enrollments_and_removed_recording(tmp_path):
    registry = tmp_path / "registry.yaml"
    register_tasks(registry)
    source = ("--registry", registry)

    def start(scope):
        return call(tmp_path, "start", *source, "--scope", scope, flow=scope, check=False)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(start, ("I005", "I005-F02")))
    assert sorted(r.returncode for r in results) == [0, 2]
    winner = json.loads(next(r for r in results if r.returncode == 0).stdout)
    lookup = ("lookup", *source, "--scope", "I005-F02")
    assert data(tmp_path, *lookup)["flow"] == winner["flow"]
    directory = Path(winner["record_dir"])
    directory.rename(tmp_path / "archived")
    assert data(tmp_path, *lookup)["flow"] is None
    data(tmp_path, "start", flow=winner["flow"])  # Same name, new unscoped ledger.
    assert data(tmp_path, *lookup)["flow"] is None
