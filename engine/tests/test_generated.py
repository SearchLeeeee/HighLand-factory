"""Unit tests for generated workflow-profile fragments."""

from __future__ import annotations

from pathlib import Path

from factorylib import config
from factorylib.generated import GeneratedBlocks
from factorylib.layout import build_layout


def _blocks(tmp_path: Path) -> GeneratedBlocks:
    cfg = config.default_config()
    cfg["project"]["name"] = "Example"
    cfg["project"]["slug"] = "example"
    layout = build_layout(tmp_path, cfg)
    return GeneratedBlocks(cfg, layout)


def test_gates_fragment_lists_every_policy_switch(tmp_path: Path) -> None:
    text = _blocks(tmp_path).workflow_profile_gates()
    for key in (
        "scope_gate",
        "quick_change",
        "review_required",
        "verification_separate",
        "merge_requires_authorization",
        "initiative_integration_required",
    ):
        assert key in text


def test_gates_fragment_has_no_parallelism_cap(tmp_path: Path) -> None:
    text = _blocks(tmp_path).workflow_profile_gates()
    assert "max_parallel_features" not in text


def test_profile_layout_uses_actual_wiki_and_registered_roots(tmp_path: Path) -> None:
    cfg = config.default_config()
    cfg["repo"]["wiki_path"] = "docs/current"
    cfg["workflow"]["process_workspaces"] = ["temporary/audit"]
    blocks = GeneratedBlocks(cfg, build_layout(tmp_path, cfg))
    for text in (blocks.workflow_profile_layout(), blocks.repo_layout_table()):
        assert "docs/current/refactor-workspace/" in text
        assert "docs/current/temporary/audit/" in text
        assert "wiki/refactor-workspace/" not in text
