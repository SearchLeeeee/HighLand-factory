"""Process roots are explicit, portable and backwards-compatible."""

from pathlib import Path

import pytest

from factorylib import config
from factorylib.workspaces import (
    DEFAULT_PROCESS_WORKSPACES,
    is_process_path,
    process_workspace_names,
    process_workspace_roots,
    project_config_for_wiki,
)


def test_older_config_keeps_defaults_and_new_roots_are_additive(tmp_path: Path) -> None:
    old = {"workflow": {"quick_change": True}}
    assert process_workspace_names(old) == DEFAULT_PROCESS_WORKSPACES
    cfg = {"workflow": {"process_workspaces": ["operations/audit", "feature-workspace"]}}
    names = process_workspace_names(cfg)
    assert names == (*DEFAULT_PROCESS_WORKSPACES, "operations/audit")
    # None of the directories need to exist before the first use.
    assert process_workspace_roots(tmp_path, cfg)[-1] == tmp_path / "operations" / "audit"
    assert is_process_path(Path("operations/audit/record.md"), tmp_path, cfg)
    assert not is_process_path(Path("operations/audit-guide.md"), tmp_path, cfg)
    assert not is_process_path(Path("concepts/feature-workspace/topic.md"), tmp_path, cfg)


@pytest.mark.parametrize("value", [".", "../authority", "/outside", "C:\\outside", "**/workspace", "a/../b", "README.md", "", None])  # no-leakage: ignore -- invalid absolute-path fixture
def test_invalid_registration_fails_config_validation(value: object) -> None:
    cfg = config.default_config()
    cfg["project"].update(name="Example", slug="example")
    cfg["workflow"]["process_workspaces"] = [value]
    errors, _ = config.validate_config(cfg)
    assert any("process_workspaces" in error for error in errors)


def test_registration_must_be_a_list() -> None:
    with pytest.raises(ValueError, match="must be a list"):
        process_workspace_names({"workflow": {"process_workspaces": "temporary/audit"}})


def test_config_discovery_matches_nested_configured_wiki_only(tmp_path: Path) -> None:
    cfg = config.default_config()
    cfg["repo"]["wiki_path"] = "docs/current"
    cfg["workflow"]["process_workspaces"] = ["temporary/audit"]
    config.save_config(tmp_path, cfg)
    discovered = project_config_for_wiki(tmp_path / "docs/current")
    assert discovered is not None
    assert process_workspace_names(discovered)[-1] == "temporary/audit"
    assert project_config_for_wiki(tmp_path / "unrelated/wiki") is None


def test_registration_cannot_use_a_file_as_a_root(tmp_path: Path) -> None:
    (tmp_path / "audit").write_text("not a directory", encoding="utf-8")
    with pytest.raises(ValueError, match="must be a directory"):
        process_workspace_roots(tmp_path, {"workflow": {"process_workspaces": ["audit"]}})
