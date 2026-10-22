#!/usr/bin/env python3
"""Inventory staged Markdown for a semantic wiki merge gate.

The script deterministically classifies a staged file or directory into
eligible Markdown, rule-skipped material (retained-history markers, code-ai and
discussion content, and already-merged Feature sources), and ignored
non-Markdown files, and emits a stable source SHA-256 receipt so a merge can be
reproduced. It is project-agnostic: the source is the only path input, no wiki,
repository, machine, or project location is assumed, and the exit status only
reports whether any eligible Markdown remains.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


SKIP_SEGMENTS = {"code-ai", "discussion", "discussions"}
RETAINED_MARKERS = {
    "retained_history.md",
    "history-route.yaml",
    "history-checksums.sha256",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="List eligible and skipped files for semantic wiki merging."
    )
    parser.add_argument("--source", required=True, help="Staged Markdown file or directory.")
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        dest="output_format",
        help="Output format; JSON is suitable for an inventory receipt.",
    )
    return parser.parse_args()


def has_skip_segment(path: Path) -> bool:
    return any(part.casefold() in SKIP_SEGMENTS for part in path.parts)


def is_merged_feature_directory(directory: Path) -> bool:
    marker = directory / "feature.yaml"
    if not marker.is_file():
        return False
    try:
        content = marker.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return False
    return bool(re.search(r"(?im)^\s*phase\s*:\s*merged\s*$", content))


def is_under_merged_feature(path: Path) -> bool:
    current = path if path.is_dir() else path.parent
    while True:
        if is_merged_feature_directory(current):
            return True
        parent = current.parent
        if parent == current:
            return False
        current = parent


def source_sha256(files: list[Path], root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(files):
        relative = path.name if path == root else path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def inventory_source(source: Path) -> dict[str, object]:
    if source.is_file():
        files = [source]
        root = source.parent
        hash_files = [source]
    else:
        files = sorted(path for path in source.rglob("*") if path.is_file())
        root = source
        hash_files = [path for path in files if path.suffix.casefold() == ".md"]

    eligible: list[Path] = []
    skipped: list[Path] = []
    ignored: list[Path] = []
    merged_history: list[Path] = []

    for path in files:
        scope_path = path.relative_to(root.parent)
        if path.name.casefold() in RETAINED_MARKERS:
            skipped.append(path)
        elif has_skip_segment(scope_path):
            skipped.append(path)
        elif is_under_merged_feature(path):
            skipped.append(path)
            merged_history.append(path)
        elif path.suffix.casefold() != ".md":
            ignored.append(path)
        else:
            eligible.append(path)

    return {
        "source": str(source),
        "source_kind": "file" if source.is_file() else "directory",
        "source_sha256": source_sha256(hash_files, root),
        "source_is_merged_feature": is_under_merged_feature(source),
        "eligible": [str(path) for path in eligible],
        "skipped": [str(path) for path in skipped],
        "merged_history": [str(path) for path in merged_history],
        "ignored": [str(path) for path in ignored],
    }


def print_text(result: dict[str, object]) -> None:
    print(f"Source: {result['source']}")
    print(f"Source SHA-256: {result['source_sha256']}")
    print("")
    print("Eligible Markdown files:")
    for path in result["eligible"]:
        print(f"- {path}")
    if not result["eligible"]:
        print("- <none>")
    print("")
    print("Skipped by rule:")
    for path in result["skipped"]:
        print(f"- {path}")
    if not result["skipped"]:
        print("- <none>")
    print("")
    print("Ignored non-Markdown files:")
    for path in result["ignored"]:
        print(f"- {path}")
    if not result["ignored"]:
        print("- <none>")


def main() -> int:
    args = parse_args()
    source = Path(args.source).expanduser().resolve(strict=False)
    if not source.exists():
        print(f"ERROR: source path does not exist: {source}", file=sys.stderr)
        return 1

    result = inventory_source(source)
    if args.output_format == "json":
        print(json.dumps(result, ensure_ascii=True, indent=2))
    else:
        print_text(result)
    return 0 if result["eligible"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
