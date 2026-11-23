import subprocess
from pathlib import Path

import pytest

from factorylib import config, memory, util


def test_incremental_scan_respects_bookmark_dirty_files_and_task_boundaries(tmp_path: Path):
    cfg = config.default_config()
    cfg["factory"]["template"] = "workspace-v2"
    cfg["workflow"]["workspace_root"] = "process"
    config.save_config(tmp_path, cfg)

    def git(*args):
        return subprocess.check_output(["git", "-C", str(tmp_path), *args], text=True).strip()

    def note(relative, text="one"):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return str(path)

    (tmp_path / "wiki").mkdir()
    git("init", "-q")
    git("config", "user.name", "Fixture")
    git("config", "user.email", "fixture@example.invalid")
    quick = "process/quick-workspace/tasks/Q1"
    feature = "process/feature-workspace/initiatives/I1/features/F1"
    refactor = "process/refactor-workspace/runs/R1"
    old = note(quick + "/experience.md")
    git("add", ".")
    git("commit", "-qm", "initial experience")
    base = git("rev-parse", "HEAD")
    assert memory.scan(tmp_path)["files"] == []
    assert memory.scan(tmp_path, quick)["files"] == [old]

    recent = note(feature + "/experience-review.md")
    initiative = note("process/feature-workspace/initiatives/I1/experience.md")
    git("add", ".")
    git("commit", "-qm", "new feature experience")
    git("commit", "--allow-empty", "-qm", f"Review Wiki experience\n\nWiki-Experience-Reviewed-Through: {base}")
    dirty = note(quick + "/experience.md", "updated")
    untracked = note(refactor + "/experience-review.md")
    note(quick + "/evidence/experience.md")
    note("wiki/product/experience.md")
    note("process/quick-workspace/Q1/experience.md")
    result = memory.scan(tmp_path)
    assert result["reviewed_through"] == base
    assert set(result["files"]) == {recent, initiative, dirty, untracked}
    with pytest.raises(util.FactoryError):
        memory.scan(tmp_path, quick + "/evidence")


def test_targeted_merge_scans_each_selected_leaf_root(tmp_path: Path):
    cfg = config.default_config()
    cfg["factory"]["template"] = "workspace-v2"
    cfg["workflow"]["workspace_root"] = "process"
    config.save_config(tmp_path, cfg)

    initiative = tmp_path / "process/feature-workspace/initiatives/I1"
    selected_leaf = initiative / "features/F1"
    other_leaf = initiative / "features/F2"
    for leaf in (selected_leaf, other_leaf):
        leaf.mkdir(parents=True)
        (leaf / "experience.md").write_text("Verified observation\n", encoding="utf-8")

    assert memory.scan(tmp_path, str(initiative))["files"] == []
    merge_scope = [initiative, selected_leaf]
    notes = [path for root in merge_scope for path in memory.scan(tmp_path, str(root))["files"]]
    assert notes == [str(selected_leaf / "experience.md")]
