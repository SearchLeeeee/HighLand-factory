# Feature 工作区使用手册

## 这套工作区解决什么问题

Feature 工作区管理「尚未进入长期文档」的需求。它重点解决三类问题：

- 原始需求过大，一次只能交付一部分，剩余事项散落在聊天和代码 TODO 里。
- 讨论或实现期间发现新边界，却没有形成可追踪的后续需求。
- 多个需求串行或并行推进，接手者无法快速判断进度和下一步动作。

这里保存的是需求从提出到合并期间的工作状态。功能完成并合并到长期 Wiki 后，长期
Wiki 重新成为唯一权威，本目录的材料降级为非权威历史。

## 权威边界

| 阶段 | 事实权威 |
| --- | --- |
| 需求定义期间 | 长期 Wiki 描述当前系统；本目录描述准备引入的变化。 |
| 验收完成但未合并 | 本目录是「待合并变化」的权威；长期 Wiki 仍是已落地系统的权威。 |
| 合并完成后 | 长期 Wiki 是业务、契约、实现、测试和运维的唯一权威。 |

本目录的任何内容都不能在合并后覆盖长期 Wiki。

## 目录结构

```text
feature-workspace/
  README.md                       # 本文件：使用手册
  registry.yaml                   # 全局登记：Initiative 列表 + feature tombstone
  migration-candidates.yaml       # 历史 deferred 候选项，需人工确认才能升级
  schema/feature-workspace-schema.md
  initiatives/
    initiative-i001-example/
      initiative.yaml             # Initiative manifest（无 README.md）
      features/
        feat-i001-f01-example/
          feature.yaml            # Leaf Feature manifest（含 closure 块）
          feasibility/            # 可选：可行性结论
          discussion/             # 需求讨论结论、测试场景、验收标准
          code-ai/                # 生成的 agent profiles
```

约定：

- 一个 Initiative 目录只有 `initiative.yaml` 和 `features/`，**没有** Initiative
  级的 `README.md`。Initiative 的说明写在 `initiative.yaml` 的字段里。
- 一个 Leaf Feature 目录只有 `feature.yaml` 和按需创建的阶段子目录。
- **闭环信息写在 `feature.yaml` 的 `closure:` 块里，不存在独立的
  `closure-manifest.yaml`。** 任何要求「另外建一个闭环清单文件」的说法都是过期
  约定。
- 目录名同时包含稳定 ID 和英文摘要，例如 `initiative-i001-example`、
  `feat-i001-f02-runner-isolation`。

## 核心概念

### Initiative

Initiative 表示一个完整业务目标，用 `I001`、`I002` 标识。它组织范围、子 Feature、
依赖与整体完成状态，但不直接进入代码实现。

### Leaf Feature

Leaf Feature 是一次可以完整讨论、实现和验收的最小业务闭环，例如 `I001-F02`。只有
Leaf Feature 能生成 Code AI profiles 并交给实现编排。

「完整」不是指实现原始愿景的全部能力，而是指 Feature 声明边界内的正常流程、失败
流程、数据与契约、交互、可观测性、测试和验收都已闭环。闭环必需项不得降级为 MVP、
TODO 或 deferred。

## 编号规则

- Initiative：`I001` 起，全局递增，使用后永不复用；下一个编号记在
  `registry.yaml` 的 `next_initiative_number`。
- Leaf Feature：`I001-F01` 起，在所属 Initiative 内递增，同样永不复用。
- 取消或被替代的需求保留原编号与终态记录，不允许回收编号给新需求。
- 迁移到新 Initiative 的 Feature 保留 `origin_feature_id`，不得改写历史编号。

## 标准工作流

### 1. 需求进入与初始分解

先为完整业务目标创建 Initiative（`initiative.yaml`）。此时**不得**创建一个承载
整个 Initiative 的宽泛 F01 直接进入业务讨论。

在任何详细讨论前必须完成初始分解：

1. 列出覆盖已确认范围的初始 Feature inventory。
2. 为每个候选 Feature 分配稳定 F 编号，登记 `depends_on` 与 `wave`。
3. 对每个候选 Feature 执行 Scope Gate。
4. `must-split` 立即拆分；`split-default` 默认拆分，只有记录结构化
   `indivisibility_reason` 后才能保留。
5. 所有初始活动 Feature 都可作为 Leaf 后，运行
   `feature_workspace.py finalize-decomposition` 封存 inventory。
6. 只有第一个 dependency-ready 的 Leaf 才进入可行性讨论或需求讨论。

### 2. Scope Gate

Scope Gate 先看结构性硬门槛，再算八维复杂度分数。只有 verdict 为 `leaf`，或
`split-default` 且写明不可拆理由，才能进入讨论；`leaf: true` 不能替代 verdict。
评分维度、阈值和硬门槛见 `schema/feature-workspace-schema.md`。

### 3. 讨论需求

