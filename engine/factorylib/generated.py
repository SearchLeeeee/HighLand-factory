"""Generated Markdown fragments used by workspace templates."""

from __future__ import annotations

import posixpath
from datetime import date
from pathlib import PurePosixPath
from typing import Any, Callable

from . import util
from .layout import Layout

COMMAND_LABELS = {
    "setup": "安装 / 初始化",
    "build": "构建",
    "lint": "静态检查",
    "typecheck": "类型检查",
    "test": "单元/集成测试",
    "e2e": "端到端测试",
    "dev": "本地开发服务",
    "verify": "验收验证",
}


def _code(value: str) -> str:
    return f"`{value}`"


def _join_commands(items: list[str]) -> str:
    if not items:
        return "_未配置_"
    return "<br>".join(_code(item) for item in items)


class GeneratedBlocks:
    """Maps ``{{generated:NAME}}`` placeholders to Markdown fragments."""

    def __init__(self, config: dict[str, Any], layout: Layout, version: str | None = None):
        self.config = config
        self.layout = layout
        self.version = version or util.factory_version()

    # -- shared accessors -------------------------------------------------
    @property
    def owners(self) -> list[dict[str, Any]]:
        owners = self.config.get("owners") or []
        return [owner for owner in owners if isinstance(owner, dict)]

    @property
    def commands(self) -> dict[str, list[str]]:
        commands = self.config.get("commands") or {}
        return {key: list(commands.get(key) or []) for key in COMMAND_LABELS}

    def owner_profile_rel(self, owner: dict[str, Any]) -> str:
        """Work-repo-relative path of an owner profile (config override wins)."""
        explicit = str(owner.get("profile") or "").strip()
        if explicit:
            return explicit
        wiki_rel = self.layout.wiki.relative_to(self.layout.work).as_posix()
        return f"{wiki_rel}/code-ai/{owner.get('id')}-agent.md"

    def owner_profile_link(self, owner: dict[str, Any]) -> str:
        """Link target for the code-ai README, relative to wiki/code-ai/."""
        wiki_rel = self.layout.wiki.relative_to(self.layout.work).as_posix()
        base = PurePosixPath(wiki_rel) / "code-ai"
        target = PurePosixPath(self.owner_profile_rel(owner))
        return posixpath.relpath(str(target), str(base))

    # -- owner/agent tables ----------------------------------------------
    def owners_table(self, owner: dict[str, Any] | None = None) -> str:
        lines = ["| Owner | ID | 代码范围 | Profile |", "| --- | --- | --- | --- |"]
        for item in self.owners:
            paths = "<br>".join(_code(path) for path in item.get("paths") or [])
            lines.append(
                f"| {item.get('title')} | `{item.get('id')}` | {paths or '_未配置_'} | "
                f"`{self.owner_profile_rel(item)}` |"
            )
        return "\n".join(lines)

    def code_ai_agent_table(self, owner: dict[str, Any] | None = None) -> str:
        lines = ["| Agent | 职责范围 | Profile |", "| --- | --- | --- |"]
        for item in self.owners:
            paths = "<br>".join(_code(path) for path in item.get("paths") or [])
            lines.append(
                f"| {item.get('title')} Agent | {paths or '见 profile'} | `{self.owner_profile_link(item)}` |"
            )
        lines.append("| Review Agent | 独立评审门禁 | `review-agent.md` |")
        lines.append("| Verification Agent | 独立验收 | 由 feature profile 生成 |")
        return "\n".join(lines)

    def owner_links(self, owner: dict[str, Any] | None = None) -> str:
        if not self.owners:
            return "_尚未配置 owner_"
        return "\n".join(
            f"- [{item.get('title')} Agent]({self.owner_profile_link(item)})"
            for item in self.owners
        )

    def review_agent_links(self, owner: dict[str, Any] | None = None) -> str:
        return "- [Review Agent](review-agent.md)\n- [Subagent Flow](subagent-flow.md)"

    # -- commands ---------------------------------------------------------
    def commands_table(self, owner: dict[str, Any] | None = None) -> str:
        lines = ["| 动作 | 命令 |", "| --- | --- |"]
        for key, label in COMMAND_LABELS.items():
            lines.append(f"| {label} | {_join_commands(self.commands.get(key, []))} |")
        return "\n".join(lines)

    def commands_detail(self, owner: dict[str, Any] | None = None) -> str:
        blocks: list[str] = []
        for key, label in COMMAND_LABELS.items():
            items = self.commands.get(key, [])
            if not items:
                continue
            blocks.append(f"### {label} (`{key}`)\n")
            blocks.append("```bash")
            blocks.extend(items)
            blocks.append("```")
        return "\n".join(blocks) if blocks else "_尚未配置任何命令；初始化时至少应提供 build 与 test。_"

    def workflow_profile_commands(self, owner: dict[str, Any] | None = None) -> str:
        lines = []
        for key, label in COMMAND_LABELS.items():
            items = self.commands.get(key, [])
            if not items:
                continue
            lines.append(f"- **{label}** (`{key}`): " + "; ".join(_code(item) for item in items))
        return "\n".join(lines) if lines else "- _尚未配置命令_"

    # -- repo / stack -----------------------------------------------------
    def repo_layout_table(self, owner: dict[str, Any] | None = None) -> str:
        repo = self.config.get("repo") or {}
        mode = repo.get("mode", "mono")
        lines = ["| 路径 | 作用 |", "| --- | --- |"]
        if mode == "split":
            lines.append(f"| `{repo.get('code_external')}` | 代码仓（独立 git 仓库） |")
        else:
            lines.append(f"| `{repo.get('code_path', 'code')}/` | 实现代码 |")
        lines.append(f"| `{repo.get('wiki_path', 'wiki')}/` | 长期权威文档与工作区 |")
        lines.append(f"| `{repo.get('wiki_path', 'wiki')}/feature-workspace/` | Feature 生命周期工作区 |")
        lines.append(f"| `{repo.get('wiki_path', 'wiki')}/code-ai/` | Agent profiles 与通用约束 |")
        return "\n".join(lines)

    def stack_summary(self, owner: dict[str, Any] | None = None) -> str:
        stack = self.config.get("project", {}).get("stack") or []
        if not stack:
            return "_初始化时未记录技术栈；请在 project.stack 中补充。_"
        return "\n".join(f"- {item}" for item in stack)

    # -- verification / security / packs ---------------------------------
    def verification_table(self, owner: dict[str, Any] | None = None) -> str:
        verification = self.config.get("verification") or {}
        lines = ["| 项目 | 值 |", "| --- | --- |"]
        lines.append(f"| 基线证据 | `{verification.get('baseline_evidence')}` |")
        lines.append(f"| 证据根 | `{verification.get('evidence_root')}` |")
        lines.append(f"| 隔离环境 | `{verification.get('isolated_env')}` |")
        return "\n".join(lines)

    def security_list(self, owner: dict[str, Any] | None = None) -> str:
        security = self.config.get("security") or {}
        forbidden = security.get("forbidden_operations") or []
        sensitive = security.get("sensitive_classes") or []
        lines = ["### 禁止操作", ""]
        lines.extend(f"- {item}" for item in forbidden) if forbidden else lines.append("- _尚未声明（初始化必须补充）_")
        lines.extend(["", "### 敏感数据类别", ""])
        lines.extend(f"- {item}" for item in sensitive) if sensitive else lines.append("- _尚未声明（初始化必须补充）_")
        return "\n".join(lines)

    def workflow_profile_security(self, owner: dict[str, Any] | None = None) -> str:
        security = self.config.get("security") or {}
        forbidden = security.get("forbidden_operations") or []
        sensitive = security.get("sensitive_classes") or []
        lines = []
        lines.append("- **禁止操作**: " + ("; ".join(forbidden) if forbidden else "_未声明_"))
        lines.append("- **敏感类别**: " + ("; ".join(sensitive) if sensitive else "_未声明_"))
        lines.append(f"- **密钥文件**: `{security.get('secrets_file')}`")
        return "\n".join(lines)

    def packs_table(self, owner: dict[str, Any] | None = None) -> str:
        packs = self.config.get("packs") or {}
        enabled = packs.get("enabled") or []
        lines = ["| Pack | 状态 |", "| --- | --- |"]
        for item in enabled:
            lines.append(f"| `{item}` | enabled |")
        for item in packs.get("disabled") or []:
            lines.append(f"| `{item}` | disabled |")
        if len(lines) == 2:
            lines.append("| _none_ | _未配置_ |")
        return "\n".join(lines)

    def workflow_profile_owners(self, owner: dict[str, Any] | None = None) -> str:
        if not self.owners:
            return "- _未配置 owner_"
        lines = []
        for item in self.owners:
            paths = ", ".join(_code(path) for path in item.get("paths") or [])
            lines.append(f"- `{item.get('id')}` — {item.get('title')} ({paths})")
        return "\n".join(lines)

    def workflow_profile_gates(self, owner: dict[str, Any] | None = None) -> str:
        workflow = self.config.get("workflow") or {}
        scope = workflow.get("scope_gate") or {}
        lines = [
            f"- scope_gate: {'on' if scope.get('enabled', True) else 'off'} "
            f"(split_default: {scope.get('split_default', True)})",
            f"- quick_change: {workflow.get('quick_change', True)}",
            f"- review_required: {workflow.get('review_required', True)}",
            f"- verification_separate: {workflow.get('verification_separate', True)}",
            f"- merge_requires_authorization: {workflow.get('merge_requires_authorization', True)}",
            f"- initiative_integration_required: {workflow.get('initiative_integration_required', True)}",
            f"- max_parallel_features: {workflow.get('max_parallel_features', 1)}",
        ]
        return "\n".join(lines)

    # -- per-owner fragments ---------------------------------------------
    def owner_paths(self, owner: dict[str, Any] | None = None) -> str:
        if not owner:
            return "_未配置_"
        return "\n".join(f"- `{path}`" for path in owner.get("paths") or [])

    def owner_role_boundaries(self, owner: dict[str, Any] | None = None) -> str:
        if not owner:
            return ""
        return (
            f"- 允许修改: 仅限 `{owner.get('id')}` 负责的路径（见上）。\n"
            "- 禁止修改: 其他 owner 的路径、`wiki/feature-workspace/` 生命周期 manifest、"
            "其他 Feature 的 profile、`.factory/state.json`。\n"
            "- 需要超出范围时：先提交 change request 给主 agent，先同步权威文档再实现。"
        )

    # -- dispatch ---------------------------------------------------------
    def get(self, name: str, owner: dict[str, Any] | None = None) -> str:
        method: Callable[..., str] | None = getattr(self, name, None)
        if method is None or name.startswith("_"):
            raise util.FactoryError(
                f"unknown generated block: {{generated:{name}}}. "
                "Add it to engine/factorylib/generated.py and document it in the template contract."
            )
        return method(owner)


def generated_names() -> list[str]:
    names = []
    for name in dir(GeneratedBlocks):
        if name.startswith("_") or name in {"get", "config", "layout", "version", "owners", "commands"}:
            continue
        attr = getattr(GeneratedBlocks, name)
        if callable(attr):
            names.append(name)
    return sorted(names)
