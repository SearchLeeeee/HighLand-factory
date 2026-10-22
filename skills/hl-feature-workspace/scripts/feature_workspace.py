"""Governance gate for generic feature workspaces.

This script validates Initiative and Leaf Feature manifests and enforces the
scope-gate, discussion, consistency, closure, dependency, and merge-readiness
state machine, including retained merged-history routing. It is fully
project-agnostic: every workspace location is supplied through explicit
``--registry``, ``--feature``, and ``--initiative`` paths, and no product,
machine, or repository name is assumed.
"""

from __future__ import annotations

import argparse
import copy
import re
import sys
from pathlib import Path
from typing import Any

import yaml

PHASES = [
    "intake",
    "feasibility",
    "scope-gate",
    "discussion",
    "implementation-docs",
    "code-ai-profiles",
    "implementation",
    "review",
    "acceptance",
    "ready-to-merge",
    "merged",
]
STATES = {
    "not-started",
    "in-progress",
    "blocked",
    "ready",
    "completed",
    "cancelled",
    "superseded",
}
CONSISTENCY_DIMENSIONS = ("business", "architecture", "contract", "code", "testing")
CONSISTENCY_STATUSES = {"pending", "in-progress", "aligned", "blocked"}
CONSISTENCY_ENFORCED_PHASES = set(PHASES[PHASES.index("implementation-docs"):])


def consistency_matrix_errors(
    feature: dict[str, Any],
    *,
    document_path: Path | None = None,
    workspace_root: Path | None = None,
    require_aligned: bool = False,
) -> list[str]:
    """Validate the five-party evidence matrix without changing lifecycle state."""
    matrix = feature.get("consistency_matrix")
    if not isinstance(matrix, dict):
        return ["consistency matrix is missing"]

    errors: list[str] = []
    missing = [name for name in CONSISTENCY_DIMENSIONS if name not in matrix]
    unexpected = sorted(set(matrix) - set(CONSISTENCY_DIMENSIONS))
    errors.extend(f"consistency matrix is missing {name}" for name in missing)
    errors.extend(f"consistency matrix has unexpected dimension {name}" for name in unexpected)

    for name in CONSISTENCY_DIMENSIONS:
        entry = matrix.get(name)
        if not isinstance(entry, dict):
            errors.append(f"consistency {name} entry must be a mapping")
            continue
        status = entry.get("status")
        if status not in CONSISTENCY_STATUSES:
            errors.append(f"consistency {name} has invalid status {status}")
        elif require_aligned and status != "aligned":
            errors.append(f"consistency {name} is not aligned")
        owner = entry.get("owner")
        if not isinstance(owner, str) or not owner.strip():
            errors.append(f"consistency {name} has no owner")
        source_refs = entry.get("source_refs")
        if not isinstance(source_refs, list) or not source_refs or not all(isinstance(item, str) and item.strip() for item in source_refs):
            errors.append(f"consistency {name} has no source refs")
        else:
            for raw_ref in source_refs:
                if Path(raw_ref).is_absolute() or raw_ref.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:[\\/]", raw_ref):
                    errors.append(f"consistency {name} source ref must be relative: {raw_ref}")
                    continue
                if document_path is not None and workspace_root is not None:
                    resolved = (document_path.parent / raw_ref).resolve()
                    try:
                        resolved.relative_to(workspace_root.resolve())
                    except ValueError:
                        errors.append(f"consistency {name} source ref points outside workspace: {raw_ref}")
                        continue
                    if not resolved.is_file():
                        errors.append(f"consistency {name} source ref is missing: {raw_ref}")

        targets = entry.get("promotion_targets")
        if not isinstance(targets, list) or not targets or not all(isinstance(item, str) and item.strip() for item in targets):
            errors.append(f"consistency {name} has no promotion targets")
        elif any("feature-workspace" in item.replace("\\", "/").casefold() for item in targets):
            errors.append(f"consistency {name} promotion target must be long-term Wiki authority")

        if status == "blocked" and (not isinstance(entry.get("blocker"), str) or not entry.get("blocker", "").strip()):
            errors.append(f"consistency {name} blocked status has no blocker")

    return sorted(set(errors))


def allocate_initiative_id(registry: dict[str, Any]) -> str:
    number = int(registry.get("next_initiative_number", 1))
    used = {item.get("id") for item in registry.get("initiatives", [])}
    while f"I{number:03d}" in used:
        number += 1
    return f"I{number:03d}"


def allocate_feature_id(initiative: dict[str, Any]) -> str:
    number = int(initiative.get("next_feature_number", 1))
    initiative_id = initiative["id"]
    used = {item.get("id") for item in initiative.get("features", [])}
    while f"{initiative_id}-F{number:02d}" in used:
        number += 1
    return f"{initiative_id}-F{number:02d}"