一次只讨论一个已登记、通过 Scope Gate 且 dependency-ready 的 Leaf Feature。父
Initiative 的 `initial_decomposition.status` 必须是 `completed`，否则先回到初始
分解。讨论中新发现的范围必须立即归类：

- 当前闭环必需：纳入当前 Feature 并重新评分。
- 前置依赖：创建阻塞 Feature，当前项暂停。
- 相邻增强：创建非阻塞 Feature，当前项继续。
- 新业务目标：创建新的 Initiative。

只写「未来支持某能力」或留 TODO 不算完成拆分。

### 4. 生成实现资料

讨论结论、测试场景和验收标准确认后，才生成领域实现文档和 Code AI profiles。生成
前再次确认：仍是 Leaf、Scope Gate 仍通过、没有未处理的阻塞子项、验收可观察可判定。

### 5. 实现、review、验收

实现编排只接受已完成 profiles 阶段的 Leaf Feature。实现期间发现新的业务需求时，
停止受影响工作并回到范围分类，不得用代码 TODO 代替正式 Feature。

实现完成后依次经过独立 review 和独立验收。只有验收通过并把结论写进
`feature.yaml` 的 `closure:` 块，Feature 才能进入 `ready-to-merge`。

### 6. Initiative 合并屏障

一个 Initiative 的任何 Feature 都不能在其他活跃 Leaf 尚未达到
`ready-to-merge/ready` 时先行合并。所有未取消、未替代的 Leaf 必须先通过验收、
闭环和依赖 gate 并进入 ready；随后才按 `depends_on` 的拓扑顺序逐个合并到长期
Wiki。

合并前先检查 Initiative 级就绪，再产出 Initiative 级集成测试交接；集成测试覆盖
跨 Feature 链路、契约、负向路径和安全边界，证据必须落在 Initiative 目录内。集成
测试未通过时，屏障不放行。实现与验收阶段可以并行，权威切换始终是一个可审计的
收尾批次。

### 7. 合并与保留历史

合并到长期 Wiki 时必须：

1. 确认所有需要长期保存的事实都有明确的长期文档目标。
2. 把 Feature 记为 `merged/completed`，并在父 `initiative.yaml` 与全局
   `registry.yaml` 写入 tombstone 结构的历史路由记录。
3. 重新验证整个 Feature 工作区。
4. 保留完整 Feature 目录及其源文档，不删除、不移动、不截断；允许新增
   `RETAINED_HISTORY.md`、`history-route.yaml` 和 checksum 清单，并从 active
   manifest 的引用与默认发现链中移除。
5. 把保留资料视为历史 provenance：合并后的唯一现行权威是长期 Wiki；新
   Initiative/Feature 不得把它加入 `context_refs`。

tombstone 只用于历史追踪与定位长期文档，不表示源目录被删除。后续需求必须创建新
Feature 并从长期 Wiki 读取基线，不得继续修改或引用已合并资料来定义新事实。

## 顺序与并行

`depends_on` 表示真实依赖，`wave` 表示建议执行批次；编号不随排期变化。

同一 Wave 的 Feature 只有在以下条件同时满足时才能并行：

- 所有依赖已 `completed`，或处于 `ready-to-merge/ready` 且验收通过、闭环完整。
- 不存在阻塞子项。
- owner 责任边界不冲突。
- 允许修改的文件范围不重叠。
- 不会同时修改同一契约。

并行度上限由 `.factory/factory.yaml` 的 `workflow.max_parallel_features` 决定。
被取消或被替代的前置需求不会自动解锁依赖。

## 维护剩余工作

不要用散落的 Markdown TODO 维护剩余工作：

- 新需求：先分配 Initiative 编号，完成初始 inventory、依赖、Wave 和逐项 Scope
  Gate；不得创建宽泛 F01 直接讨论。
- 拆分：分配新 F 编号，记录依赖、Wave 和下一步；`must-split` 必须在讨论前拆完。
- 阻塞：保留原 phase，把 state 改为 `blocked` 并写明 blocker。
- 恢复：移除已解决的 blocker，指定下一步负责的环节。
- 取消：保留编号并记录原因。替代：使用 `superseded` 并记录替代编号。
- 验收：记录通过或失败证据。合并：记录长期文档路径与合并证据。
- 历史 deferred：先写入 `migration-candidates.yaml`，人工确认后才能升级为正式
  需求。

状态只由流程技能在阶段边界更新；人工修正 YAML 后必须运行共享校验，不要手工把
phase 推到后续阶段。

## 隔离规则

- 本目录默认排除在长期搜索、派生索引、Graph、MOC、长期记忆和知识发现之外。
- 长期 Wiki 的 MOC、阅读路径和权威地图不链接本目录内的任何文件。
- 只有明确的 Initiative/Feature 请求、交接或审计请求才能定向读取。
- 本目录中的 I/F 编号、retained 路径和反向历史链接不得写进长期权威文档。
- 需要历史溯源时，另起隔离 session 按 tombstone 定向查找，只把精简结论带回主线。
