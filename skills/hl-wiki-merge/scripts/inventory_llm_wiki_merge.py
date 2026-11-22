#!/usr/bin/env python3
"""Inventory staged Markdown, or current-state Wiki Markdown when requested.

The script deterministically classifies a staged file or directory into
eligible Markdown, rule-skipped material (retained-history markers, code-ai and
discussion content, and already-merged Feature sources), and ignored
non-Markdown files, and emits a stable source SHA-256 receipt so a merge can be
reproduced. It is project-agnostic: the source is the only path input, no wiki,
repository, machine, or project location is assumed, and the exit status only
reports whether any eligible Markdown remains.

``--wiki-root`` selects current-state inventory instead of a staged source.
That mode uses the shared explicit process-workspace registry, does not read
excluded content, and hashes only the included current-state Markdown corpus.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "engine"))
from factorylib.workspaces import (  # noqa: E402
    process_workspace_names,
    process_workspace_roots,
    project_config_for_wiki,
)


SKIP_SEGMENTS = {"code-ai", "discussion", "discussions"}
RETAINED_MARKERS = {
    "retained_history.md",
    "history-route.yaml",
    "history-checksums.sha256",
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="List eligible and skipped files for semantic wiki merging."
    )
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--source", help="Explicit staged Markdown file or directory; preserves existing merge rules.")
    scope.add_argument("--wiki-root", help="Inventory current-state Wiki Markdown with registered process roots excluded.")
    parser.add_argument(
        "--process-workspace", action="append", default=[],
        help="Additional explicit Wiki-relative process directory; only with --wiki-root; repeatable.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        dest="output_format",
        help="Output format; JSON is suitable for an inventory receipt.",
    )
    args = parser.parse_args(argv)
    if args.process_workspace and not args.wiki_root:
        parser.error("--process-workspace requires --wiki-root")
    return args


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

    from factorylib import config
    from factorylib.layout import build_layout
    from factorylib.memory import NOTE, task_root

    project = next((parent for parent in (root, *root.parents) if config.config_path(parent).is_file()), None)
    layout = build_layout(project, config.load_config(project)) if project else None
    for path in files:
        if layout and NOTE.fullmatch(path.name) and task_root(path.resolve().parent, layout):
            skipped.append(path)
            continue
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


def inventory_wiki(
    wiki_root: Path,
    project_config: dict[str, Any] | None = None,
    *,
    process_workspaces: tuple[str, ...] | list[str] = (),
) -> dict[str, object]:
    """Inventory canonical Markdown without treating process history as truth."""
    root = wiki_root.expanduser().resolve(strict=False)
    if not root.is_dir():
        raise ValueError(f"Wiki root is not a directory: {root}")
    config = project_config if project_config is not None else project_config_for_wiki(root)
    names = process_workspace_names(config, additional=process_workspaces)
    roots = process_workspace_roots(root, config, additional=process_workspaces)
    eligible: list[Path] = []
    skipped: list[Path] = []
    ignored: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(path.resolve(strict=False).is_relative_to(process_root) for process_root in roots):
            skipped.append(path)
        elif path.suffix.casefold() != ".md":
            ignored.append(path)
        else:
            eligible.append(path)
    return {
        "source": str(root),
        "source_kind": "canonical-wiki",
        "source_sha256": source_sha256(eligible, root),
        "source_is_merged_feature": False,
        "process_workspaces": list(names),
        "eligible": [str(path) for path in eligible],
        "skipped": [str(path) for path in skipped],
        "merged_history": [],
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


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    source = Path(args.wiki_root or args.source).expanduser().resolve(strict=False)
    if not source.exists():
        print(f"ERROR: source path does not exist: {source}", file=sys.stderr)
        return 1

    try:
        result = (
            inventory_wiki(source, process_workspaces=args.process_workspace)
            if args.wiki_root else inventory_source(source)
        )
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if args.output_format == "json":
        print(json.dumps(result, ensure_ascii=True, indent=2))
    else:
        print_text(result)
    return 0 if result["eligible"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