def transition_feature(
    feature: dict[str, Any],
    *,
    phase: str | None = None,
    state: str,
    next_action: dict[str, str] | None = None,
    blocked_by: list[str] | None = None,
    initial_decomposition_complete: bool | None = None,
) -> dict[str, Any]:
    if state not in STATES:
        raise ValueError(f"invalid state: {state}")
    current_phase = feature.get("phase")
    target_phase = phase or current_phase
    if target_phase not in PHASES:
        raise ValueError(f"invalid phase: {target_phase}")
    if phase and PHASES.index(phase) < PHASES.index(current_phase):
        raise ValueError("phase regression requires a separately documented governance decision")
    if phase and PHASES.index(phase) > PHASES.index(current_phase) + 1:
        raise ValueError("phase transitions may advance only one skill boundary at a time")
    entering_discussion = (
        PHASES.index(current_phase) < PHASES.index("discussion")
        <= PHASES.index(target_phase)
    )
    if entering_discussion:
        entry_errors = discussion_entry_errors(feature)
        if entry_errors:
            raise ValueError("; ".join(entry_errors))
        if initial_decomposition_complete is not True:
            raise ValueError(
                "initiative initial decomposition must be completed before discussion"
            )
    if state not in {"completed", "cancelled", "superseded"} and not next_action:
        raise ValueError("nonterminal transition requires next_action")
    updated = copy.deepcopy(feature)
    updated["phase"] = target_phase
    updated["state"] = state
    if next_action is None:
        updated.pop("next_action", None)
    else:
        updated["next_action"] = next_action
    if blocked_by:
        updated["blocked_by"] = list(blocked_by)
    else:
        updated.pop("blocked_by", None)
    return updated


def scope_verdict(scores: list[int], hard_gates: list[str]) -> str:
    if len(scores) != 8 or any(score < 0 or score > 3 for score in scores):
        raise ValueError("scope scores must contain eight values from 0 through 3")
    if hard_gates:
        return "must-split"
    total = sum(scores)
    if total <= 8:
        return "leaf"
    if total <= 13:
        return "split-default"
    return "must-split"


def discussion_entry_errors(feature: dict[str, Any]) -> list[str]:
    """Return fail-closed errors for a Feature entering discussion."""
    errors: list[str] = []
    if feature.get("leaf") is not True:
        errors.append("feature is not a confirmed leaf")
    gate = feature.get("scope_gate")
    if not isinstance(gate, dict):
        errors.append("scope_gate is missing")
        return errors
    try:
        expected = scope_verdict(gate.get("scores", []), gate.get("hard_gates", []))
    except ValueError as exc:
        errors.append(str(exc))
        return errors
    if gate.get("verdict") != expected:
        errors.append("scope_gate verdict mismatch")
        return errors
    if expected == "must-split":
        errors.append("scope_gate requires splitting before discussion")
    elif expected == "split-default":
        reason = gate.get("indivisibility_reason")
        if not isinstance(reason, str) or not reason.strip():
            errors.append(
                "split-default scope_gate requires a written indivisibility_reason before discussion"
            )
    return errors


def initial_decomposition_errors(
    initiative: dict[str, Any],
    *,
    required: bool = False,
) -> list[str]:
    """Validate the Initiative's frozen initial Leaf Feature inventory."""
    features = initiative.get("features", [])
    discussion_started = any(
        feature.get("state") not in {"completed", "cancelled", "superseded"}
        and feature.get("phase") in PHASES
        and PHASES.index(feature["phase"]) >= PHASES.index("discussion")
        for feature in features
    )
    if not required and not discussion_started:
        return []

    decomposition = initiative.get("initial_decomposition")
    if not isinstance(decomposition, dict) or decomposition.get("status") != "completed":
        return ["initial decomposition is not completed"]

    feature_ids = decomposition.get("feature_ids")
    if (
        not isinstance(feature_ids, list)
        or not feature_ids
        or not all(isinstance(item, str) and item for item in feature_ids)
    ):
        return ["initial decomposition has no feature_ids"]
    if len(feature_ids) != len(set(feature_ids)):
        return ["initial decomposition contains duplicate feature_ids"]

    by_id = {feature.get("id"): feature for feature in features}
    errors: list[str] = []
    for feature_id in feature_ids:
        feature = by_id.get(feature_id)
        if feature is None:
            errors.append(f"initial decomposition references unknown feature {feature_id}")
            continue
        if feature.get("state") in {"completed", "cancelled", "superseded"}:
            continue
        errors.extend(
            f"{feature_id}: {error}" for error in discussion_entry_errors(feature)
        )
    return sorted(set(errors))


