# workspace 模板维护说明

> **这是模板维护者文档，不是工作仓库的内容。**
>
> 两条硬性约束：
>
> 1. **不要在本目录写任何项目事实。** 项目名称、命令、owner、端口、验收结论都属于
>    具体工作仓库，属于 `.factory/factory.yaml` 和 `wiki/`。模板里只能出现结构性
>    说明、占位符和默认值。
> 2. **本文件与 `README.md.tmpl` 争用同一个产物路径。** 引擎当前已在
>    `engine/factorylib/render.py` 的 `SKIP_TEMPLATE_FILES` 中排除本文件，因此它不会
>    被复制进工作仓库。改引擎时必须保留这个排除项，否则本文件会覆盖渲染后的
>    `README.md`。

## 这个目录是什么

`templates/workspace/` 是一个工作仓库的完整骨架。`factory init` 把它实例化到
目标目录：标量占位符被替换，`.tmpl` 去掉后缀，其余文件原样复制。

`templates/workspace/wiki/code-ai/` 由另一份模板负责，本目录不包含、也不应创建
该子目录下的任何文件（根 MOC 只是链接到 `code-ai/README.md`，由对方保证存在）。

## 引擎契约（摘要）

- 后缀 `.tmpl` 的文件：渲染后写出去掉 `.tmpl` 的路径；其余文件按字节复制。
- 标量占位符：`{{dotted.key}}`；生成 Markdown 片段：`{{generated:NAME}}`。
- 未知占位符是硬错误：只能用下面两张表列出的名字。

## 标量占位符与使用位置

| 占位符 | 含义 | 出现位置 |
| --- | --- | --- |
| `{{project.name}}` | 项目显示名 | `README.md.tmpl`、`AGENTS.md.tmpl`、`CLAUDE.md.tmpl`、`.factory/factory.yaml.tmpl` |
| `{{project.slug}}` | 仓库/包标识（ASCII） | `.factory/factory.yaml.tmpl` |
| `{{project.one_liner}}` | 一句话定位 | `README.md.tmpl`、`.factory/factory.yaml.tmpl` |
| `{{project.language.docs}}` | 文档语言 | `.factory/factory.yaml.tmpl` |
| `{{project.license}}` | 许可证标识 | `.factory/factory.yaml.tmpl` |
| `{{repo.mode}}` | `mono` / `split` | `README.md.tmpl`、`.factory/factory.yaml.tmpl` |
| `{{repo.default_branch}}` | 主分支名 | `README.md.tmpl`、`.factory/factory.yaml.tmpl` |
| `{{generated:date}}` | 生成日期 | `README.md.tmpl`、`wiki/README.md.tmpl`、`wiki/governance/workflow-profile.md.tmpl` |
| `{{generated:factory_version}}` | factory 版本 | `README.md.tmpl`、`.factory/factory.yaml.tmpl`、`wiki/governance/workflow-profile.md.tmpl` |

## 生成 Markdown 片段与使用位置

| 片段 | 用途 | 出现位置 |
| --- | --- | --- |
| `{{generated:owners_table}}` | 代码 owner 责任表 | `wiki/02-file-authority-map.md.tmpl` |
| `{{generated:security_list}}` | 项目边界/安全条目列表 | `wiki/03-current-decisions.md.tmpl` |
| `{{generated:workflow_profile_owners}}` | 门禁摘要中的 owner 段 | `wiki/governance/workflow-profile.md.tmpl` |
| `{{generated:workflow_profile_commands}}` | 门禁摘要中的命令段 | 同上 |
| `{{generated:workflow_profile_gates}}` | 门禁摘要中的流程门禁段 | 同上 |
| `{{generated:workflow_profile_security}}` | 门禁摘要中的安全段 | 同上 |
| `{{generated:verification_table}}` | 验证设置表（基线证据/证据根/隔离方式） | `wiki/governance/workflow-profile.md.tmpl` |
| `{{generated:packs_table}}` | 启用 packs 表 | 同上 |
| `{{generated:commands_table}}` | 命令表 | 由 owner/feature profile 模板使用（本目录未使用） |
| `{{generated:code_ai_agent_table}}` | Code AI agent profile 表 | 由 `wiki/code-ai/` 使用（本目录未使用） |

片段可能展开为空字符串；模板必须保证空值下仍是合法 Markdown（小节保留标题和一句
说明，不依赖片段提供标点或闭合结构）。

## 文件映射

渲染（`.tmpl`）：

| 模板路径 | 产物路径 |
| --- | --- |
| `README.md.tmpl` | `README.md` |
| `AGENTS.md.tmpl` | `AGENTS.md` |
| `CLAUDE.md.tmpl` | `CLAUDE.md` |
| `.factory/factory.yaml.tmpl` | `.factory/factory.yaml`（**当前引擎不渲染**，见下方缺口） |
| `wiki/README.md.tmpl` | `wiki/README.md` |
| `wiki/00-spec.md.tmpl` | `wiki/00-spec.md` |
| `wiki/01-reading-guide.md.tmpl` | `wiki/01-reading-guide.md` |
| `wiki/02-file-authority-map.md.tmpl` | `wiki/02-file-authority-map.md` |
| `wiki/03-current-decisions.md.tmpl` | `wiki/03-current-decisions.md` |
| `wiki/governance/workflow-profile.md.tmpl` | `wiki/governance/workflow-profile.md` |

