"""Template rendering and write planning for work-repo generation."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from . import config as config_mod
from . import util
from .generated import GeneratedBlocks
from .layout import Layout

PLACEHOLDER_RE = re.compile(r"\{\{([A-Za-z0-9_.:\-]+)\}\}")
TEMPLATE_SUFFIX = ".tmpl"

# Maintainer-only files that must never be copied into a generated work repo.
SKIP_TEMPLATE_FILES = {
    "README.md",
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
        self.blocks = GeneratedBlocks(project_config, layout, self.version)
        self.scalars = self._build_scalars()

    # -- context ----------------------------------------------------------
    def _build_scalars(self) -> dict[str, str]:
        flat = util.flatten(self.config)
        flat["generated.date"] = date.today().isoformat()
        flat["generated.factory_version"] = self.version
        flat["layout.code"] = util.rel_posix(self.layout.code, self.layout.work)
        flat["layout.wiki"] = util.rel_posix(self.layout.wiki, self.layout.work)
        return flat

    def _map_rel(self, rel: str) -> str | None:
        """Map template paths (``code/``, ``wiki/``) onto configured folder names.

        Returns ``None`` when the template file must not be written at all
        (``split`` mode: the code tree belongs to the external code repo).
        """
        repo = self.config.get("repo") or {}
        wiki_name = str(repo.get("wiki_path") or "wiki").strip("/")
        code_name = str(repo.get("code_path") or "code").strip("/")
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

    # -- plan -------------------------------------------------------------
    def plan(self, *, force: bool = False, only: set[str] | None = None) -> Plan:
        if not self.template_root.is_dir():
            raise RenderError(f"template root not found: {self.template_root}")
        plan = Plan(work=self.work)
        state = config_mod.load_state(self.work)
        generated_hashes: dict[str, str] = state.get("generated_files") or {}

        for source in sorted(self.template_root.rglob("*")):
            if not source.is_file():
                continue
            rel_source = source.relative_to(self.template_root).as_posix()
            if rel_source in SKIP_TEMPLATE_FILES:
                continue
            if rel_source.endswith(TEMPLATE_SUFFIX):
                rel_out = self._map_rel(rel_source[: -len(TEMPLATE_SUFFIX)])
                content = self.render(source.read_text(encoding="utf-8"))
                generated = True
            else:
                rel_out = self._map_rel(rel_source)
                content = source.read_text(encoding="utf-8")
                generated = False
            if rel_out is None:
                continue
            if only and rel_out not in only:
                continue
            plan.files.append(
                self._planned(rel_out, content, generated, rel_source, force, generated_hashes)
            )

        # Per-owner files.
        owner_profile_template = self.owner_template_root / "owner-agent.md.tmpl"
        owner_manifest_template = self.template_root / OWNER_MANIFEST_TEMPLATE
        for owner in self.blocks.owners:
            owner_id = str(owner.get("id"))
            explicit_profile = str(owner.get("profile") or "").strip()
            if owner_profile_template.is_file():
                content = self.render(owner_profile_template.read_text(encoding="utf-8"), owner=owner)
                rel = explicit_profile or self._map_rel(f"wiki/code-ai/{owner_id}-agent.md")
                if rel is not None and (not only or rel in only):
                    plan.files.append(
                        self._planned(rel, content, True, "templates/owner-templates/owner-agent.md.tmpl", force, generated_hashes)
                    )
            if owner_manifest_template.is_file():
                content = self.render(owner_manifest_template.read_text(encoding="utf-8"), owner=owner)
                rel = self._map_rel(f"wiki/code-ai/_manifests/{owner_id}.yml")
                if rel is not None and (not only or rel in only):
                    plan.files.append(
                        self._planned(rel, content, True, OWNER_MANIFEST_TEMPLATE, force, generated_hashes)
                    )
        return plan

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

    def plan_upgrade(self) -> Plan:
        """Refresh generated files that are unchanged since the last generation.

        Files that were edited by the project (hash differs from the recorded
        generated hash) are reported as skipped and never overwritten.
        """
        if not self.template_root.is_dir():
            raise RenderError(f"template root not found: {self.template_root}")
        plan = Plan(work=self.work)
        state = config_mod.load_state(self.work)
        generated_hashes: dict[str, str] = state.get("generated_files") or {}

        for source in sorted(self.template_root.rglob("*")):
            if not source.is_file():
                continue
            rel_source = source.relative_to(self.template_root).as_posix()
            if rel_source in SKIP_TEMPLATE_FILES:
                continue
            if rel_source.endswith(TEMPLATE_SUFFIX):
                rel_out = self._map_rel(rel_source[: -len(TEMPLATE_SUFFIX)])
                content = self.render(source.read_text(encoding="utf-8"))
                generated = True
            else:
                rel_out = self._map_rel(rel_source)
                content = source.read_text(encoding="utf-8")
                generated = False
            if rel_out is None:
                continue
            plan.files.append(self._planned_upgrade(rel_out, content, generated, rel_source, generated_hashes))

        owner_profile_template = self.owner_template_root / "owner-agent.md.tmpl"
        owner_manifest_template = self.template_root / OWNER_MANIFEST_TEMPLATE
        for owner in self.blocks.owners:
            owner_id = str(owner.get("id"))
            explicit_profile = str(owner.get("profile") or "").strip()
            if owner_profile_template.is_file():
                content = self.render(owner_profile_template.read_text(encoding="utf-8"), owner=owner)
                rel = explicit_profile or self._map_rel(f"wiki/code-ai/{owner_id}-agent.md")
                if rel is not None:
                    plan.files.append(self._planned_upgrade(rel, content, True, "templates/owner-templates/owner-agent.md.tmpl", generated_hashes))
            if owner_manifest_template.is_file():
                content = self.render(owner_manifest_template.read_text(encoding="utf-8"), owner=owner)
                rel = self._map_rel(f"wiki/code-ai/_manifests/{owner_id}.yml")
                if rel is not None:
                    plan.files.append(self._planned_upgrade(rel, content, True, OWNER_MANIFEST_TEMPLATE, generated_hashes))
        return plan

    def _planned_upgrade(
        self,
        rel: str,
        content: str,
        generated: bool,
        source: str,
        generated_hashes: dict[str, str],
    ) -> PlannedFile:
        target = self.work / rel
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
