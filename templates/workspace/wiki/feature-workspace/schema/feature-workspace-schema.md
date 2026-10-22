# Feature 工作区数据与门禁规范

本文件是 `feature-workspace/` 的数据契约：字段含义、编号规则、状态枚举、拆分门槛
和合并条件。它不定义业务事实，业务事实以长期 Wiki 为准。

## 1. 权威边界

YAML manifest 只负责需求生命周期状态，不负责定义长期产品事实。

- 活动期间：Feature 文档描述待实现的变化，长期 Wiki 描述当前系统。
- 合并完成后：长期 Wiki 成为唯一权威。
- tombstone 只保存 ID、终态、来源关系、合并证据和长期文档路径。

任何 manifest 内容都不能在合并后覆盖长期 Wiki。

## 2. 稳定编号

### Initiative ID

格式 `I001`、`I002`。全局递增，使用后永不复用；下一个可用编号记录在
`registry.yaml` 的 `next_initiative_number`。

目录格式：

```text
initiative-i001-example
```

### Feature ID

格式 `I001-F01`、`I001-F02`。F 编号在所属 Initiative 内递增，使用后永不复用。

目录格式：

```text
feat-i001-f02-runner-isolation
```

Feature 被迁移到新 Initiative 时保留 `origin_feature_id`，不得通过重写历史编号
掩盖来源。

## 3. 生命周期字段

### phase

```text
intake
feasibility
scope-gate
discussion
implementation-docs
code-ai-profiles
implementation
review
acceptance
ready-to-merge
merged
```

### state

```text
not-started
in-progress
blocked
ready
completed
cancelled
superseded
```

`phase` 表示流程走到哪里，`state` 表示当前运行状态。Feature 被阻塞时保留原
phase，用 `state: blocked` 加 blocker 说明，不得用 `blocked` 覆盖阶段信息。

非终态 Feature 必须声明下一步：

```yaml
next_action:
  skill: hl-feature-discuss
  instruction: "继续完成该 Leaf Feature 的需求讨论"
```

状态只在技能边界更新，不记录单个问题的问答进度。正常情况每次只前进一个边界；
回退必须另行记录治理原因。

### 3.1 Initiative 初始分解

Initiative 创建后、任何 Leaf 进入 `discussion` 前，必须先建立并封存初始 Feature
inventory：

```yaml
initial_decomposition:
  status: completed
  feature_ids:
    - I001-F01
    - I001-F02
```

约束：

- `feature_ids` 记录封存时全部非终态初始 Leaf，必须非空、唯一且能在 Initiative
  内解析。
- 封存前每个初始 Feature 必须已有稳定 ID、`depends_on`、正整数 `wave` 和有效
  Scope Gate。
- `must-split` 不能进入完成态，必须先拆分并标记 `superseded`。
- `split-default` 默认继续拆分；若保留，Scope Gate 必须包含非空
  `indivisibility_reason`。
- 使用 `feature_workspace.py finalize-decomposition` 写入完成态，不得手工伪造。
- 后续讨论中新建的前置或相邻 Feature 不改写初始 inventory，但其自身仍须通过
  Scope Gate。
- 任何非终态 Feature 处于 `discussion` 或更后阶段时，缺失或无效的
  `initial_decomposition` 都是阻断错误。

## 4. Scope Gate

### 八个评分维度

每项 0 至 3 分：

1. 业务闭环数量。
2. 涉及的实现领域数量。
3. 契约变化范围。
4. 数据模型与迁移复杂度。
5. 外部依赖。
6. 权限、敏感数据或资金风险。
7. 测试与验收矩阵。
8. 关键未知性。

### 阈值

| 总分 | verdict | 处理 |
| --- | --- | --- |
| 0–8 | `leaf` | 可以作为 Leaf Feature 进入讨论。 |
| 9–13 | `split-default` | 默认拆分；保留时必须写非空 `indivisibility_reason`。 |
| 14–24 | `must-split` | 必须在讨论前拆分。 |

`leaf: true` 只是 manifest 声明，不能覆盖 Scope Gate。Feature 进入 `discussion`
及以后阶段时，校验必须重新计算 verdict 并 fail closed：`must-split` 一律拒绝，
`split-default` 缺少不可拆理由时拒绝。

### 结构性硬门槛

命中任意一项即必须拆分，不能用其他低分抵消：

- 同时包含多个可以独立产生价值的业务闭环。
- 同时重定义多个尚未明确的核心契约。
- 把安全边界（权限、机密、资金或生产写操作）与普通产品行为绑在一次实现里。
- 存在一个未验证依赖，失败后会推翻整体方案。
- 无法用一组连贯的端到端验收场景证明完成。

