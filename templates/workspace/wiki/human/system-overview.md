# 系统总览

> 骨架文档：保留小节标题即可用；接入真实项目后逐节替换为事实，不要留下「待补充」
> 之外的模糊描述。

## 一句话定位

用一句话说明系统为谁解决什么问题。

## 做什么

- 核心能力一：。
- 核心能力二：。
- 核心能力三：。

## 不做什么

明确写出被排除的能力，比写能力清单更能约束后续实现。每条边界都要能在
[当前决策](../03-current-decisions.md)或 `governance/` 中找到对应规则。

- 明确不做的事一：。
- 明确不做的事二：。

## 主要组成部分

| 部分 | 职责 | 权威文档 |
| --- | --- | --- |
| 代码根 `code/` | 可执行实现与测试 | `code/` 内各自 README |
| 文档根 `wiki/` | 长期权威文档 | [Wiki 根 MOC](../README.md) |
| 配置面 `.factory/` | 项目身份、命令与门禁 | `governance/workflow-profile.md` |

## 关键约束

- 数据与安全的敏感类别见 `factory.yaml` 的 `security`。
- 流程门禁见[当前决策](../03-current-decisions.md)与
  [Workflow Profile](../governance/workflow-profile.md)。

## 下一步读什么

- 想动手改代码：读[阅读路径](../01-reading-guide.md)中的「Agent / Code AI 实现者」。
- 想改文档：读[Wiki 运行规范](../00-spec.md)。
