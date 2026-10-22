# Quick Workspace

本目录保存有界 bugfix 与细节调整（Quick Change）的过程记录、验证证据和升级交接。
它不是当前系统的权威，也不是需求生命周期 manifest。

## 权威与发现边界

- 本目录只是过程材料：不构成当前系统事实，不参与长期知识发现。
- 默认排除在长期记忆、派生索引、常规 Wiki 检索、Graph 视图、MOC 导航、新
  Feature 的 `context_refs` 以及「当前系统行为」类报告之外。
- 只有当前 quick 流程、显式交接或审计请求点名某条记录时才定向读取。
- Feature 工作区的默认隔离规则对本目录同样适用。

## 目录结构

```text
quick-workspace/
  README.md
  schema/quick-record-schema.md
  active/<quick-id>.md
  completed/<quick-id>.md
  escalated/<quick-id>.md
```

记录在受理时创建于 `active/`。实现完成并通过可重复验证后移动到 `completed/`；
当重流程（Feature 工作区）接管时移动到 `escalated/`。`completed/` 与 `escalated/`
中的记录只追加，不改写既有结论。

## 状态含义

| 状态 | 含义 |
| --- | --- |
| `active` | 正在受理、grilling、实现或验证中。 |
| `completed` | 已实现并通过可重复验证，等待或已完成长期 Wiki 交接。 |
| `escalated` | 超出 Quick Change 边界，已由 Feature 工作区接管。 |

## 升级规则

出现以下任一情况必须升级为 Feature，不允许在 Quick Change 里硬做：

- 需要改动多个 owner 的责任范围，或跨多个实现领域。
- 需要重定义契约、数据模型或数据迁移。
- 需要修改安全边界、权限、机密处理或生产写操作。
- 无法用一组连贯的端到端验证场景证明完成。
- 讨论中出现新的业务目标，或范围持续扩张。

升级时在记录中补齐 `escalation_reason` 与 `next_skill`，移动到 `escalated/`，并在
Feature 工作区创建对应需求。Quick 记录本身不成为 Feature manifest。

## 长期 Wiki 交接

- `completed` 记录只是 staged source，不改变长期权威。
- 需要 owner 授权后执行语义合并，产生长期文档更新、MOC 更新和完整校验。
- 校验失败时保留记录与证据，不要删除。
- 不要因为「做完了」就删除 quick 记录：除非保留策略明确改变，否则它们作为非权威
  过程历史保留。

## 与其他工作区的关系

- 与 Feature 工作区的区别：Quick 记录是一次性过程记录，没有 phase/state 状态机，
  也没有依赖与 Wave。
- 与长期 Wiki 的区别：长期 Wiki 描述现在成立的事实；本目录描述「这次怎么改的」。
