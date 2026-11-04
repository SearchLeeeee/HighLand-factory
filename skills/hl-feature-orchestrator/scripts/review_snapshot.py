#!/usr/bin/env python3
"""Capture and verify the exact Git revision and files covered by a review."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any


class SnapshotError(Exception):
    """The review target cannot be captured or no longer matches its snapshot."""


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise SnapshotError(message or f"git {' '.join(args)} failed ({result.returncode})")
    return result


def _repo_root(repo: Path) -> Path:
    result = _git(repo, "rev-parse", "--show-toplevel")
    return Path(result.stdout.decode("utf-8").strip()).resolve()


def _head(repo: Path) -> str:
    result = _git(repo, "rev-parse", "--verify", "HEAD")
    return result.stdout.decode("ascii").strip()


def _relative_path(value: str) -> str:
    normalized = value.replace("\\", "/")
    path = PurePosixPath(normalized)
    if (
        path.is_absolute()
        or PureWindowsPath(normalized).drive
        or "\x00" in normalized
        or not path.parts
        or any(part in ("", ".", "..") for part in path.parts)
    ):
        raise SnapshotError(f"review file must be a normalized repository-relative path: {value!r}")
    return path.as_posix()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _matches_revision(repo: Path, revision: str, relative: str) -> bool:
    tracked = _git(repo, "cat-file", "-e", f"{revision}:{relative}", check=False)
    if tracked.returncode:
        raise SnapshotError(f"review file is not present in {revision}: {relative}")
    result = _git(repo, "diff", "--quiet", revision, "--", relative, check=False)
    if result.returncode not in (0, 1):
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise SnapshotError(message or f"git diff failed for {relative}")
    return result.returncode == 0


def capture_snapshot(repo: Path, files: list[str], output: Path) -> dict[str, Any]:
    root = _repo_root(repo.resolve())
    revision = _head(root)
    paths = sorted({_relative_path(item) for item in files})
    if not paths:
        raise SnapshotError("at least one reviewed file is required")

    records: list[dict[str, str]] = []
    for relative in paths:
        path = root.joinpath(*PurePosixPath(relative).parts)
        if not path.is_file():
            raise SnapshotError(f"review file is missing: {relative}")
        digest = _sha256(path.read_bytes())
        # Git's diff applies checkout normalization (for example, core.autocrlf)
        # while the receipt hashes the bytes the reviewer actually reads.
        if not _matches_revision(root, revision, relative):
            raise SnapshotError(f"review file differs from the frozen revision: {relative}")
        records.append({"path": relative, "sha256": digest})

    receipt: dict[str, Any] = {
        "schema_version": 1,
        "revision": revision,
        "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "files": records,
    }
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    temporary.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output)
    return receipt


def verify_snapshot(repo: Path, snapshot: Path) -> list[str]:
    root = _repo_root(repo.resolve())
    try:
        receipt = json.loads(snapshot.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SnapshotError(f"cannot read review snapshot: {exc}") from exc
    if not isinstance(receipt, dict) or receipt.get("schema_version") != 1:
        raise SnapshotError("unsupported or malformed review snapshot")
    revision = receipt.get("revision")
    records = receipt.get("files")
    if not isinstance(revision, str) or not revision or not isinstance(records, list) or not records:
        raise SnapshotError("review snapshot has no revision or reviewed files")

    problems: list[str] = []
    current_revision = _head(root)
    if current_revision != revision:
        problems.append(f"revision changed: expected {revision}, found {current_revision}")
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("path"), str) or not isinstance(record.get("sha256"), str):
            raise SnapshotError("review snapshot contains a malformed file record")
        relative = _relative_path(record["path"])
        path = root.joinpath(*PurePosixPath(relative).parts)
        if not path.is_file():
            problems.append(f"review file is missing: {relative}")
            continue
        digest = _sha256(path.read_bytes())
        if digest != record["sha256"]:
            problems.append(f"review file changed: {relative}")
    return problems


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)
    capture = subparsers.add_parser("capture", help="capture a frozen review target")
    capture.add_argument("--repo", type=Path, required=True)
    capture.add_argument("--file", action="append", required=True, dest="files")
    capture.add_argument("--output", type=Path, required=True)
    verify = subparsers.add_parser("verify", help="fail if the reviewed target has changed")
    verify.add_argument("--repo", type=Path, required=True)
    verify.add_argument("--snapshot", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.action == "capture":
            receipt = capture_snapshot(args.repo, args.files, args.output)
            print(f"REVIEW SNAPSHOT captured revision={receipt['revision']} files={len(receipt['files'])}")
            return 0
        problems = verify_snapshot(args.repo, args.snapshot)
        if problems:
            print("REVIEW SNAPSHOT STALE; review must be repeated:", file=sys.stderr)
            for problem in problems:
                print(f"- {problem}", file=sys.stderr)
            return 1
        print("REVIEW SNAPSHOT VALID")
        return 0
    except SnapshotError as exc:
        print(f"REVIEW SNAPSHOT ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
