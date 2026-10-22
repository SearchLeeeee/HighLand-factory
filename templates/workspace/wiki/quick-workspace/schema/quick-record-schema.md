# Quick Record Schema

每条记录是一个带 YAML frontmatter 的 Markdown 文件。它是过程交接材料，永远不是
生命周期 manifest。

## 必需 frontmatter

```yaml
id: quick-YYYYMMDD-###
title: ""
kind: bugfix | adjustment
status: draft | grilling | ready-for-implementation | implementing | verification | completed | escalated | blocked
created_at: ""
updated_at: ""
scope_verdict: pending | lightweight | escalate
escalation_reason: null
next_skill: null
wiki_targets: []
wiki_merge_readiness: ready | needs-target | blocked
```

字段说明：

| 字段 | 含义 |
| --- | --- |
| `id` | `quick-` + 日期 + 三位序号，全局唯一，不复用。 |
| `title` | 一句话说明这次改什么。 |
| `kind` | `bugfix`（行为错误）或 `adjustment`（细节调整）。 |
| `status` | 记录在当前流程中的位置。 |
| `scope_verdict` | `pending` 未评估、`lightweight` 可以走 Quick 通道、`escalate` 必须升级。 |
| `escalation_reason` | 升级时必须给出具体原因，不允许写「太大了」。 |
| `next_skill` | 下一步负责的环节；`null` 表示当前无待办。 |
| `wiki_targets` | 受影响的长期文档相对路径列表。 |
| `wiki_merge_readiness` | `ready` 可合并、`needs-target` 缺目标文档、`blocked` 被阻塞。 |

`status` 与 `scope_verdict` 只由 quick 流程解释；不得加入 Feature 状态机、Feature
registry 或长期 Wiki 权威文档。

## 必需小节

1. Request：原始请求与预期行为。
2. Feasibility Grill：可行性追问的关键结论。
3. Scope Gate：`scope_verdict` 的判定依据。
4. Confirmed Change Points：确认要改的点，逐条对应文件范围。
5. Context Compaction：可复用的压缩上下文。
6. Implementation Notes：实现摘要与取舍。
7. Verification Evidence：证据字段见下节。
8. Wiki Merge Handoff：`wiki_targets` 与待合并结论。
9. Open Questions / Residual Risk：未决问题与残余风险。

## 证据字段

验证证据至少记录：

```yaml
verification:
  executed_at: ""
  environment: ""        # 隔离方式或环境标识
  commands: []           # 实际执行的命令，与 workflow-profile 一致
  result: passed | failed | not-applicable
  evidence_paths: []     # 原始日志/截图/输出的相对路径
  notes: ""
```

要求：

- `commands` 必须是真实执行过的命令，不能写「按需要运行」。
- `result` 必须可判定；失败就是失败，不得用「部分通过」模糊。
- 证据文件与记录一起保留，不因完成而删除。
- 证据中不得出现真实密钥、完整账号或私有端点。

## 升级规则

- `scope_verdict: escalate` 时，必须补齐 `escalation_reason`、`next_skill` 和
  `wiki_targets`，并把记录移动到 `escalated/`。
- 升级后的生命周期由 Feature 工作区接管；本记录只作为来源引用，不改写为
  `initiative.yaml` 或 `feature.yaml`。
- `completed/` 与 `escalated/` 中的记录只追加：修正与新证据写进 `Addenda` 小节，
  既有结论保持原样。

## 命名与保留

- 文件名与 `id` 一致：`quick-YYYYMMDD-###.md`。
- 序号在同一天内递增；跨天重新从 `001` 开始。
- 记录不因完成而删除；清理只能由明确的保留策略决定。
