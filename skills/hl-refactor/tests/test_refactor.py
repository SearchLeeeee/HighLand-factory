"""Behavioral CLI tests against real generated projects and Git repositories."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

FACTORY = Path(__file__).resolve().parents[3]
SCRIPT = FACTORY / "skills/hl-refactor/scripts/refactor.py"


def command(*args: str | Path, expected: int = 0) -> subprocess.CompletedProcess[str]:
    result = subprocess.run([str(arg) for arg in args], text=True, capture_output=True, timeout=45)
    assert result.returncode == expected, result.stdout + result.stderr
    return result


def git(work: Path, *args: str) -> str:
    return command("git", "-C", work, *args).stdout.strip()


def commit(work: Path, message: str = "fixture") -> str:
    git(work, "add", ".")
    git(work, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-m", message)
    return git(work, "rev-parse", "HEAD")


class Project:
    def __init__(self, work: Path, temporary: Path):
        self.work = work
        self.temporary = temporary
        self.run = ""
        self.record: Path | None = None

    def invoke(self, name: str, *args: str | Path, expected: int = 0):
        common = [sys.executable, SCRIPT, name, "--work", self.work]
        if name != "start":
            common += ["--run", self.run]
        result = command(*common, *args, expected=expected)
        if expected:
            return result
        value = json.loads(result.stdout)
        if name == "start":
            self.run = value["run"]
            self.record = Path(value["record"])
        return value

    def start(self, *args: str | Path):
        return self.invoke("start", "--mode", "full", "--actor", "implementer-session", *args)

    def data(self):
        return json.loads(self.record.read_text(encoding="utf-8"))

    def evidence(self, text: str = "Observed behavior, source references, commands, results and limits.\n") -> Path:
        path = self.temporary / "evidence.txt"
        path.write_text(text, encoding="utf-8")
        return path

    def candidates(self, items: list[dict] | None = None, expected: int = 0):
        payload = {"coverage": {"checked": ["Source app entry, its tests and corresponding current Wiki claims in both directions"], "limitations": ["No deployment observation"]}, "candidates": items or []}
        source = self.temporary / "candidates.json"
        source.write_text(json.dumps(payload), encoding="utf-8")
        return self.invoke("candidates", "--input", source, expected=expected)

    def receipt(self, kind: str, verdict: str = "pass", actor: str = "independent-reviewer", expected: int = 0):
        args = ["--kind", kind, "--verdict", verdict, "--actor", actor, "--evidence", self.evidence()]
        if kind == "test":
            args += ["--command", "python -m pytest", "--exit-code", "0" if verdict == "pass" else "1"]
        return self.invoke("record-check", *args, expected=expected)


@pytest.fixture
def project(tmp_path: Path) -> Project:
    answers = tmp_path / "answers.yaml"
    answers.write_text("""project:
  name: Refactor Fixture
  slug: refactor-fixture
  one_liner: A temporary maintenance fixture
  stack: [Python]
  visibility: private
repo:
  mode: mono
  default_branch: main
owners:
  - id: core
    title: Core
    paths: [code]
commands:
  test: [python -m pytest]
  verify: [python -m pytest]
security:
  forbidden_operations: [unapproved production writes]
  sensitive_classes: [credentials]
