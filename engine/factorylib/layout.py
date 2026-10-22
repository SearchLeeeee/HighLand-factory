"""Resolved work-repo layout and machine values."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import util

WIKI_SUBDIRS = {
    "feature_workspace": "feature-workspace",
    "quick_workspace": "quick-workspace",
    "code_ai": "code-ai",
}


@dataclass(frozen=True)
class Layout:
    work: Path
    code: Path
    wiki: Path
    feature_workspace: Path
    quick_workspace: Path
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

    def as_dict(self) -> dict[str, str]:
        return {
            "work": str(self.work),
            "code": str(self.code),
            "wiki": str(self.wiki),
            "feature_workspace": str(self.feature_workspace),
            "quick_workspace": str(self.quick_workspace),
            "code_ai": str(self.code_ai),
            "workflow_profile": str(self.workflow_profile),
            "registry": str(self.registry),
            "init_record": str(self.init_record),
            "baseline_evidence": str(self.baseline_evidence),
            "factory_root": str(self.factory_root),
            "python": str(self.python),
        }


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

    return Layout(
        work=work,
        code=code,
        wiki=wiki,
        feature_workspace=wiki / WIKI_SUBDIRS["feature_workspace"],
        quick_workspace=wiki / WIKI_SUBDIRS["quick_workspace"],
        code_ai=wiki / WIKI_SUBDIRS["code_ai"],
        workflow_profile=wiki / "governance" / "workflow-profile.md",
        registry=wiki / WIKI_SUBDIRS["feature_workspace"] / "registry.yaml",
        init_record=wiki / "governance" / "init-record.md",
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
    return [str(path) for path in expected if not path.exists()]
