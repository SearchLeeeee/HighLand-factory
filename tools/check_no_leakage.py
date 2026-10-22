#!/usr/bin/env python3
"""Fail if project-specific leakage appears in generic factory assets.

Scanned roots: skills/, engine/, templates/, install/, packs/.
Private names are kept in an encoded pattern list so they are not spelled out here.

Exit codes: 0 clean, 1 findings, 2 usage error.
"""

from __future__ import annotations

import argparse
import base64
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCANNED_DIRS = ("skills", "engine", "templates", "install", "packs")
TEXT_SUFFIXES = {".md", ".py", ".ps1", ".sh", ".yaml", ".yml", ".json", ".txt", ".tmpl", ".cmd"}


def _dec(value: str) -> str:
    """Decode one private detection pattern (kept encoded on purpose)."""
    return base64.b64decode(value).decode("utf-8")


_ENCODED_RULES = [
    ("aGlnaFtcc18tXT9sYW5kKD8hW1xzXy1dP2ZhY3Rvcnkp", "private project name"),
    ("Y3VzdG9tdHJhZGVy", "private workspace name"),
    ("XGJsbG0td2lraVxi", "legacy wiki folder name"),
    ("XGJpYmtyXGI=", "private vendor name"),
    ("XGJmbm9zXGI=", "private vendor name"),
    ("XGJxbGliXGI=", "private vendor name"),
    ("XGIodGVycmF8bHVuYSlcYg==", "private model tier name"),
]

RULES = [(re.compile(_dec(pattern), re.IGNORECASE), label) for pattern, label in _ENCODED_RULES] + [
    (re.compile(r"\$\{(SKILLS_ROOT|WORKSPACE_ROOT|REPO_CODE|REPO_DOCS|WIKI_ROOT|PYTHON|NODE)\}"), "machine token"),
    (re.compile(r"\b[A-Za-z]:[\\/]"), "absolute Windows path"),
    (re.compile(r"(?<![\w.-])/(home|Users)/"), "absolute POSIX home path"),
]

ALLOW: set[str] = set()


def iter_files(root: Path = ROOT) -> list[Path]:
    files: list[Path] = []
    for name in SCANNED_DIRS:
        base = root / name
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
                if any(part in {"__pycache__", ".pytest_cache"} for part in path.parts):
                    continue
                files.append(path)
    return files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check generic factory assets for project leakage.")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    findings: list[tuple[Path, int, str, str]] = []
    for path in iter_files(root):
        try:
            text = path.read_text(encoding="utf-8-sig", errors="replace")
        except OSError as exc:
            findings.append((path, 0, "read error", str(exc)))
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            if "no-leakage: ignore" in line:
                continue
            for pattern, label in RULES:
                if pattern.search(line):
                    findings.append((path, line_number, label, line.strip()[:160]))

    if findings:
        print(f"LEAKAGE: {len(findings)} finding(s) in generic assets")
        for path, line_number, label, snippet in findings:
            rel = path.relative_to(root).as_posix()
            print(f"  {rel}:{line_number}: {label}: {snippet}")
        return 1
    if args.verbose:
        print(f"clean: scanned {len(iter_files(root))} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
