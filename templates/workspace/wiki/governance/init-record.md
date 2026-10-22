# 初始化记录

本文件记录工作仓库初始化的 provenance：运行模式、生效配置、初始答案、假设、生成
文件哈希与下一步。`factory init` 会用真实记录覆盖本骨架；在那之前，它只说明仓库尚未
通过引擎初始化。

## 状态

- 若本段仍在：说明当前仓库还没有执行 `factory init`，或初始化记录被删除。请运行
  `factory init --work .`（升级时用 `factory upgrade`）。
- 本文件是历史证据，不是流程门禁的事实源。门禁以 `.factory/factory.yaml` 和
  [Workflow Profile](workflow-profile.md) 为准。

## 初始化的最小验收

1. `factory doctor --work .` 无 error（warning 需要逐项确认）。
2. 按 `.factory/factory.yaml` 的 `commands` 跑通一次，并把结果记进
   [初始化基线证据](../validation/init-baseline.md)。
3. 之后再提交第一个 commit，保证仓库历史从可复现的基线开始。