## 5. Initiative 爆炸复核

该复核不是每次 Scope Gate 的固定步骤。首次完成 Feature 拆分后，只有出现以下信号
才触发：

- 多个相互独立的业务目标。
- 多条基本互不依赖的交付路线。
- 超过八个 Leaf Feature。
- 超过四个执行 Wave。
- 后续发生重大范围扩张。

拆分时把原 Initiative 标记 `superseded`，用 `split_into` 指向新的扁平 Initiative
ID。禁止建立多层嵌套编号。

## 6. 讨论中发现新范围

所有新增范围必须归入以下四类之一：

| 分类 | 处理方式 |
| --- | --- |
| 当前闭环必需 | 纳入当前 Feature 并重新评分 |
| 前置依赖 | 创建阻塞 Feature，当前项暂停 |
| 相邻增强 | 创建非阻塞 Feature，当前项继续 |
| 新业务目标 | 创建新的 Initiative |

没有稳定 ID、状态和回链的 TODO 或 deferred 不构成有效交接；需要留档的先写入
`migration-candidates.yaml`。

## 7. 依赖与 Wave

`depends_on` 是真实依赖，`wave` 是排期建议。

依赖项处于 `completed`，或处于 `ready-to-merge/ready` 且验收通过、闭环完整时才算
满足。取消或 `superseded` 不会自动释放依赖，必须更新依赖指向或重新作出业务决策。

同一 Wave 不代表一定可以并行；执行前还要检查 owner、文件范围和共享契约是否冲突，
并遵守 `workflow.max_parallel_features` 上限。

## 8. Manifest 引用

`registry.yaml` 通过相对路径引用 `initiative.yaml`，`initiative.yaml` 继续引用各
个 `feature.yaml`。校验和进度报告必须递归解析这些引用，不能只看 registry 的表面
内容。

引用项的 ID 必须与被引用文件内部 ID 完全一致。路径缺失、ID 不匹配、重复编号、
悬空依赖或依赖环均属阻断错误。

## 9. 闭环与合并条件

闭环信息写在 `feature.yaml` 的 `closure:` 块里；不存在独立的闭环清单文件。

`closure:` 至少包含：

```yaml
closure:
  acceptance_status: passed
  evidence: []
  canonical_docs: []
  retained_source: {}
```

Feature 进入合并前必须满足：

- 是 Leaf Feature。
- phase 为 `ready-to-merge`，state 为 `ready`。
- 验收通过，且 `closure:` 中记录了长期文档目标与验证证据。
- 所有前置依赖已满足：`completed`，或 `ready-to-merge/ready` 且验收/闭环完整。
- Initiative 内所有未取消、未替代的 Leaf 已先进入 `ready-to-merge/ready`。
- Initiative 级集成测试交接已产出，且集成测试通过、证据位于 Initiative 目录内。
- 没有阻塞子项。
- tombstone 目标已在父 `initiative.yaml` 或全局 `registry.yaml` 中登记。

满足后才允许按依赖拓扑逐个合并。合并成功后保留 tombstone，并保留完整的 staged
Feature 目录作为历史、非权威 provenance；保留目录不得继续被 active manifest 引用，
不进入默认发现或报告，也不得成为新行动的 `context_refs`。长期 Wiki 是唯一现行
权威，后续变化必须创建新 Feature。

## 10. 保留历史的读取规则

合并降级时允许在保留目录中新增路由材料，但不得改写原始结论正文：

- `RETAINED_HISTORY.md`：声明非权威、隔离读取与 canonical authority 边界。
- `history-route.yaml`：按语义主题路由到相对源文件、heading 和 canonical 目标。

外部 merged/tombstone 记录必须包含：

```yaml
canonical_docs:
  - implementation/example.md
merge_evidence:
  - integration-testing/evidence/example.md
retained_source:
  path: features/feat-i001-f02-example
  marker: RETAINED_HISTORY.md
  route: history-route.yaml
```

`canonical_docs` 不能指向 `feature-workspace` 历史材料；权威文档不得写入 I/F 编号、
retained 路径或反向历史链接。历史审计必须带着具体问题、由新起的隔离 session
完成 tombstone 定位、route 读取、checksum 校验和窄范围阅读；主线只接收精简结论。

## 11. 历史内容迁移

旧文档中的 MVP、v1、TODO、deferred 或 future extension 不能自动视为正式需求。

先写入 `migration-candidates.yaml`，保留来源文件和原始语义，再由人工分类为
`accepted-feature`、`rejected`、`duplicate` 或 `informational-boundary`。只有
`accepted-feature` 才进入正式 Initiative/Feature 工作区。
