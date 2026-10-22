"""Project configuration: defaults, loading, validation and hashing."""

from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any

from . import util

CONFIG_SCHEMA = 1
CONFIG_REL = Path(".factory") / "factory.yaml"
LOCAL_REL = Path(".factory") / "local.yaml"
STATE_REL = Path(".factory") / "state.json"

CONFIG_HEADER = """# Project configuration for HighLand-factory.
# This file is the single source of truth for project-scoped workflow values.
# Edit it, then run: factory doctor --work .
# Machine-scoped values live in .factory/local.yaml (gitignored).

"""

DEFAULT_CONFIG: dict[str, Any] = {
    "schema": CONFIG_SCHEMA,
    "factory": {
        "version": ">=0.1.0 <0.2.0",
        "template": "workspace-v1",
    },
    "project": {
        "name": "",
        "slug": "",
        "one_liner": "",
        "stack": [],
        "language": {"docs": "zh-CN", "code": "en", "commit": "zh-CN"},
        "license": "MIT",
        "visibility": "private",
    },
    "repo": {
        "mode": "mono",
        "default_branch": "main",
        "code_path": "code",
        "wiki_path": "wiki",
        "code_external": None,
        "remote": None,
        "commit": {"format": "conventional"},
    },
    "owners": [
        {"id": "core", "title": "Core", "paths": ["code"]},
    ],
    "commands": {
        "setup": [],
        "build": [],
        "lint": [],
        "typecheck": [],
        "test": [],
        "e2e": [],
        "dev": [],
        "verify": [],
    },
    "verification": {
        "baseline_evidence": "wiki/validation/init-baseline.md",
        "evidence_root": "wiki/feature-workspace",
        "isolated_env": "local",
    },
    "workflow": {
        "scope_gate": {"enabled": True, "split_default": True},
        "quick_change": True,
        "review_required": True,
        "verification_separate": True,
        "merge_requires_authorization": True,
        "initiative_integration_required": True,
        "max_parallel_features": 1,
    },
    "security": {
        "forbidden_operations": [],
        "sensitive_classes": [],
        "secrets_file": ".factory/local.yaml",
    },
    "agents": {
        "platforms": ["dsh", "claude", "codex"],
        "review_model": None,
        "verification_model": None,
    },
    "packs": {
        "enabled": ["commit"],
        "disabled": [],
    },
}

COMMAND_KEYS = ("setup", "build", "lint", "typecheck", "test", "e2e", "dev", "verify")
TOP_LEVEL_KEYS = set(DEFAULT_CONFIG)
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
OWNER_ID_RE = re.compile(r"^[a-z][a-z0-9-]*$")


class ConfigError(util.FactoryError):
    """Raised when the project configuration is invalid."""


def default_config() -> dict[str, Any]:
    return copy.deepcopy(DEFAULT_CONFIG)


def config_path(work: Path) -> Path:
    return work / CONFIG_REL


def local_path(work: Path) -> Path:
    return work / LOCAL_REL


def state_path(work: Path) -> Path:
    return work / STATE_REL


def load_config(work: Path) -> dict[str, Any]:
    path = config_path(work)
    if not path.is_file():
        raise ConfigError(
            f"{path} not found. Initialize the work repo first: factory init --work {work}"
        )
    data = util.load_yaml_file(path)
    if not isinstance(data, dict):
        raise ConfigError(f"{path} must contain a YAML mapping")
    return data


def load_local(work: Path) -> dict[str, Any]:
    path = local_path(work)
    if not path.is_file():
        return {}
    data = util.load_yaml_file(path)
    return data if isinstance(data, dict) else {}


def load_state(work: Path) -> dict[str, Any]:
    path = state_path(work)
    if not path.is_file():
        return {}
    try:
        data = util.read_json_file(path)
    except util.FactoryError:
        return {}
    return data if isinstance(data, dict) else {}


def save_config(work: Path, config: dict[str, Any]) -> None:
    util.write_yaml(config_path(work), config, header=CONFIG_HEADER)


def save_local(work: Path, local: dict[str, Any]) -> None:
    util.write_yaml(
        local_path(work),
        local,
        header="# Machine-scoped factory values. Gitignored; safe to contain absolute paths.\n",
    )


def save_state(work: Path, state: dict[str, Any]) -> None:
    util.write_json(state_path(work), state)


def merge_answers(answers: dict[str, Any] | None) -> dict[str, Any]:
    config = default_config()
    if answers:
        if not isinstance(answers, dict):
            raise ConfigError("answers file must contain a YAML mapping")
        config = util.deep_merge(config, answers)
    return config