def validate_dependency_graph(initiative: dict[str, Any]) -> list[str]:
    features = initiative.get("features", [])
    ids = [item.get("id") for item in features]
    errors: list[str] = []
    if len(ids) != len(set(ids)):
        errors.append("duplicate feature id")
    known = set(ids)
    graph: dict[str, list[str]] = {}
    for item in features:
        feature_id = item.get("id")
        dependencies = item.get("depends_on", [])
        graph[feature_id] = dependencies
        for dependency in dependencies:
            if dependency not in known:
                errors.append(f"{feature_id} has unknown dependency {dependency}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            errors.append(f"dependency cycle contains {node}")
            return
        if node in visited:
            return
        visiting.add(node)
        for dependency in graph.get(node, []):
            visit(dependency)
        visiting.remove(node)
        visited.add(node)

    for feature_id in graph:
        visit(feature_id)
    return sorted(set(errors))


def merge_readiness_errors(
    feature: dict[str, Any],
    initiative: dict[str, Any] | None = None,
) -> list[str]:
    errors: list[str] = []
    errors.extend(consistency_matrix_errors(feature, require_aligned=True))
    if feature.get("leaf") is not True:
        errors.append("feature is not an implementation leaf")
    if feature.get("phase") != "ready-to-merge":
        errors.append("feature phase is not ready-to-merge")
    if feature.get("state") != "ready":
        errors.append("feature state is not ready")
    if feature.get("blocking_children"):
        errors.append("feature has a blocking child")
    if not feature.get("acceptance", {}).get("passed"):
        errors.append("acceptance has not passed")
    closure = feature.get("closure", {})
    if not closure.get("canonical_docs"):
        errors.append("closure has no canonical docs")
    if not closure.get("validation_evidence"):
        errors.append("closure has no validation evidence")
    if not closure.get("tombstone_target"):
        errors.append("closure has no external tombstone target")
    if initiative is not None:
        by_id = {item.get("id"): item for item in initiative.get("features", [])}
        for dependency in feature.get("depends_on", []):
            if not dependency_is_satisfied(by_id.get(dependency, {})):
                errors.append(f"dependency {dependency} is not completed or merge-ready")
    return errors


def dependency_is_satisfied(feature: dict[str, Any]) -> bool:
    """Return whether a feature can satisfy another feature's dependency."""
    if feature.get("state") == "completed":
        return True
    return not merge_readiness_errors(feature)


def ready_features(initiative: dict[str, Any]) -> list[str]:
    features = initiative.get("features", [])
    by_id = {item.get("id"): item for item in features}
    candidates = [
        item
        for item in features
        if item.get("state") == "ready"
        and all(
            dependency_is_satisfied(by_id.get(dependency, {}))
            for dependency in item.get("depends_on", [])
        )
    ]
    if not candidates:
        return []
    minimum_wave = min(item.get("wave", 0) for item in candidates)
    return sorted(item["id"] for item in candidates if item.get("wave", 0) == minimum_wave)


def integration_testing_errors(initiative: dict[str, Any]) -> list[str]:
    integration = initiative.get("integration_testing")
    if not isinstance(integration, dict):
        return ["initiative integration testing handoff is missing"]
    handoff = integration.get("handoff")
    if not isinstance(handoff, str) or not handoff:
        return ["initiative integration testing handoff is missing"]
    manifest_path = initiative.get("_manifest_path")
    if manifest_path and not (Path(manifest_path).parent / handoff).is_file():
        return [f"initiative integration testing handoff is missing: {handoff}"]
    if integration.get("passed") is not True:
        return ["initiative integration testing has not passed"]
    evidence = integration.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        return ["initiative integration testing has no evidence"]
    if manifest_path:
        root = Path(manifest_path).parent
        missing = [item for item in evidence if not isinstance(item, str) or not (root / item).is_file()]
        if missing:
            return ["initiative integration testing evidence is missing: " + ", ".join(map(str, missing))]
    return []


def initiative_merge_readiness_errors(initiative: dict[str, Any]) -> list[str]:
    """Require full ready state plus passed Initiative integration testing before merge."""
    errors = integration_testing_errors(initiative)
    for feature in initiative.get("features", []):
        if feature.get("leaf") is not True or feature.get("state") in {"cancelled", "superseded"}:
            continue
        feature_errors = merge_readiness_errors(feature, initiative)
        if feature_errors:
            feature_id = feature.get("id", "<missing>")
            errors.extend(f"{feature_id}: {error}" for error in feature_errors)
    return errors


def render_integration_handoff(initiative: dict[str, Any]) -> str:
    lines = [f"# {initiative['id']} Integration Test Handoff", "", "## Merge Gate", "", "All active Leaf Features are ready. Integration testing must pass and record evidence before any Feature merge.", "", "## Included Features", ""]
    for feature in sorted(initiative.get("features", []), key=lambda item: item.get("id", "")):
        if feature.get("leaf") is not True or feature.get("state") in {"cancelled", "superseded"}:
            continue
        lines.extend([f"### `{feature['id']}` {feature.get('title', '')}", ""])
        dependencies = feature.get("depends_on", [])
        lines.append("- Dependencies: " + (", ".join(f"`{item}`" for item in dependencies) if dependencies else "none"))
        acceptance = feature.get("acceptance", {}).get("evidence", [])
        lines.append("- Acceptance evidence:")
        lines.extend(f"  - `{item}`" for item in acceptance) if acceptance else lines.append("  - none recorded")
        validation = feature.get("closure", {}).get("validation_evidence", [])
        lines.append("- Closure validation:")
        lines.extend(f"  - `{item}`" for item in validation) if validation else lines.append("  - none recorded")
        lines.append("")
    lines.extend(["## Required Evidence", "", "- End-to-end dependency-chain execution results.", "- Cross-Feature contract and boundary assertions.", "- Production-safety, redaction, and negative-path results where applicable.", "- Exact commands, environment identity, timestamps, and immutable evidence paths.", "", "## Result", "", "Record PASS only through `initiative-integration-result` after every required test passes. A failure blocks all Feature merges for this Initiative.", ""])
    return "\n".join(lines)


def render_progress(registry: dict[str, Any]) -> str:
    snapshot = copy.deepcopy(registry)
    lines = ["# Feature Progress", ""]
    for initiative in sorted(snapshot.get("initiatives", []), key=lambda item: item["id"]):
        lines.append(
            f"## {initiative['id']} {initiative.get('title', '')} "
            f"[{initiative.get('state', 'unknown')}]"
        )
        decomposition = initiative.get("initial_decomposition")
        if (
            initiative.get("state") not in {"completed", "cancelled", "superseded"}
            and (
                not isinstance(decomposition, dict)
                or decomposition.get("status") != "completed"
            )
        ):
            lines.append(
                "- Next: $hl-feature-workspace - complete the initial Feature "
                "inventory, Scope Gates, dependencies, Waves, and finalize-decomposition"
            )
        for feature in sorted(initiative.get("features", []), key=lambda item: item["id"]):
            lines.append(
                f"- {feature['id']} {feature.get('title', '')}: "
                f"{feature.get('phase', 'unknown')} / {feature.get('state', 'unknown')}"
            )
            next_action = feature.get("next_action")
            if next_action:
                lines.append(
                    f"  Next: ${next_action.get('skill', 'unspecified')} - "
                    f"{next_action.get('instruction', 'no instruction')}"
                )
        ready = ready_features(initiative)
        if ready:
            lines.append(f"- Ready in parallel: {', '.join(ready)}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data or {}


def write_yaml(path: Path, value: dict[str, Any]) -> None:
    """Persist a workspace manifest as UTF-8 YAML, preserving key order + non-ASCII."""
    text = yaml.safe_dump(value, sort_keys=False, allow_unicode=True, default_flow_style=False)
    path.write_text(text, encoding="utf-8")


def write_feature(path: Path, feature: dict[str, Any]) -> None:
    write_yaml(path, feature)


def apply_transition(
    feature_path: Path,
    *,
    state: str,
    phase: str | None = None,
    next_action: dict[str, str] | None = None,
    blocked_by: list[str] | None = None,
    initial_decomposition_complete: bool | None = None,
) -> dict[str, Any]:
    """Apply a governance-checked lifecycle transition and persist it to disk.

    Loads the feature manifest, validates + applies the transition via
    ``transition_feature`` (which enforces no phase regression, one-phase-at-a-time,
    and next_action on nonterminal states), and writes the result back.  Any
    governance violation raises before the file is touched.
    """
    feature = load_yaml(feature_path)
    updated = transition_feature(
        feature,
        phase=phase,
        state=state,
        next_action=next_action,
        blocked_by=blocked_by,
        initial_decomposition_complete=initial_decomposition_complete,
    )
    write_feature(feature_path, updated)
    return updated


def retained_merged_feature_root(path: Path, workspace_root: Path) -> Path | None:
    """Return the retained merged Feature root containing path, if any.

    Retained sources remain on disk for provenance but are deliberately excluded
    from active context discovery. A merged/completed feature manifest marks that
    authority boundary.
    """
    workspace = workspace_root.resolve()
    current = path.resolve() if path.is_dir() else path.resolve().parent
    while True:
        try:
            current.relative_to(workspace)
        except ValueError:
            return None
        manifest_path = current / "feature.yaml"
        if manifest_path.is_file():
            manifest = load_yaml(manifest_path)
            if manifest.get("phase") == "merged" and manifest.get("state") == "completed":
                return current
        if current == workspace:
            return None
        current = current.parent


def validate_context_refs(
    document: dict[str, Any],
    *,
    document_path: Path,
    workspace_root: Path,
) -> list[str]:
    refs = document.get("context_refs", [])
    if refs is None:
        return []
    if not isinstance(refs, list):
        return ["context refs must be a list"]

    errors: list[str] = []
    seen: set[str] = set()
    workspace = workspace_root.resolve()
    for index, ref in enumerate(refs):
        label = f"context ref #{index + 1}"
        if not isinstance(ref, dict):
            errors.append(f"{label} must be a mapping")
            continue
        raw_path = ref.get("path")
        if not isinstance(raw_path, str) or not raw_path.strip():
            errors.append(f"{label} has missing path")
            continue
        required = ref.get("required", False)
        if not isinstance(required, bool):
            errors.append(f"{label} required must be boolean")
            continue
        if raw_path in seen:
            errors.append(f"{label} duplicates path {raw_path}")
            continue
        seen.add(raw_path)

        relative = Path(raw_path)
        if relative.is_absolute():
            errors.append(f"{label} path must be relative: {raw_path}")
            continue
        resolved = (document_path.parent / relative).resolve()
        try:
            resolved.relative_to(workspace)
        except ValueError:
            errors.append(f"{label} points outside workspace: {raw_path}")
            continue
        if retained_merged_feature_root(resolved, workspace_root) is not None:
            errors.append(
                f"{label} points into retained merged Feature source: {raw_path}; "
                "use canonical long-term wiki authority instead"
            )
            continue
        if required and not resolved.is_file():
            errors.append(f"{label} required file is missing: {raw_path}")
    return sorted(set(errors))


def load_registry(path: Path) -> dict[str, Any]:
    registry = load_yaml(path)
    root = path.parent
    resolved_initiatives: list[dict[str, Any]] = []
    for entry in registry.get("initiatives", []):
        if entry.get("manifest"):
            initiative_path = root / entry["manifest"]
            initiative = load_yaml(initiative_path)
            initiative["_manifest_path"] = str(initiative_path)
            initiative_context_errors = validate_context_refs(
                initiative,
                document_path=initiative_path,
                workspace_root=root,
            )
            if initiative_context_errors:
                initiative["_context_ref_errors"] = initiative_context_errors
            if initiative.get("id") != entry.get("id"):
                initiative["_reference_error"] = "initiative id does not match registry entry"
            initiative_root = initiative_path.parent
            resolved_features: list[dict[str, Any]] = []
            for feature_entry in initiative.get("features", []):
                if feature_entry.get("manifest"):
                    feature = load_yaml(initiative_root / feature_entry["manifest"])
                    feature_path = initiative_root / feature_entry["manifest"]
                    feature["_source_manifest_path"] = str(feature_path)
                    feature["_workspace_root"] = str(root)
                    feature_context_errors = validate_context_refs(
                        feature,
                        document_path=feature_path,
                        workspace_root=root,
                    )
                    if feature_context_errors:
                        feature["_context_ref_errors"] = feature_context_errors
                    if feature.get("id") != feature_entry.get("id"):
                        feature["_reference_error"] = "feature id does not match initiative entry"
                    resolved_features.append(feature)
                else:
                    inline_feature = copy.deepcopy(feature_entry)
                    inline_feature["_container_manifest_path"] = str(initiative_path)
                    inline_feature["_workspace_root"] = str(root)
                    resolved_features.append(inline_feature)
            initiative["features"] = resolved_features
            resolved_initiatives.append(initiative)
        else:
            resolved_initiatives.append(entry)
    registry["initiatives"] = resolved_initiatives
    return registry


def merged_routing_errors(feature: dict[str, Any]) -> list[str]:
    """Validate the retained-history routing record for a merged Feature."""
    if feature.get("phase") != "merged":
        return []
    errors: list[str] = []
    if feature.get("state") != "completed":
        errors.append("merged Feature state is not completed")
    if feature.get("_source_manifest_path"):
        errors.append("merged Feature source remains actively referenced by manifest")
    canonical = feature.get("canonical_docs")
    if not isinstance(canonical, list) or not canonical or not all(isinstance(item, str) and item for item in canonical):
        errors.append("merged routing record has no canonical docs")
    elif any("feature-workspace/" in item.replace("\\", "/").casefold() for item in canonical):
        errors.append("merged canonical docs must not point into feature-workspace history")
    evidence = feature.get("merge_evidence")
    if not isinstance(evidence, list) or not evidence or not all(isinstance(item, str) and item for item in evidence):
        errors.append("merged routing record has no merge evidence")
    retained = feature.get("retained_source")
    required = ("path", "marker", "route", "checksum_manifest")
    if not isinstance(retained, dict):
        errors.append("merged routing record has no retained source metadata")
        return errors
    for key in required:
        if not isinstance(retained.get(key), str) or not retained[key]:
            errors.append(f"merged retained source has no {key}")

    container = feature.get("_container_manifest_path")
    workspace_raw = feature.get("_workspace_root")
    if container and workspace_raw and not any(error.startswith("merged retained source has no") for error in errors):
        base = Path(container).parent.resolve()
        workspace = Path(workspace_raw).resolve()
        source_root = (base / retained["path"]).resolve()
        try:
            source_root.relative_to(workspace)
        except ValueError:
            errors.append("merged retained source points outside workspace")
            return errors
        if not source_root.is_dir():
            errors.append("merged retained source directory is missing")
            return errors
        for key in ("marker", "route", "checksum_manifest"):
            target = (source_root / retained[key]).resolve()
            try:
                target.relative_to(source_root)
            except ValueError:
                errors.append(f"merged retained source {key} points outside retained root")
                continue
            if not target.is_file():
                errors.append(f"merged retained source {key} is missing")
    return errors


def validate_registry(registry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    initiatives = registry.get("initiatives", [])
    initiative_ids = [item.get("id") for item in initiatives]
    if len(initiative_ids) != len(set(initiative_ids)):
        errors.append("duplicate initiative id")
    for initiative in initiatives:
        initiative_id = initiative.get("id", "<missing>")
        if not re.fullmatch(r"I\d{3,}", str(initiative_id)):
            errors.append(f"{initiative_id}: invalid initiative id")
        if initiative.get("_reference_error"):
            errors.append(f"{initiative_id}: {initiative['_reference_error']}")
        for context_error in initiative.get("_context_ref_errors", []):
            errors.append(f"{initiative_id}: {context_error}")
        if initiative.get("state") not in STATES:
            errors.append(f"{initiative_id}: invalid initiative state {initiative.get('state')}")
        errors.extend(
            f"{initiative_id}: {error}"
            for error in validate_dependency_graph(initiative)
        )
        errors.extend(
            f"{initiative_id}: {error}"
            for error in initial_decomposition_errors(initiative)
        )
        feature_ids = {item.get("id") for item in initiative.get("features", [])}
        for feature in initiative.get("features", []):
            feature_id = feature.get("id")
            if not re.fullmatch(rf"{re.escape(str(initiative_id))}-F\d{{2,}}", str(feature_id)):
                errors.append(f"{feature_id}: invalid feature id or parent")
            if feature.get("_reference_error"):
                errors.append(f"{feature_id}: {feature['_reference_error']}")
            for context_error in feature.get("_context_ref_errors", []):
                errors.append(f"{feature_id}: {context_error}")
            phase = feature.get("phase")
            state = feature.get("state")
            if phase not in PHASES:
                errors.append(f"{feature_id}: invalid phase {phase}")
            if state not in STATES:
                errors.append(f"{feature_id}: invalid state {state}")
            terminal = state in {"completed", "cancelled", "superseded"}
            if not terminal and feature.get("leaf") is not True:
                errors.append(f"{feature_id}: active implementation item must be a leaf")
            if not terminal and not feature.get("next_action"):
                errors.append(f"{feature_id}: missing next_action")
            wave = feature.get("wave")
            if not terminal and (not isinstance(wave, int) or wave < 1):
                errors.append(f"{feature_id}: wave must be a positive integer")
            for blocker in feature.get("blocking_children", []):
                if blocker not in feature_ids:
                    errors.append(f"{feature_id}: unknown blocking child {blocker}")
            if phase in PHASES[PHASES.index("discussion"):] and not terminal:
                errors.extend(
                    f"{feature_id}: {error}"
                    for error in discussion_entry_errors(feature)
                )
            if phase in CONSISTENCY_ENFORCED_PHASES and not terminal:
                manifest_path = Path(feature["_source_manifest_path"]) if feature.get("_source_manifest_path") else None
                workspace_path = Path(feature["_workspace_root"]) if feature.get("_workspace_root") else None
                errors.extend(
                    f"{feature_id}: {error}"
                    for error in consistency_matrix_errors(
                        feature,
                        document_path=manifest_path,
                        workspace_root=workspace_path,
                    )
                )
            if phase == "ready-to-merge":
                errors.extend(f"{feature_id}: {error}" for error in merge_readiness_errors(feature, initiative))
            if phase == "merged":
                errors.extend(f"{feature_id}: {error}" for error in merged_routing_errors(feature))
    return sorted(set(errors))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate and report generic feature workspaces.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("validate", "report"):
        child = subparsers.add_parser(command)
        child.add_argument("--registry", type=Path, required=True)
    merge_parser = subparsers.add_parser("merge-ready")
    merge_parser.add_argument("--feature", type=Path, required=True)
    initiative_merge_parser = subparsers.add_parser("initiative-merge-ready")
    initiative_merge_parser.add_argument("--registry", type=Path, required=True)
    initiative_merge_parser.add_argument("--initiative", required=True)
    handoff_parser = subparsers.add_parser("initiative-integration-handoff")
    handoff_parser.add_argument("--registry", type=Path, required=True)
    handoff_parser.add_argument("--initiative", required=True)
    handoff_parser.add_argument("--output", type=Path, required=True)
    result_parser = subparsers.add_parser("initiative-integration-result")
    result_parser.add_argument("--registry", type=Path, required=True)
    result_parser.add_argument("--initiative", required=True)
    result_parser.add_argument("--evidence", action="append", required=True)
    decomposition_parser = subparsers.add_parser(
        "finalize-decomposition",
        description="Freeze the initial dependency-ready Leaf Feature inventory before discussion.",
    )
    decomposition_parser.add_argument("--registry", type=Path, required=True)
    decomposition_parser.add_argument("--initiative", required=True)
    transition_parser = subparsers.add_parser(
        "transition",
        description="Apply a governance-checked lifecycle transition to a feature manifest.",
    )
    transition_parser.add_argument("--feature", type=Path, required=True)
    transition_parser.add_argument("--state", required=True)
    transition_parser.add_argument("--phase", default=None)
    transition_parser.add_argument("--next-skill", default=None)
    transition_parser.add_argument("--next-instruction", default=None)
    transition_parser.add_argument("--blocked-by", nargs="*", default=None)
    transition_parser.add_argument("--registry", type=Path, default=None)
    transition_parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    if args.command in {"initiative-integration-handoff", "initiative-integration-result"}:
        raw_registry = load_yaml(args.registry)
        entry = next((item for item in raw_registry.get("initiatives", []) if item.get("id") == args.initiative), None)
        if entry is None or not entry.get("manifest"):
            print(f"ERROR: unknown initiative {args.initiative}", file=sys.stderr)
            return 1
        manifest_path = args.registry.parent / entry["manifest"]
        initiative = load_yaml(manifest_path)
        if args.command == "initiative-integration-handoff":
            output = args.output.resolve()
            try:
                relative_output = output.relative_to(manifest_path.parent.resolve())
            except ValueError:
                print("ERROR: handoff output must stay inside the initiative directory", file=sys.stderr)
                return 1
            resolved_registry = load_registry(args.registry)
            resolved_initiative = next(
                item for item in resolved_registry.get("initiatives", []) if item.get("id") == args.initiative
            )
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(render_integration_handoff(resolved_initiative), encoding="utf-8")
            initiative["integration_testing"] = {"handoff": relative_output.as_posix(), "passed": False, "evidence": []}
            handoff_ref = {"path": relative_output.as_posix(), "kind": "integration-test-handoff", "required": True}
            refs = initiative.setdefault("context_refs", [])
            if not any(ref.get("path") == handoff_ref["path"] for ref in refs if isinstance(ref, dict)):
                refs.append(handoff_ref)
            write_yaml(manifest_path, initiative)
            print(f"wrote integration handoff: {output}")
            return 0
        integration = initiative.get("integration_testing")
        if not isinstance(integration, dict) or not integration.get("handoff"):
            print("ERROR: generate the initiative integration handoff first", file=sys.stderr)
            return 1
        evidence = []
        for raw_path in args.evidence:
            candidate = Path(raw_path).resolve()
            try:
                evidence.append(candidate.relative_to(manifest_path.parent.resolve()).as_posix())
            except ValueError:
                print("ERROR: integration evidence must stay inside the initiative directory", file=sys.stderr)
                return 1
            if not candidate.is_file():
                print(f"ERROR: integration evidence is missing: {candidate}", file=sys.stderr)
                return 1
        integration.update({"passed": True, "evidence": evidence})
        initiative["integration_testing"] = integration
        write_yaml(manifest_path, initiative)
        print(f"recorded integration testing PASS for {args.initiative}")
        return 0

    if args.command == "finalize-decomposition":
        raw_registry = load_yaml(args.registry)
        entry = next(
            (
                item
                for item in raw_registry.get("initiatives", [])
                if item.get("id") == args.initiative
            ),
            None,
        )
        if entry is None or not entry.get("manifest"):
            print(f"ERROR: unknown initiative {args.initiative}", file=sys.stderr)
            return 1
        manifest_path = args.registry.parent / entry["manifest"]
        raw_initiative = load_yaml(manifest_path)
        registry = load_registry(args.registry)
        initiative = next(
            item
            for item in registry.get("initiatives", [])
            if item.get("id") == args.initiative
        )
        active_features = [
            feature
            for feature in initiative.get("features", [])
            if feature.get("state") not in {"completed", "cancelled", "superseded"}
        ]
        record = {
            "status": "completed",
            "feature_ids": sorted(feature["id"] for feature in active_features),
        }
        initiative["initial_decomposition"] = record
        errors = validate_registry(registry)
        errors.extend(
            f"{args.initiative}: {error}"
            for error in initial_decomposition_errors(initiative, required=True)
        )
        if not active_features:
            errors.append(f"{args.initiative}: initial decomposition has no active Feature")
        if errors:
            for error in sorted(set(errors)):
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        raw_initiative["initial_decomposition"] = record
        write_yaml(manifest_path, raw_initiative)
        print(
            f"finalized initial decomposition for {args.initiative}: "
            + ", ".join(record["feature_ids"])
        )
        return 0

    if args.command == "initiative-merge-ready":
        registry = load_registry(args.registry)
        initiatives = {item.get("id"): item for item in registry.get("initiatives", [])}
        initiative = initiatives.get(args.initiative)
        if initiative is None:
            print(f"ERROR: unknown initiative {args.initiative}", file=sys.stderr)
            return 1
        errors = initiative_merge_readiness_errors(initiative)
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        print(f"initiative {args.initiative} is ready for ordered feature merges")
        return 0

    if args.command in {"validate", "report"}:
        registry = load_registry(args.registry)
        errors = validate_registry(registry)
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        if args.command == "report":
            print(render_progress(registry), end="")
        else:
            print("feature workspace is valid")
        return 0

    if args.command == "transition":
        next_action: dict[str, str] | None = None
        if args.next_skill or args.next_instruction:
            if not (args.next_skill and args.next_instruction):
                print(
                    "ERROR: --next-skill and --next-instruction must be provided together",
                    file=sys.stderr,
                )
                return 1
            next_action = {"skill": args.next_skill, "instruction": args.next_instruction}
        feature = load_yaml(args.feature)
        target_phase = args.phase or feature.get("phase")
        entering_discussion = (
            feature.get("phase") in PHASES
            and target_phase in PHASES
            and PHASES.index(feature["phase"]) < PHASES.index("discussion")
            <= PHASES.index(target_phase)
        )
        initial_decomposition_complete: bool | None = None
        if entering_discussion:
            if args.registry is None:
                print(
                    "ERROR: --registry is required when entering discussion",
                    file=sys.stderr,
                )
                return 1
            registry = load_registry(args.registry)
            initiative = next(
                (
                    item
                    for item in registry.get("initiatives", [])
                    if any(
                        candidate.get("id") == feature.get("id")
                        for candidate in item.get("features", [])
                    )
                ),
                None,
            )
            if initiative is None:
                print("ERROR: feature is not registered under an Initiative", file=sys.stderr)
                return 1
            decomposition_errors = initial_decomposition_errors(
                initiative, required=True
            )
            if decomposition_errors:
                for error in decomposition_errors:
                    print(f"ERROR: {error}", file=sys.stderr)
                return 1
            initial_decomposition_complete = True
        try:
            if args.dry_run:
                updated = transition_feature(
                    feature,
                    phase=args.phase,
                    state=args.state,
                    next_action=next_action,
                    blocked_by=args.blocked_by,
                    initial_decomposition_complete=initial_decomposition_complete,
                )
                print(
                    yaml.safe_dump(
                        updated, sort_keys=False, allow_unicode=True, default_flow_style=False
                    ),
                    end="",
                )
            else:
                updated = apply_transition(
                    args.feature,
                    state=args.state,
                    phase=args.phase,
                    next_action=next_action,
                    blocked_by=args.blocked_by,
                    initial_decomposition_complete=initial_decomposition_complete,
                )
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        print(
            f"transitioned {args.feature.name}: "
            f"phase={updated.get('phase')} state={updated.get('state')}"
        )
        if args.registry is not None:
            registry = load_registry(args.registry)
            errors = validate_registry(registry)
            if errors:
                for error in errors:
                    print(f"ERROR: {error}", file=sys.stderr)
                return 1
            print("feature workspace is valid")
        return 0

    feature = load_yaml(args.feature)
    errors = merge_readiness_errors(feature)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("feature is ready to merge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
