# Validation

本目录是验证记录与证据索引的长期权威：哪次变更、用什么环境、跑了什么、结论如何。

## 文档

- [初始化基线证据](init-baseline.md)：首次跑通各条命令的基线记录，后续回归的比较
  基准。
- 初始阶段不预置其他子文档。新文档随项目推进逐步加入，每个条目一行：「链接 + 一句
  角色说明」。
- 每条验证记录至少包含：变更标识、环境、命令、可复现步骤、原始证据位置、结论。
- 证据目录由 `.factory/factory.yaml` 的 `verification.evidence_root` 指定；实际路径以
  配置和 [Workflow Profile](../governance/workflow-profile.md) 为准，不要假定本目录。
- 结论要可判定（通过/失败/不适用），禁止只写「已验证」。

冲突裁决见[文件权威地图](../02-file-authority-map.md)；导航入口见[Wiki 根 MOC](../README.md)。
