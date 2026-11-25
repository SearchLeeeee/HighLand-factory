"""End-to-end tests: init a temporary work repo, run doctor and both gates."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from factorylib import config, util
from factorylib.config import default_config
from factorylib.layout import build_layout
from factorylib.render import Renderer

ENGINE = Path(__file__).resolve().parents[1] / "factory.py"


def test_v2_renders_code_ai_links_to_existing_engineering_facts(tmp_path):
    config = default_config()
    config["factory"]["template"] = "workspace-v2"
    config["owners"] = [{"id": "core", "title": "Core", "paths": ["code"]}]
    layout = build_layout(tmp_path, config)
    engineering_facts = layout.wiki / "engineering/project-facts.md"
    engineering_facts.parent.mkdir(parents=True)
    engineering_facts.write_text("# Project facts\n", encoding="utf-8")
    assert Path(layout.as_dict()["project_facts"]) == engineering_facts
    files = {item.rel: item.content for item in Renderer(tmp_path, config, layout).plan_upgrade().files}
    assert "wiki/code-ai/project-facts.md" not in files
    assert files["wiki/code-ai/README.md"].count("(../engineering/project-facts.md)") == 3
    assert "(../engineering/project-facts.md)" in files["wiki/code-ai/core-agent.md"]


def run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ENGINE), *args],
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else None,
        timeout=300,
    )


def write_answers(path: Path, *, name: str = "Smoke Project") -> Path:
    path.write_text(
        f"""
project:
  name: {name}
  slug: smoke-project
  one_liner: A smoke test project
  stack:
    - Python 3.12
  visibility: private
repo:
  mode: mono
  default_branch: main
owners:
  - id: core
    title: Core
    paths:
      - code
commands:
  test:
    - python -m pytest
  verify:
    - python -m pytest
security:
  forbidden_operations:
    - production writes without explicit authorization
  sensitive_classes:
    - credentials
