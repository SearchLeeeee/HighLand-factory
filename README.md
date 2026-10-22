# HighLand-factory

一套**项目无关**的 AI 辅助研发流程：从需求可行性拷问、Feature 拆解、讨论、实现、独立评审、验收，到长期 Wiki 语义合并，全程有可执行门禁和可追溯状态。

它只做流程，不装项目事实。流程仓库和你的工作仓库分离：

```text
HighLand-factory/          # 本仓库，clone 一次，装到各个 agent
        │
        │  $hl-factory-init 生成 / 接管
        ▼
<你的工作仓库>/            # 一个 git 仓库，两个文件夹
  code/                    # 代码
  wiki/                    # 长期权威文档 + feature-workspace + code-ai
  .factory/               # 项目配置（提交）+ 机器配置（忽略）
```

这就是核心设计：**一个工作仓库，`code/` 与 `wiki/` 两个文件夹；流程仓库不保存任何项目内容；初始化把项目事实写进工作仓库的配置和模板生成物。**

---

## 现在是什么状态

v0.1 已可用，核心链路已跑通：

- [x] 架构与契约：[docs/architecture.md](docs/architecture.md)、[docs/skill-contract.md](docs/skill-contract.md)
- [x] 初始化问卷与 DoD：[docs/init-questionnaire.md](docs/init-questionnaire.md)
- [x] engine：`init / adopt / doctor / upgrade / status / resolve / gate`
- [x] 工作仓库模板（wiki 权威 + code-ai + feature-workspace + quick-workspace）
- [x] 核心 skills（14 个，统一 `hl-` 前缀，避免与其他流程重名）+ 3 个可选 pack（`hl-commit` / `hl-dev-runtime` / `hl-remote-verify`）
- [x] 安装脚本 + CI 守卫（模板冒烟、门禁测试、无项目泄漏）
- [x] 已用一套现有双仓项目的临时副本做 split 模式 adopt 验证（0 门禁错误）

尚未做：GitHub 仓库创建与 push（需要仓库所有者授权）。

---

## 快速开始

前置：Git、Python ≥ 3.10（安装脚本会自举一个带 PyYAML 的 venv，或直接使用 `uv`）。

```bash
# 1. clone 流程仓库
git clone git@github.com:SearchLeeeee/HighLand-factory.git ~/HighLand-factory

# 2. 安装到本机（把 skills 链到 Codex / Claude / DSH 的技能目录，并生成 factory 命令）
cd ~/HighLand-factory
./install/install.sh          # Windows: .\install\install.ps1

# 3. 在目标目录初始化一个工作仓库
mkdir ~/my-project && cd ~/my-project
factory init --work .

# 4. 检查
factory doctor --work .
```

Windows 下路径示例：

```powershell
git clone https://github.com/SearchLeeeee/HighLand-factory.git D:\HighLand-factory
D:\HighLand-factory\install\install.ps1
mkdir D:\my-project
cd D:\my-project
D:\HighLand-factory\bin\factory.cmd init --work .
D:\HighLand-factory\bin\factory.cmd doctor --work .
```

如果你已经用别的工具管理 agent skills（例如 agent-config），用 `-NoSkills` / `--no-skills` 只装引擎，再把 `<factory>/skills` 注册为该工具的 external skill root；需要可选 pack 时加 `-WithPacks` / `--with-packs`。

第 3 步之后，用你惯用的 agent 打开工作仓库，输入 `$hl-factory-init`（对话式初始化）或直接从 `$hl-feasibility-grill` 开始。

---

## 四个核心概念

### 1. 流程仓库（本仓库）

只包含引擎、skills、模板、安装脚本和文档。升级方式是 `git pull` + `factory upgrade`。**不要**把项目文档、项目配置、密钥或领域知识提交到这里；CI 会检查项目泄漏。

### 2. 工作仓库

一个普通 git 仓库，顶层固定两个文件夹：

| 目录 | 内容 |
| --- | --- |
| `code/` | 实现代码。`mono` 模式下与 wiki 同仓；`split` 模式下指向外部代码仓 |
| `wiki/` | 长期权威文档、`feature-workspace/`、`quick-workspace/`、`code-ai/` agent profiles |

`.factory/factory.yaml` 是唯一项目配置真源；`.factory/local.yaml` 存本机路径和运行时，不提交。

### 3. 工作流摘要

`wiki/governance/workflow-profile.md` 由引擎从 `factory.yaml` 生成：语言、布局、owner、真实命令、门禁开关、安全边界。**所有 skill 第一步先读它**，所以 skill 里不需要出现任何项目名、绝对路径或机器 token。

