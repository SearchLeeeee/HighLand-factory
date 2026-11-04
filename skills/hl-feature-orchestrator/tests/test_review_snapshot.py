from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "review_snapshot.py"
SPEC = importlib.util.spec_from_file_location("review_snapshot", SCRIPT)
assert SPEC and SPEC.loader
review_snapshot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review_snapshot)


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.name", "Factory Test")
    git(repo, "config", "user.email", "factory-test@example.invalid")
    source = repo / "src" / "module.py"
    source.parent.mkdir()
    source.write_text("VALUE = 1\n", encoding="utf-8")
    git(repo, "add", "src/module.py")
    git(repo, "commit", "-m", "initial")
    return repo


def test_capture_and_verify_same_frozen_revision(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    receipt = tmp_path / "evidence" / "review-snapshot.json"

    captured = review_snapshot.capture_snapshot(repo, ["src/module.py"], receipt)
    assert captured["revision"] == git(repo, "rev-parse", "HEAD")
    assert captured["files"] == [
        {
            "path": "src/module.py",
            "sha256": review_snapshot._sha256((repo / "src" / "module.py").read_bytes()),
        }
    ]
    assert review_snapshot.verify_snapshot(repo, receipt) == []


def test_source_edit_invalidates_snapshot(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    receipt = tmp_path / "review-snapshot.json"
    review_snapshot.capture_snapshot(repo, ["src/module.py"], receipt)

    (repo / "src" / "module.py").write_text("VALUE = 2\n", encoding="utf-8")
    assert review_snapshot.verify_snapshot(repo, receipt) == ["review file changed: src/module.py"]


def test_new_commit_invalidates_snapshot_even_if_reviewed_file_is_unchanged(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    receipt = tmp_path / "review-snapshot.json"
    review_snapshot.capture_snapshot(repo, ["src/module.py"], receipt)

    (repo / "README.md").write_text("A new commit during review.\n", encoding="utf-8")
    git(repo, "add", "README.md")
    git(repo, "commit", "-m", "concurrent change")
    problems = review_snapshot.verify_snapshot(repo, receipt)
    assert len(problems) == 1
    assert problems[0].startswith("revision changed: expected ")


def test_capture_rejects_uncommitted_reviewed_file(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    (repo / "src" / "module.py").write_text("VALUE = 2\n", encoding="utf-8")

    with pytest.raises(review_snapshot.SnapshotError, match="differs from the frozen revision"):
        review_snapshot.capture_snapshot(repo, ["src/module.py"], tmp_path / "snapshot.json")


def test_capture_rejects_untracked_file(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    (repo / "new.py").write_text("VALUE = 2\n", encoding="utf-8")

    with pytest.raises(review_snapshot.SnapshotError, match="not present in"):
        review_snapshot.capture_snapshot(repo, ["new.py"], tmp_path / "snapshot.json")


def test_capture_rejects_paths_outside_repository(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)

    with pytest.raises(review_snapshot.SnapshotError, match="repository-relative"):
        review_snapshot.capture_snapshot(repo, ["../outside.py"], tmp_path / "snapshot.json")


def test_cli_fails_closed_when_target_changes_during_review(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    receipt = tmp_path / "review-snapshot.json"
    capture = subprocess.run(
        [
            sys.executable, str(SCRIPT), "capture", "--repo", str(repo),
            "--file", "src/module.py", "--output", str(receipt),
        ],
        capture_output=True,
        text=True,
    )
    assert capture.returncode == 0, capture.stdout + capture.stderr

    (repo / "src" / "module.py").write_text("VALUE = 2\n", encoding="utf-8")
    verify = subprocess.run(
        [
            sys.executable, str(SCRIPT), "verify", "--repo", str(repo),
            "--snapshot", str(receipt),
        ],
        capture_output=True,
        text=True,
    )
    assert verify.returncode == 1
    assert "REVIEW SNAPSHOT STALE" in verify.stderr
    assert "review file changed: src/module.py" in verify.stderr