""",
        encoding="utf-8",
    )
    return path


def test_init_doctor_and_gates(tmp_path: Path) -> None:
    work = tmp_path / "work"
    answers = write_answers(tmp_path / "answers.yaml")
    init = run("init", "--work", str(work), "--answers", str(answers), "--python", sys.executable)
    assert init.returncode == 0, init.stdout + init.stderr
    assert (work / ".factory" / "factory.yaml").is_file()
    assert (work / "wiki" / "README.md").is_file()
    assert (work / "wiki" / "engineering" / "workflow-profile.md").is_file()
    assert (work / "workspace" / "feature-workspace" / "registry.yaml").is_file()
    assert (work / "workspace" / "refactor-workspace" / "README.md").is_file()
    assert "refactor-workspace/" not in (work / "wiki" / "README.md").read_text(encoding="utf-8")
    for name in ("product/README.md", "engineering/README.md", "by-type.md", "engineering/init-baseline.md"):
        assert (work / "wiki" / name).is_file()
    assert not (work / "wiki" / "role-memory" / "implementation.md").exists()
    assert (work / "wiki" / "code-ai" / "core-agent.md").is_file()
    workspace_readme = (work / "README.md").read_text(encoding="utf-8")
    assert workspace_readme.startswith("# Smoke Project")
    assert "workspace template maintenance" not in workspace_readme.lower()
    for topic in ("architecture", "domain", "features", "implementation", "testing"):
        assert not (work / "wiki" / topic / "README.md").exists()
        assert f"{topic}/README.md" not in (work / "wiki" / "README.md").read_text(encoding="utf-8")
    gitignore = (work / ".gitignore").read_text(encoding="utf-8")
    assert ".factory/local.yaml" in gitignore
    assert ".factory/worktrees/" in gitignore

    config_text = (work / ".factory" / "factory.yaml").read_text(encoding="utf-8")
    assert "max_parallel_features" not in config_text
    profile_text = (work / "wiki" / "engineering" / "workflow-profile.md").read_text(encoding="utf-8")
    assert "max_parallel_features" not in profile_text

    doctor = run("doctor", "--work", str(work), "--json")
    payload = json.loads(doctor.stdout)
    assert payload["ok"] is True, json.dumps(payload, indent=2, ensure_ascii=False)

    gate = run("gate", "all", "--work", str(work))
    assert gate.returncode == 0, gate.stdout + gate.stderr


def test_dry_run_does_not_write(tmp_path: Path) -> None:
    work = tmp_path / "work"
    answers = write_answers(tmp_path / "answers.yaml")
    result = run("init", "--work", str(work), "--answers", str(answers), "--dry-run", "--json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["counts"]["create"] > 10
    assert not work.exists()


def test_adopt_split_preserves_existing_docs(tmp_path: Path) -> None:
    work = tmp_path / "docs-repo"
    work.mkdir()
    (work / "wiki").mkdir()
    (work / "wiki" / "README.md").write_text("# Existing home\n", encoding="utf-8")
    code = tmp_path / "code-repo"
    code.mkdir()
    (code / "app.py").write_text("print('hi')\n", encoding="utf-8")
    answers = write_answers(tmp_path / "answers.yaml", name="Adopted Project")

    result = run(
        "adopt",
        "--work",
        str(work),
        "--code",
        str(code),
        "--answers",
        str(answers),
        "--python",
        sys.executable,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    config_text = (work / ".factory" / "factory.yaml").read_text(encoding="utf-8")
    assert "mode: split" in config_text
    assert "code_external:" in config_text
    home = (work / "wiki" / "README.md").read_text(encoding="utf-8")
    assert home.startswith("# Existing home\n"), home
    assert "00-spec.md" in home  # init linked generated files into the existing MOC


@pytest.mark.parametrize("command", ["status", "resolve"])
def test_status_and_resolve(tmp_path: Path, command: str) -> None:
    work = tmp_path / "work"
    answers = write_answers(tmp_path / "answers.yaml")
    assert run("init", "--work", str(work), "--answers", str(answers), "--python", sys.executable).returncode == 0
    result = run(command, "--work", str(work), "--json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload


def test_upgrade_check_and_restore_generated_file(tmp_path: Path) -> None:
    work = tmp_path / "work"
    answers = write_answers(tmp_path / "answers.yaml")
    assert run("init", "--work", str(work), "--answers", str(answers), "--python", sys.executable).returncode == 0

    clean = run("upgrade", "--work", str(work), "--check", "--json")
    assert clean.returncode == 0, clean.stdout + clean.stderr
    assert json.loads(clean.stdout)["counts"]["overwrite"] == 0

    (work / "wiki" / "engineering" / "workflow-profile.md").unlink()
    dirty = run("upgrade", "--work", str(work), "--check", "--json")
    assert dirty.returncode == 1
    assert json.loads(dirty.stdout)["counts"]["create"] == 1

    assert run("upgrade", "--work", str(work), "--apply").returncode == 0
    doctor = run("doctor", "--work", str(work), "--json")
    assert json.loads(doctor.stdout)["ok"] is True


@pytest.mark.parametrize("template", ["workspace-v1", "workspace-v2"])
def test_upgrade_refreshes_legacy_code_ai_rules_and_preserves_customizations(tmp_path: Path, template: str) -> None:
    work = tmp_path / "work"
    answers = write_answers(tmp_path / "answers.yaml")
    with answers.open("a", encoding="utf-8") as stream:
        stream.write(f"\nfactory:\n  template: {template}\n")
    init = run("init", "--work", str(work), "--answers", str(answers), "--python", sys.executable)
    assert init.returncode == 0, init.stdout + init.stderr

    blocks = Path("wiki/code-ai/_blocks")
    index_path = blocks / "README.md"
    index = work / index_path
    legacy = {
        Path("AGENTS.md"): (work / "AGENTS.md").read_text(encoding="utf-8").replace(
            "本地提交本次任务范围内的改动，无需另行授权", "提交已授权的改动"
        ),
        blocks / "agent-notes-rule.md": "# 记录头（固定五字段）\n\n**Edit when**\n",
        blocks / "coding-discipline.md": "# 编码纪律\n\n记录每一次动作与原因。\n",
        blocks / "commit-granularity.md": "# 提交粒度\n\n提交前取得用户授权。\n",
        blocks / "review-gate.md": "# 评审门\n\n未授权提交仍可评审。\n",
        index_path: index.read_text(encoding="utf-8").replace("源码注释与交接记录的写法", "五字段记录头与维护时机"),
    }
    state = config.load_state(work)
    for path, text in legacy.items():
        util.write_text(work / path, text)
        state["generated_files"][path.as_posix()] = util.sha256_file(work / path)
    config.save_state(work, state)

    custom_index = legacy[index_path] + "\n项目自己的阅读顺序。\n"
    util.write_text(index, custom_index)
    upgrade = run("upgrade", "--work", str(work), "--apply")
    assert upgrade.returncode == 0, upgrade.stdout + upgrade.stderr

    assert "取消五字段记录头" in (work / blocks / "agent-notes-rule.md").read_text(encoding="utf-8")
    assert "记录每一次动作与原因" not in (work / blocks / "coding-discipline.md").read_text(encoding="utf-8")
    for path in (Path("AGENTS.md"), blocks / "commit-granularity.md"):
        content = (work / path).read_text(encoding="utf-8")
        assert "无需另行授权" in content
        assert "推送" in content and "单独授权" in content
    assert "可识别的未提交内容可以直接评审与验证" in (work / blocks / "review-gate.md").read_text(encoding="utf-8")
    assert index.read_text(encoding="utf-8") == custom_index
    assert not list((work / blocks).glob("*.tmpl"))
    gate = run("gate", "all", "--work", str(work))
    assert gate.returncode == 0, gate.stdout + gate.stderr


def test_init_with_custom_wiki_path(tmp_path: Path) -> None:
    work = tmp_path / "work"
    answers = tmp_path / "answers.yaml"
    answers.write_text(
        """
