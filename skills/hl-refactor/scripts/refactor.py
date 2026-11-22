#!/usr/bin/env python3
"""Small, local control plane for a manually requested maintenance run.

This helper inventories source identities and enforces declared boundaries. It
does not discover refactoring opportunities or establish business correctness;
those remain the scanning, implementing and reviewing agents' responsibilities.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

FACTORY = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(FACTORY / "engine"))

from factorylib import config as config_mod  # noqa: E402
from factorylib.layout import build_layout  # noqa: E402
from factorylib.workspaces import is_process_path, process_workspace_names  # noqa: E402


class RefactorError(ValueError):
    """A failed maintenance precondition, with an actionable CLI diagnostic."""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex)
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def git(root: Path, *args: str) -> bytes:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True)
    if result.returncode:
        raise RefactorError("Git could not establish the source identity: " + result.stderr.decode(errors="replace").strip())
    return result.stdout


def within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def load_context(work: Path) -> tuple[Any, dict[str, Any]]:
    work = work.expanduser().resolve()
    config = config_mod.load_config(work)
    errors, _ = config_mod.validate_config(config)
    if errors:
        raise RefactorError("Invalid project configuration: " + "; ".join(errors))
    local = config_mod.load_local(work)
    layout = build_layout(work, config, local)
    required = (layout.local_yaml, layout.workflow_profile, layout.registry)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RefactorError("Missing project startup authority: " + ", ".join(missing))
    if not layout.code.is_dir() or not layout.wiki.is_dir():
        raise RefactorError("The configured code and Wiki directories must both exist")
    process_workspace_names(config)  # Validate explicit process-root registration.
    return layout, config


def preflight(layout: Any) -> dict[str, Any]:
    """Reuse the existing parser/validator, then enforce *final* closure."""
    source = layout.factory_root / "skills/hl-feature-workspace/scripts/feature_workspace.py"
    if not source.is_file():
        raise RefactorError(f"Feature lifecycle parser is missing: {source}")
    spec = importlib.util.spec_from_file_location("_hl_refactor_feature_workspace", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        raw_registry = module.load_yaml(layout.registry)
        if not isinstance(raw_registry, dict) or not isinstance(raw_registry.get("initiatives"), list):
            raise RefactorError("Lifecycle registry must explicitly contain an initiatives list; an empty or missing authority is not proof of no active work")
        registry = module.load_registry(layout.registry)
        errors = module.validate_registry(registry)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, yaml.YAMLError) as exc:
        raise RefactorError(f"Cannot validate lifecycle authority: {exc}") from exc
    terminal = {"completed", "cancelled", "superseded"}
    for initiative in registry.get("initiatives", []):
        identifier = initiative.get("id", "<missing>")
        if initiative.get("state") not in terminal:
            errors.append(f"{identifier}: Initiative is not finally closed ({initiative.get('state')})")
        for feature in initiative.get("features", []):
            feature_id = feature.get("id", "<missing>")
            if feature.get("state") not in terminal:
                errors.append(f"{feature_id}: effective Feature is still active")
            elif feature.get("state") == "completed" and feature.get("phase") != "merged":
                errors.append(f"{feature_id}: phase completion is not final merged closure")
        # A cancelled/superseded parent never hides an active child.
    if errors:
        raise RefactorError("Maintenance requires all Initiatives to be closed:\n" + "\n".join(sorted(set(errors))))
    return registry


def namespace(path: Path, layout: Any) -> str | None:
    roots = [("wiki", layout.wiki), ("code", layout.code), ("work", layout.work)]
    roots.sort(key=lambda item: len(item[1].parts), reverse=True)
    for name, root in roots:
        if within(path, root):
            relative = path.relative_to(root).as_posix()
            return f"{name}:{relative}"
    return None


def excluded(path: Path, layout: Any, config: dict[str, Any]) -> bool:
    if is_process_path(path, layout.wiki, config):
        return True
    return path in {layout.local_yaml, layout.state_json} or within(path, layout.work / ".factory/worktrees")


def source_path(raw: str, layout: Any, config: dict[str, Any]) -> tuple[str, Path]:
    """Accept exact canonical files only; scopes cannot escape through symlinks."""
    if not isinstance(raw, str) or ":" not in raw:
        raise RefactorError(f"Expected code:, wiki: or work: exact-file scope, got {raw!r}")
    prefix, relative = raw.split(":", 1)
    roots = {"code": layout.code, "wiki": layout.wiki, "work": layout.work}
    pure = PurePosixPath(relative)
    if prefix not in roots or not relative or "\\" in relative or pure.is_absolute() or any(part in {"..", "."} for part in relative.split("/")) or any(char in relative for char in "*?[]") or ":" in relative:
        raise RefactorError(f"Invalid exact-file scope: {raw}")
    path = roots[prefix] / relative
    if not within(path.resolve(), roots[prefix]) or path.is_symlink():
        raise RefactorError(f"Scope escapes its root or names a symlink: {raw}")
    if path.is_dir() or excluded(path, layout, config) or ".git" in pure.parts:
        raise RefactorError(f"Scope is a directory or protected process path: {raw}")
    canonical = namespace(path, layout)
    if canonical != raw:
        raise RefactorError(f"Use the canonical scope {canonical}, not {raw}")
    # Ignored files cannot be guarded by a tracked/untracked Git inventory.
    root = Path(git(path.parent if path.parent.exists() else roots[prefix], "rev-parse", "--show-toplevel").decode().strip()).resolve()
    relative_git = path.relative_to(root).as_posix()
    ignored = subprocess.run(["git", "-C", str(root), "check-ignore", "--no-index", "--quiet", "--", relative_git], capture_output=True)
    tracked = git(root, "ls-files", "--", relative_git)
    if ignored.returncode == 0 and not tracked:
        raise RefactorError(f"Ignored file cannot be an enforceable edit scope: {raw}")
    return raw, path


def snapshot(layout: Any, config: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    identities: dict[str, Any] = {}
    roots: set[Path] = set()
    for role in ("work", "code", "wiki"):
        directory = getattr(layout, role)
        root = Path(git(directory, "rev-parse", "--show-toplevel").decode().strip()).resolve()
        common = Path(git(root, "rev-parse", "--path-format=absolute", "--git-common-dir").decode().strip()).resolve()
        identities[role] = {"path": str(directory), "git_root": str(root), "git_common_dir": str(common), "head": git(root, "rev-parse", "--verify", "HEAD").decode().strip()}
        roots.add(root)
    files: dict[str, str] = {}
    dirty: list[str] = []
    limitations: list[str] = []
    for root in sorted(roots):
        algorithm = git(root, "rev-parse", "--show-object-format").decode().strip()
        # Compare both sides of the index: a staged edit reverted in the
        # worktree has no HEAD diff, yet its index object is not current bytes.
        reported_changes = set(git(root, "diff", "--name-only", "-z").split(b"\0"))
        reported_changes.update(git(root, "diff", "--cached", "--name-only", "-z").split(b"\0"))
        # Missing sparse files must be reported as unavailable scan coverage.
        sparse: set[bytes] = set()
        for tagged in git(root, "ls-files", "-v", "-z").split(b"\0"):
            if not tagged:
                continue
            tag, raw = tagged[:1], tagged[2:]
            if tag.upper() == b"S":
                sparse.add(raw)
        entries: dict[bytes, tuple[str, str]] = {}
        for entry in git(root, "ls-files", "--stage", "-z").split(b"\0"):
            if not entry:
                continue
            metadata, raw = entry.split(b"\t", 1)
            mode, oid, stage = metadata.decode().split()
            if stage != "0":
                raise RefactorError("Resolve Git index conflicts before maintenance")
            entries[raw] = (mode, oid)
        for raw in git(root, "ls-files", "--others", "--exclude-standard", "-z").split(b"\0"):
            if raw:
                entries[raw] = ("", "")
        for raw, (mode, oid) in entries.items():
            path = root / os.fsdecode(raw)
            key = namespace(path, layout)
            if key is None or excluded(path, layout, config):
                continue
            if mode == "160000":
                limitations.append(f"{key}: submodule pointer only; nested implementation is outside this inventory")
            else:
                # Bind evidence to the same raw worktree representation for
                # clean, staged, dirty and index-flagged files. Git objects may
                # contain LF while Windows checks out CRLF; switching between
                # object IDs and raw bytes would invalidate unchanged sources.
                indexed = (mode, oid)
                if not path.exists() and not path.is_symlink():
                    if raw in sparse:
                        limitations.append(f"{key}: skip-worktree/sparse path is absent; its implementation is not available for this working-tree scan")
                    else:
                        dirty.append(key)
                    continue
                if path.is_symlink():
                    data = os.fsencode(os.readlink(path))
                    mode = "120000"
                elif path.is_file():
                    data = path.read_bytes()
                    mode = "100755" if os.name != "nt" and path.stat().st_mode & stat.S_IXUSR else (mode or "100644")
                    if os.name != "nt" and not path.stat().st_mode & stat.S_IXUSR:
                        mode = "100644"
                else:
                    raise RefactorError(f"Unsupported source file type: {path}")
                oid = hashlib.new(algorithm, b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
                if raw in reported_changes or not indexed[1]:
                    dirty.append(key)
            files[key] = mode + ":" + oid
    def clean(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: clean(item) for key, item in value.items() if not key.startswith("_")}
        if isinstance(value, list):
            return [clean(item) for item in value]
        return value
    authority = {"config": config, "python": str(layout.python), "factory_root": str(layout.factory_root), "paths": {name: str(getattr(layout, name)) for name in ("work", "code", "wiki")}}
    repo_identity = {role: {key: value for key, value in identity.items() if key != "head"} for role, identity in identities.items()}
    return {"at": now(), "timezone": "UTC", "repos": identities, "files": dict(sorted(files.items())), "dirty_paths": sorted(set(dirty)), "config_digest": digest(authority), "lifecycle_digest": digest(clean(registry)), "limitations": sorted(set(limitations)), "content_digest": digest({"files": files, "repos": repo_identity, "authority": authority, "lifecycle": clean(registry)})}


def changed_paths(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    left, right = before["files"], after["files"]
    return sorted(key for key in left.keys() | right.keys() if left.get(key) != right.get(key))


def repo_roots(current: dict[str, Any]) -> dict[str, Any]:
    return {role: {key: value for key, value in identity.items() if key != "head"} for role, identity in current["repos"].items()}


def check_range(run: dict[str, Any], current: dict[str, Any]) -> None:
    if run["mode"] != "latest":
        return
    for role, bounded in run["scope"]["ranges"].items():
        identity = current["repos"][role]
        result = subprocess.run(["git", "-C", identity["git_root"], "merge-base", "--is-ancestor", bounded["head"], identity["head"]], capture_output=True)
        if result.returncode:
            raise RefactorError(f"latest {role} range is no longer incorporated in the current baseline; start a new manual run with current range evidence")


def unchanged(before: dict[str, Any], after: dict[str, Any], label: str) -> None:
    if before["content_digest"] != after["content_digest"]:
        paths = changed_paths(before, after)
        raise RefactorError(f"{label} is stale; re-scan and obtain a current selection. Changed source: {', '.join(paths[:20]) or 'configuration/lifecycle authority'}")


def latest_range(args: Any, layout: Any, config: dict[str, Any], registry: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    required = (args.initiative, args.base, args.head, args.range_evidence)
    if not all(required):
        raise RefactorError("latest requires --initiative, --base, --head and --range-evidence establishing the latest completed Initiative and its complete effective range; use full if unavailable")
    target = next((item for item in registry.get("initiatives", []) if item.get("id") == args.initiative), None)
    if target is None or target.get("state") != "completed":
        raise RefactorError("latest must name an explicitly completed Initiative in the validated registry")
    code_root, wiki_root = (Path(current["repos"][role]["git_root"]) for role in ("code", "wiki"))
    if code_root != wiki_root and not (args.wiki_base and args.wiki_head):
        raise RefactorError("Split Git identities require separate --wiki-base and --wiki-head, including an explicit no-change range when applicable")
    if bool(args.wiki_base) != bool(args.wiki_head):
        raise RefactorError("Supply both --wiki-base and --wiki-head")
    ranges: dict[str, Any] = {}
    scope: set[str] = set()
    for role, root, base, head in (("code", code_root, args.base, args.head), ("wiki", wiki_root, args.wiki_base or args.base, args.wiki_head or args.head)):
        base_oid = git(root, "rev-parse", "--verify", base + "^{commit}").decode().strip()
        head_oid = git(root, "rev-parse", "--verify", head + "^{commit}").decode().strip()
        for ancestor, descendant in ((base_oid, head_oid), (head_oid, current["repos"][role]["head"])):
            result = subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", ancestor, descendant], capture_output=True)
            if result.returncode:
                raise RefactorError(f"{role} range must be ordered and incorporated into the current HEAD")
        names = []
        # Disable rename folding so both old and new paths remain auditable.
        for raw in git(root, "diff", "--no-renames", "--name-only", "-z", base_oid, head_oid).split(b"\0"):
            if not raw:
                continue
            path = root / os.fsdecode(raw)
            key = namespace(path, layout)
            if key and not excluded(path, layout, config):
                names.append(key)
                scope.add(key)
        ranges[role] = {"base": base_oid, "head": head_oid, "changed_paths": sorted(set(names))}
    return {"initiative": args.initiative, "evidence": args.range_evidence, "ranges": ranges, "seed_paths": sorted(scope), "current_uncommitted_paths": current["dirty_paths"], "note": "Explicit evidence must establish recency, all effective Leaves, integration fixes and final Wiki updates. The helper validates refs and ancestry, not semantic completeness."}


def run_file(layout: Any, identifier: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,100}", identifier):
        raise RefactorError("Invalid run identifier")
    result = layout.refactor_workspace / "runs" / identifier / "run.json"
    if not within(result.resolve(), layout.refactor_workspace):
        raise RefactorError("Refactor run records must remain inside the configured Refactor workspace")
    return result


def event(path: Path, run: dict[str, Any], action: str, detail: Any) -> None:
    item = {"at": now(), "action": action, "detail": detail}
    with (path.parent / "events.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(item, ensure_ascii=False) + "\n")
    run["updated_at"] = item["at"]
    dump(path, run)


def guarded_snapshot(layout: Any, config: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    current = snapshot(layout, config, preflight(layout))
    check_range(run, current)
    baseline = run["snapshot"]
    if current["lifecycle_digest"] != baseline["lifecycle_digest"] or current["config_digest"] != baseline["config_digest"]:
        raise RefactorError("Lifecycle or configuration authority changed; pause and re-establish maintenance scope")
    if run.get("editing_started"):
        allowed = set(run["selection"]["paths"])
        outside = set(changed_paths(baseline, current)) - allowed
        if outside:
            raise RefactorError("Changes outside selected exact-file scopes: " + ", ".join(sorted(outside)))
    else:
        unchanged(baseline, current, "Scan evidence")
    return current


def receipt(path: Path, source: Path) -> dict[str, str]:
    source = source.expanduser().resolve()
    if not source.is_file() or not source.stat().st_size:
        raise RefactorError(f"Evidence must be a nonempty file: {source}")
    data = source.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    directory = path.parent / "evidence"
    directory.mkdir(exist_ok=True)
    target = directory / (uuid.uuid4().hex[:12] + "-" + source.name)
    target.write_bytes(data)
    return {"path": str(target.relative_to(path.parent).as_posix()), "sha256": sha, "source": str(source)}


def validate_receipt(path: Path, item: dict[str, Any]) -> None:
    evidence = path.parent / item["evidence"]["path"]
    if not evidence.is_file() or hashlib.sha256(evidence.read_bytes()).hexdigest() != item["evidence"]["sha256"]:
        raise RefactorError("Saved evidence is missing or changed: " + str(evidence))


def parse_csv(value: str) -> list[str]:
    return list(dict.fromkeys(item.strip() for item in value.split(",") if item.strip()))


def nonempty(value: str) -> str:
    if not value.strip():
        raise argparse.ArgumentTypeError("must contain a meaningful nonempty value")
    return value


def validate_candidates(payload: Any, layout: Any, config: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or not isinstance(payload.get("coverage"), dict):
        raise RefactorError("Candidate input needs coverage and candidates")
    for name in ("checked", "limitations"):
        values = payload["coverage"].get(name)
        if not isinstance(values, list) or not all(isinstance(item, str) and item.strip() for item in values):
            raise RefactorError(f"coverage.{name} must be a string list")
    if not payload["coverage"]["checked"]:
        raise RefactorError("Record actual checked coverage, including zero-candidate scans")
    candidates = payload.get("candidates")
    if not isinstance(candidates, list):
        raise RefactorError("candidates must be a list")
    ids: set[str] = set()
    for candidate in candidates:
        if not isinstance(candidate, dict) or not re.fullmatch(r"R\d{3,}", str(candidate.get("id", ""))):
            raise RefactorError("Each candidate needs a stable R001-style id")
        identifier = candidate["id"]
        if identifier in ids:
            raise RefactorError("Duplicate candidate: " + identifier)
        ids.add(identifier)
        for name in ("title", "problem", "benefit", "proposed_action", "cost", "risk", "recommendation"):
            if not isinstance(candidate.get(name), str) or not candidate[name].strip():
                raise RefactorError(f"{identifier}: missing {name}")
        if candidate.get("kind") not in {"refactor", "test", "wiki", "investigate", "behavior", "handoff"}:
            raise RefactorError(f"{identifier}: unsupported kind")
        for name in ("evidence", "acceptance", "paths", "depends_on"):
            values = candidate.get(name)
            if not isinstance(values, list) or not all(isinstance(item, str) and item.strip() for item in values):
                raise RefactorError(f"{identifier}: {name} must be a string list")
            if name in {"evidence", "acceptance"} and not values:
                raise RefactorError(f"{identifier}: {name} cannot be empty")
        if candidate["kind"] not in {"investigate", "handoff"} and not candidate["paths"]:
            raise RefactorError(f"{identifier}: implementation needs explicit file scopes")
        for raw in candidate["paths"]:
            source_path(raw, layout, config)
        if candidate["kind"] == "test":
            for name in ("original_protection", "continued_protection"):
                if not isinstance(candidate.get(name), str) or not candidate[name].strip():
                    raise RefactorError(f"{identifier}: test cleanup needs {name}")
    graph = {item["id"]: item["depends_on"] for item in candidates}
    def visit(identifier: str, active: set[str], done: set[str]) -> None:
        if identifier in active:
            raise RefactorError("Candidate dependency cycle: " + identifier)
        if identifier in done:
            return
        if identifier not in graph:
            raise RefactorError("Unknown candidate dependency: " + identifier)
        for child in graph[identifier]:
            visit(child, active | {identifier}, done)
        done.add(identifier)
    done: set[str] = set()
    for identifier in graph:
        visit(identifier, set(), done)
    return candidates


def start(args: Any, layout: Any, config: dict[str, Any]) -> dict[str, Any]:
    identifier = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-") + uuid.uuid4().hex[:8]
    path = run_file(layout, identifier)
    run: dict[str, Any] = {"schema": 1, "id": identifier, "created_at": now(), "timezone": "UTC", "mode": args.mode, "actor": args.actor, "budget": args.budget, "status": "starting", "candidates": [], "candidate_history": [], "selection": None, "checks": [], "resolutions": [], "editing_started": False, "exclusions": list(process_workspace_names(config))}
    try:
        path.parent.mkdir(parents=True, exist_ok=False)
        registry = preflight(layout)
        current = snapshot(layout, config, registry)
        run["snapshot"] = current
        run["scope"] = latest_range(args, layout, config, registry, current) if args.mode == "latest" else {"seed_paths": list(current["files"]), "note": "Inventory only; report actual semantic coverage and limitations separately."}
        run["status"] = "scanning"
        event(path, run, "start", {"mode": args.mode, "budget": args.budget})
    except Exception as exc:
        run["status"] = "blocked"
        if path.parent.is_dir():
            event(path, run, "start-failed", {"error": str(exc)})
        retained = f"Blocked run retained at {path}" if path.is_file() else "Run directory could not be created"
        raise RefactorError(f"{exc}\n{retained}") from exc
    scope_summary = run["scope"] if args.mode == "latest" else {"seed_path_count": len(run["scope"]["seed_paths"]), "inventory_record": str(path), "note": run["scope"]["note"]}
    return {"run": identifier, "record": str(path), "status": run["status"], "inventory_count": len(current["files"]), "scope": scope_summary, "limitations": current["limitations"]}


def operate(args: Any, layout: Any, config: dict[str, Any], path: Path, run: dict[str, Any]) -> dict[str, Any]:
    command = args.command
    if command == "show":
        return run
    if run["status"] in {"completed", "scan-completed", "blocked"}:
        raise RefactorError("This run is closed or never passed startup; start a new manual run")
    if command == "pause":
        try:
            run["pause_snapshot"] = snapshot(layout, config, preflight(layout))
        except Exception as exc:
            run["pause_snapshot"] = None
            run["pause_snapshot_error"] = str(exc)
        previous = run["status"]
        run["resume_status"] = previous
        run["status"] = "paused"
        event(path, run, "pause", {"reason": args.reason})
        return {"status": "paused"}
    if command == "resume":
        current = guarded_snapshot(layout, config, run)
        if run["status"] == "paused":
            if not run.get("pause_snapshot"):
                raise RefactorError("Pause could not preserve a valid source identity; start a new scan after resolving the recorded failure")
            unchanged(run["pause_snapshot"], current, "Paused source")
            run["status"] = run["resume_status"]
        event(path, run, "resume", {"snapshot": current["content_digest"]})
        return {"status": run["status"]}
    if run["status"] == "paused":
        raise RefactorError("Run is paused; resume and recheck evidence first")
    if command == "refresh":
        if run["editing_started"]:
            raise RefactorError("Cannot refresh an implementation baseline; pause and preserve the incomplete outcome")
        current = snapshot(layout, config, preflight(layout))
        baseline = run["snapshot"]
        if any(current[key] != baseline[key] for key in ("lifecycle_digest", "config_digest")) or repo_roots(current) != repo_roots(baseline):
            raise RefactorError("Refresh cannot adopt changed lifecycle/configuration/repository authority; pause and start a new manual run with current range proof")
        check_range(run, current)
        if run["mode"] == "latest" and not args.range_evidence:
            raise RefactorError("latest refresh needs --range-evidence re-establishing recency and completeness for the recorded ranges")
        run["candidate_history"].append({"at": now(), "snapshot": run.get("candidate_snapshot", run["snapshot"]), "coverage": run.get("coverage"), "candidates": run["candidates"], "selection": run["selection"]})
        run.update(snapshot=current, candidates=[], selection=None, status="scanning")
        run.pop("coverage", None)
        run.pop("candidate_snapshot", None)
        if run["mode"] == "full":
            run["scope"]["seed_paths"] = list(current["files"])
        else:
            run["scope"]["current_uncommitted_paths"] = current["dirty_paths"]
            run["scope"].setdefault("evidence_history", []).append({"at": now(), "evidence": run["scope"]["evidence"]})
            run["scope"]["evidence"] = args.range_evidence
        event(path, run, "refresh", {"reason": args.reason, "approval_invalidated": True})
        return {"status": "scanning", "approval_invalidated": True}
    current = guarded_snapshot(layout, config, run)
    if command == "check":
        event(path, run, "check", {"snapshot": current["content_digest"]})
        return {"status": run["status"], "changed_paths": changed_paths(run["snapshot"], current), "snapshot": current["content_digest"]}
    if command == "candidates":
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        candidates = validate_candidates(payload, layout, config)
        if run["editing_started"]:
            by_id = {item["id"]: item for item in candidates}
            if any(by_id.get(item["id"]) != item for item in run["candidates"]):
                raise RefactorError("After edits start, existing candidates are immutable; append newly evidenced candidates before requesting expanded selection")
        run["candidate_history"].append({"at": now(), "snapshot": run.get("candidate_snapshot"), "coverage": run.get("coverage"), "candidates": run["candidates"], "selection": run["selection"]})
        run["candidates"] = candidates
        run["coverage"] = payload["coverage"]
        run["candidate_snapshot"] = current
        if not run["editing_started"]:
            run["status"] = "candidates"
            run["selection"] = None
        event(path, run, "candidates", {"ids": [item["id"] for item in candidates], "coverage": payload["coverage"]})
        return {"status": run["status"], "candidates": len(candidates), "coverage": payload["coverage"]}
    if command == "select":
        if "candidate_snapshot" not in run:
            raise RefactorError("Record candidates and actual coverage before selection")
        unchanged(run["candidate_snapshot"], current, "Candidate evidence")
        selected, ack = set(parse_csv(args.ids)), set(parse_csv(args.ack_behavior))
        ack.update((run.get("selection") or {}).get("behavior_acknowledgements", []))
        by_id = {item["id"]: item for item in run["candidates"]}
        if selected - by_id.keys():
            raise RefactorError("Unknown selected candidates: " + ", ".join(sorted(selected - by_id.keys())))
        if run["editing_started"] and not set(run["selection"]["ids"]) <= selected:
            raise RefactorError("Cannot remove already authorized implementation items after edits begin")
        paths: set[str] = set()
        for identifier in selected:
            candidate = by_id[identifier]
            if candidate["kind"] == "behavior" and identifier not in ack:
                raise RefactorError(f"{identifier}: observable behavior requires explicit --ack-behavior")
            if set(candidate["depends_on"]) - selected:
                raise RefactorError(f"{identifier}: select its required dependencies together")
            if candidate["kind"] not in {"investigate", "handoff"}:
                paths.update(candidate["paths"])
        run["selection"] = {"at": now(), "ids": sorted(selected), "paths": sorted(paths), "decision": args.decision, "behavior_acknowledgements": sorted(ack & selected), "snapshot": current["content_digest"]}
        run["pending_selection_check"] = True
        if not run["editing_started"]:
            run["status"] = "selected"
        event(path, run, "selection", run["selection"])
        return run["selection"]
    if command == "begin":
        if not run.get("selection"):
            raise RefactorError("Explicit selection is required before implementation")
        if not run["editing_started"] or run.get("pending_selection_check"):
            unchanged(run["candidate_snapshot"], current, "Selected candidate evidence")
        if args.id and args.id not in run["selection"]["ids"]:
            raise RefactorError("Implementation unit was not selected")
        run["editing_started"] = True
        run["pending_selection_check"] = False
        run["status"] = "implementing"
        event(path, run, "begin-unit", {"id": args.id, "snapshot": current["content_digest"]})
        return {"status": "implementing", "approved_paths": run["selection"]["paths"]}
    if command == "resolve":
        if not run["editing_started"] or args.id not in run["selection"]["ids"]:
            raise RefactorError("Begin a selected implementation/investigation unit first")
        candidate = next(item for item in run["candidates"] if item["id"] == args.id)
        permitted = {"investigate": {"investigated", "transferred"}, "handoff": {"transferred"}}.get(candidate["kind"], {"fixed"})
        if args.outcome not in permitted:
            raise RefactorError(f"{candidate['kind']} candidate cannot be reported as {args.outcome}")
        item = {"id": args.id, "at": now(), "outcome": args.outcome, "note": args.note, "actual_cost": args.actual_cost, "evidence": receipt(path, args.evidence), "snapshot": current["content_digest"]}
        run["resolutions"].append(item)
        event(path, run, "resolve", item)
        return item
    if command == "record-check":
        if args.kind in {"review", "handoff"} and args.actor == run["actor"]:
            raise RefactorError("Review and Agent handoff require an actor independent of the implementer")
        if args.kind == "test" and (not args.check_command or args.exit_code is None):
            raise RefactorError("Test evidence needs --command and --exit-code")
        if args.verdict == "pass" and args.exit_code not in {None, 0}:
            raise RefactorError("A failing command cannot be recorded as PASS")
        item = {"kind": args.kind, "at": now(), "verdict": args.verdict, "actor": args.actor, "command": args.check_command, "exit_code": args.exit_code, "evidence": receipt(path, args.evidence), "snapshot": current["content_digest"]}
        run["checks"].append(item)
        event(path, run, "record-check", item)
        return item
    if command == "verify-wiki":
        from factorylib.doctor import run_gate
        code, out, err = run_gate(layout, "wiki")
        output = path.parent / "evidence" / (uuid.uuid4().hex[:12] + "-wiki-structure.txt")
        output.parent.mkdir(exist_ok=True)
        output.write_text(f"UTC: {now()}\nexit_code: {code}\n{out}\n{err}\n", encoding="utf-8")
        # The validator is read-only; any source change during it invalidates the receipt.
        after = guarded_snapshot(layout, config, run)
        unchanged(current, after, "Wiki verification")
        item = {"kind": "wiki-structure", "at": now(), "verdict": "pass" if code == 0 else "fail", "actor": "factory gate wiki", "command": "factory gate wiki", "exit_code": code, "evidence": {"path": output.relative_to(path.parent).as_posix(), "sha256": hashlib.sha256(output.read_bytes()).hexdigest()}, "snapshot": current["content_digest"]}
        run["checks"].append(item)
        event(path, run, "verify-wiki", item)
        return item
    if command == "finish":
        if "coverage" not in run:
            raise RefactorError("Record actual scan coverage before closure")
        if run["candidates"] and not run.get("selection"):
            raise RefactorError("Candidates require an explicit recorded disposition; select no IDs to retain all")
        selected = set((run.get("selection") or {}).get("ids", []))
        resolved = {item["id"]: item for item in run["resolutions"]}
        if selected - resolved.keys():
            raise RefactorError("Selected candidates remain unresolved: " + ", ".join(sorted(selected - resolved.keys())))
        for item in resolved.values():
            validate_receipt(path, item)
        latest = {item["kind"]: item for item in run["checks"] if item["snapshot"] == current["content_digest"]}
        changed = changed_paths(run["snapshot"], current)
        if args.scan_only and (changed or any(item["outcome"] == "fixed" for item in resolved.values())):
            raise RefactorError("Scan-only closure cannot contain source edits or claim implementation fixes")
        required = {"wiki", "wiki-structure"}
        if selected:
            required |= {"review", "handoff"}
        if changed:
            required.add("test")
        for kind in sorted(required):
            item = latest.get(kind)
            diagnostic = args.scan_only and kind in {"wiki", "wiki-structure"}
            if not item or (not diagnostic and item["verdict"] != "pass"):
                raise RefactorError(f"Current {kind} PASS evidence is required; old or failed evidence cannot close this run")
            validate_receipt(path, item)
        if args.scan_only and any(latest[kind]["verdict"] != "pass" for kind in ("wiki", "wiki-structure")) and not run.get("selection"):
            raise RefactorError("Retaining known scan failures needs an explicit disposition: select --ids '' --decision '<user decision and residuals>'")
        run["final_snapshot"] = current
        run["summary"] = args.summary
        run["remaining_candidates"] = sorted({item["id"] for item in run["candidates"]} - selected)
        run["status"] = "scan-completed" if args.scan_only else "completed"
        run["closure_type"] = "diagnostic-scan" if args.scan_only else "verified-maintenance"
        event(path, run, "finish", {"summary": args.summary, "closure_type": run["closure_type"], "changed_paths": changed, "remaining_candidates": run["remaining_candidates"]})
        return {"status": run["status"], "closure_type": run["closure_type"], "record": str(path), "changed_paths": changed, "remaining_candidates": run["remaining_candidates"]}
    raise RefactorError("Unsupported command: " + command)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    for name in ("start", "show", "candidates", "select", "begin", "check", "resume", "refresh", "resolve", "record-check", "verify-wiki", "finish", "pause"):
        child = commands.add_parser(name)
        child.add_argument("--work", type=Path, required=True)
        if name != "start":
            child.add_argument("--run", required=True)
        if name == "start":
            child.add_argument("--mode", choices=("full", "latest"), required=True)
            child.add_argument("--actor", required=True, type=nonempty, help="implementing agent/session identifier")
            child.add_argument("--budget", type=nonempty, default="unspecified; establish before selection")
            for flag in ("initiative", "base", "head", "wiki-base", "wiki-head", "range-evidence"):
                child.add_argument("--" + flag, type=nonempty)
        elif name == "candidates":
            child.add_argument("--input", type=Path, required=True)
        elif name == "select":
            child.add_argument("--ids", required=True, help="comma-separated candidate IDs; empty string retains all")
            child.add_argument("--decision", required=True, type=nonempty, help="user's selection and cost/behavior decision")
            child.add_argument("--ack-behavior", default="")
        elif name == "begin":
            child.add_argument("--id", help="selected unit; re-run at each implementation boundary")
        elif name == "resolve":
            child.add_argument("--id", required=True)
            child.add_argument("--outcome", choices=("fixed", "investigated", "transferred"), required=True)
            child.add_argument("--evidence", type=Path, required=True)
            child.add_argument("--note", required=True, type=nonempty)
            child.add_argument("--actual-cost", required=True, type=nonempty)
        elif name == "record-check":
            child.add_argument("--kind", choices=("test", "wiki", "review", "handoff"), required=True)
            child.add_argument("--evidence", type=Path, required=True)
            child.add_argument("--verdict", choices=("pass", "fail", "blocked"), required=True)
            child.add_argument("--actor", required=True, type=nonempty)
            child.add_argument("--command", dest="check_command", type=nonempty)
            child.add_argument("--exit-code", type=int)
        elif name in {"pause", "refresh"}:
            child.add_argument("--reason", required=True, type=nonempty)
            if name == "refresh":
                child.add_argument("--range-evidence", type=nonempty, help="required for latest: re-establish the recorded range's completeness and recency")
        elif name == "finish":
            child.add_argument("--summary", required=True, type=nonempty)
            child.add_argument("--scan-only", action="store_true", help="diagnostic closure without edits/fixes; preserves existing Wiki failures instead of claiming verified maintenance")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    path, run = None, None
    try:
        layout, config = load_context(args.work)
        if args.command == "start":
            output = start(args, layout, config)
        else:
            path = run_file(layout, args.run)
            if args.command == "show" and not path.exists() and layout.retained_process_root:
                archive = layout.retained_process_root / layout.refactor_workspace.name
                relative = path.relative_to(layout.refactor_workspace)
                retained = (archive / relative).resolve()
                if retained.is_relative_to(archive) and retained.is_file():
                    print(retained.read_text(encoding="utf-8"))
                    return 0
            run = json.loads(path.read_text(encoding="utf-8"))
            output = operate(args, layout, config, path, run)
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 1 if args.command == "verify-wiki" and output["verdict"] != "pass" else 0
    except (RefactorError, config_mod.ConfigError, OSError, ValueError) as exc:
        if path is not None and run is not None:
            event(path, run, "command-failed", {"command": args.command, "error": str(exc)})
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
