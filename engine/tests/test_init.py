"""End-to-end tests: init a temporary work repo, run doctor and both gates."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ENGINE = Path(__file__).resolve().parents[1] / "factory.py"


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
    assert (work / "wiki" / "governance" / "workflow-profile.md").is_file()
    assert (work / "wiki" / "feature-workspace" / "registry.yaml").is_file()
    assert (work / "wiki" / "code-ai" / "core-agent.md").is_file()
    workspace_readme = (work / "README.md").read_text(encoding="utf-8")
    assert workspace_readme.startswith("# Smoke Project")
    assert "workspace template maintenance" not in workspace_readme.lower()
    for topic in ("architecture", "domain", "features", "implementation", "product", "testing"):
        assert not (work / "wiki" / topic / "README.md").exists()
        assert f"{topic}/README.md" not in (work / "wiki" / "README.md").read_text(encoding="utf-8")
    gitignore = (work / ".gitignore").read_text(encoding="utf-8")
    assert ".factory/local.yaml" in gitignore
    assert ".factory/worktrees/" in gitignore

    config_text = (work / ".factory" / "factory.yaml").read_text(encoding="utf-8")
    assert "max_parallel_features" not in config_text
    profile_text = (work / "wiki" / "governance" / "workflow-profile.md").read_text(encoding="utf-8")
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

    (work / "wiki" / "governance" / "workflow-profile.md").unlink()
    dirty = run("upgrade", "--work", str(work), "--check", "--json")
    assert dirty.returncode == 1
    assert json.loads(dirty.stdout)["counts"]["create"] == 1

    assert run("upgrade", "--work", str(work), "--apply").returncode == 0
    doctor = run("doctor", "--work", str(work), "--json")
    assert json.loads(doctor.stdout)["ok"] is True


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

