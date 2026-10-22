"""Unit tests for layout resolution."""

from __future__ import annotations

from pathlib import Path

from factorylib import config, layout


def _cfg(mode: str = "mono") -> dict:
    cfg = config.default_config()
    cfg["project"]["name"] = "Example"
    cfg["project"]["slug"] = "example"
    cfg["repo"]["mode"] = mode
    if mode == "split":
        cfg["repo"]["code_external"] = "../external-code"
    return cfg


def test_mono_layout(tmp_path: Path) -> None:
    work = tmp_path / "work"
    work.mkdir()
    resolved = layout.build_layout(work, _cfg(), {"factory_root": str(tmp_path), "python": "python"})
    assert resolved.code == work / "code"
    assert resolved.wiki == work / "wiki"
    assert resolved.feature_workspace == work / "wiki" / "feature-workspace"
    assert resolved.registry == work / "wiki" / "feature-workspace" / "registry.yaml"


def test_split_layout_uses_external_code(tmp_path: Path) -> None:
    work = tmp_path / "work"
    work.mkdir()
    resolved = layout.build_layout(work, _cfg("split"), {"factory_root": str(tmp_path), "python": "python"})
    assert resolved.code == (work / "../external-code").resolve()
    assert resolved.wiki == work / "wiki"


def test_custom_wiki_path(tmp_path: Path) -> None:
    work = tmp_path / "work"
    work.mkdir()
    cfg = _cfg()
    cfg["repo"]["wiki_path"] = "docs-root"
    resolved = layout.build_layout(work, cfg, {})
    assert resolved.wiki == work / "docs-root"
    assert resolved.feature_workspace == work / "docs-root" / "feature-workspace"
