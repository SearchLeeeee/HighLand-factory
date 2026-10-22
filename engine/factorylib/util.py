"""Shared utilities for the HighLand-factory engine.

The engine is deliberately dependency-light: standard library plus PyYAML.
It must run on Windows and POSIX with Python >= 3.10.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - exercised only on broken installs
    yaml = None  # type: ignore


FACTORY_ROOT = Path(__file__).resolve().parents[2]
ENGINE_ROOT = FACTORY_ROOT / "engine"
TEMPLATE_ROOT = FACTORY_ROOT / "templates" / "workspace"
OWNER_TEMPLATE_ROOT = FACTORY_ROOT / "templates" / "owner-templates"
SKILLS_ROOT = FACTORY_ROOT / "skills"

DATE_UNSET = "1970-01-01"


class FactoryError(RuntimeError):
    """A user-facing, actionable engine error."""


def require_yaml() -> Any:
    if yaml is None:
        raise FactoryError(
            "PyYAML is not installed for this Python interpreter. "
            "Run the engine with the interpreter recorded in .factory/local.yaml, "
            "or bootstrap one with: python -m venv .venv && .venv/bin/pip install pyyaml "
            "(see install/install.ps1 or install/install.sh)."
        )
    return yaml


def load_yaml_file(path: Path) -> Any:
    yaml = require_yaml()
    try:
        text = path.read_text(encoding="utf-8-sig")
    except FileNotFoundError as exc:
        raise FactoryError(f"file not found: {path}") from exc
    except OSError as exc:
        raise FactoryError(f"cannot read {path}: {exc}") from exc
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise FactoryError(f"invalid YAML in {path}: {exc}") from exc
    return {} if data is None else data


def dump_yaml(data: Any) -> str:
    yaml = require_yaml()
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=1000, default_flow_style=False)


def read_json_file(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise FactoryError(f"file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise FactoryError(f"invalid JSON in {path}: {exc}") from exc


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".factory-tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def write_yaml(path: Path, data: Any, header: str = "") -> None:
    body = dump_yaml(data)
    text = (header + "\n" if header else "") + body
    write_text(path, text)


def write_json(path: Path, data: Any) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False) + "\n")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def factory_version() -> str:
    try:
        return (FACTORY_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    except OSError:
        return "0.0.0-dev"


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge ``override`` into ``base``; lists are replaced."""
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def flatten(data: dict[str, Any], prefix: str = "") -> dict[str, str]:
    """Flatten a nested mapping into dotted keys (used for template placeholders)."""
    flat: dict[str, str] = {}
    for key, value in data.items():
        dotted = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, dict):
            flat.update(flatten(value, dotted))
        elif isinstance(value, list):
            flat[dotted] = ", ".join(str(item) for item in value)
        elif value is None:
            flat[dotted] = ""
        else:
            flat[dotted] = str(value)
    return flat


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug or "project"


def json_default(value: Any) -> Any:  # pragma: no cover - convenience only
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"not JSON serializable: {type(value)!r}")


def print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2, default=json_default))


def is_git_repo(path: Path) -> bool:
    return (path / ".git").exists()


def find_work_root(start: Path) -> Path:
    """Walk upward until a directory containing .factory/factory.yaml is found."""
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".factory" / "factory.yaml").is_file():
            return candidate
    raise FactoryError(
        f"no initialized work repo found from {start} (missing .factory/factory.yaml). "
        "Run: factory init --work <path>"
    )


def rel_posix(path: Path, base: Path) -> str:
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def echo_stderr(message: str) -> None:
    print(message, file=sys.stderr)