### 4. 可执行门禁

流程不靠散文约束：

- `feature_workspace.py`：唯一生命周期状态机（Feature/Initiative 状态、依赖、Scope Gate、合并门禁、集成证据）
- `validate_llm_wiki.py`：长期 Wiki 唯一内容门禁（唯一入口、≤3 跳可达、链接完整、工作区隔离）
- `trace_feature_history.py`：唯一历史溯源读取器
- 其余 skill 通过 `factory gate ...` 调用它们，散文只解释"何时调用"，不重新定义规则

---

## 初始化：从零项目 vs 现存项目

`init` 与 `adopt` 共用同一个生成器，区别只在**前置条件**和**对已有文件的处理**。

### 从零项目

```bash
factory init --work <新目录> [--answers answers.yaml]
```

- 目录不存在会自动创建；默认 `mono` 模式（`code/` + `wiki/` 同仓）。
- 生成完整骨架（约 57 个文件）：入口 `README.md` / `AGENTS.md` / `CLAUDE.md`、`code/` 种子、wiki 权威骨架、`workflow-profile.md`、`feature-workspace/`、`quick-workspace/`、`code-ai/` profiles、baseline。
- 不生成业务代码；命令为空、baseline 为 pending、未 `git init` 时 `factory doctor` 会给出 warning。
- 目录**不要求为空**：已存在文件同样跳过，只补缺失骨架；混入已有内容时先跑 `--dry-run` 看计划。

### 现存项目（adopt）

```bash
factory adopt --work <docs仓> --code <code仓> [--wiki <wiki目录>] [--answers answers.yaml]
```

- `<work>` 与 `--code` 必须已存在；代码在 work 内 → `mono`，在 work 外 → `split`；wiki 自动探测 `wiki/`、`docs/`，其他目录名必须用 `--wiki` 显式指定。
- **已有文件一律不覆盖**：只补缺失的通用骨架；现有权威文档只追加 MOC 链接和 `.gitignore` 条目，不改写正文；代码仓只读引用，不复制、不移动、不改历史。
- 不迁移旧 Feature ID、旧 wiki 目录结构、旧 skills（v0.1 不做自动迁移）；旧 registry 若不兼容，`factory doctor` 会报错，需要人工处理。
- `--dry-run` 完全只读；不运行 adopt 就不会碰任何现有仓库。
- 已初始化的仓库（已有 `.factory/factory.yaml`）会被拒绝，应改用 `factory doctor` / `$hl-factory-doctor`。

### 建议

- 任何 `init` / `adopt` 都先跑 `--dry-run --json` 看计划，再决定是否落盘。
- 现存项目先打标签（如 `git tag pre-adopt-<date>`），把“机械生成”和“人工修链接/配置”分成两次提交。
- 不要用 `--force` 覆盖已有文件；`--force` 只用于明确的重建。
- 如果只是把 HighLand-factory 当流程参考，**不需要对任何现有仓库运行 init/adopt**：新建一个空目录跑 `factory init` 即可得到一套完整示例工作仓库。
- 初始化后先跑 `factory doctor --strict`，再把 `factory.yaml` 里的 build/test/verify 实跑一遍并更新 baseline。

完整问卷与验收标准见 [初始化问卷与 DoD](docs/init-questionnaire.md)。

---

## 日常循环

```text
$hl-feasibility-grill        需求能否做、要不要做（技术可行性拷问）
  -> $hl-feature-workspace   建 Initiative + 初始 Feature inventory + Scope Gate
  -> $hl-feature-discuss     逐个 Leaf Feature 讨论到结论
  -> $hl-feature-profile-generate   生成可直接投喂的 agent profiles
  -> $hl-feature-orchestrator       实现 -> 独立 review -> 独立 verification
  -> $hl-feature-progress    随时只读查看进度、阻塞、下一步
  -> $hl-initiative-merge    Initiative 全部 ready 后的跨 Feature 集成验收
  -> $hl-wiki-merge          语义合并进长期 Wiki，保留历史，切换权威
```

小 bug / 小调整走 `$hl-quick-change`，超出边界自动升级到上面的重流程。

---

## 升级

工厂仓库更新后，用升级脚本把新版本同步到本机 agent：

```bash
cd <factory>
git pull --ff-only
./install/upgrade.ps1        # Windows；macOS/Linux: ./install/upgrade.sh
```

它会做三件事：

