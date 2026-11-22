"""Read task-local experience notes selected by a task path or Wiki Git changes."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from . import config, util
from .layout import Layout, build_layout

NOTE = re.compile(r"experience(?:-[^/]+)?\.md\Z")
BOOKMARK = re.compile(r"^Wiki-Experience-Reviewed-Through: ([0-9a-fA-F]{40}|[0-9a-fA-F]{64})\s*$", re.M)


def task_patterns(layout: Layout):
    return (
        (layout.feature_workspace, ("initiatives", "*")),
        (layout.feature_workspace, ("initiatives", "*", "features", "*")),
        (layout.quick_workspace, ("tasks", "*")),
        (layout.refactor_workspace, ("runs", "*")),
    )


def task_root(path: Path, layout: Layout) -> bool:
    for base, shape in task_patterns(layout):
        if path.is_relative_to(base):
            parts = path.relative_to(base).parts
            if len(shape) == len(parts) and all(a == "*" or a == b for a, b in zip(shape, parts)):
                return True
    return False


def git(directory: Path, *args: str, optional: bool = False) -> bytes:
    result = subprocess.run(["git", "-C", str(directory), *args], capture_output=True)
    if result.returncode and not optional:
        raise util.FactoryError(result.stderr.decode(errors="replace").strip() or "Git operation failed")
    return b"" if result.returncode else result.stdout


def scan(work: Path, task: str | None = None) -> dict:
    layout = build_layout(work, config.load_config(work), config.load_local(work))
    bookmark = None
    head = None
    warning = None
    if task:
        directory = (work / task).resolve()
        if not directory.is_dir() or not task_root(directory, layout):
            raise util.FactoryError("--task must identify an existing configured Feature, Quick or Refactor task directory")
        candidates = directory.glob("experience*.md")
    else:
        repo = git(layout.wiki, "rev-parse", "--show-toplevel", optional=True)
        if not repo:
            raise util.FactoryError("global memory-scan requires a Git repository; use --task for an explicit task")
        root = Path(os.fsdecode(repo).strip()).resolve()
        head = git(root, "rev-parse", "--verify", "HEAD", optional=True).decode().strip() or None
        filters = [
            ":(top,glob)" + (base.relative_to(root).joinpath(*shape, "experience*.md")).as_posix()
            for base, shape in task_patterns(layout) if base.is_relative_to(root)
        ]
        if not filters:
            raise util.FactoryError("configured task roots are outside the Wiki Git repository; use --task")
        changed = set()
        if head:
            messages = git(root, "log", "-1", "--format=%B", "--grep=^Wiki-Experience-Reviewed-Through: ").decode("utf-8", errors="replace")
            match = BOOKMARK.search(messages)
            if messages and not match:
                warning = "Ignoring malformed Wiki experience bookmark; reviewing working-tree clues only."
            if match:
                bookmark = match.group(1)
                try:
                    git(root, "merge-base", "--is-ancestor", bookmark, head)
                except util.FactoryError:
                    warning = "Bookmark is not an ancestor of the current Wiki HEAD; reviewing working-tree clues only."
                    bookmark = None
            if bookmark:
                changed.update(git(root, "diff", "--name-only", "-z", bookmark, head, "--", *filters).split(b"\0"))
            changed.update(git(root, "diff", "--name-only", "-z", "HEAD", "--", *filters).split(b"\0"))
        changed.update(git(root, "diff", "--cached", "--name-only", "-z", "--", *filters).split(b"\0"))
        changed.update(git(root, "ls-files", "--others", "--exclude-standard", "-z", "--", *filters).split(b"\0"))
        candidates = (root / os.fsdecode(raw) for raw in changed if raw)
    notes = []
    for path in sorted(candidates):
        if NOTE.fullmatch(path.name) and path.is_file() and task_root(path.resolve().parent, layout) and not path.is_symlink():
            notes.append(str(path))
    return {"reviewed_through": bookmark, "head": head, "files": notes, "warning": warning}


def run(args) -> int:
    result = scan(Path(args.work).expanduser().resolve(), args.task)
    if args.json:
        util.print_json(result)
    else:
        if result["warning"]:
            util.echo_stderr(result["warning"])
        print("Reviewed source revision:", result["head"] or "(unavailable)")
        for path in result["files"]:
            print(path)
    return 0
