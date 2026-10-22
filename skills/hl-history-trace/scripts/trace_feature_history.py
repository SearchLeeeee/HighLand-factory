"""Provenance gate for canonical authority documentation.

The script resolves an explicit question from a canonical authority document
through merged/tombstoned Feature records to at most one retained,
non-authoritative Feature source, ranks route entries by semantic question
terms, and generates or verifies retained-source checksum manifests so history
stays reproducible and contained. It is project-agnostic: the registry, route
file, retained root, output, and manifest are all explicit arguments, and no
project, repository, or machine path is assumed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

EXCLUDED_CHECKSUM_FILES = {"history-checksums.sha256"}


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def authority_key(raw: str) -> str:
    normalized = raw.replace("\\", "/").strip()
    parts = [part for part in normalized.split("/") if part]
    return "/".join(parts).casefold()


def string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def merged_records(registry_path: Path) -> list[tuple[dict[str, Any], Path]]:
    registry = load_yaml(registry_path)
    workspace_root = registry_path.parent.resolve()
    records: list[tuple[dict[str, Any], Path]] = []
    seen: set[str] = set()

    def add(record: dict[str, Any], base: Path) -> None:
        feature_id = record.get("id")
        if not isinstance(feature_id, str) or not re.fullmatch(r"I\d{3,}-F\d{2,}", feature_id):
            return
        if record.get("phase") != "merged" or record.get("state") != "completed":
            return
        if feature_id not in seen:
            seen.add(feature_id)
            records.append((record, base))

    for entry in registry.get("initiatives", []):
        if not isinstance(entry, dict):
            continue
        manifest = entry.get("manifest")
        if isinstance(manifest, str):
            initiative_path = (workspace_root / manifest).resolve()
            if not inside(initiative_path, workspace_root) or not initiative_path.is_file():
                continue
            initiative = load_yaml(initiative_path)
            for feature in initiative.get("features", []):
                if isinstance(feature, dict):
                    add(feature, initiative_path.parent)
            for feature in initiative.get("feature_tombstones", []):
                if isinstance(feature, dict):
                    add(feature, initiative_path.parent)
        for feature in entry.get("feature_tombstones", []):
            if isinstance(feature, dict):
                add(feature, workspace_root)
    for feature in registry.get("feature_tombstones", []):
        if isinstance(feature, dict):
            add(feature, workspace_root)
    return records


def canonical_docs(record: dict[str, Any]) -> list[str]:
    direct = string_list(record.get("canonical_docs"))
    if direct:
        return direct
    closure = record.get("closure")
    return string_list(closure.get("canonical_docs")) if isinstance(closure, dict) else []


def retained_metadata(record: dict[str, Any]) -> dict[str, str]:
    value = record.get("retained_source")
    if not isinstance(value, dict):
        return {}
    return {key: item for key, item in value.items() if isinstance(item, str)}


def locate(args: argparse.Namespace) -> int:
    registry = args.registry.resolve()
    workspace_root = registry.parent
    wanted = authority_key(args.authority_doc)
    candidates = []
    for record, base in merged_records(registry):
        matches = [doc for doc in canonical_docs(record) if authority_key(doc) == wanted]
        if not matches:
            continue
        retained = retained_metadata(record)
        raw_root = retained.get("path")
        if not raw_root:
            continue
        source_root = (base / raw_root).resolve()
        if not inside(source_root, workspace_root):
            print(f"ERROR: retained source escapes workspace for {record.get('id')}", file=sys.stderr)
            return 1
        route_file = (source_root / retained.get("route", "history-route.yaml")).resolve()
        if not inside(route_file, source_root):
            print(f"ERROR: retained route escapes source root for {record.get('id')}", file=sys.stderr)
            return 1
        candidates.append(
            {
                "feature_id": record.get("id"),
                "canonical_doc": matches[0],
                "retained_root": str(source_root),
                "route_file": str(route_file),
                "question": args.question,
                "route_exists": route_file.is_file(),
            }
        )
    print(json.dumps({"authority_doc": args.authority_doc, "question": args.question, "candidates": candidates}, ensure_ascii=False, indent=2))
    return 0 if candidates else 2


def route(args: argparse.Namespace) -> int:
    route_file = args.route_file.resolve()
    data = load_yaml(route_file)
    source_root = route_file.parent
    question = args.question.casefold()
    ranked = []
    for index, item in enumerate(data.get("routes", [])):
        if not isinstance(item, dict):
            continue
        terms = string_list(item.get("question_terms"))
        topic = item.get("topic") if isinstance(item.get("topic"), str) else ""
        score = sum(1 for term in terms if term.casefold() in question)
        if topic and topic.casefold() in question:
            score += 2
        refs = []
        valid = True
        for ref in item.get("source_refs", []):
            if not isinstance(ref, dict) or not isinstance(ref.get("path"), str):
                continue
            resolved = (source_root / ref["path"]).resolve()
            if not inside(resolved, source_root):
                valid = False
                break
            refs.append({"path": ref["path"], "headings": string_list(ref.get("headings")), "exists": resolved.is_file()})
        if not valid:
            print(f"ERROR: route #{index + 1} escapes retained root", file=sys.stderr)
            return 1
        ranked.append(
            {
                "score": score,
                "topic": topic,
                "question_terms": terms,
                "canonical_targets": string_list(item.get("canonical_targets")),
                "source_refs": refs,
            }
        )
    ranked.sort(key=lambda item: (-item["score"], item["topic"]))
    matched = [item for item in ranked if item["score"] > 0]
    result = matched if matched else ranked[:5]
    print(json.dumps({"question": args.question, "matched": bool(matched), "routes": result}, ensure_ascii=False, indent=2))
    return 0 if result else 2


def iter_checksum_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.name not in EXCLUDED_CHECKSUM_FILES
    )


def checksum(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    output = args.output.resolve()
    if not inside(output, root):
        print("ERROR: checksum manifest must stay inside retained root", file=sys.stderr)
        return 1
    lines = []
    for path in iter_checksum_files(root):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.relative_to(root).as_posix()}")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {len(lines)} checksums: {output}")
    return 0


def verify(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    manifest = args.manifest.resolve()
    if not inside(manifest, root) or not manifest.is_file():
        print("ERROR: checksum manifest is missing or outside retained root", file=sys.stderr)
        return 1
    errors = []
    checked = 0
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match:
            errors.append(f"invalid checksum line: {line}")
            continue
        expected, relative = match.groups()
        path = (root / relative).resolve()
        if not inside(path, root) or not path.is_file():
            errors.append(f"missing or outside root: {relative}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        checked += 1
        if actual != expected:
            errors.append(f"checksum mismatch: {relative}")
    result = {"checked": checked, "passed": not errors, "errors": errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Trace canonical authority questions to retained Feature history.")
    commands = result.add_subparsers(dest="command", required=True)
    locate_parser = commands.add_parser("locate")
    locate_parser.add_argument("--registry", type=Path, required=True)
    locate_parser.add_argument("--authority-doc", required=True)
    locate_parser.add_argument("--question", required=True)
    locate_parser.set_defaults(func=locate)
    route_parser = commands.add_parser("route")
    route_parser.add_argument("--route-file", type=Path, required=True)
    route_parser.add_argument("--question", required=True)
    route_parser.set_defaults(func=route)
    checksum_parser = commands.add_parser("checksum")
    checksum_parser.add_argument("--root", type=Path, required=True)
    checksum_parser.add_argument("--output", type=Path, required=True)
    checksum_parser.set_defaults(func=checksum)
    verify_parser = commands.add_parser("verify")
    verify_parser.add_argument("--root", type=Path, required=True)
    verify_parser.add_argument("--manifest", type=Path, required=True)
    verify_parser.set_defaults(func=verify)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
