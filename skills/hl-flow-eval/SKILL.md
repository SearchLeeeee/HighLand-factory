---
name: hl-flow-eval
description: Review a recorded factory-flow by ledger directory and flow ID for agent behavior, delivered artifacts and performance. For an assigned experiment, grade its frozen task, rubric and first delivery.
---

# 独立流程评估

## 按流程编号复盘

用户提供工作根或共享记录根及流程编号时，从 `factory debug flow report --work WORK --flow ID` 开始。使用共享位置时传 `--records RECORDS`。当前进行中或已封存的记录均可只读复盘。

1. 按阶段、角色及事件的 `parent` 还原派工和交接。从 `review_events`、`open_steps` 和 `slowest_steps` 选择首次失败、修复或长时间步骤，按 `--event SEQ` 取证，需要上下文时使用 `--events`。
2. 在 `record_dir` 下按报告中的相对路径打开 stdout、stderr 和各次交付的文件。结合退出码和验收条件区分首次交付与后续修复。
3. 引用事件号、角色和产出版本。区别命令实测耗时、登记边界之间的时长和原因未知的空档；将人工或 agent 填写的说明和用量标明来源。没有经过录制入口的活动注明覆盖缺口。完整步骤见 `docs/flow-eval.md`。

## 分组实验评分

On an initialized work repo run `factory resolve --work <WORK_ROOT> --json`, read `<wiki>/README.md` first, then the current responsibility’s page in `<role_memory>/` if present. Use the returned paths and follow `<FACTORY_ROOT>/skills/hl-workflow-governance/references/wiki-memory.md` for role routing and task experience.

从本组裁判目录读取评分材料、项目配置和首次交付版本。通过工作仓的本机配置定位工厂与 Python，读取 workflow profile。只消费本组材料。记录评估版本、首场 merge 状态、首次交付和首次求助时点。

先从冻结版本运行题目定义的正式入口，用 subprocess 分别捕获 stdout、stderr 和退出码。用同一材料覆盖正例、边界与无关失败。裁判样例只放在分配的裁判目录。保留首次结果，修复单列。

再使用 factory debug report 读取本组记录，按采集覆盖、用户可见对话、工具实际返回和操作人观察判断是否需要帮助。区分正常产品裁决、自行纠错、人工给线索和交付后修复。缺乏依据记为未知。文件名不能证明 Agent 看到了对应正文，合并输出不能证明输出流。

在对话中报告整组是否形成交接、首次交付是否正确、是否独立完成、成本是否完整。若首场没有 merge，第二场记为未运行。列实际样例、继承与新引入的错误、时间、已知 token、缺失范围、人工次数和证据定位。分别计执行、记忆整理、一次性迁移和裁判成本。本轮只评价分配的任务。
