# 约束块（_blocks）

本目录存放可复用的**项目级约束块**。块是通用规则的唯一事实源，owner profile 与 feature profile 只引用、不复制。

## 1. 什么是块

- 一个块只表达一个可独立理解的约束主题，例如启动、安全、文档同步、评审。
- 块面向所有角色，不绑定具体 owner、具体 feature 或具体实现。
- 块内不得出现项目特有事实：不得写具体路径、命令、服务名、人员、业务规则或技术栈断言。
- 块的长度应控制在可一次读完的范围内；超过时拆分为多个块。

## 2. 组合规则

1. **块是唯一事实源**：同一约束只在块中维护一份正文。
2. **manifest 只声明组合**：哪个 profile 引用哪些块、包含哪些领域章节，写在 `_manifests/` 中。
3. **顶层 profile 必须完整、可直接执行**：owner profile 与评审 profile 要包含全部领域章节和有效引用，读者无需再猜。
4. **禁止把块正文粘贴进 feature profile**：feature profile 使用相对路径引用块，复制正文会造成版本漂移。
5. **引用使用相对路径**：从 `wiki/code-ai/` 出发写 `_blocks/<block>.md`；不要使用绝对路径或 wiki 链接语法。
6. **块变更必须重同步**：修改块后，按 `_manifests/` 声明重新生成或逐项核对所有受影响 profile，并在交接中记录。
7. **块不得互相复制**：块之间可以互相引用，但不得把另一块的正文抄进来。
8. **新增块必须登记**：在本页清单与相关 manifest 中同时登记，否则视为未生效。

## 3. 引用方式

- owner profile 或 feature profile：`[_blocks/startup-core.md](_blocks/startup-core.md)`。
- manifest：在 `global_blocks` 中写 `_blocks/startup-core.md`。
- 本页清单：同级相对链接，如 `[startup-core.md](startup-core.md)`。

引用只表达“适用”，不表达“可以跳过”。块与任务指令冲突时，先停止并升级，不得静默取舍。

## 4. 变更流程

1. 提出变更理由与影响面。
2. 修改块正文，保持单一主题与通用性。
3. 更新本页清单、相关 manifest 与受影响 profile。
4. 检查所有引用仍然有效、可达。
5. 在评审中确认没有引入项目特有事实或规则冲突。

## 5. 块清单

| 块 | 作用 |
| --- | --- |
| [startup-core.md](startup-core.md) | 启动阅读顺序、启动摘要与开工前停止条件 |
| [project-safety-boundaries.md](project-safety-boundaries.md) | 凭据、敏感数据、不可逆操作与最小权限边界 |
| [doc-sync-rule.md](doc-sync-rule.md) | 行为与契约变化时的文档同步要求 |
| [readme-sync-rule.md](readme-sync-rule.md) | 入口 README 的更新、链接与可达性规则 |
| [agent-notes-rule.md](agent-notes-rule.md) | 五字段记录头与 agent 记录的维护时机 |
| [commit-granularity.md](commit-granularity.md) | 按仓库模式划分的提交粒度与顺序 |
| [logging-and-diagnostics.md](logging-and-diagnostics.md) | 日志分级、结构化、脱敏与可诊断性 |
| [handoff-output.md](handoff-output.md) | 交接文档的固定结构与必备字段 |
| [common-definition-of-done.md](common-definition-of-done.md) | 通用完成定义与交付前自检 |
| [review-gate.md](review-gate.md) | 强制评审条件、独立性与阻断规则 |
| [review-agent-contract.md](review-agent-contract.md) | 评审报告的固定章节与结论约定 |
| [testing-quality-gate.md](testing-quality-gate.md) | 测试分层、回归与证据质量要求 |
| [fixture-governance.md](fixture-governance.md) | 测试夹具的来源、脱敏、确定性与治理 |
