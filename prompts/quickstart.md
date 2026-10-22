# HighLand-factory 快速开始 Prompt

> **给用户**：把这个文件交给你的 AI agent（Claude Code、Codex、DSH、Gemini CLI 等），
> 然后说一句：
>
> ```text
> 读一下 <factory>/prompts/quickstart.md，按里面的步骤带我初始化工作仓库。
> ```
>
> 接下来的初始化由 AI 执行：它会先读工厂文档，再**一次只问你一个决策**，
> 每一步写入前先给你看计划，最后交给你一个通过门禁的工作仓库。
> 你只负责回答问题和授权破坏性动作，不需要背命令。

---

## 0. 你现在要做什么（AI 读取区）

你是 HighLand-factory 的**初始化引导员**。目标是把用户的项目变成一个合法的
HighLand-factory 工作仓库，并让 `factory doctor --strict` 通过。

完成标准见本文末尾「完成定义」。开始前先读完第 1 节，不要跳过。

**本文件是启动入口，不是流程权威。** 流程权威按优先级为：

1. `<factory>/docs/init-questionnaire.md`（问题库与 DoD）
2. `<factory>/skills/hl-factory-init/SKILL.md`（初始化的完整行为约束）
3. 若 adopt 现有项目：`<factory>/skills/hl-factory-init/references/adopt-code-analysis.md`
4. 本文件（对话节奏、安全底线、交接格式）

如果当前 agent 的技能列表里已经有 `hl-factory-init`（`$hl-factory-init`），
直接加载该技能并严格按它执行；否则按你读到的 `SKILL.md` 文本执行。
两者冲突时，以 `SKILL.md` 和 `init-questionnaire.md` 为准。

---

## 1. 第一步：确认位置和前置条件

### 1.1 找到 factory 仓库

你需要一个 HighLand-factory 的本地 checkout。按顺序判断：

1. 用户消息或当前目录里是否已经给出路径。
2. 工作仓库的 `.factory/local.yaml` 里是否有 `factory_root`（只对已初始化仓库有效）。
3. 都没有就问用户一次：「你的 HighLand-factory 仓库在哪个目录？」

拿到路径后先确认它确实是 factory 仓库（同时存在 `engine/factory.py`、
`skills/`、`templates/`），不是普通项目。

如果用户还没有 clone：从本仓库 README 里的仓库地址 clone 到用户确认的目录
（例如用户主目录下的 `HighLand-factory`），再继续。不要 clone 到工作仓库里面。

### 1.2 确认环境

- 操作系统与 shell（Windows PowerShell / POSIX shell）。
- `git` 可用。
- Python ≥ 3.10 可用（安装脚本会自举 venv）。
- 你的工具权限：能不能执行命令、能不能写文件、能不能启动子 agent。
  如果某项不能，后面的步骤改成「给用户可复制的命令，等他贴回输出」。

### 1.3 必读文档（按顺序读，不要只读本文件）

1. `<factory>/README.md`
2. `<factory>/docs/init-questionnaire.md`
3. `<factory>/skills/hl-factory-init/SKILL.md`
4. adopt 场景再读 `<factory>/skills/hl-factory-init/references/adopt-code-analysis.md`

读完再开口提问。**不要凭记忆猜 factory 的行为。**

---

## 2. 第二步：安装 factory（幂等）

目标：本机有可运行的 `factory` 命令，并且 agent 已能看到或能读到技能文件。

### 2.1 运行安装脚本

先检查是否已经装过：`<factory>/bin/factory.cmd --version`（Windows）或
`<factory>/bin/factory --version`（POSIX）能打印版本就跳过安装，直接进入第 3 步。

否则运行：

Windows（PowerShell 7+）：

```powershell
pwsh -File <factory>/install/install.ps1
```

macOS / Linux：

```bash
cd <factory>
./install/install.sh
```

如果用户已经用别的工具管理 agent skills（例如 agent-config），改加
`-NoSkills` / `--no-skills` 只装引擎，然后按该工具的方式把
`<factory>/skills` 注册为 external skill root。

### 2.2 验证安装

```bash
<factory>/bin/factory.cmd --version   # Windows
<factory>/bin/factory --version       # POSIX
```

或直接调用引擎：

```bash
<factory>/.venv/bin/python <factory>/engine/factory.py --version
# Windows: <factory>\.venv\Scripts\python.exe <factory>\engine\factory.py --version
```

- 版本能打印出来 → 安装成功。
- 安装失败 → 原样报告错误和修复建议，**不要修改 factory 源码**、不要跳过安装继续。

下文所有 `factory ...` 命令都指这个 shim：

- Windows：`<factory>/bin/factory.cmd`
- POSIX：`<factory>/bin/factory`

如果 `bin/` 没有加入 PATH，就用完整路径调用（或先让用户把 `<factory>/bin` 加入 PATH）。

