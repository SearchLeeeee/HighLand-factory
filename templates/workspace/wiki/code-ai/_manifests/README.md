# Profile 清单（_manifests）

本目录存放 profile 的**组合声明**。manifest 说明一个 profile 由哪些通用块和哪些领域章节组成；真正可执行的是顶层 profile 文件。

## 1. 职责边界

- manifest 是声明，不是执行入口；不要把任务说明、临时状态或大段规则写进 manifest。
- 顶层 `<owner>-agent.md` 才是可执行 profile，必须完整、可直接阅读和执行。
- 块正文只在 `_blocks/` 维护；manifest 只登记块路径，不复制块内容。
- 项目特有事实只写入 `project-facts.md`，不写入 manifest。

## 2. 文件命名

- 每个 profile 一份 manifest，文件名与 profile 的 id 对齐。
- owner profile 使用工厂提供的 `owner.yml.tmpl` 渲染，每个 owner 一份。
- 评审 profile 使用固定的 `review-agent.yml`，不含 owner 占位符。
- 渲染后的 manifest 位于本目录，不得手工改写生成结果；要改就改模板或配置后重新生成。

## 3. 字段约定

| 字段 | 必填 | 含义 |
| --- | --- | --- |
| `id` | 是 | profile 唯一标识，与文件名、输出文件对应 |
| `title` | 是 | 人类可读名称 |
| `output` | 是 | 生成的可执行 profile 路径，相对 wiki 根 |
| `composition_model` | 是 | 组合模型；`blocks-plus-domain-sections` 表示通用块加领域章节 |
| `global_blocks` | 是 | 引用的通用块相对路径列表，顺序即建议阅读顺序 |
| `domain_sections` | 是 | 该 profile 必须包含的领域章节标识列表 |
| `notes` | 否 | 组合意图、维护提醒与生成约束 |

新增字段前先确认工厂渲染器支持；未知字段视为未生效。

## 4. 标准块清单

owner profile 的标准块集合固定为：

`startup-core`、`project-safety-boundaries`、`doc-sync-rule`、`readme-sync-rule`、`agent-notes-rule`、`commit-granularity`、`logging-and-diagnostics`、`handoff-output`、`common-definition-of-done`、`review-gate`、`review-agent-contract`、`testing-quality-gate`、`fixture-governance`。

评审 profile 不需要 `commit-granularity`，其余块保持同等安全与质量下限。

## 5. 组合与同步规则

1. 先确定职责与写入范围，再选择块；不要为了“看起来完整”堆砌块。
2. 领域章节必须覆盖：身份与范围、何时使用、必读顺序、可写与禁写范围、工作循环、评审关注点、交接规则。
3. 块变更后，按 manifest 找到所有引用它的 profile，逐项重新生成或核对。
4. manifest 与顶层 profile 不一致时，以 manifest 为声明源修复 profile，反之亦然，不能两处各写一套。
5. 删除 profile 时同时删除 manifest 与入口链接，避免孤儿文件。

## 6. 当前清单

- 评审 profile 声明：[review-agent.yml](review-agent.yml)
- owner profile 声明模板：`owner.yml.tmpl`，由引擎按配置的 owner 列表渲染为
  `<owner-id>.yml`（每个 owner 一个文件，文件名即 owner id）。

具体 owner 列表以工厂配置为准；本目录不记录人员姓名或分工状态。