按字节复制：

| 模板路径 | 产物路径 |
| --- | --- |
| `.gitignore` | `.gitignore` |
| `.factory/local.example.yaml` | `.factory/local.example.yaml` |
| `.factory/README.md` | `.factory/README.md` |
| `code/README.md` | `code/README.md` |
| `code/.gitkeep` | `code/.gitkeep` |
| `wiki/human/README.md` | `wiki/human/README.md` |
| `wiki/human/system-overview.md` | `wiki/human/system-overview.md` |
| `wiki/product/README.md` | `wiki/product/README.md` |
| `wiki/domain/README.md` | `wiki/domain/README.md` |
| `wiki/architecture/README.md` | `wiki/architecture/README.md` |
| `wiki/implementation/README.md` | `wiki/implementation/README.md` |
| `wiki/features/README.md` | `wiki/features/README.md` |
| `wiki/governance/README.md` | `wiki/governance/README.md` |
| `wiki/governance/init-record.md` | `wiki/governance/init-record.md`（骨架，init 会用真实记录覆盖） |
| `wiki/testing/README.md` | `wiki/testing/README.md` |
| `wiki/validation/README.md` | `wiki/validation/README.md` |
| `wiki/validation/init-baseline.md` | `wiki/validation/init-baseline.md`（骨架，`Status: pending`） |
| `wiki/feature-workspace/README.md` | `wiki/feature-workspace/README.md` |
| `wiki/feature-workspace/registry.yaml` | `wiki/feature-workspace/registry.yaml` |
| `wiki/feature-workspace/migration-candidates.yaml` | `wiki/feature-workspace/migration-candidates.yaml` |
| `wiki/feature-workspace/schema/feature-workspace-schema.md` | 同名 |
| `wiki/quick-workspace/README.md` | `wiki/quick-workspace/README.md` |
| `wiki/quick-workspace/schema/quick-record-schema.md` | 同名 |
| `wiki/quick-workspace/{active,completed,escalated}/.gitkeep` | 同名 |

`templates/workspace/README.md`（本文件）**不参与复制**，见顶部第 2 条。

## 改模板后的验证

1. 在 `%TEMP%` 下用脚本把 `templates/workspace/wiki` 复制到临时目录，替换全部标量
   占位符、把每个 `{{generated:*}}` 替换为空字符串，去掉 `.tmpl` 后缀。
2. 用现有 wiki 校验器跑一遍临时 wiki：必须 `VALID`（warning 允许）。
3. 检查每个渲染后的相对链接目标都存在；`feature-workspace/` 与
   `quick-workspace/` 内部文件不得出现在长期 MOC 的链接中。
4. 新仓库的 root MOC 必须能在 3 跳内到达每一个长期 Markdown 文件。
5. 最强的一步（可选，需要引擎可用）：
   `factory init --work <临时目录> --answers <answers.yaml>` 之后运行
   `factory gate all --work <临时目录>`，必须是 `VALID` / `feature workspace is
   valid`，且 `factory doctor` 为 0 error。

## 与引擎的已知缺口（需要引擎侧或 init 侧决定）

1. `templates/workspace/.factory/factory.yaml.tmpl` 目前在
   `engine/factorylib/render.py` 的 `SKIP_TEMPLATE_FILES` 里：`factory init` 用
   `DEFAULT_CONFIG` + answers 序列化生成 `.factory/factory.yaml`，不使用本模板。本
   文件因此是可读的规格说明。若引擎改为渲染它，必须保持
   `config.validate_config` 的约束：`project.stack` 必须是列表、
   `workflow.scope_gate` 必须是 `{enabled, split_default}` 映射、`owners[].paths`
   非空、`repo.code_path`/`wiki_path` 为仓库内相对路径。
2. `factory init` 会写 `wiki/governance/init-record.md` 和
   `wiki/validation/init-baseline.md`。本模板已提供同名骨架并在目录 MOC 中登记，所以
   生成的仓库不会出现 `ORPHAN_MARKDOWN`；init 覆盖骨架内容后链接依然有效。若引擎以后
   自己补 MOC 链接，会与本模板的两行链接重复（无害，可择一删除）。注意：`init-baseline.md`
   存在时 `_write_baseline` 会跳过写入，基线文档以模板骨架为准。
3. `engine/factorylib/config.py` 的 `DEFAULT_CONFIG` 里
   `verification.evidence_root` 是 `wiki/feature-workspace`，而本模板约定证据根为
   `wiki/validation`；需要在问卷/默认值上对齐，否则 workflow-profile 会展示与
   `validation/README.md` 说法不一致的路径。
4. `packs.enabled` 引擎默认 `["commit"]`，本模板默认 `[]`（不预置工程包）。若引擎
   保持默认，生成仓库的 packs 表会与本模板注释不同——两者都以
   `.factory/factory.yaml` 的实际值为准。

## 不要做的事

- 不要在模板里写死项目名、命令、端口、路径、owner 或验收结论。
- 不要新增未在引擎中注册的占位符名字。
- 不要在 `templates/workspace/wiki/` 里创建 `moc/`、`maps/`、`decisions/`
  `discussions/` 之类的第二套入口目录。
- 不要创建或修改 `templates/workspace/wiki/code-ai/`。