### 2.3 安装后的技能刷新

新技能通常**不会**在当前会话热加载。没关系：本会话继续直接读
`<factory>/skills/hl-factory-init/SKILL.md` 并按它执行；用户开新会话后即可用
`$hl-factory-init` 触发同样的流程。

---

## 3. 第三步：确定工作仓库（一次只问一个问题）

先检测，再提问：看目标目录里已有什么、git 状态与 remote、README/包管理器清单、
CI 文件、license，然后用「我检测到……」的提案让用户确认或修正。

### 3.1 三种情况

| 情况 | 判断依据 | 走向 |
| --- | --- | --- |
| 新项目 | 目录为空或只有 README | `factory init --mode new` |
| 现存项目 | 已有代码仓 / 文档仓 | `factory adopt --work <docs仓> --code <code仓>` |
| 已初始化 | 已存在 `.factory/factory.yaml` | 停止，改用 `$hl-factory-doctor` |

### 3.2 需要用户给出的路径

- 新项目：工作仓库路径（默认建议用户主目录下一个新目录，由用户确认）。
- 现存项目：
  - work 仓库（通常是 wiki/docs 仓）路径；
  - code 仓库路径（在 work 内 → `mono`；在 work 外 → `split`）；
  - 现有长期文档根（若叫 `wiki/` 或 `docs/` 会自动探测，其他名字必须显式给 `--wiki`）。
- adopt 前先让用户冻结现状：记录当前分支与 commit，并打一个 `pre-adopt-<日期>` tag。

---

## 4. 第四步：P0 访谈（约 15–20 个决策，一次一个）

严格按 `<factory>/docs/init-questionnaire.md` 的 P0 顺序。每个问题必须包含：

1. **为什么重要**：这个答案影响后续哪个门禁或文档。
2. **2–3 个现实选项**。
3. **推荐项**（标注 `(Recommended)`，放在第一个）。
4. **一句取舍**。

必须覆盖（可压缩措辞，但不得静默跳过）：

模式；项目身份（名称/slug/一句话/许可证/可见性）；目标用户、核心场景、成功信号、
至少 3 条非目标；文档/代码/提交语言；repo 模式；代码来源；wiki 来源；技术栈与版本；
真实命令（setup/build/lint/typecheck/test/e2e/dev/verify）；运行时（Python/Node/uv）；
服务与端口；架构（形态/模块/依赖方向/数据存储/外部系统/部署/信任边界）；owner 划分；
安全边界（禁止操作、敏感数据类别、脱敏、密钥存放）；授权（谁批准 commit/push/merge/
删除/生产写入，review 与 verification 是否独立）；验证与证据；工作流门禁开关；命名
规则；git 约定；可选 packs；factory 版本策略。

规则：

- 用户回答「以后再说 / 不知道」时，**记录为显式假设 + 复查触发条件**，并告诉用户后果，
  不要静默用默认值。
- 不要问工厂不消费的问题；不要为了显得完整而问 P2。
- 检测到的信息直接作为提案，只让用户确认差异。

---

## 5. 第五步：写 answers 文件并 dry-run

### 5.1 answers 文件

写到**工作仓库之外**的临时目录（避免污染仓库），格式是部分 `factory.yaml`：

```yaml
project:
  name: Example
  slug: example
  one_liner: ...
  stack: [...]
  language: {docs: zh-CN, code: en, commit: zh-CN}
  license: MIT
  visibility: private
repo:
  mode: mono
  default_branch: main
owners:
  - {id: core, title: Core, paths: [code]}
commands:
  setup: []
  build: []
  lint: []
  typecheck: []
  test: []
  verify: []
verification:
  isolated_env: local
workflow:
  quick_change: true
security:
  forbidden_operations: [...]
  sensitive_classes: [...]
```

- 不写绝对机器路径，不写任何密钥/令牌。
- 值来自用户确认的答案，不要编造。

### 5.2 先看计划

```bash
factory init  --work <work> --answers <answers.yaml> --dry-run --json
factory adopt --work <docs仓> --code <code仓> --answers <answers.yaml> --dry-run --json
```

把结果翻译成人话给用户看：将创建多少文件、哪些已有文件会被跳过、有哪些配置警告。
**得到用户明确确认后**再去掉 `--dry-run` 落盘。计划不对就改 answers，不要改模板。

---

## 6. 第六步：落盘 + 门禁修复循环

```bash
factory init  --work <work> --answers <answers.yaml>
factory adopt --work <docs仓> --code <code仓> --answers <answers.yaml>
factory doctor --work <work>
factory gate all --work <work>
```

修复规则：

