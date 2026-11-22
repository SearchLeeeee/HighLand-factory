"""Resolved work-repo layout and machine values."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import util
from .workspaces import PROCESS_WORKSPACE_DIRS, retained_workspace_root

WIKI_SUBDIRS = {
    **PROCESS_WORKSPACE_DIRS,
    "code_ai": "code-ai",
}


@dataclass(frozen=True)
class Layout:
    work: Path
    code: Path
    wiki: Path
    feature_workspace: Path
    quick_workspace: Path
    refactor_workspace: Path
    template: str
    process_root: Path
    retained_process_root: Path | None
    role_memory: Path
    code_ai: Path
    workflow_profile: Path
    registry: Path
    init_record: Path
    baseline_evidence: Path
    factory_yaml: Path
    local_yaml: Path
    state_json: Path
    factory_root: Path
    python: Path

    @property
    def project_facts(self) -> Path:
        engineering_facts = self.wiki / "engineering/project-facts.md"
        if self.template == "workspace-v2" and engineering_facts.is_file():
            return engineering_facts
        return self.code_ai / "project-facts.md"

    @property
    def retained_registry(self) -> Path | None:
        if self.retained_process_root:
            return self.retained_process_root / WIKI_SUBDIRS["feature_workspace"] / "registry.yaml"
        return None

    def as_dict(self) -> dict[str, str]:
        paths = {
            "process_root": str(self.process_root),
            "role_memory": str(self.role_memory),
            "work": str(self.work),
            "code": str(self.code),
            "wiki": str(self.wiki),
            "feature_workspace": str(self.feature_workspace),
            "quick_workspace": str(self.quick_workspace),
            "refactor_workspace": str(self.refactor_workspace),
            "code_ai": str(self.code_ai),
            "project_facts": str(self.project_facts),
            "workflow_profile": str(self.workflow_profile),
            "registry": str(self.registry),
            "init_record": str(self.init_record),
            "baseline_evidence": str(self.baseline_evidence),
            "factory_root": str(self.factory_root),
            "python": str(self.python),
        }
        if self.retained_process_root:
            paths["retained_process_root"] = str(self.retained_process_root)
            for key, name in PROCESS_WORKSPACE_DIRS.items():
                paths[f"retained_{key}"] = str(self.retained_process_root / name)
            paths["retained_registry"] = str(self.retained_registry)
        return paths


def resolve_path(work: Path, value: str | None) -> Path:
    if not value:
        return work
    path = Path(value)
    return path if path.is_absolute() else (work / path)


def build_layout(work: Path, config: dict[str, Any], local: dict[str, Any] | None = None) -> Layout:
    work = work.resolve()
    local = local or {}
    repo = config.get("repo") or {}
    verification = config.get("verification") or {}

    wiki = resolve_path(work, str(repo.get("wiki_path") or "wiki")).resolve()
    code_raw = repo.get("code_external") if repo.get("mode") == "split" else repo.get("code_path")
    code = resolve_path(work, str(code_raw or "code")).resolve()
    factory_root = Path(str(local.get("factory_root") or util.FACTORY_ROOT)).expanduser().resolve()
    python = Path(str(local.get("python") or sys.executable)).expanduser()

    workflow = config.get("workflow") or {}
    v2 = (config.get("factory") or {}).get("template") == "workspace-v2"
    process = resolve_path(work, workflow.get("workspace_root") or ("workspace" if v2 else str(wiki))).resolve()
    if not process.is_relative_to(work) or process == work:
        raise util.FactoryError("workflow.workspace_root must be a directory inside the work repository")
    engineering = wiki / ("engineering" if v2 and process != wiki else "governance")
    return Layout(
        template=(config.get("factory") or {}).get("template", "workspace-v1"),
        process_root=process,
        retained_process_root=retained_workspace_root(work, config, process),
        role_memory=wiki / "role-memory",
        work=work,
        code=code,
        wiki=wiki,
        feature_workspace=process / WIKI_SUBDIRS["feature_workspace"],
        quick_workspace=process / WIKI_SUBDIRS["quick_workspace"],
        refactor_workspace=process / WIKI_SUBDIRS["refactor_workspace"],
        code_ai=wiki / WIKI_SUBDIRS["code_ai"],
        workflow_profile=engineering / "workflow-profile.md",
        registry=process / WIKI_SUBDIRS["feature_workspace"] / "registry.yaml",
        init_record=engineering / "init-record.md",
        baseline_evidence=resolve_path(work, str(verification.get("baseline_evidence") or "wiki/validation/init-baseline.md")),
        factory_yaml=work / ".factory" / "factory.yaml",
        local_yaml=work / ".factory" / "local.yaml",
        state_json=work / ".factory" / "state.json",
        factory_root=factory_root,
        python=python,
    )


def missing_layout_paths(layout: Layout) -> list[str]:
    expected = [
        layout.work,
        layout.wiki,
        layout.feature_workspace,
        layout.quick_workspace,
        layout.code_ai,
        layout.registry,
        layout.workflow_profile,
    ]
    if layout.template == "workspace-v2":
        expected.extend(layout.wiki / name for name in ("README.md", "product/README.md", "engineering/README.md", "by-type.md"))
    if layout.retained_registry:
        expected.append(layout.retained_registry)
    return [str(path) for path in expected if not path.exists()]
