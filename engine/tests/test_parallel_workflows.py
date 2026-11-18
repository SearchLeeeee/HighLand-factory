"""Independent worktrees can run factory mutations without project reservations."""

from __future__ import annotations

import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1] / "factory.py"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(ENGINE), *args], capture_output=True, text=True, timeout=60)


def git(path: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(path), *args], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def test_linked_worktree_upgrades_can_run_concurrently(tmp_path: Path) -> None:
    primary = tmp_path / "primary"
    initialized = run("init", "--work", str(primary))
    assert initialized.returncode == 0, initialized.stdout + initialized.stderr
    git(primary, "init", "-q")
    git(primary, "add", ".")
    git(primary, "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "baseline")
    worktrees = [tmp_path / "feature-one", tmp_path / "feature-two"]
    for path in worktrees:
        git(primary, "worktree", "add", "-qb", path.name, str(path))
        for name in ("local.yaml", "state.json"):
            shutil.copy2(primary / ".factory" / name, path / ".factory" / name)
    assert len({git(path, "rev-parse", "--git-common-dir") for path in worktrees}) == 1
    # Previous versions left these markers; they no longer reserve the repository.
    legacy = primary / ".git/factory-maintenance.lock"
    legacy.write_text("old reservation\n", encoding="utf-8")
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda path: run("upgrade", "--apply", "--work", str(path)), worktrees))
    for path, result in zip(worktrees, results):
        assert result.returncode == 0, result.stdout + result.stderr
        assert not (path / ".factory/factory-maintenance.lock").exists()
    assert legacy.read_text(encoding="utf-8") == "old reservation\n"


def test_missing_adoption_target_is_not_created(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    code = tmp_path / "code"
    code.mkdir()
    result = run("adopt", "--work", str(missing), "--code", str(code))
    assert result.returncode == 2
    assert "existing work directory" in result.stderr
    assert not missing.exists()
