"""Executable mutual exclusion across factory entry points and repositories."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pytest

from factorylib import maintenance

ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / "engine" / "factory.py"
STATE = ROOT / "skills" / "hl-feature-workspace" / "scripts" / "feature_workspace.py"


def run(script: Path, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True, env=env, timeout=60)


def git(path: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(path), *args], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def configured(path: Path, code: Path | None = None) -> Path:
    (path / ".factory").mkdir(parents=True)
    repo = {"mode": "split" if code else "mono", "code_path": "code", "wiki_path": "wiki"}
    if code:
        repo["code_external"] = str(code)
    (path / ".factory" / "factory.yaml").write_text(json.dumps({"repo": repo}), encoding="utf-8")
    return path


def test_atomic_acquisition_has_one_owner(tmp_path: Path) -> None:
    work = configured(tmp_path / "work")
    barrier = Barrier(2)

    def contender(name: str):
        barrier.wait(timeout=10)
        try:
            return maintenance.acquire(work, name, "workflow")
        except maintenance.MaintenanceError:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(contender, ("first", "second")))
    winners = [result for result in results if result]
    assert len(winners) == 1
    lease = winners[0]
    maintenance.check_access(work, lease["token"])
    with pytest.raises(maintenance.MaintenanceError):
        maintenance.check_access(work)
    with pytest.raises(maintenance.MaintenanceError):
        maintenance.release(work, "wrong-owner")
    assert all(Path(path).is_file() for path in lease["lock_paths"])
    maintenance.release(work, lease["token"])
    assert not maintenance.status(work)


def test_nested_guard_borrows_token_and_exception_releases_owned_lease(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv(maintenance.TOKEN_ENV, raising=False)
    work = configured(tmp_path / "work")
    with pytest.raises(RuntimeError, match="operation failed"):
        with maintenance.mutation_guard(work, purpose="workflow") as outer:
            with maintenance.mutation_guard(work) as inner:
                assert inner["token"] == outer["token"]
            maintenance.check_access(work, outer["token"])
            raise RuntimeError("operation failed")
    assert not maintenance.status(work)
    assert maintenance.TOKEN_ENV not in os.environ
    with pytest.raises(maintenance.MaintenanceError, match="no active reservation"):
        maintenance.check_access(work, outer["token"])


def test_split_repos_sharing_code_cannot_reserve_concurrently(tmp_path: Path) -> None:
    code = tmp_path / "shared-code"
    code.mkdir()
    git(code, "init", "-q")
    first = configured(tmp_path / "first", code)
    second = configured(tmp_path / "second", code)
    lease = maintenance.acquire(first, "refactor-one", "refactor:scan")
    with pytest.raises(maintenance.MaintenanceError):
        maintenance.acquire(second, "workflow-two", "workflow")
    assert not (second / ".factory" / maintenance.LOCK_NAME).exists()
    maintenance.release(first, lease["token"])
    other = maintenance.acquire(second, "workflow-two", "workflow")
    maintenance.release(second, other["token"])


def test_linked_worktrees_share_repository_lock(tmp_path: Path) -> None:
    primary = configured(tmp_path / "primary")
    git(primary, "init", "-q")
    git(primary, "add", ".factory/factory.yaml")
    git(primary, "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "baseline")
    linked = tmp_path / "linked"
    git(primary, "worktree", "add", "-qb", "linked", str(linked))
    lease = maintenance.acquire(primary, "main-worktree", "refactor:scan")
    with pytest.raises(maintenance.MaintenanceError):
        maintenance.acquire(linked, "linked-worktree", "workflow")
    maintenance.release(primary, lease["token"])
    assert not (linked / ".factory" / maintenance.LOCK_NAME).exists()


def test_partial_or_corrupt_lease_fails_closed(tmp_path: Path) -> None:
    work = configured(tmp_path / "work")
    git(work, "init", "-q")
    lease = maintenance.acquire(work, "owner", "refactor")
    shared = next(Path(path) for path in lease["lock_paths"] if ".git" in Path(path).parts)
    original = shared.read_bytes()
    shared.unlink()
    with pytest.raises(maintenance.MaintenanceError, match="incomplete"):
        maintenance.check_access(work, lease["token"])
    shared.write_text("interrupted write", encoding="utf-8")
    with pytest.raises(maintenance.MaintenanceError, match="unreadable"):
        maintenance.check_access(work, lease["token"])
    with pytest.raises(maintenance.MaintenanceError, match="unreadable"):
        maintenance.release(work, lease["token"])
    shared.write_bytes(original)
    maintenance.release(work, lease["token"])


def test_exact_owner_can_release_interrupted_lock_transaction(tmp_path: Path) -> None:
    work = configured(tmp_path / "work")
    git(work, "init", "-q")
    lease = maintenance.acquire(work, "owner", "workflow")
    paths = [Path(path) for path in lease["lock_paths"]]
    primary = work / ".factory" / maintenance.LOCK_NAME
    shared = next(path for path in paths if path != primary)
    shared.unlink()  # interrupted release, primary is retained until last
    maintenance.release(work, lease["token"])
    assert not maintenance.status(work)
    lease = maintenance.acquire(work, "owner", "workflow")
    primary.unlink()  # a partial acquisition can retain only another resource
    maintenance.release(work, lease["token"])
    assert not maintenance.status(work)


def test_recovery_does_not_remove_new_owner_of_previously_missing_peer(tmp_path: Path, monkeypatch) -> None:
    code = tmp_path / "code"
    code.mkdir()
    git(code, "init", "-q")
    first = configured(tmp_path / "first", code)
    second = configured(tmp_path / "second", code)
    old = maintenance.acquire(first, "old", "workflow")
    shared = code / ".git" / maintenance.LOCK_NAME
    shared.unlink()
    read = maintenance._read
    replacement = {}

    def acquire_between_check_and_delete(path: Path):
        value = read(path)
        if path == shared and value is None and not replacement:
            replacement.update(maintenance.acquire(second, "new", "workflow"))
        return value

    monkeypatch.setattr(maintenance, "_read", acquire_between_check_and_delete)
    maintenance.release(first, old["token"])
    maintenance.check_access(second, replacement["token"])
    maintenance.release(second, replacement["token"])


def test_cli_status_redacts_token_and_release_requires_owner(tmp_path: Path) -> None:
    work = configured(tmp_path / "work")
    acquired = run(ENGINE, "maintenance-lock", "--work", str(work), "--action", "acquire", "--owner", "session", "--purpose", "workflow")
    assert acquired.returncode == 0, acquired.stderr
    lease = json.loads(acquired.stdout)
    status = run(ENGINE, "maintenance-lock", "--work", str(work), "--action", "status")
    assert status.returncode == 0
    assert lease["token"] not in status.stdout
    denied = run(ENGINE, "maintenance-check", "--work", str(work))
    assert denied.returncode != 0
    allowed = run(ENGINE, "maintenance-check", "--work", str(work), "--token", lease["token"])
    assert allowed.returncode == 0, allowed.stderr
    released = run(ENGINE, "maintenance-lock", "--work", str(work), "--action", "release", "--token", lease["token"])
    assert released.returncode == 0, released.stderr


def test_lifecycle_writes_rejected_even_with_refactor_token(tmp_path: Path) -> None:
    work = configured(tmp_path / "work")
    registry = work / "wiki" / "feature-workspace" / "registry.yaml"
    registry.parent.mkdir(parents=True)
    registry.write_text("version: 1\ninitiatives: []\n", encoding="utf-8")
    feature = registry.parent / "feature.yaml"
    feature.write_text("id: untouched\n", encoding="utf-8")
    before = feature.read_bytes()
    lease = maintenance.acquire(work, "refactor-run", "refactor:scan")
    for env in (dict(os.environ), {**os.environ, maintenance.TOKEN_ENV: lease["token"]}):
        result = run(STATE, "transition", "--feature", str(feature), "--state", "completed", env=env)
        assert result.returncode != 0
        assert "refactor" in result.stderr
        assert feature.read_bytes() == before
    read = run(STATE, "report", "--registry", str(registry))
    assert read.returncode == 0, read.stdout + read.stderr
    maintenance.release(work, lease["token"])


def test_engine_mutation_blocked_but_readonly_commands_work(tmp_path: Path) -> None:
    work = tmp_path / "work"
    initialized = run(ENGINE, "init", "--work", str(work))
    assert initialized.returncode == 0, initialized.stdout + initialized.stderr
    lease = maintenance.acquire(work, "refactor-run", "refactor:scan")
    before = (work / ".factory" / "factory.yaml").read_bytes()
    for args in (("upgrade",), ("upgrade", "--apply"), ("init", "--force")):
        denied = run(ENGINE, *args, "--work", str(work))
        assert denied.returncode != 0
        assert "reserved" in denied.stderr or "reservation" in denied.stderr
    assert (work / ".factory" / "factory.yaml").read_bytes() == before
    for args in (("status", "--json"), ("resolve", "--json"), ("gate", "all"), ("upgrade", "--check")):
        result = run(ENGINE, *args, "--work", str(work))
        assert result.returncode == 0, result.stdout + result.stderr
    maintenance.release(work, lease["token"])


def test_missing_adoption_target_is_not_created_by_guard(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    code = tmp_path / "code"
    code.mkdir()
    result = run(ENGINE, "adopt", "--work", str(missing), "--code", str(code))
    assert result.returncode != 0
    assert not missing.exists()


def test_linked_manifest_cannot_bypass_project_lease(tmp_path: Path) -> None:
    work = configured(tmp_path / "work")
    external = tmp_path / "external-manifests"
    external.mkdir()
    feature = external / "feature.yaml"
    feature.write_text("id: untouched\n", encoding="utf-8")
    linked = work / "linked-manifests"
    if os.name == "nt":
        created = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(linked), str(external)],
            capture_output=True, text=True, timeout=30,
        )
        assert created.returncode == 0, created.stdout + created.stderr
    else:
        linked.symlink_to(external, target_is_directory=True)
    assert maintenance.find_work(linked / "feature.yaml") == work
    lease = maintenance.acquire(work, "refactor-run", "refactor:scan")
    before = feature.read_bytes()
    try:
        denied = run(STATE, "transition", "--feature", str(linked / "feature.yaml"), "--state", "completed")
        assert denied.returncode != 0
        assert "reservation already held by refactor-run" in denied.stderr
        assert feature.read_bytes() == before
    finally:
        maintenance.release(work, lease["token"])