""", encoding="utf-8")
    work = tmp_path / "work"
    command(sys.executable, FACTORY / "engine/factory.py", "init", "--work", work, "--answers", answers, "--python", sys.executable)
    (work / "code/app.py").write_text("def answer():\n    return 42\n", encoding="utf-8")
    git(work, "init", "-b", "main")
    commit(work)
    return Project(work, tmp_path)


def candidate(identifier: str = "R001", kind: str = "refactor", paths: list[str] | None = None) -> dict:
    return {"id": identifier, "title": "Make the existing answer discoverable", "kind": kind,
            "problem": "Two consumers cannot find the capability through their normal entry", "evidence": ["code:app.py answer() and two caller references"],
            "benefit": "One documented capability entry for future agents", "proposed_action": "Clarify the contract in the selected file", "cost": "Low: inspect both callers, make the edit, run contract tests and review", "risk": "No observable behavior change", "recommendation": "Implement", "paths": paths or ["code:app.py"], "acceptance": ["Answer remains 42; next agent locates the entry"], "depends_on": []}


def selected(project: Project, item: dict | None = None) -> None:
    project.start()
    project.candidates([item or candidate()])
    project.invoke("select", "--ids", "R001", "--decision", "User selected R001 within stated cost")
    project.invoke("begin", "--id", "R001")


def test_full_snapshot_tracks_worktree_bytes_and_excludes_registered_process_roots(project: Project):
    config_path = project.work / ".factory/factory.yaml"
    config = yaml.safe_load(config_path.read_text())
    config["workflow"]["process_workspaces"] = ["maintenance-notes"]
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    process = project.work / "wiki/maintenance-notes"
    process.mkdir()
    (process / "current.md").write_text("not current authority\n")
    (project.work / "code/new.py").write_text("draft = True\n")
    (project.work / "code/app.py").write_text("def answer():\n    return 43\n")
    project.start("--budget", "Inspect one service; edit only selected items")
    record = project.data()
    assert "code:new.py" in record["snapshot"]["files"]
    assert "code:app.py" in record["snapshot"]["dirty_paths"]
    assert not any("maintenance-notes" in key or "refactor-workspace" in key or "factory-maintenance.lock" in key for key in record["snapshot"]["files"])
    (process / "current.md").write_text("process evidence can change\n")
    project.invoke("check")
    assert record["snapshot"]["repos"]["code"]["head"] == git(project.work, "rev-parse", "HEAD")


@pytest.mark.parametrize("initiative_state,phase,feature_state", [("in-progress", "intake", "not-started"), ("completed", "implementation", "completed"), ("cancelled", "intake", "not-started")])
def test_all_initiatives_preflight_rejects_active_or_phase_only_completion(project: Project, initiative_state: str, phase: str, feature_state: str):
    registry = {"initiatives": [{"id": "I001", "state": "completed", "features": []}, {"id": "I002", "state": initiative_state, "features": [{"id": "I002-F01", "phase": phase, "state": feature_state, "leaf": True, "wave": 1, "next_action": "continue"}]}]}
    (project.work / "wiki/feature-workspace/registry.yaml").write_text(yaml.safe_dump(registry))
    result = project.invoke("start", "--mode", "full", "--actor", "fixture", expected=2)
    assert "I002" in result.stderr
    assert not (project.work / ".factory/factory-maintenance.lock").exists()
    records = list((project.work / "wiki/refactor-workspace/runs").glob("*/run.json"))
    assert len(records) == 1 and json.loads(records[0].read_text())["status"] == "blocked"


def test_latest_does_not_guess_last_commit_or_highest_identifier(project: Project):
    result = project.invoke("start", "--mode", "latest", "--actor", "fixture", expected=2)
    assert "--range-evidence" in result.stderr
    assert not (project.work / ".git/factory-maintenance.lock").exists()


def test_latest_explicit_complete_range_preserves_rename_and_deleted_paths(project: Project):
    registry = project.work / "wiki/feature-workspace/registry.yaml"
    registry.write_text(yaml.safe_dump({"initiatives": [{"id": "I001", "state": "completed", "features": []}]}))
    (project.work / "code/obsolete.py").write_text("old = True\n")
    base = commit(project.work, "before initiative")
    (project.work / "code/first_leaf.py").write_text("first_leaf = True\n")
    commit(project.work, "first leaf complete")
    (project.work / "code/app.py").rename(project.work / "code/capability.py")
    (project.work / "code/obsolete.py").unlink()
    commit(project.work, "remaining leaves and integration complete")
    wiki_home = project.work / "wiki/README.md"
    wiki_home.write_text(wiki_home.read_text(encoding="utf-8") + "\nFinal Initiative documentation.\n", encoding="utf-8")
    head = commit(project.work, "final wiki update")
    started = project.invoke("start", "--mode", "latest", "--actor", "fixture", "--initiative", "I001", "--base", base, "--head", head, "--range-evidence", "Closure ledger establishes I001 latest: all Leaves, integration and final Wiki included")
    assert {"code:first_leaf.py", "code:app.py", "code:capability.py", "code:obsolete.py", "wiki:README.md"} <= set(started["scope"]["seed_paths"])
    assert git(project.work, "diff", "--name-only", "HEAD^", "HEAD") == "wiki/README.md"
    assert "code:app.py" not in project.data()["snapshot"]["files"]
    (project.work / "code/capability.py").write_text("def answer():\n    # Current uncommitted clarification.\n    return 42\n")
    project.invoke("refresh", "--reason", "Source changed", expected=2)
    project.invoke("refresh", "--reason", "Repeat the bounded scan", "--range-evidence", "Rechecked I001 is latest and recorded ranges cover every effective Leaf and final Wiki; inspect current uncommitted clarification too")
    assert "code:capability.py" in project.data()["scope"]["current_uncommitted_paths"]
    assert len(project.data()["scope"]["evidence_history"]) == 1
    registry.write_text(yaml.safe_dump({"initiatives": [{"id": "I001", "state": "completed", "features": []}, {"id": "I002", "state": "completed", "features": []}]}))
    rejected = project.invoke("refresh", "--reason", "Cannot adopt a different latest Initiative", "--range-evidence", "Old proof", expected=2)
    assert "changed lifecycle" in rejected.stderr


def test_source_change_stales_selection_and_refresh_invalidates_old_approval(project: Project):
    project.start()
    project.candidates([candidate()])
    (project.work / "code/app.py").write_text("answer = 44\n")
    failed = project.invoke("select", "--ids", "R001", "--decision", "Approve old scan", expected=2)
    assert "stale" in failed.stderr
    project.invoke("refresh", "--reason", "External code changed; repeat semantic scan")
    assert project.data()["selection"] is None
    assert "coverage" not in project.data()
    project.invoke("select", "--ids", "", "--decision", "Old approval cannot survive", expected=2)
    assert "command-failed" in (project.record.parent / "events.jsonl").read_text()


def test_selected_evidence_is_rechecked_before_first_edit_and_expanded_scope(project: Project):
    project.start()
    first = candidate()
    project.candidates([first])
    project.invoke("select", "--ids", "R001", "--decision", "User selected the first item")
    original = (project.work / "code/app.py").read_text()
    (project.work / "code/app.py").write_text("changed_after_selection = True\n")
    project.invoke("begin", expected=2)
    (project.work / "code/app.py").write_text(original)
    project.invoke("begin", "--id", "R001")
    second = candidate("R002", paths=["code:second.py"])
    project.candidates([first, second])
    project.invoke("select", "--ids", "R001,R002", "--decision", "User expands scope to R002 with its full cost")
    (project.work / "code/second.py").write_text("arrived_before_recheck = True\n")
    result = project.invoke("begin", "--id", "R002", expected=2)
    assert "stale" in result.stderr


def test_unrelated_empty_commit_and_process_notes_do_not_stale_evidence(project: Project):
    project.start()
    project.candidates([candidate()])
    git(project.work, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "--allow-empty", "-m", "unrelated metadata")
    (project.record.parent / "scan-note.md").write_text("Evidence captured during scan\n")
    project.invoke("select", "--ids", "R001", "--decision", "Current sources unchanged")
    project.invoke("begin")


def test_snapshot_uses_actual_bytes_when_staged_edit_is_reverted_in_worktree(project: Project):
    source = project.work / "code/app.py"
    original = source.read_bytes()
    actual_blob = git(project.work, "hash-object", "--no-filters", "code/app.py")
    source.write_text("staged_but_not_current = True\n")
    git(project.work, "add", "code/app.py")
    source.write_bytes(original)
    project.start()
    before = project.data()["snapshot"]
    assert before["files"]["code:app.py"] == "100644:" + actual_blob
    assert "code:app.py" in before["dirty_paths"]
    git(project.work, "reset", "HEAD", "--", "code/app.py")
    after = project.invoke("check")
    assert after["snapshot"] == before["content_digest"]


@pytest.mark.parametrize("flag", ["--assume-unchanged", "--skip-worktree"])
def test_index_flags_cannot_hide_actual_source_changes(project: Project, flag: str):
    git(project.work, "config", "core.autocrlf", "true")
    source = project.work / "code/app.py"
    source.write_bytes(b"def answer():\r\n    return 42\r\n")
    assert git(project.work, "diff", "--name-only") == ""
    project.start()
    project.candidates([candidate()])
    git(project.work, "update-index", flag, "code/app.py")
    # Index flags alone must not invalidate identical CRLF working bytes.
    project.invoke("check")
    source.write_text("def answer():\n    return 900\n")
    assert git(project.work, "diff", "--name-only") == ""
    failed = project.invoke("check", expected=2)
    assert "code:app.py" in failed.stderr and "stale" in failed.stderr


def test_sparse_missing_source_is_reported_as_unavailable_coverage(project: Project):
    git(project.work, "update-index", "--skip-worktree", "code/app.py")
    (project.work / "code/app.py").unlink()
    result = project.start()
    assert "code:app.py" not in project.data()["snapshot"]["files"]
    assert any("code:app.py" in limitation and "not available" in limitation for limitation in result["limitations"])


def test_split_latest_requires_and_records_independent_wiki_range(project: Project):
    code = project.temporary / "external-code"
    code.mkdir()
    (code / "app.py").write_text("value = 1\n")
    git(code, "init", "-b", "main")
    code_base = commit(code, "before code initiative")
    (code / "app.py").write_text("value = 2\n")
    code_head = commit(code, "complete code initiative")
    configuration = project.work / ".factory/factory.yaml"
    values = yaml.safe_load(configuration.read_text())
    values["repo"].update(mode="split", code_external=str(code))
    configuration.write_text(yaml.safe_dump(values), encoding="utf-8")
    (project.work / "wiki/feature-workspace/registry.yaml").write_text(yaml.safe_dump({"initiatives": [{"id": "I001", "state": "completed", "features": []}]}))
    wiki_base = commit(project.work, "before wiki final update")
    wiki_home = project.work / "wiki/README.md"
    wiki_home.write_text(wiki_home.read_text(encoding="utf-8") + "\nCurrent capability value is 2.\n", encoding="utf-8")
    wiki_head = commit(project.work, "final wiki update")
    args = ["--mode", "latest", "--actor", "fixture", "--initiative", "I001", "--base", code_base, "--head", code_head, "--range-evidence", "Latest closure ledger includes code and Wiki identities, all Leaves and final integration"]
    rejected = project.invoke("start", *args, expected=2)
    assert "--wiki-base" in rejected.stderr
    accepted = project.invoke("start", *args, "--wiki-base", wiki_base, "--wiki-head", wiki_head)
    assert accepted["scope"]["ranges"]["code"]["head"] == code_head
    assert accepted["scope"]["ranges"]["wiki"]["head"] == wiki_head
    assert {"code:app.py", "wiki:README.md"} <= set(accepted["scope"]["seed_paths"])
    identities = project.data()["snapshot"]["repos"]
    assert identities["code"]["git_common_dir"] != identities["wiki"]["git_common_dir"]


def test_scopes_reject_process_paths_traversal_and_missing_behavior_ack(project: Project):
    project.start()
    for raw in ("wiki:feature-workspace/registry.yaml", "code:../README.md", "code:*.py", "work:code/app.py"):
        project.candidates([candidate(paths=[raw])], expected=2)
    project.candidates([candidate(kind="behavior")])
    project.invoke("select", "--ids", "R001", "--decision", "Missing individual impact decision", expected=2)
    project.invoke("select", "--ids", "R001", "--decision", "User accepts returning a different answer", "--ack-behavior", "R001")


def test_test_cleanup_requires_original_and_continued_protection(project: Project):
    project.start()
    item = candidate(kind="test")
    result = project.candidates([item], expected=2)
    assert "original_protection" in result.stderr
    item.update(original_protection="Old test checked the public answer", continued_protection="Public contract test continues covering the same valid behavior")
    project.candidates([item])


def test_every_editing_unit_checks_scope_and_new_lifecycle_activity(project: Project):
    selected(project)
    (project.work / "code/app.py").write_text("def answer():\n    # Public entry.\n    return 42\n")
    project.invoke("begin", "--id", "R001")
    unexpected = project.work / "code/unapproved.py"
    unexpected.write_text("unauthorized = True\n")
    failed = project.invoke("check", expected=2)
    assert "code:unapproved.py" in failed.stderr
    unexpected.unlink()
    registry = project.work / "wiki/feature-workspace/registry.yaml"
    registry.write_text(yaml.safe_dump({"initiatives": [{"id": "I009", "state": "in-progress", "features": []}]}))
    failed = project.invoke("begin", "--id", "R001", expected=2)
    assert "I009" in failed.stderr


def test_pause_releases_resume_checks_external_source_and_keeps_history(project: Project):
    project.start()
    project.candidates([])
    project.invoke("pause", "--reason", "Release while a different session investigates")
    assert not (project.work / ".factory/factory-maintenance.lock").exists()
    project.invoke("resume")
    project.invoke("pause", "--reason", "Await user")
    (project.work / "code/app.py").write_text("external = True\n")
    project.invoke("resume", expected=2)
    assert not (project.work / ".factory/factory-maintenance.lock").exists()
    assert project.data()["status"] == "paused"
    assert (project.record.parent / "events.jsonl").read_text().count('"action": "pause"') == 2


def test_owned_partial_release_can_pause_and_resume_the_same_run(project: Project):
    selected(project)
    identifier = project.run
    original_snapshot = project.data()["snapshot"]
    (project.work / ".git/factory-maintenance.lock").unlink()
    paused = project.invoke("pause", "--reason", "Recover an interrupted owned release")
    assert paused["released"] is True and project.data()["pause_lease_error"]
    assert not (project.work / ".factory/factory-maintenance.lock").exists()
    resumed = project.invoke("resume")
    assert resumed["status"] == "implementing" and project.data()["id"] == identifier
    assert project.data()["snapshot"] == original_snapshot
    assert project.data()["selection"]["ids"] == ["R001"]
    project.invoke("pause", "--reason", "Recovery exercise complete")


def test_direct_resume_recovers_only_owned_partial_lease_and_rechecks_source(project: Project):
    project.start()
    project.candidates([candidate()])
    identifier = project.run
    old_token = project.data()["lease"]["token"]
    (project.work / ".git/factory-maintenance.lock").unlink()
    project.invoke("resume")
    assert project.data()["id"] == identifier and project.data()["lease"]["token"] != old_token
    assert project.data()["lease_history"][-1]["token"] == old_token
    (project.work / ".git/factory-maintenance.lock").unlink()
    (project.work / "code/app.py").write_text("external_change = True\n")
    rejected = project.invoke("resume", expected=2)
    assert "stale" in rejected.stderr
    assert not (project.work / ".factory/factory-maintenance.lock").exists()
    assert project.data()["candidates"][0]["id"] == "R001"
    assert "partial-lease-released" in (project.record.parent / "events.jsonl").read_text()


def test_partial_recovery_never_removes_a_differently_owned_peer(project: Project):
    project.start()
    primary = project.work / ".factory/factory-maintenance.lock"
    peer = project.work / ".git/factory-maintenance.lock"
    original_primary = primary.read_bytes()
    other = json.loads(peer.read_text())
    other["token"] = "another-owner-token"
    peer.write_text(json.dumps(other))
    project.invoke("pause", "--reason", "Do not override another owner", expected=2)
    assert primary.read_bytes() == original_primary
    assert json.loads(peer.read_text())["token"] == "another-owner-token"
    project.invoke("resume", expected=2)
    assert primary.read_bytes() == original_primary
    assert json.loads(peer.read_text())["token"] == "another-owner-token"


def test_investigation_never_authorizes_source_changes(project: Project):
    selected(project, candidate(kind="investigate"))
    assert project.data()["selection"]["paths"] == []
    (project.work / "code/app.py").write_text("should_not_change = True\n")
    project.invoke("check", expected=2)


def test_finish_requires_fresh_independent_evidence_and_preserves_failures(project: Project):
    selected(project)
    (project.work / "code/app.py").write_text("def answer():\n    # Shared public capability.\n    return 42\n")
    project.invoke("resolve", "--id", "R001", "--outcome", "fixed", "--evidence", project.evidence(), "--note", "Entry clarified; behavior unchanged", "--actual-cost", "One file, one contract check and independent review")
    project.receipt("test", "fail")
    project.receipt("wiki")
    project.receipt("review", actor="implementer-session", expected=2)
    project.receipt("review")
    project.receipt("handoff")
    project.invoke("verify-wiki")
    failed = project.invoke("finish", "--summary", "Cannot finish with failing tests", expected=2)
    assert "test PASS" in failed.stderr
    project.receipt("test")
    (project.work / "code/app.py").write_text("def answer():\n    # Shared, documented public capability.\n    return 42\n")
    project.invoke("finish", "--summary", "Stale evidence cannot finish", expected=2)
    for kind in ("test", "wiki", "review", "handoff"):
        project.receipt(kind)
    project.invoke("verify-wiki")
    result = project.invoke("finish", "--summary", "Selected contract clarification verified; no deployment claim")
    assert result["status"] == "completed"
    assert not (project.work / ".factory/factory-maintenance.lock").exists()
    assert any(item["verdict"] == "fail" for item in project.data()["checks"])


def test_wiki_baseline_failure_can_close_only_as_honest_diagnostic_scan(project: Project):
    (project.work / "wiki/README.md").write_text("# Broken fixture\n\n[missing](missing.md)\n")
    project.start()
    project.candidates([candidate(kind="wiki", paths=["wiki:README.md"])])
    project.invoke("select", "--ids", "", "--decision", "User retains R001 and baseline Wiki failures for a later session")
    project.receipt("wiki", "fail")
    project.invoke("verify-wiki", expected=1)
    project.invoke("finish", "--summary", "Cannot claim verified maintenance", expected=2)
    result = project.invoke("finish", "--scan-only", "--summary", "Diagnostic scan done. R001 and baseline broken links remain; no claim of complete consistency")
    assert result["status"] == "scan-completed"
    assert result["remaining_candidates"] == ["R001"]


def test_scan_only_cannot_hide_source_changes(project: Project):
    selected(project)
    (project.work / "code/app.py").write_text("def answer():\n    return 43\n")
    project.invoke("resolve", "--id", "R001", "--outcome", "fixed", "--evidence", project.evidence(), "--note", "Changed", "--actual-cost", "Small")
    result = project.invoke("finish", "--scan-only", "--summary", "Attempt to skip implementation verification", expected=2)
    assert "Scan-only" in result.stderr


def test_zero_candidate_scan_finishes_without_artificial_edit_or_permission(project: Project):
    project.start()
    project.candidates([])
    project.receipt("wiki")
    project.invoke("verify-wiki")
    result = project.invoke("finish", "--scan-only", "--summary", "Actual covered scope has no worthwhile changes; deployment not observed")
    assert result["changed_paths"] == [] and result["status"] == "scan-completed"