1. 重建/校验 `<factory>/.venv` 与 `bin/factory`；
2. 把 `skills/` 和 `packs/` 重新链接到各 agent 的技能根目录：新增的补上、已删除的清理掉，非 factory 管理的链接不动；
3. 可选刷新已初始化的 work repo：`-Work <path>` 更新其 `local.yaml`，加 `-ApplyWorkUpgrade` 还会应用生成物升级并跑 doctor。

常用参数：

| 参数 | 作用 |
| --- | --- |
| `-Pull` / `--pull` | 先执行 `git pull --ff-only` 再同步 |
| `-Work <path>` / `--work <path>` | 刷新指定 work repo（可多个） |
| `-ApplyWorkUpgrade` / `--apply-work-upgrade` | 对 work repo 执行 `factory upgrade --apply` + doctor |
| `-NoSkills` / `--no-skills` | 只更新引擎，不动 agent 技能根（适合 agent-config 等外部管理器） |
| `-SkillsRoot <path>` / `--skills-root <path>` | 链接到自定义技能根，而不是自动探测的 agent 目录 |
| `-WithPacks` / `--with-packs` | 同时链接可选 packs |

同步后重启 agent 会话，让技能列表重新加载。

### 交给 agent-config 管理时怎么更新

如果 agent 技能根由 [agent-config](https://github.com/SearchLeeeee/agent-config) 统一管理，不要让本仓库的 `install/upgrade` 直接写 agent 目录；把 factory 作为 **external skill root** 注册一次，之后更新只有两步。

**首次注册**（在 agent-config 仓库里，路径按本机实际值）：

```yaml
# sources.yaml
external_skill_roots:
  - id: highland-factory-skills
    root: ${FACTORY_ROOT}
    skills_subdir: skills
  - id: highland-factory-packs
    root: ${FACTORY_ROOT}
    skills_subdir: packs
```

```yaml
# local/machine.yaml（不进 git）
vars:
  FACTORY_ROOT: D:/HighLand-factory
```

然后运行 `tools/sync.ps1`，agent-config 会把 `skills/hl-*` 和 `packs/hl-*` 以 junction 方式挂到各 agent 技能根。

**日常更新**：

```bash
git -C D:/HighLand-factory pull --ff-only
D:/HighLand-factory/install/upgrade.ps1 -NoSkills     # 更新引擎/venv，不动 agent 目录
D:/agent-config/tools/sync.ps1                        # 新增/删除/改名的 skill 需要这一步
D:/agent-config/tools/doctor.ps1                      # 验证 agent 是否能看到
```

说明：

- external root 是原地 junction，**skill 内容更新会立即生效**；只有新增/删除/重命名 skill 时才必须重跑 `sync.ps1`。
- `-NoSkills` 只更新 `<factory>/.venv` 和 `bin/factory`；work repo 的生成物升级仍用 `-Work <path> -ApplyWorkUpgrade`。
- factory skills 不含 `${TOKEN}`，符合 agent-config external root "不渲染、原地读取"的约束。
- 所有技能都带 `hl-` 前缀，与 agent-config 里原有技能不冲突；旧的项目专属技能可以保留给现有项目，也可以之后在 agent-config 里逐步退役。

## 仓库结构

```text
HighLand-factory/
  engine/            # 确定性 CLI（本仓库的"机器门禁入口"）
  skills/            # 流程技能，统一 hl- 前缀，无项目事实
  templates/         # 工作仓库骨架（wiki / code-ai / .factory / code）
  install/           # 安装/升级脚本、生成 factory 命令
  packs/             # 可选能力（hl-commit / hl-dev-runtime / hl-remote-verify）
  docs/              # 架构、技能契约、初始化问卷、定制、升级、FAQ
  examples/          # 最小示例、adopt 现有项目的配置示例
```

## 文档

- [架构与设计决策](docs/architecture.md)
- [技能契约（每个 skill 必须遵守）](docs/skill-contract.md)
- [技能与 pack 目录](docs/skill-catalog.md)
- [初始化问卷与 DoD](docs/init-questionnaire.md)
- [定制与维护](docs/customization.md)
- [升级与漂移处理](docs/upgrade.md)
- [FAQ](docs/faq.md)
- [Adopt 现有双仓项目示例](examples/adopt-existing-project/README.md)

## 与旧流程的关系

HighLand-factory 把一套已跑通的私有流程抽象成通用实现，但不是任何具体项目的复制品：去掉了双仓绑定、机器 token 渲染、领域事实和厂商依赖，改成固定布局 + 项目配置 + 可执行门禁 + 初始化/升级闭环。技能命名与职责见 [docs/skill-contract.md](docs/skill-contract.md#5-skill-naming)。

## License

[MIT](LICENSE)