project:
  name: Custom Wiki
  slug: custom-wiki
repo:
  wiki_path: docs-root
verification:
  baseline_evidence: docs-root/evidence/current-baseline.md
owners:
  - id: core
    title: Core
    paths: [code]
commands:
  test: [python -m pytest]
  verify: [python -m pytest]
""",
        encoding="utf-8",
    )
    init = run("init", "--work", str(work), "--answers", str(answers), "--python", sys.executable)
    assert init.returncode == 0, init.stdout + init.stderr
    assert (work / "docs-root" / "README.md").is_file()
    assert not (work / "wiki").exists()
    assert (work / "workspace" / "refactor-workspace" / "README.md").is_file()
    profile = (work / "docs-root" / "engineering" / "workflow-profile.md").read_text(encoding="utf-8")
    assert "workspace/refactor-workspace/" in profile
    assert (work / "docs-root/evidence/current-baseline.md").is_file()
    gate = run("gate", "all", "--work", str(work))
    assert gate.returncode == 0, gate.stdout + gate.stderr


def test_init_with_owner_profile_override(tmp_path: Path) -> None:
    work = tmp_path / "work"
    answers = tmp_path / "answers.yaml"
    answers.write_text(
        """
project:
  name: Profile Override
  slug: profile-override
owners:
  - id: backend
    title: Backend
    paths: [code]
    profile: docs-root/code-ai/backend-agent.md
repo:
  wiki_path: docs-root
commands:
  test: [python -m pytest]
  verify: [python -m pytest]
""",
        encoding="utf-8",
    )
    init = run("init", "--work", str(work), "--answers", str(answers), "--python", sys.executable)
    assert init.returncode == 0, init.stdout + init.stderr
    profile = work / "docs-root" / "code-ai" / "backend-agent.md"
    assert profile.is_file()
    assert not (work / "docs-root" / "code-ai" / "backend-agent-agent.md").exists()
    gate = run("gate", "all", "--work", str(work))
    assert gate.returncode == 0, gate.stdout + gate.stderr


def test_adopt_rerun_preserves_project_config(tmp_path: Path) -> None:
    """A second adopt must not reset owners, commands or packs to defaults."""
    work = tmp_path / "docs-repo"
    work.mkdir()
    (work / "wiki").mkdir()
    (work / "wiki" / "README.md").write_text("# Home\n", encoding="utf-8")
    code = tmp_path / "code-repo"
    code.mkdir()
    answers = write_answers(tmp_path / "answers.yaml", name="Rerun Project")
    adopt = ["adopt", "--work", str(work), "--code", str(code), "--python", sys.executable]
    assert run(*adopt, "--answers", str(answers)).returncode == 0
    before = (work / ".factory" / "factory.yaml").read_text(encoding="utf-8")
    assert "name: Rerun Project" in before

    # Re-running with no answers must keep the recorded project values.
    second = run(*adopt)
    assert second.returncode == 0, second.stdout + second.stderr
    after = (work / ".factory" / "factory.yaml").read_text(encoding="utf-8")
    assert "name: Rerun Project" in after
    assert "python -m pytest" in after
    assert run("doctor", "--work", str(work), "--skip-gates").returncode == 0


def test_adopt_rerun_keeps_relative_code_external(tmp_path: Path) -> None:
    """The portable relative form must survive a re-run."""
    docs = tmp_path / "docs-repo"
    docs.mkdir()
    (docs / "wiki").mkdir()
    (docs / "wiki" / "README.md").write_text("# Home\n", encoding="utf-8")
    code = tmp_path / "code-repo"
    code.mkdir()
    answers = tmp_path / "answers.yaml"
    answers.write_text(
        """
