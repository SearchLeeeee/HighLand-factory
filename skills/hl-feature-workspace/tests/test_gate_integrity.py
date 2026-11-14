"""Exercise gate decisions and failed writes through the public command path."""

import importlib.util
import re
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml


@pytest.fixture
def fw():
    path = Path(__file__).parents[1] / "scripts" / "feature_workspace.py"
    spec = importlib.util.spec_from_file_location("gate_integrity_workspace", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def workspace(tmp_path, fw):
    root = tmp_path / "workspace"
    feature_path = root / "initiative" / "feature" / "feature.yaml"
    feature_path.parent.mkdir(parents=True)
    feature = {
        "id": "I007-F01", "title": "Example", "leaf": True,
        "phase": "acceptance", "state": "completed", "wave": 1,
        "depends_on": [],
        "scope_gate": {"scores": [1] * 8, "hard_gates": [], "verdict": "leaf"},
        "acceptance": {"passed": True, "evidence": ["acceptance.md"]},
        "closure": {
            "canonical_docs": ["implementation/example.md"],
            "validation_evidence": ["validation.md"],
            "tombstone_target": "../../registry.yaml",
        },
        "consistency_matrix": {
            name: {
                "status": "aligned", "owner": "core",
                "source_refs": ["source.md"],
                "promotion_targets": ["implementation/example.md"],
            }
            for name in ("business", "architecture", "contract", "code", "testing")
        },
    }
    for name in ("acceptance.md", "validation.md", "source.md"):
        (feature_path.parent / name).write_text("Synthetic evidence\n", encoding="utf-8")
    fw.write_yaml(feature_path, feature)
    fw.write_yaml(root / "initiative" / "initiative.yaml", {
        "id": "I007", "state": "in-progress",
        "initial_decomposition": {"status": "completed", "feature_ids": ["I007-F01"]},
        "features": [{"id": "I007-F01", "manifest": "feature/feature.yaml"}],
    })
    registry = root / "registry.yaml"
    fw.write_yaml(registry, {
        "initiatives": [{"id": "I007", "manifest": "initiative/initiative.yaml"}],
    })
    return registry, feature_path


def transition(fw, workspace, *extra):
    registry, feature_path = workspace
    return fw.main([
        "transition", "--registry", str(registry), "--feature", str(feature_path),
        "--phase", "ready-to-merge", "--state", "ready",
        "--next-skill", "hl-wiki-merge", "--next-instruction", "Merge after preflight",
        *extra,
    ])


@pytest.mark.parametrize("passed", [False, "false", "true", 1, None])
def test_non_boolean_true_never_releases_ready_or_writes(fw, workspace, passed):
    _, path = workspace
    feature = fw.load_yaml(path)
    feature["acceptance"]["passed"] = passed
    fw.write_yaml(path, feature)
    before = path.read_bytes()
    assert transition(fw, workspace) == 1
    assert path.read_bytes() == before
    feature.update(phase="ready-to-merge", state="ready")
    assert fw.merge_readiness_errors(feature)


@pytest.mark.parametrize("field", ["acceptance", "closure"])
@pytest.mark.parametrize("evidence", [[], "acceptance.md", [""], [None], ["missing.md"], ["."]])
def test_malformed_or_missing_evidence_rejected_by_all_gate_entrypoints(fw, workspace, field, evidence):
    registry, path = workspace
    feature = fw.load_yaml(path)
    key = "evidence" if field == "acceptance" else "validation_evidence"
    feature[field][key] = evidence
    feature.update(phase="ready-to-merge", state="ready", next_action={"skill": "hl-wiki-merge", "instruction": "Merge"})
    fw.write_yaml(path, feature)
    before = path.read_bytes()
    assert fw.main(["validate", "--registry", str(registry)]) == 1
    assert fw.main(["merge-ready", "--feature", str(path)]) == 1
    assert transition(fw, workspace) == 1
    assert path.read_bytes() == before


def test_valid_ready_uses_manifest_relative_evidence_and_keeps_future_targets(fw, workspace, monkeypatch, tmp_path):
    registry, path = workspace
    monkeypatch.chdir(tmp_path)
    assert transition(fw, workspace) == 0
    assert fw.main(["validate", "--registry", str(registry)]) == 0
    assert fw.main(["merge-ready", "--feature", str(path)]) == 0
    assert not (path.parent / "implementation" / "example.md").exists()
    assert not list(path.parent.glob("*.tmp"))


def test_invalid_sibling_rejects_candidate_without_touching_any_manifest(fw, workspace):
    registry, path = workspace
    initiative_path = registry.parent / "initiative" / "initiative.yaml"
    initiative = fw.load_yaml(initiative_path)
    initiative["features"].append({"id": "I007-F02", "leaf": True, "phase": "intake", "state": "in-progress", "wave": 0})
    fw.write_yaml(initiative_path, initiative)
    before = {p: p.read_bytes() for p in (registry, path, initiative_path)}
    assert transition(fw, workspace) == 1
    assert all(p.read_bytes() == content for p, content in before.items())


def test_unregistered_candidate_cannot_claim_registry_validation(fw, workspace):
    registry, path = workspace
    other = path.with_name("unregistered.yaml")
    fw.write_yaml(other, fw.load_yaml(path))
    before = other.read_bytes()
    assert fw.main([
        "transition", "--registry", str(registry), "--feature", str(other),
        "--phase", "ready-to-merge", "--state", "ready",
        "--next-skill", "hl-wiki-merge", "--next-instruction", "Merge",
    ]) == 1
    assert other.read_bytes() == before


def test_dry_run_validates_same_candidate_without_writing(fw, workspace):
    _, path = workspace
    before = path.read_bytes()
    assert transition(fw, workspace, "--dry-run") == 0
    assert path.read_bytes() == before
    feature = fw.load_yaml(path)
    feature["acceptance"]["passed"] = False
    fw.write_yaml(path, feature)
    before = path.read_bytes()
    assert transition(fw, workspace, "--dry-run") == 1
    assert path.read_bytes() == before


def test_direct_transition_cannot_bypass_ready_gate(fw, workspace):
    _, path = workspace
    feature = fw.load_yaml(path)
    feature["acceptance"]["passed"] = False
    fw.write_yaml(path, feature)
    before = path.read_bytes()
    with pytest.raises(ValueError, match="acceptance"):
        fw.apply_transition(path, phase="ready-to-merge", state="ready", next_action={"skill": "hl-wiki-merge", "instruction": "Merge"})
    assert path.read_bytes() == before


def test_replace_failure_preserves_original_and_cleans_temporary_file(fw, workspace):
    _, path = workspace
    before = path.read_bytes()
    with patch("os.replace", side_effect=OSError("synthetic replace failure")):
        with pytest.raises(OSError, match="synthetic replace failure"):
            fw.write_yaml(path, {"state": "ready"})
    assert path.read_bytes() == before
    assert not list(path.parent.glob("*.tmp"))


@pytest.mark.parametrize("section,value", [("acceptance", None), ("acceptance", []), ("closure", [])])
def test_malformed_gate_sections_return_errors_instead_of_crashing(fw, workspace, section, value):
    registry, path = workspace
    feature = fw.load_yaml(path)
    feature[section] = value
    feature.update(phase="ready-to-merge", state="ready", next_action={"skill": "hl-wiki-merge", "instruction": "Merge"})
    fw.write_yaml(path, feature)
    assert fw.main(["validate", "--registry", str(registry)]) == 1
    assert fw.main(["merge-ready", "--feature", str(path)]) == 1


def test_evidence_paths_cannot_escape_registry_workspace(fw, workspace, tmp_path):
    _, path = workspace
    outside = tmp_path / "outside.md"
    outside.write_text("Synthetic outside evidence", encoding="utf-8")
    feature = fw.load_yaml(path)
    feature["acceptance"]["evidence"] = ["../../../outside.md"]
    fw.write_yaml(path, feature)
    assert transition(fw, workspace) == 1
    feature["acceptance"]["evidence"] = [str(outside.resolve())]
    fw.write_yaml(path, feature)
    assert transition(fw, workspace) == 1


def test_schema_closure_example_is_accepted_by_real_gate(fw, workspace):
    _, path = workspace
    schema = Path(__file__).parents[3] / "templates" / "workspace" / "wiki" / "feature-workspace" / "schema" / "feature-workspace-schema.md"
    examples = [yaml.safe_load(block) for block in re.findall(r"```yaml\s*\n(.*?)```", schema.read_text(encoding="utf-8"), re.DOTALL)]
    example = next(item for item in examples if isinstance(item, dict) and "acceptance" in item and "closure" in item)
    feature = fw.load_yaml(path)
    feature.update(example)
    for raw in example["acceptance"]["evidence"] + example["closure"]["validation_evidence"]:
        evidence = path.parent / raw
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_text("Synthetic evidence for schema contract", encoding="utf-8")
    fw.write_yaml(path, feature)
    assert transition(fw, workspace) == 0


def test_integration_pass_rejected_before_write_when_leaf_not_ready(fw, workspace):
    registry, _ = workspace
    initiative_path = registry.parent / "initiative" / "initiative.yaml"
    handoff = initiative_path.parent / "handoff.md"
    result = initiative_path.parent / "result.md"
    handoff.write_text("Synthetic handoff", encoding="utf-8")
    result.write_text("Synthetic result", encoding="utf-8")
    initiative = fw.load_yaml(initiative_path)
    initiative["integration_testing"] = {"handoff": "handoff.md", "passed": False, "evidence": []}
    fw.write_yaml(initiative_path, initiative)
    before = initiative_path.read_bytes()
    command = ["initiative-integration-result", "--registry", str(registry), "--initiative", "I007", "--evidence", str(result)]
    assert fw.main(command) == 1
    assert initiative_path.read_bytes() == before
    assert transition(fw, workspace) == 0
    assert fw.main(command) == 0
    assert fw.main(["initiative-merge-ready", "--registry", str(registry), "--initiative", "I007"]) == 0


@pytest.mark.parametrize("inline_initiative", [False, True])
@pytest.mark.parametrize("missing", [None, "context", "matrix"])
def test_inline_records_obey_the_same_reference_gates(fw, workspace, inline_initiative, missing):
    registry, feature_path = workspace
    initiative_path = registry.parent / "initiative" / "initiative.yaml"
    base = registry.parent if inline_initiative else initiative_path.parent
    feature = fw.load_yaml(feature_path)
    feature.update(phase="ready-to-merge", state="ready", next_action={"skill": "hl-wiki-merge", "instruction": "Merge"})
    feature["acceptance"]["evidence"] = [(feature_path.parent / "acceptance.md").relative_to(base).as_posix()]
    feature["closure"]["validation_evidence"] = [(feature_path.parent / "validation.md").relative_to(base).as_posix()]
    for entry in feature["consistency_matrix"].values():
        entry["source_refs"] = ["missing.md" if missing == "matrix" else (feature_path.parent / "source.md").relative_to(base).as_posix()]
    if missing == "context":
        feature["context_refs"] = [{"path": "missing.md", "required": True}]
    initiative = fw.load_yaml(initiative_path)
    initiative["features"] = [feature]
    if inline_initiative:
        fw.write_yaml(registry, {"initiatives": [initiative]})
    else:
        fw.write_yaml(initiative_path, initiative)
    assert fw.main(["validate", "--registry", str(registry)]) == (0 if missing is None else 1)
