"""Explicit process-workspace roots shared by layout, Wiki gates and maintenance.

Roots are directories relative to the configured Wiki, not filename patterns.
The built-in workspaces stay excluded for older configs with no registration
key. Projects may add roots through ``workflow.process_workspaces``.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any


PROCESS_WORKSPACE_DIRS = {
    "feature_workspace": "feature-workspace",
    "quick_workspace": "quick-workspace",
    "refactor_workspace": "refactor-workspace",
}
DEFAULT_PROCESS_WORKSPACES = tuple(PROCESS_WORKSPACE_DIRS.values())


def workspace_name(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("workflow.process_workspaces entries must be non-empty strings")
    name = value.strip().replace("\\", "/").rstrip("/")
    parts = name.split("/")
    if (
        not name
        or PurePosixPath(name).is_absolute()
        or PureWindowsPath(name).drive
        or any(part in {"", ".", ".."} for part in parts)
        or any(char in name for char in "*?[]\r\n\0")
    ):
        raise ValueError(
            "workflow.process_workspaces entries must be explicit Wiki-relative "
            f"directory paths without traversal or globs: {value!r}"
        )
    if PurePosixPath(name).suffix.casefold() == ".md":
        raise ValueError(f"workflow.process_workspaces must name directories, not Markdown files: {value!r}")
    return name


def process_workspace_names(
    config: Mapping[str, Any] | None = None, *, additional: Iterable[str] = ()
) -> tuple[str, ...]:
    """Return built-in and explicitly registered Wiki-relative directory names."""
    workflow = (config or {}).get("workflow", {})
    if not isinstance(workflow, Mapping):
        raise ValueError("workflow must be a mapping")
    registered = workflow.get("process_workspaces", [])
    if not isinstance(registered, list):
        raise ValueError("workflow.process_workspaces must be a list of directory paths")
    names = list(DEFAULT_PROCESS_WORKSPACES)
    for value in [*registered, *additional]:
        name = workspace_name(value)
        if name not in names:
            names.append(name)
    return tuple(names)


def process_workspace_roots(
    wiki_root: Path, config: Mapping[str, Any] | None = None, *, additional: Iterable[str] = ()
) -> tuple[Path, ...]:
    """Resolve roots; absent directories are valid and can be created lazily."""
    wiki = wiki_root.expanduser().resolve(strict=False)
    config = config or {}
    configured_path = (config.get("workflow") or {}).get("workspace_root")
    v2 = (config.get("factory") or {}).get("template") == "workspace-v2"
    work = wiki
    wiki_name = Path((config.get("repo") or {}).get("wiki_path") or "wiki")
    for _ in wiki_name.parts:
        work = work.parent
    base = wiki
    if configured_path or v2:
        base = (work / workspace_name(configured_path or "workspace")).resolve()
        if not base.is_relative_to(work) or base == work:
            raise ValueError("workflow.workspace_root escapes work repository")
    roots: list[Path] = []
    for name in process_workspace_names(config, additional=additional):
        parent = base if name in DEFAULT_PROCESS_WORKSPACES else wiki
        root = (parent / name).resolve(strict=False)
        if root == parent or not root.is_relative_to(parent):
            raise ValueError(f"process workspace must stay inside its Wiki: {name!r}")
        if root.exists() and not root.is_dir():
            raise ValueError(f"process workspace must be a directory: {name!r}")
        roots.append(root)
    retained = retained_workspace_root(work, config, base)
    if retained:
        for name in DEFAULT_PROCESS_WORKSPACES:
            root = (retained / name).resolve()
            if not root.is_relative_to(retained) or root == retained:
                raise ValueError(f"retained process workspace escapes its root: {name}")
            roots.append(root)
    return tuple(roots)


def retained_workspace_root(work: Path, config: Mapping[str, Any], active: Path) -> Path | None:
    """An optional former process root reserved for explicit historical lookup."""
    value = (config.get("workflow") or {}).get("retained_workspace_root")
    if value is None:
        return None
    root = (work / workspace_name(value)).resolve()
    if root == work or not root.is_relative_to(work) or root.is_relative_to(active) or active.is_relative_to(root):
        raise ValueError("workflow.retained_workspace_root must be inside the work repo and separate from the active process root")
    return root


def retained_registry_for(registry: Path) -> Path | None:
    """Find the archive for either configured registry path."""
    registry = registry.resolve()
    for parent in registry.parents:
        if not (parent / ".factory" / "factory.yaml").is_file():
            continue
        from . import config, layout

        paths = layout.build_layout(parent, config.load_config(parent))
        if registry in {paths.registry, paths.retained_registry}:
            return paths.retained_registry
    return None


def is_process_path(
    path: Path,
    wiki_root: Path,
    config: Mapping[str, Any] | None = None,
    *,
    additional: Iterable[str] = (),
) -> bool:
    """Whether an absolute path (or Wiki-relative path) is under a process root."""
    wiki = wiki_root.expanduser().resolve(strict=False)
    target = (path if path.is_absolute() else wiki / path).resolve(strict=False)
    return any(target.is_relative_to(root) for root in process_workspace_roots(wiki, config, additional=additional))


def project_config_for_wiki(wiki_root: Path) -> dict[str, Any] | None:
    """Find the nearest factory config whose configured Wiki is exactly this root.

    Standalone Wiki tools need no YAML dependency when no factory project is
    present. A project config is read with the engine's existing YAML loader;
    invalid registered roots or unreadable YAML must never silently widen scan.
    """
    wiki = wiki_root.expanduser().resolve(strict=False)
    for parent in (wiki, *wiki.parents):
        config_path = parent / ".factory" / "factory.yaml"
        if not config_path.is_file():
            continue
        from . import util

        try:
            data = util.load_yaml_file(config_path)
        except util.FactoryError as exc:
            raise ValueError(str(exc)) from exc
        if not isinstance(data, dict):
            raise ValueError(f"factory configuration must be a mapping: {config_path}")
        repo = data.get("repo") or {}
        if not isinstance(repo, dict):
            raise ValueError(f"repo must be a mapping: {config_path}")
        configured_wiki = (parent / str(repo.get("wiki_path") or "wiki")).resolve(strict=False)
        if configured_wiki == wiki:
            return data
    return None