def config_hash(config: dict[str, Any]) -> str:
    import json

    canonical = json.dumps(config, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return util.sha256_text(canonical)


def validate_config(config: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Return (errors, warnings). Errors block init/doctor; warnings need --strict."""
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(config, dict):
        return ["configuration must be a YAML mapping"], warnings

    unknown = sorted(set(config) - TOP_LEVEL_KEYS - {key for key in config if str(key).startswith("x-")})
    for key in unknown:
        errors.append(f"unknown configuration section: {key!r} (use an x- prefix for extensions)")

    if config.get("schema") != CONFIG_SCHEMA:
        errors.append(f"schema must be {CONFIG_SCHEMA}")

    factory = config.get("factory") or {}
    if not isinstance(factory, dict) or not str(factory.get("version") or "").strip():
        errors.append("factory.version is required")

    project = config.get("project") or {}
    if not isinstance(project, dict):
        errors.append("project must be a mapping")
        project = {}
    name = str(project.get("name") or "").strip()
    slug = str(project.get("slug") or "").strip()
    if not name:
        errors.append("project.name is required")
    if not slug:
        errors.append("project.slug is required")
    elif not SLUG_RE.match(slug):
        errors.append(f"project.slug must match {SLUG_RE.pattern}: {slug!r}")
    language = project.get("language") or {}
    if not isinstance(language, dict) or not str(language.get("docs") or "").strip():
        errors.append("project.language.docs is required")
    visibility = str(project.get("visibility") or "")
    if visibility not in {"public", "private", "mixed"}:
        errors.append("project.visibility must be public, private or mixed")
    stack = project.get("stack")
    if not isinstance(stack, list):
        errors.append("project.stack must be a list")
    if not str(project.get("one_liner") or "").strip():
        warnings.append("project.one_liner is empty")

    repo = config.get("repo") or {}
    if not isinstance(repo, dict):
        errors.append("repo must be a mapping")
        repo = {}
    mode = str(repo.get("mode") or "")
    if mode not in {"mono", "split"}:
        errors.append("repo.mode must be mono or split")
    for key in ("code_path", "wiki_path"):
        value = str(repo.get(key) or "")
        if not value:
            errors.append(f"repo.{key} is required")
        else:
            path = Path(value)
            if path.is_absolute() or value.startswith(("/", "\\")) or ".." in path.parts:
                errors.append(f"repo.{key} must be a relative path inside the work repo: {value!r}")
    if mode == "split" and not str(repo.get("code_external") or "").strip():
        errors.append("repo.code_external is required when repo.mode is split")
    if not str(repo.get("default_branch") or "").strip():
        errors.append("repo.default_branch is required")

    owners = config.get("owners")
    if not isinstance(owners, list) or not owners:
        errors.append("owners must be a non-empty list")
        owners = []
    seen: set[str] = set()
    for index, owner in enumerate(owners):
        if not isinstance(owner, dict):
            errors.append(f"owners[{index}] must be a mapping")
            continue
        owner_id = str(owner.get("id") or "")
        if not OWNER_ID_RE.match(owner_id):
            errors.append(f"owners[{index}].id must match {OWNER_ID_RE.pattern}: {owner_id!r}")
        if owner_id in seen:
            errors.append(f"duplicate owner id: {owner_id}")
        seen.add(owner_id)
        if not str(owner.get("title") or "").strip():
            errors.append(f"owners[{index}].title is required")
        paths = owner.get("paths")
        if not isinstance(paths, list) or not paths:
            errors.append(f"owners[{index}].paths must be a non-empty list")
        profile = owner.get("profile")
        if profile is not None:
            profile_text = str(profile).strip()
            if not profile_text:
                errors.append(f"owners[{index}].profile must not be empty when present")
            else:
                profile_path = Path(profile_text)
                if profile_path.is_absolute() or profile_text.startswith(("/", "\\")) or ".." in profile_path.parts:
                    errors.append(f"owners[{index}].profile must be a relative path inside the work repo")
                elif profile_path.suffix.lower() != ".md":
                    errors.append(f"owners[{index}].profile must point to a Markdown file")

    commands = config.get("commands")
    if not isinstance(commands, dict):
        errors.append("commands must be a mapping")
        commands = {}
    for key in commands:
        if key not in COMMAND_KEYS:
            errors.append(f"unknown commands key: {key!r} (allowed: {', '.join(COMMAND_KEYS)})")
    for key in COMMAND_KEYS:
        value = commands.get(key, [])
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            errors.append(f"commands.{key} must be a list of strings")
    for key in ("test", "verify"):
        if not commands.get(key):
            warnings.append(f"commands.{key} is empty; acceptance evidence will be weak")

    verification = config.get("verification")
    if not isinstance(verification, dict):
        errors.append("verification must be a mapping")

    workflow = config.get("workflow")
    if not isinstance(workflow, dict):
        errors.append("workflow must be a mapping")
    else:
        for key in (
            "quick_change",
            "review_required",
            "verification_separate",
            "merge_requires_authorization",
            "initiative_integration_required",
        ):
            if not isinstance(workflow.get(key), bool):
                errors.append(f"workflow.{key} must be a boolean")
        max_parallel = workflow.get("max_parallel_features")
        if not isinstance(max_parallel, int) or max_parallel < 1:
            errors.append("workflow.max_parallel_features must be a positive integer")

    security = config.get("security")
    if not isinstance(security, dict):
        errors.append("security must be a mapping")
    else:
        for key in ("forbidden_operations", "sensitive_classes"):
            if not isinstance(security.get(key), list):
                errors.append(f"security.{key} must be a list")
        if not str(security.get("secrets_file") or "").strip():
            errors.append("security.secrets_file is required")

    agents = config.get("agents")
    if not isinstance(agents, dict):
        errors.append("agents must be a mapping")
    elif not isinstance(agents.get("platforms"), list):
        errors.append("agents.platforms must be a list")

    packs = config.get("packs")
    if not isinstance(packs, dict):
        errors.append("packs must be a mapping")
    else:
        for key in ("enabled", "disabled"):
            if not isinstance(packs.get(key), list):
                errors.append(f"packs.{key} must be a list")

    return errors, warnings


def require_valid(config: dict[str, Any]) -> None:
    errors, _ = validate_config(config)
    if errors:
        raise ConfigError("invalid project configuration:\n- " + "\n- ".join(errors))
