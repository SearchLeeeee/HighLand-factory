"""Unit tests for configuration defaults, merging and validation."""

from __future__ import annotations

import copy

import pytest

from factorylib import config


def _valid() -> dict:
    cfg = config.default_config()
    cfg["project"]["name"] = "Example"
    cfg["project"]["slug"] = "example"
    return cfg


def test_defaults_are_valid_after_identity() -> None:
    errors, warnings = config.validate_config(_valid())
    assert errors == []
    assert any("test" in warning for warning in warnings)


def test_unknown_top_level_key_is_rejected() -> None:
    cfg = _valid()
    cfg["surprise"] = True
    errors, _ = config.validate_config(cfg)
    assert any("unknown configuration section" in error for error in errors)


def test_extension_prefix_is_allowed() -> None:
    cfg = _valid()
    cfg["x-team"] = {"name": "core"}
    errors, _ = config.validate_config(cfg)
    assert errors == []


def test_invalid_slug_rejected() -> None:
    cfg = _valid()
    cfg["project"]["slug"] = "Bad Slug!"
    errors, _ = config.validate_config(cfg)
    assert any("project.slug" in error for error in errors)


def test_split_requires_external_code() -> None:
    cfg = _valid()
    cfg["repo"]["mode"] = "split"
    errors, _ = config.validate_config(cfg)
    assert any("code_external" in error for error in errors)
    cfg["repo"]["code_external"] = "../code"
    errors, _ = config.validate_config(cfg)
    assert errors == []


def test_absolute_repo_path_rejected() -> None:
    cfg = _valid()
    cfg["repo"]["code_path"] = "/absolute/code"
    errors, _ = config.validate_config(cfg)
    assert any("relative path" in error for error in errors)


def test_duplicate_owner_rejected() -> None:
    cfg = _valid()
    cfg["owners"] = [
        {"id": "core", "title": "Core", "paths": ["code"]},
        {"id": "core", "title": "Core again", "paths": ["code"]},
    ]
    errors, _ = config.validate_config(cfg)
    assert any("duplicate owner" in error for error in errors)


def test_answers_deep_merge_does_not_mutate_defaults() -> None:
    before = copy.deepcopy(config.DEFAULT_CONFIG)
    merged = config.merge_answers({"project": {"name": "X", "language": {"docs": "en"}}})
    assert merged["project"]["name"] == "X"
    assert merged["project"]["language"]["docs"] == "en"
    assert merged["project"]["language"]["code"] == "en"
    assert config.DEFAULT_CONFIG == before


def test_config_hash_is_stable() -> None:
    cfg = _valid()
    assert config.config_hash(cfg) == config.config_hash(copy.deepcopy(cfg))
    cfg["project"]["name"] = "Other"
    assert config.config_hash(cfg) != config.config_hash(_valid())


@pytest.mark.parametrize(
    ("current", "spec", "expected"),
    [
        ("0.1.0", ">=0.1.0 <0.2.0", True),
        ("0.2.0", ">=0.1.0 <0.2.0", False),
        ("0.1.0", "0.1.0", True),
        ("0.1.1", "0.1.0", False),
        ("0.3.5", "^0.3.0", True),
        ("0.4.0", "^0.3.0", False),
    ],
)
def test_version_satisfies(current: str, spec: str, expected: bool) -> None:
    from factorylib import doctor

    assert doctor.version_satisfies(current, spec)[0] is expected