project:
  name: Relative Split
  slug: relative-split
repo:
  mode: split
  code_external: ../code-repo
""",
        encoding="utf-8",
    )
    adopt = ["adopt", "--work", str(docs), "--code", str(code), "--python", sys.executable]
    assert run(*adopt, "--answers", str(answers)).returncode == 0
    config_text = (docs / ".factory" / "factory.yaml").read_text(encoding="utf-8")
    assert "code_external: ../code-repo" in config_text

    assert run(*adopt).returncode == 0
    config_text = (docs / ".factory" / "factory.yaml").read_text(encoding="utf-8")
    assert "code_external: ../code-repo" in config_text, config_text


def test_adopt_rerun_does_not_duplicate_gitignore_block(tmp_path: Path) -> None:
    work = tmp_path / "docs-repo"
    work.mkdir()
    (work / "wiki").mkdir()
    (work / "wiki" / "README.md").write_text("# Home\n", encoding="utf-8")
    code = tmp_path / "code-repo"
    code.mkdir()
    answers = write_answers(tmp_path / "answers.yaml", name="Gitignore Project")
    adopt = ["adopt", "--work", str(work), "--code", str(code), "--python", sys.executable]
    assert run(*adopt, "--answers", str(answers)).returncode == 0
    assert run(*adopt).returncode == 0
    text = (work / ".gitignore").read_text(encoding="utf-8")
    assert text.count("# --- HighLand-factory machine state (never commit) ---") == 1, text
    assert text.count(".factory/local.yaml") == 1, text


def test_adopt_rerun_keeps_init_record_generated_files(tmp_path: Path) -> None:
    """The generated-file table must not collapse to _none_ on a re-run."""
    work = tmp_path / "docs-repo"
    work.mkdir()
    (work / "wiki").mkdir()
    (work / "wiki" / "README.md").write_text("# Home\n", encoding="utf-8")
    code = tmp_path / "code-repo"
    code.mkdir()
    answers = write_answers(tmp_path / "answers.yaml", name="Record Project")
    adopt = ["adopt", "--work", str(work), "--code", str(code), "--python", sys.executable]
    assert run(*adopt, "--answers", str(answers)).returncode == 0
    assert run(*adopt).returncode == 0
    record = (work / "wiki" / "governance" / "init-record.md").read_text(encoding="utf-8")
    assert "| _none_ | _n/a_ |" not in record, record
    assert "workflow-profile.md" in record


def test_adopt_rerun_keeps_recorded_answers(tmp_path: Path) -> None:
    """The answers block is provenance; a re-run without answers must keep it."""
    work = tmp_path / "docs-repo"
    work.mkdir()
    (work / "wiki").mkdir()
    (work / "wiki" / "README.md").write_text("# Home\n", encoding="utf-8")
    code = tmp_path / "code-repo"
    code.mkdir()
    answers = write_answers(tmp_path / "answers.yaml", name="Provenance Project")
    adopt = ["adopt", "--work", str(work), "--code", str(code), "--python", sys.executable]
    assert run(*adopt, "--answers", str(answers)).returncode == 0
    assert run(*adopt).returncode == 0
    record = (work / "wiki" / "governance" / "init-record.md").read_text(encoding="utf-8")
    assert "Provenance Project" in record, record
    assert "python -m pytest" in record, record


def test_adopt_does_not_auto_link_registered_process_history(tmp_path: Path) -> None:
    work = tmp_path / "docs-repo"
    for relative, text in {
        "wiki/README.md": "# Existing home\n",
        "wiki/refactor-workspace/old/report.md": "# Process\n[Old](missing.md)\n",
        "wiki/temporary/audit/report.md": "# Process\n[Old](missing.md)\n",
        "wiki/product-workspace/guide.md": "# Current business concept\n",
    }.items():
        path = work / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    code = tmp_path / "code-repo"
    code.mkdir()
    answers = write_answers(tmp_path / "answers.yaml")
    with answers.open("a", encoding="utf-8") as handle:
        handle.write("\nworkflow:\n  process_workspaces: [temporary/audit]\n")
    adopted = run("adopt", "--work", str(work), "--code", str(code), "--answers", str(answers), "--python", sys.executable)
    assert adopted.returncode == 0, adopted.stdout + adopted.stderr
    home = (work / "wiki/README.md").read_text(encoding="utf-8")
    assert "refactor-workspace/" not in home
    assert "temporary/audit/" not in home
    assert "product-workspace/guide.md" in home
    gate = run("gate", "wiki", "--work", str(work))
    assert gate.returncode == 0, gate.stdout + gate.stderr


def test_upgrade_older_project_adds_refactor_workspace_with_optional_config_absent(tmp_path: Path) -> None:
    from factorylib import config

    work = tmp_path / "work"
    answers = write_answers(tmp_path / "answers.yaml")
    with answers.open("a", encoding="utf-8") as stream:
        stream.write("\nfactory:\n  template: workspace-v1\n")
    initialized = run("init", "--work", str(work), "--answers", str(answers), "--python", sys.executable)
    assert initialized.returncode == 0, initialized.stdout + initialized.stderr
    (work / "wiki/refactor-workspace/README.md").unlink()
    (work / "wiki/refactor-workspace").rmdir()
    old_config = config.load_config(work)
    old_config["workflow"].pop("process_workspaces")
    config.save_config(work, old_config)
    upgrade = run("upgrade", "--work", str(work), "--apply")
    assert upgrade.returncode == 0, upgrade.stdout + upgrade.stderr
    assert (work / "wiki/refactor-workspace/README.md").is_file()
    assert "refactor-workspace/" not in (work / "wiki/README.md").read_text(encoding="utf-8")
    doctor = run("doctor", "--work", str(work), "--json")
    assert json.loads(doctor.stdout)["ok"], doctor.stdout + doctor.stderr


def test_explicit_migration_preserves_reviewed_pages_and_old_task_roots(tmp_path: Path):
    import os
    from factorylib import config

    work = tmp_path / "legacy"
    answers = write_answers(tmp_path / "answers.yaml")
    with answers.open("a", encoding="utf-8") as stream:
        stream.write("\nfactory:\n  template: workspace-v1\n")
    assert run("init", "--work", str(work), "--answers", str(answers)).returncode == 0
    wiki = work / "wiki"
    home = wiki / "README.md"
    for name in ("product/README.md", "engineering/README.md", "by-type.md"):
        page = wiki / name
        page.parent.mkdir(exist_ok=True)
        page.write_text("# Reviewed navigation\n", encoding="utf-8")
        with home.open("a", encoding="utf-8") as stream:
            stream.write(f"\n- [Reviewed navigation]({name})\n")
    for page in [base / name for base in (work, work / "code") for name in ("AGENTS.md", "CLAUDE.md")] + [
        wiki / "code-ai/core-agent.md", wiki / "code-ai/review-agent.md"
    ]:
        pointer = Path(os.path.relpath(home, page.parent)).as_posix()
        page.write_text(f"# Startup\n\n[Common home]({pointer})\n", encoding="utf-8")
    before = home.read_bytes()
    preflight = run("migrate-wiki", "--work", str(work))
    assert preflight.returncode == 0, preflight.stdout + preflight.stderr
    assert config.load_config(work)["factory"]["template"] == "workspace-v1"
    assert run("migrate-wiki", "--work", str(work), "--apply").returncode == 0
    paths = json.loads(run("resolve", "--work", str(work), "--json").stdout)
    assert Path(paths["process_root"]) == wiki
    assert Path(paths["workflow_profile"]) == wiki / "governance/workflow-profile.md"
    assert Path(paths["registry"]).is_file()
    assert run("upgrade", "--work", str(work), "--apply").returncode == 0
    assert home.read_bytes() == before
    home.unlink()
    assert run("upgrade", "--work", str(work), "--apply").returncode == 0
    assert not home.exists()


def test_new_split_init_plans_external_startup_and_preserves_existing_content(tmp_path: Path):
    work = tmp_path / "docs"
    code = tmp_path / "implementation"
    code.mkdir()
    existing = code / "AGENTS.md"
    existing.write_text("# Local conventions\n", encoding="utf-8")
    args = ("init", "--work", str(work), "--code", str(code))
    planned = run(*args, "--dry-run", "--json")
    assert planned.returncode == 0, planned.stderr
    files = json.loads(planned.stdout)["files"]
    assert any(row["path"] == str(existing) and row["action"] == "overwrite" for row in files)
    assert existing.read_text() == "# Local conventions\n"
    assert run(*args).returncode == 0
    content = existing.read_text(encoding="utf-8")
    assert content.startswith("# Local conventions\n")
    assert "../docs/wiki/README.md" in content
    assert run(*args, "--force").returncode == 0
    assert existing.read_text(encoding="utf-8") == content
