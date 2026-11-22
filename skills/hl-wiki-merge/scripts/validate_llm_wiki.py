#!/usr/bin/env python3
"""Validate deterministic Markdown navigation for a project-agnostic long-term wiki.

The gate requires a single README.md home, rejects competing home pages, broken
local links/anchors, Obsidian wikilinks, deleted legacy routes, orphans, and MOC
routes deeper than three hops, and isolates explicitly registered process
workspaces; it recognizes only ATX headings and same-line inline
links/images (code is masked, HTML navigation and setext headings are not
edges), existence-checks local images without making them edges, never fetches
external URLs, and takes its root only from the required ``--wiki-root`` flag so
that no project or machine path is assumed.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "engine"))
from factorylib.workspaces import (  # noqa: E402
    process_workspace_names,
    process_workspace_roots,
    project_config_for_wiki,
)

HOME = "README.md"
COMPETING_HOME_NAMES = {"home.md", "index.md", "_index.md"}
EXTERNAL_SCHEMES = {"http", "https", "mailto", "tel", "data", "ftp", "ftps"}
BACKTICK = chr(96)
FENCE_RE = re.compile(r"^[ ]{0,3}((?:" + re.escape(BACKTICK) + r"){3,}|~{3,})(.*)$")
ATX_RE = re.compile(r"^[ ]{0,3}#{1,6}[ \t]+(.+?)[ \t]*#*[ \t]*$")
WIKILINK_RE = re.compile(r"\[\[[^\]\r\n]+\]\]")
LEGACY_RE = re.compile(
    r"(?i)(?<![\w-])(?:decisions|discussions)[\\/]"
    r"|(?<![\w-])04-open-questions\.md(?![\w-])"
)
HTML_ANCHOR_RE = re.compile(
    r"""<a\s+[^>]*(?:id|name)\s*=\s*["']([^"']+)["'][^>]*>""", re.I
)


@dataclass(frozen=True, order=True)
class Diagnostic:
    severity: str
    code: str
    path: str
    line: int
    message: str


@dataclass(frozen=True)
class MarkdownLink:
    destination: str
    line: int
    is_image: bool


@dataclass
class ValidationResult:
    errors: list[Diagnostic]
    warnings: list[Diagnostic]
    files_scanned: int
    files_excluded: int
    links_checked: int
    process_workspaces: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.errors


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate long-term wiki Markdown navigation.",
        epilog=(
            "Built-in and explicitly registered process-workspace roots are excluded. External URLs are not "
            "fetched. Non-ASCII anchors are warning-only in this version."
        ),
    )
    parser.add_argument(
        "--wiki-root", type=Path, required=True,
        help="Path to the long-term wiki root (required).",
    )
    parser.add_argument(
        "--process-workspace", action="append", default=[],
        help="Additional explicit directory relative to the Wiki; repeatable. Project config is read automatically.",
    )
    parser.add_argument(
        "--format", choices=("text", "json"), default="text",
        dest="output_format", help="Output format for a machine-readable validation receipt.",
    )
    return parser.parse_args(argv)


def _is_excluded(path: Path, roots: tuple[Path, ...]) -> bool:
    target = path.resolve(strict=False)
    return any(target.is_relative_to(root) for root in roots)


def _process_reference_pattern(root: Path, names: tuple[str, ...]) -> re.Pattern[str]:
    alternatives = "|".join(re.escape(name).replace("/", r"[\\/]") for name in names)
    # Links are also checked after path resolution below. This catches bare
    # discovery instructions without treating nested similarly named folders
    # (e.g. concepts/feature-workspace/) as registered process roots.
    return re.compile(
        r"(?<![\w./\\-])(?:\.\.?[\\/])*(?:"
        + re.escape(root.name) + r"[\\/])?(?:" + alternatives + r")[\\/]"
    )


def _mask_fences(text: str) -> str:
    output: list[str] = []
    fence_char = ""
    fence_length = 0
    for line in text.splitlines(keepends=True):
        body = line.rstrip("\r\n")
        ending = line[len(body):]
        match = FENCE_RE.match(body)
        if not fence_char:
            if match:
                fence_char = match.group(1)[0]
                fence_length = len(match.group(1))
                output.append(" " * len(body) + ending)
            else:
                output.append(line)
            continue
        stripped = body.lstrip(" ")
        leading = len(body) - len(stripped)
        closes = (
            leading <= 3
            and stripped.startswith(fence_char * fence_length)
            and not stripped.rstrip(fence_char).strip()
        )
        output.append(" " * len(body) + ending)
        if closes:
            fence_char = ""
            fence_length = 0
    return "".join(output)


def _mask_inline_code(text: str) -> str:
    chars = list(text)
    index = 0
    while index < len(chars):
        if chars[index] != BACKTICK:
            index += 1
            continue
        end = index
        while end < len(chars) and chars[end] == BACKTICK:
            end += 1
        marker = BACKTICK * (end - index)
        close = text.find(marker, end)
        if close < 0:
            index = end
            continue
        for position in range(index, close + len(marker)):
            if chars[position] not in "\r\n":
                chars[position] = " "
        index = close + len(marker)
    return "".join(chars)


def _line(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _closing(text: str, start: int, opener: str, closer: str) -> int | None:
    depth = 1
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == opener:
            depth += 1
        elif char == closer:
            depth -= 1
            if depth == 0:
                return index
        elif char in "\r\n":
            return None
    return None


def _destination(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    if value.startswith("<"):
        escaped = False
        for index, char in enumerate(value[1:], 1):
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == ">":
                return value[1:index]
        return ""
    escaped = False
    depth = 0
    for index, char in enumerate(value):
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == "(":
            depth += 1
        elif char == ")" and depth:
            depth -= 1
        elif char.isspace() and depth == 0:
            return value[:index]
    return value


def _links(text: str) -> list[MarkdownLink]:
    found: list[MarkdownLink] = []
    index = 0
    while index < len(text):
        image = text.startswith("![", index)
        label_start = index + (2 if image else 1)
        if (not image and text[index] != "[") or label_start > len(text):
            index += 1
            continue
        label_end = _closing(text, label_start, "[", "]")
        if label_end is None:
            index += 1
            continue
        cursor = label_end + 1
        while cursor < len(text) and text[cursor] in " \t":
            cursor += 1
        if cursor >= len(text) or text[cursor] != "(":
            index = label_end + 1
            continue
        destination_end = _closing(text, cursor + 1, "(", ")")
        if destination_end is None:
            index = label_end + 1
            continue
        found.append(MarkdownLink(
            _destination(text[cursor + 1:destination_end]), _line(text, index), image
        ))
        index = destination_end + 1
    return found


def _unescape(value: str) -> str:
    return re.sub(r"\\([\\*{}\[\]()#+.!_<>\-])", r"\1", value)


def _external(destination: str) -> bool:
    if destination.startswith("//"):
        return True
    if re.match(r"^[A-Za-z]:[\\/]", destination):
        return False
    scheme = urlsplit(destination).scheme.casefold()
    return bool(scheme) and (scheme in EXTERNAL_SCHEMES or len(scheme) > 1)


def _split(destination: str) -> tuple[str, str]:
    destination = _unescape(destination.strip())
    if destination.startswith("#"):
        return "", unquote(destination[1:])
    parsed = urlsplit(destination)
    return unquote(parsed.path), unquote(parsed.fragment)


def _raw_target(root: Path, source: Path, destination: str) -> Path:
    normalized = destination.replace("\\", "/")
    if re.match(r"^[A-Za-z]:/", normalized):
        candidate = Path(normalized)
    elif normalized.startswith("/"):
        candidate = root / normalized.lstrip("/")
    else:
        candidate = source.parent / normalized
    return candidate


def _resolve(root: Path, source: Path, destination: str) -> tuple[Path, str | None]:
    candidate = _raw_target(root, source, destination).resolve(strict=False)
    try:
        relative = candidate.relative_to(root.resolve(strict=False)).as_posix()
    except ValueError:
        relative = None
    return candidate, relative


def _slug(heading: str) -> str:
    heading = re.sub(r"<[^>]+>", "", heading)
    heading = re.sub(r"[*_~]", "", heading).strip().casefold()
    heading = "".join(c for c in heading if c.isalnum() or c in " -_")
    return re.sub(r"[ \t]+", "-", heading)


def _anchors(text: str) -> set[str]:
    anchors = {match.group(1) for match in HTML_ANCHOR_RE.finditer(text)}
    counts: dict[str, int] = {}
    for line in _mask_fences(text).splitlines():
        match = ATX_RE.match(_mask_inline_code(line))
        if not match:
            continue
        slug = _slug(match.group(1))
        count = counts.get(slug, 0)
        counts[slug] = count + 1
        anchors.add(slug if count == 0 else f"{slug}-{count}")
    return anchors


def _diag(severity: str, code: str, path: str, line: int, message: str) -> Diagnostic:
    return Diagnostic(severity, code, path, line, message)


def validate_wiki(
    wiki_root: Path,
    project_config: dict[str, Any] | None = None,
    *,
    process_workspaces: tuple[str, ...] | list[str] = (),
) -> ValidationResult:
    root = wiki_root.expanduser().resolve(strict=False)
    errors: list[Diagnostic] = []
    warnings: list[Diagnostic] = []
    if not root.is_dir():
        errors.append(_diag("ERROR", "WIKI_ROOT_MISSING", ".", 0, f"not a directory: {root}"))
        return ValidationResult(errors, warnings, 0, 0, 0)

    try:
        config = project_config if project_config is not None else project_config_for_wiki(root)
        names = process_workspace_names(config, additional=process_workspaces)
        process_roots = process_workspace_roots(root, config, additional=process_workspaces)
    except ValueError as exc:
        errors.append(_diag("ERROR", "PROCESS_WORKSPACE_CONFIG", ".", 0, str(exc)))
        return ValidationResult(errors, warnings, 0, 0, 0)
    discovery_names = tuple(
        item.relative_to(root).as_posix() if item.is_relative_to(root) else item.parent.name + "/" + item.name
        for item in process_roots
    )
    process_ref_re = _process_reference_pattern(root, discovery_names)

    included: dict[str, Path] = {}
    excluded = 0
    markdown_files = (
        path for path in root.rglob("*")
        if path.is_file() and path.suffix.casefold() == ".md"
    )
    for path in sorted(markdown_files, key=lambda p: p.as_posix().casefold()):
        relative_path = path.relative_to(root)
        if _is_excluded(path, process_roots):
            excluded += 1
        else:
            included[relative_path.as_posix()] = path

    if HOME not in included:
        errors.append(_diag("ERROR", "HOME_MISSING", HOME, 0, "primary home is missing"))
    for relative in included:
        pure = PurePosixPath(relative)
        if len(pure.parts) == 1 and pure.name.casefold() in COMPETING_HOME_NAMES:
            errors.append(_diag(
                "ERROR", "COMPETING_HOME", relative, 1,
                "root-level home/index competes with README.md",
            ))

    texts: dict[str, str] = {}
    for relative, path in included.items():
        try:
            texts[relative] = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as exc:
            errors.append(_diag("ERROR", "READ_ERROR", relative, 0, str(exc)))

    anchors = {relative: _anchors(text) for relative, text in texts.items()}
    graph: dict[str, set[str]] = {relative: set() for relative in included}
    checked = 0

    for relative, text in texts.items():
        source = included[relative]
        no_fences = _mask_fences(text)
        parseable = _mask_inline_code(no_fences)

        for match in WIKILINK_RE.finditer(parseable):
            errors.append(_diag(
                "ERROR", "OBSIDIAN_WIKILINK", relative, _line(parseable, match.start()),
                f"Obsidian wikilink is forbidden: {match.group(0)}",
            ))
        for match in LEGACY_RE.finditer(no_fences):
            errors.append(_diag(
                "ERROR", "LEGACY_REFERENCE", relative, _line(no_fences, match.start()),
                f"reference uses deleted legacy route: {match.group(0)}",
            ))

        discovery = (
            PurePosixPath(relative).name.casefold() in {"readme.md", "index.md", "_index.md"}
            or relative.casefold() in {"01-reading-guide.md", "02-file-authority-map.md"}
        )
        discovery_lines: set[int] = set()
        if discovery:
            for match in process_ref_re.finditer(parseable):
                line = _line(parseable, match.start())
                discovery_lines.add(line)
                errors.append(_diag(
                    "ERROR", "FEATURE_WORKSPACE_DISCOVERY", relative,
                    line,
                    "default discovery must not traverse into a registered process workspace",
                ))

        child_navigation = set()
        in_children = False
        for number, line in enumerate(parseable.splitlines(), 1):
            if re.match(r"^ {0,3}#{1,2}(?:\s|$)", line):
                in_children = bool(re.fullmatch(r" {0,3}##\s+子页导航(?:\s+#+)?\s*", line))
            elif in_children:
                child_navigation.add(number)
        for link in _links(parseable):
            if not link.destination or _external(link.destination):
                continue
            checked += 1
            destination_path, fragment = _split(link.destination)
            if destination_path:
                target, target_relative = _resolve(root, source, destination_path)
            else:
                target, target_relative = source, relative

            raw_target = _raw_target(root, source, destination_path) if destination_path else source
            if any(_is_excluded(part, process_roots) for part in (raw_target, *raw_target.parents)):
                # Preserve legacy diagnostic codes for gate consumers; they
                # now apply to all roots from the shared process registry.
                errors.append(_diag(
                    "ERROR", "FEATURE_WORKSPACE_LINK", relative, link.line,
                    f"link traverses into an excluded workspace path: {link.destination}",
                ))
                if discovery and link.line not in discovery_lines:
                    errors.append(_diag(
                        "ERROR", "FEATURE_WORKSPACE_DISCOVERY", relative, link.line,
                        "default discovery must not traverse into a registered process workspace",
                    ))
                continue
            outside_wiki = target_relative is None
            if outside_wiki:
                try:
                    target.relative_to(root.parent.resolve(strict=False))
                except ValueError:
                    errors.append(_diag(
                        "ERROR", "OUTSIDE_WIKI_LINK", relative, link.line,
                        f"local link escapes the repository root: {link.destination}",
                    ))
                    continue
            if target.is_dir():
                target = target / "README.md"
                if not outside_wiki:
                    target_relative = target.relative_to(root).as_posix()
            if not target.exists():
                errors.append(_diag(
                    "ERROR", "BROKEN_LOCAL_LINK", relative, link.line,
                    f"target does not exist: {link.destination}",
                ))
                continue

            if (
                not outside_wiki
                and not link.is_image
                and target.suffix.casefold() == ".md"
            ):
                if target_relative not in included:
                    errors.append(_diag(
                        "ERROR", "EXCLUDED_MARKDOWN_LINK", relative, link.line,
                        f"Markdown target is outside the long-term scan: {link.destination}",
                    ))
                    continue
                source_name = PurePosixPath(relative).name.casefold()
                if source_name in {"readme.md", "index.md", "_index.md", "by-type.md"} or link.line in child_navigation:
                    graph[relative].add(target_relative)

            if (
                not outside_wiki
                and fragment
                and target.suffix.casefold() == ".md"
            ):
                if any(ord(char) > 127 for char in fragment):
                    warnings.append(_diag(
                        "WARNING", "NON_ASCII_ANCHOR", relative, link.line,
                        f"non-ASCII anchor is warning-only: #{fragment}",
                    ))
                elif fragment not in anchors.get(target_relative, set()):
                    errors.append(_diag(
                        "ERROR", "BROKEN_LOCAL_ANCHOR", relative, link.line,
                        f"anchor does not exist: #{fragment} in {target_relative}",
                    ))

    distance: dict[str, int] = {}
    if HOME in graph:
        distance[HOME] = 0
        queue = deque([HOME])
        while queue:
            current = queue.popleft()
            for target in sorted(graph[current]):
                if target not in distance:
                    distance[target] = distance[current] + 1
                    queue.append(target)
    for relative in included:
        if relative == HOME:
            continue
        if relative not in distance:
            errors.append(_diag(
                "ERROR", "ORPHAN_MARKDOWN", relative, 1,
                "not reachable from README.md through Markdown links",
            ))
        elif distance[relative] > 3:
            errors.append(_diag(
                "ERROR", "MOC_ROUTE_DEPTH", relative, 1,
                f"shortest route from README.md is {distance[relative]} hops (maximum 3)",
            ))

    errors.sort()
    warnings.sort()
    return ValidationResult(errors, warnings, len(included), excluded, checked, names)


def _print(root: Path, result: ValidationResult) -> None:
    print(f"Wiki root: {root.expanduser().resolve(strict=False)}")
    for item in result.errors + result.warnings:
        location = item.path if item.line <= 0 else f"{item.path}:{item.line}"
        print(f"{item.severity} [{item.code}] {location}: {item.message}")
    print()
    print(
        f"Summary: {result.files_scanned} Markdown files scanned, "
        f"{result.files_excluded} excluded, {result.links_checked} local targets checked, "
        f"{len(result.errors)} errors, {len(result.warnings)} warnings."
    )
    print("VALID" if result.ok else "INVALID")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = validate_wiki(args.wiki_root, process_workspaces=args.process_workspace)
    if args.output_format == "json":
        payload = {
            "wiki_root": str(args.wiki_root.expanduser().resolve(strict=False)),
            "ok": result.ok,
            "files_scanned": result.files_scanned,
            "files_excluded": result.files_excluded,
            "process_workspaces": list(result.process_workspaces),
            "links_checked": result.links_checked,
            "error_count": len(result.errors),
            "warning_count": len(result.warnings),
            "errors": [asdict(item) for item in result.errors],
            "warnings": [asdict(item) for item in result.warnings],
        }
        print(json.dumps(payload, ensure_ascii=True, sort_keys=True))
    else:
        _print(args.wiki_root, result)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
