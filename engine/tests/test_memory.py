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
