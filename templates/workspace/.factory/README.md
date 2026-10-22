# `.factory/` 说明

本目录是工作仓库的机器可读控制面，只放三类文件。三者职责不同，不要混用。

## `factory.yaml` —— 唯一事实源

- 项目身份、语言、owner、命令、验证、流程门禁、安全边界和 agent 配置的唯一
  事实源。
- 由 `factory init` 生成，由 `factory upgrade` 升级；手工修改后必须重新运行
  `factory upgrade`。
- `wiki/governance/workflow-profile.md` 是它的渲染产物：只读、由工具生成，
  不允许手工编辑。两者必须同一次变更一起提交。

## `local.yaml` —— 机器级覆盖

- 只承载「这台机器」的差异：`factory_root`、Python/Node 解释器、端口、私有
  环境变量。
- 真实仓库中该文件被 `.gitignore` 忽略，永远不提交；新机器从
  `local.example.yaml` 复制。
- 冲突时以 `factory.yaml` 为准。`local.yaml` 只能覆盖路径与运行时选择，
  不能改变门禁、owner、安全边界或项目身份。

## `state.json` —— 工具运行状态

- 由工具写入的缓存与进度状态（上次运行时间、迁移标记等），可重建。
- 被 `.gitignore` 忽略，不属于文档权威，不参与 review。

## 读取顺序（对人和 agent 都适用）

1. `.factory/local.yaml`：确认本机路径与解释器（不存在时用
   `local.example.yaml` 的默认值并提示用户创建）。
2. `wiki/governance/workflow-profile.md`：确认当前 owner、命令、验证要求、
   门禁、安全边界和启用中的 packs。
3. 需要精确字段时再回到 `.factory/factory.yaml`。

所有 factory skills 都按这个顺序启动，不允许跳过第 1、2 步直接改代码或改
长期文档。

## 修改规则

- 改门禁、安全边界、owner 或命令：先改 `factory.yaml`，运行 `factory upgrade`，
  再同步 `wiki/governance/` 下的解释性文档。
- 只改本机路径或端口：改 `local.yaml`，不要提交。
- 不要在本目录写项目业务事实、验收结论或设计说明；这些属于 `wiki/`。
- 不要手工创建 `state.json`，也不要把它当作输入。
