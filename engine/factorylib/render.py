"""Template rendering and write planning for work-repo generation."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from . import config as config_mod
from . import util
from .generated import GeneratedBlocks
from .layout import Layout
from .workspaces import process_workspace_roots

PLACEHOLDER_RE = re.compile(r"\{\{([A-Za-z0-9_.:\-]+)\}\}")
TEMPLATE_SUFFIX = ".tmpl"

# Template artifacts that are not work-repo outputs.
SKIP_TEMPLATE_FILES = {
    ".factory/factory.yaml.tmpl",
    "wiki/code-ai/_manifests/owner.yml.tmpl",
}
OWNER_MANIFEST_TEMPLATE = "wiki/code-ai/_manifests/owner.yml.tmpl"


class RenderError(util.FactoryError):
    pass


@dataclass
class PlannedFile:
    rel: str
    action: str  # create | overwrite | skip
    generated: bool
    reason: str = ""
    content: str | None = None
    source: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": self.rel,
            "action": self.action,
            "generated": self.generated,
            "reason": self.reason,
            "source": self.source,
        }


@dataclass
class Plan:
    work: Path
    files: list[PlannedFile] = field(default_factory=list)

    def counts(self) -> dict[str, int]:
        counts = {"create": 0, "overwrite": 0, "skip": 0}
        for item in self.files:
            counts[item.action] = counts.get(item.action, 0) + 1
        return counts

    def as_dict(self) -> dict[str, Any]:
        return {"work": str(self.work), "counts": self.counts(), "files": [item.as_dict() for item in self.files]}


class Renderer:
    def __init__(
        self,
        work: Path,
        project_config: dict[str, Any],
        layout: Layout,
        *,
        template_root: Path | None = None,
        owner_template_root: Path | None = None,
        version: str | None = None,
    ):
        self.work = work.resolve()
        self.config = project_config
        self.layout = layout
        self.version = version or util.factory_version()
        self.template_root = (template_root or util.TEMPLATE_ROOT).resolve()
        self.owner_template_root = (owner_template_root or util.OWNER_TEMPLATE_ROOT).resolve()
        self.v2 = (project_config.get("factory") or {}).get("template") == "workspace-v2"
        self.overlay = self.template_root.parent / "workspace-v2"
        self.blocks = GeneratedBlocks(project_config, layout, self.version)
        self.scalars = self._build_scalars()

    # -- context ----------------------------------------------------------
    def _build_scalars(self) -> dict[str, str]:
        flat = util.flatten(self.config)
        flat["generated.date"] = date.today().isoformat()
        flat["generated.factory_version"] = self.version
        flat["layout.code"] = util.rel_posix(self.layout.code, self.layout.work)
        flat["layout.wiki"] = util.rel_posix(self.layout.wiki, self.layout.work)
        home = self.layout.wiki / "README.md"
        try:
            flat["layout.code_to_home"] = Path(os.path.relpath(home, self.layout.code)).as_posix()
        except ValueError:  # Windows split repos on different volumes
            flat["layout.code_to_home"] = home.as_uri()
        flat["layout.workflow_profile"] = util.rel_posix(self.layout.workflow_profile, self.layout.work)
        flat["layout.code_ai_project_facts"] = Path(
            os.path.relpath(self.layout.project_facts, self.layout.code_ai)
        ).as_posix()
        self.process_roots = process_workspace_roots(self.layout.wiki, self.config)
        baseline = self.layout.baseline_evidence
        if baseline.is_relative_to(self.layout.wiki) and not any(baseline.is_relative_to(root) for root in self.process_roots):
            relative = Path(os.path.relpath(baseline, self.layout.wiki / "engineering")).as_posix()
            flat["layout.baseline_reference"] = f"[验证基线](<{relative}>)"
        else:
            flat["layout.baseline_reference"] = "验证基线位置见[流程与命令](workflow-profile.md)"
        flat["layout.feature_workspace"] = util.rel_posix(self.layout.feature_workspace, self.layout.work)
        return flat

    def _map_rel(self, rel: str) -> str | None:
        """Map template paths (``code/``, ``wiki/``) onto configured folder names.

        Returns ``None`` when the template file must not be written at all
        (``split`` mode: the code tree belongs to the external code repo).
        """
        repo = self.config.get("repo") or {}
        wiki_name = str(repo.get("wiki_path") or "wiki").strip("/")
        code_name = str(repo.get("code_path") or "code").strip("/")
        if self.v2:
            if rel == "wiki/code-ai/project-facts.md" and self.scalars["layout.code_ai_project_facts"] != "project-facts.md":
                return None
            if rel == "wiki/engineering/workflow-profile.md":
                return self.layout.workflow_profile.relative_to(self.work).as_posix()
            if rel == "wiki/engineering/init-record.md":
                return self.layout.init_record.relative_to(self.work).as_posix()
            for attr in ("feature_workspace", "quick_workspace", "refactor_workspace"):
                root = getattr(self.layout, attr)
                prefix = "wiki/" + root.name + "/"
                if rel.startswith(prefix):
                    return util.rel_posix(root, self.layout.work) + "/" + rel[len(prefix):]
        if rel == "code" or rel.startswith("code/"):
            if str(repo.get("mode") or "mono") == "split":
                return None
            if code_name != "code":
                return code_name if rel == "code" else code_name + rel[len("code"):]
            return rel
        if rel == "wiki" or rel.startswith("wiki/"):
            if wiki_name != "wiki":
                return wiki_name if rel == "wiki" else wiki_name + rel[len("wiki"):]
        return rel

    def _lookup(self, key: str, owner: dict[str, Any] | None) -> str:
        if key.startswith("generated:"):
            name = key.split(":", 1)[1]
            scalar_key = f"generated.{name}"
            if scalar_key in self.scalars:
                return self.scalars[scalar_key]
            return self.blocks.get(name, owner)
        if key.startswith("owner."):
            if not owner:
                raise RenderError(f"placeholder {{{{ {key} }}}} is only valid in per-owner templates")
            value = owner.get(key.split(".", 1)[1])
            if value is None:
                raise RenderError(f"owner is missing field {key!r}")
            return str(value)
        if key in self.scalars:
            return self.scalars[key]
        raise RenderError(f"unknown template placeholder: {{{{ {key} }}}}")

    def render(self, text: str, owner: dict[str, Any] | None = None) -> str:
        errors: list[str] = []

        def replace(match: re.Match[str]) -> str:
            key = match.group(1)
            try:
                return self._lookup(key, owner)
            except RenderError as exc:
                errors.append(str(exc))
                return match.group(0)

        rendered = PLACEHOLDER_RE.sub(replace, text)
        if errors:
            unique = sorted(set(errors))
            raise RenderError("template rendering failed:\n- " + "\n- ".join(unique))
        return rendered

    def _sources(self):
        sources = {}
        for source in self.template_root.rglob("*"):
            if not source.is_file():
                continue
            rel = source.relative_to(self.template_root).as_posix()
            if rel in SKIP_TEMPLATE_FILES:
                continue
            if self.v2 and (
                rel.startswith(("wiki/governance/", "wiki/human/", "wiki/validation/"))
                or (rel.startswith("wiki/") and rel.count("/") == 1 and rel != "wiki/README.md.tmpl")
            ):
                continue
            sources[rel] = source
        if self.v2:
            for source in self.overlay.rglob("*"):
                if source.is_file():
                    rel = source.relative_to(self.overlay).as_posix()
                    if rel in SKIP_TEMPLATE_FILES:
                        continue
                    sources.pop(rel.removesuffix(TEMPLATE_SUFFIX), None)
                    sources[rel] = source
        return sorted(sources.items())

    # -- plan -------------------------------------------------------------
    def plan(self, *, force: bool = False, only: set[str] | None = None) -> Plan:
        return self._template_plan(force=force, only=only, upgrade=False)

    def plan_upgrade(self) -> Plan:
        return self._template_plan(force=False, only=None, upgrade=True)

    def _template_plan(self, *, force: bool, only: set[str] | None, upgrade: bool) -> Plan:
        if not self.template_root.is_dir():
            raise RenderError(f"template root not found: {self.template_root}")
        plan = Plan(work=self.work)
        state = config_mod.load_state(self.work)
        generated_hashes: dict[str, str] = state.get("generated_files") or {}

        def add(rel, content, generated, source):
            if rel is None or (only is not None and rel not in only):
                return
            if upgrade:
                planned = self._planned_upgrade(rel, content, generated, source, generated_hashes)
            else:
                planned = self._planned(rel, content, generated, source, force, generated_hashes)
            plan.files.append(planned)

        for rel_source, source in self._sources():
            generated = rel_source.endswith(TEMPLATE_SUFFIX)
            rel_out = self._map_rel(rel_source.removesuffix(TEMPLATE_SUFFIX))
            content = source.read_text(encoding="utf-8")
            if generated or (self.v2 and source.is_relative_to(self.overlay)):
                content = self.render(content)
            add(rel_out, content, generated, rel_source)

        # Per-owner files.
        owner_profile_template = self.owner_template_root / ("owner-agent-v2.md.tmpl" if self.v2 else "owner-agent.md.tmpl")
        owner_manifest_template = self.template_root / OWNER_MANIFEST_TEMPLATE
        if self.v2:
            owner_manifest_template = self.overlay / OWNER_MANIFEST_TEMPLATE
        for owner in self.blocks.owners:
            owner_id = str(owner.get("id"))
            explicit_profile = str(owner.get("profile") or "").strip()
            if owner_profile_template.is_file():
                content = self.render(owner_profile_template.read_text(encoding="utf-8"), owner=owner)
                rel = explicit_profile or self._map_rel(f"wiki/code-ai/{owner_id}-agent.md")
                if self.v2 and explicit_profile:
                    parent = (self.work / explicit_profile).parent
                    def relocate(link):
                        target = self.layout.code_ai / link.group(1)
                        return "](" + Path(os.path.relpath(target, parent)).as_posix() + ")"
                    content = re.sub(r"\]\(([^() :]+)\)", relocate, content)
                add(rel, content, True, "templates/owner-templates/" + owner_profile_template.name)
            if owner_manifest_template.is_file():
                content = self.render(owner_manifest_template.read_text(encoding="utf-8"), owner=owner)
                rel = self._map_rel(f"wiki/code-ai/_manifests/{owner_id}.yml")
                add(rel, content, True, OWNER_MANIFEST_TEMPLATE)
        if self.v2 and not upgrade:
            self._plan_split_entries(plan)
            self._complete_index(plan)
        return plan

    def _plan_split_entries(self, plan: Plan) -> None:
        if (self.config.get("repo") or {}).get("mode") != "split":
            return
        if not self.layout.code.is_dir():
            raise RenderError(f"external code repository is missing: {self.layout.code}")
        for name in ("AGENTS.md", "CLAUDE.md"):
            target = self.layout.code / name
            template = self.overlay / "code" / (name + ".tmpl")
            entry = self.render(template.read_text(encoding="utf-8")).strip()
            action = "create"
            if target.exists():
                existing = target.read_text(encoding="utf-8-sig")
                if any(old in existing for old in ("00-spec", "02-file-authority-map", "03-current-decisions")):
                    raise RenderError(f"review existing startup instructions and reconcile them with the Wiki home before init: {target}")
                if self.scalars["layout.code_to_home"] in existing and "职责" in existing:
                    action = "skip"
                else:
                    action = "overwrite"
                    entry = existing.rstrip() + "\n\n" + entry.partition("\n")[2].strip()
            plan.files.append(PlannedFile(str(target), action, False, "shared Wiki home in external code repository", entry + "\n", str(template)))

    def _complete_index(self, plan: Plan) -> None:
        index = next((item for item in plan.files if self.work / item.rel == self.layout.wiki / "by-type.md"), None)
        if index is None or index.action == "skip":
            return
        topics: dict[str, list[str]] = {}
        paths = {self.work / item.rel for item in plan.files} | {self.layout.baseline_evidence}
        categories = {
            "overview.md": "概览与导航", "decisions.md": "决策",
            "workflow-profile.md": "配置与执行契约", "init-record.md": "来源与验证",
            "init-baseline.md": "来源与验证", "authority.md": "规范与约束", "wiki-protocol.md": "规范与约束",
        }
        for path in sorted(paths):
            if path.suffix.lower() != ".md" or not path.is_relative_to(self.layout.wiki):
                continue
            relative = path.relative_to(self.layout.wiki)
            if len(relative.parts) < 2 or any(path.is_relative_to(root) for root in self.process_roots):
                continue
            kind = categories.get(relative.name, "配置与执行契约" if relative.parts[0] == "code-ai" else "主题")
            if relative.name == "README.md":
                kind = "概览与导航"
            elif "_blocks" in relative.parts:
                kind = "规范与约束"
            elif relative.parts[0] == "role-memory":
                kind = "角色经验"
            topics.setdefault(kind, []).append(f"- [{relative.as_posix()}]({relative.as_posix()})")
        index.content = (index.content or "").rstrip() + "\n\n" + "\n\n".join(
            f"## {heading}\n\n" + "\n".join(links) for heading, links in topics.items()
        ) + "\n"

    def _planned(
        self,
        rel: str,
        content: str,
        generated: bool,
        source: str,
        force: bool,
        generated_hashes: dict[str, str],
    ) -> PlannedFile:
        target = self.work / rel
        if not target.exists():
            return PlannedFile(rel=rel, action="create", generated=generated, content=content, source=source)
        if self.v2 and (target in (self.layout.wiki / "README.md", self.layout.wiki / "by-type.md") or target.is_relative_to(self.layout.role_memory)):
            return PlannedFile(rel, "skip", False, "project-owned Wiki page", source=source)
        if force:
            return PlannedFile(rel=rel, action="overwrite", generated=generated, reason="--force", content=content, source=source)
        if generated and rel in generated_hashes and util.sha256_file(target) == generated_hashes[rel]:
            return PlannedFile(
                rel=rel,
                action="skip",
                generated=generated,
                reason="unchanged generated file; use --force to rewrite",
                content=content,
                source=source,
            )
        return PlannedFile(rel=rel, action="skip", generated=generated, reason="exists; not overwritten", content=content, source=source)

    def _planned_upgrade(
        self,
        rel: str,
        content: str,
        generated: bool,
        source: str,
        generated_hashes: dict[str, str],
    ) -> PlannedFile:
        target = self.work / rel
        wiki_relative = (self.work / rel).relative_to(self.layout.wiki).as_posix() if (self.work / rel).is_relative_to(self.layout.wiki) else None
        project_topic = self.v2 and wiki_relative and wiki_relative.startswith(("product/", "engineering/")) and target != self.layout.workflow_profile
        if project_topic or wiki_relative in {"README.md", "by-type.md"} or (wiki_relative or "").startswith("role-memory/"):
            return PlannedFile(rel, "skip", False, "project-owned Wiki navigation and memory", source=source)
        if self.v2 and self.layout.process_root == self.layout.wiki and wiki_relative and not target.exists() and target != self.layout.workflow_profile:
            return PlannedFile(rel, "skip", False, "preserve migrated project structure", source=source)
        if not target.exists():
            return PlannedFile(rel=rel, action="create", generated=generated, content=content, source=source)
        if generated and rel in generated_hashes and util.sha256_file(target) == generated_hashes[rel]:
            if util.sha256_text(content) == util.sha256_file(target):
                return PlannedFile(rel=rel, action="skip", generated=generated, reason="up to date", content=content, source=source)
            return PlannedFile(rel=rel, action="overwrite", generated=generated, reason="refresh generated file", content=content, source=source)
        return PlannedFile(rel=rel, action="skip", generated=generated, reason="locally modified or not generated", content=content, source=source)

    # -- apply ------------------------------------------------------------
    def apply(self, plan: Plan) -> dict[str, str]:
        hashes: dict[str, str] = {}
        for item in plan.files:
            if item.action == "skip" or item.content is None:
                continue
            target = self.work / item.rel
            util.write_text(target, item.content)
            hashes[item.rel] = util.sha256_text(item.content)
        return hashes