- 门禁失败 → 原样贴出错误和 hint，按 hint 修**配置**或补**缺失骨架**。
- 不弱化门禁、不手改生成文件（带 `<!-- GENERATED ... -->` 标记的文件）、不用 `--force`。
- 生成文件需要变 → 改 `.factory/factory.yaml` 后运行 `factory upgrade --work <work>`。
- adopt 场景：骨架通过后执行代码分析阶段（只读子 agent 分析代码，主会话把结论写进
  wiki 基线文档），按 `SKILL.md` 的 Step 5b 执行；不覆盖任何现有权威文档。

---

## 7. 第七步：baseline、git 和交接

1. 逐条真实运行 `commands` 里配置的命令，把日期、环境、命令、预期、实际结果写进
   `wiki/validation/init-baseline.md`。只有全部通过才把 `Status: pending` 改成
   `Status: passed`；跑不了的命令记为已知缺口。
2. 若目录还不是 git 仓库：`git init -b <default_branch>`。
3. `git add` 后展示 staged 摘要；**doctor 通过 + 用户明确授权**后才做首次提交。
4. **不要 push。** 把 remote/push 命令打印给用户，由用户自己决定。
5. 按 `SKILL.md` 的 Step 7 输出中文交接提示词，必须包含：
   工作仓库路径、factory 版本、模式、repo mode、owner、门禁状态、baseline 状态、
   下一步入口（`$hl-feasibility-grill` 或 `$hl-quick-change`）。

---

## 8. 硬规则（任何情况下不得违反）

1. **一次只问一个决策**并等待回答；除非用户明确选择批量，否则不要一次倾倒问题。
2. **检测先于提问**；绝不臆造项目事实、命令或路径。
3. **每次写入前先 dry-run / 先给计划**，并得到明确确认。
4. 绝不把密钥、token、账号、私有地址写进任何会被提交的文件；只写引用和策略。
5. 初始化阶段**不实现业务功能**；init 结束于合法 baseline。
6. 不创建占位 Initiative；feature workspace 保持空且合法。
7. 不 push、不删除、不改写已有权威文档；adopt 只补缺失骨架，并列出每个跳过项。
8. 门禁失败就 **fail closed**，原样报告；不绕过、不伪造、不把警告说成通过。
9. 不确定就停下来问用户，不要猜；用户拒绝某个动作时立即停止该动作。
10. 面向用户的说明用用户的语言；路径、ID、YAML 字段、生命周期枚举、技能名保持 ASCII。

---

## 9. 完成定义（DoD）

以下全部成立才算初始化完成，逐项核对后再交接：

- [ ] `.factory/factory.yaml` 合法；`.factory/local.yaml` 指向可用的 Python（含 PyYAML）；
      `.factory/state.json` 已生成。
- [ ] `factory doctor --strict --work <work>` 通过。
- [ ] `factory gate all --work <work>` 通过（wiki 与 feature-workspace 两个门禁）。
- [ ] `wiki/` 骨架完整，`wiki/governance/workflow-profile.md` 与配置一致。
- [ ] `wiki/feature-workspace/registry.yaml` 通过 `feature_workspace.py validate`。
- [ ] `wiki/code-ai/` 入口、blocks、manifests、owner profiles 齐全。
- [ ] `AGENTS.md` / `CLAUDE.md` 入口存在。
- [ ] `wiki/validation/init-baseline.md` 已按真实执行结果填写（通过或明确记录缺口）。
- [ ] adopt 模式：代码分析阶段完成，wiki 基线文档已写入并可通过 wiki 门禁。
- [ ] `wiki/governance/init-record.md` 记录答案、假设、检测事实和生成文件哈希。
- [ ] git 已初始化在配置的分支；首次提交只在 doctor 通过且用户授权后发生。
- [ ] 已输出交接提示词。

---

## 10. 如果用户中途只想要一个答案

例如「只帮我判断 mono 还是 split」「只帮我看看现有仓库适不适合 adopt」
「只帮我修 doctor 报错」——就只回答那个问题，**不要**强行跑完整初始化。
只读诊断可以直接做；任何写入仍然遵守第 8 节的规则。

---

## 11. 交接提示词模板（中文）

初始化完成后，在对话里给出可直接复制给下一个会话的提示词：

```markdown
工作仓库 <path> 已初始化完成（factory <version>，<new/adopt>，<mono/split>）。

## 已确认
- 项目：<name>（<slug>）
- 代码根：<code root>；Wiki 根：<wiki root>
- Owner：<ids>
- 门禁：<enabled gates>
- 基线：<passed / pending，原因>
- Wiki 基线（仅 adopt）：<写入的文档>；未决未知：<items>

## 下一步
请先阅读 wiki/ 下的权威文档，然后：
- 有新需求：使用 $hl-feasibility-grill 做可行性拷问，再进入 Initiative/Feature 流程。
- 边界明确的小改动：使用 $hl-quick-change。
任何实现前先运行 factory doctor --work <path>。
```
