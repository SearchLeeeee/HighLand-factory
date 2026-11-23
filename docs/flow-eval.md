# 跨 agent 流程录制与复盘

一次任务使用一个流程编号。讨论可以在 Claude 中完成，实现交给 Codex，CI 或另一个 agent 可以接手验收。它们通过同一个工厂 CLI 写入流程记录。角色名用于阅读，步骤和交接通过本流程内的事件号关联。录制从显式启动后开始。

**每条独立流程默认关闭 debug，包括快速流程。** 在启动任务时直接说“修复 A，这条流程开 debug”，agent 才为 A 建立录制。开场省略 debug 时，整条流程走普通入口，不创建录制目录，也不用回答是否开启。开始后的普通讨论、旧提示里出现的编号以及同目录下已有的录制库，都不触发开启。

同一流程换 agent、切换阶段或派发子任务时，接手方沿用同一编号和记录根。有交接提示时直接携带两项信息。新会话直接继续已登记的 Initiative 或 Feature 时，可以从工作仓查回。流程最终结束时由协调 agent 封存。比如 A 完成后，你在同一个聊天里说“再修复 B”，B 默认关闭。如果也要录 B，在 B 的开场明确说明，工厂会使用新的流程编号。

### 新会话直接继续一个 Feature

在开场给整个 Initiative 开 debug 时，agent 将录制与正式 Initiative ID 关联。只给单个 Feature 开启时，关联它的完整 ID。此后你可以直接说“继续 F02 的讨论”。进度查询和直接进入讨论的入口都会先用登记册定位目标；若多个 Initiative 都有适用的 F02，只需确定要继续哪个 Initiative。

```text
factory debug flow start --work WORK --flow change-17 --scope I005
factory debug flow lookup --work WORK --scope I005-F02
```

第二条命令是 agent 的只读查询。若 `change-17` 尚在录制，返回流程编号、命中的授权范围和记录根，即使当初使用了自定义 `--records`。同一登记册中，只给 `I005-F01` 授权时，查询 F02 返回 `flow: null`。整项 Initiative 的录制在 Initiative 流程结束时封存，F01 交付后可以继续记 F02。

可行性讨论开场时若尚无正式 ID，agent 用 `start --pending-scope initiative` 或 `feature` 先记录已授权的范围类型，得到正式 ID 后用 `bind --flow change-17 --scope I005` 补上关联。开场时未声明范围的旧录制仍可通过其交接提示继续。查询使用权威工作根下的本地索引 `.factory/analysis/flow-scopes.sqlite3`，按登记册和完整 ID 匹配，并检查录制仍存在且未封存。首次只读查询不会创建索引。

### 启动与交接

在工作仓根目录运行下列命令。后续命令省略 `--work` 时使用当前目录；从子目录、独立 worktree 或其他客户端调用时，传交接中约定的 `--work WORK_ROOT`。默认记录位置为 `WORK_ROOT/.factory/analysis/flows/change-17/`，初始化工作仓已忽略这个机器状态目录。若不同 checkout 要共用本次复盘，可让各端传入指向同一可读写记录根的 `--records RECORDS`，并用各自的 `--work` 定位产出。记录目录含 SQLite 账本和原始产出，使用者需要相应的文件权限。存储需要支持 SQLite 文件锁。封存后可把整个流程目录复制给复盘者。

```text
factory debug flow start --flow change-17
factory debug flow begin --flow change-17 --phase discussion --agent product-owner --label "确认验收条件"
```

`begin` 返回 `step`。在阶段内用 `note` 记录会影响后续判断的决策、阻塞、重试、交付或交接。选定文件可用重复的 `--artifact` 参数在当时留存，包括二进制文件。下例假定第一步事件号为 1，请使用实际返回值。

```text
factory debug flow note --flow change-17 --phase discussion --agent product-owner --kind decision --parent 1 --message "确定空输入的验收条件" --artifact docs/acceptance.md
factory debug flow end --flow change-17 --step 1 --outcome completed
factory debug flow note --flow change-17 --phase discussion --agent product-owner --kind handoff --to-phase implementation --message "交给实现，沿用已确认的验收条件" --artifact docs/acceptance.md
```

`start` 和 `note --kind handoff` 返回可放进任务提示词的 `handoff` 文本，包含流程编号、目的阶段、工作根和记录根。派工和交接还带上游事件号，接手方用 `--parent` 关联它，并用自己的角色记录。没有下游动作的交接仍留在时间线上。录制不需要客户端 hooks、会话链接或厂商会话 ID。

### 采集实际执行

用 `run` 包住原有测试、门禁、构建或验证命令。它按当前目录和参数运行原程序，转发标准输出、错误输出和退出码，同时分别保留两个输出流及单调时钟测得的命令耗时。下例假定交接事件号为 4。

```text
factory debug flow run --flow change-17 --phase verification --agent verifier --parent 4 --label "回归验证" --artifact results.xml -- python -m pytest --junitxml=results.xml
```

`--` 后填写可执行程序与参数；需要 shell 语法时显式调用对应 shell。交互式工具、人工等待和跨 agent 工作可用 `begin/end` 记录边界，完成者可用 `--agent` 填自己的角色。两个边界之间的墙钟时间可能包含人工等待和并行工作。有可靠用量数据时，在 `end` 传入 `--tokens`。失败、缺失产出和未结束步骤都保留，记录材料应限于允许写入该目录的命令、输出与文件。

### 复盘

协调 agent 在整条流程完成或取消时封存，阶段交接和暂时等待仍属于当前流程。运行中也可以随时读取报告。

```text
factory debug flow seal --flow change-17
factory debug flow report --flow change-17
factory debug flow report --flow change-17 --event 4
factory debug flow report --flow change-17 --events
```

摘要按阶段列出角色、耗时最长的步骤、阻塞与失败、最长观察空档、交接和产出版本。按事件号查看原命令或 agent 的记录。命令输出保存在 `events/<开始事件号>/stdout.log` 和 `stderr.log`，交付文件保存在 `events/<登记或结束事件号>/artifacts/<原相对路径>`。报告里的 `object` 是相对于 `record_dir` 的文件路径，可直接打开。复盘结束后可以删除这一条流程的整个记录目录；业务工作区中的原件仍在原位。

并发步骤可能重叠，事件空档的原因需用两端记录核实。对于通过其他工具完成、也未写事件的动作，报告无法复原。若需要以未完成状态封存，`seal --incomplete` 保留这些步骤供事后检查。

给新 agent 的复盘提示可以直接写：“使用 `$hl-flow-eval` 复盘工作根 WORK 的 change-17。找到首次失败，比较交付和修复的产出，指出耗时最长的实测命令和仍缺证据的环节，并引用事件号。” [复盘 skill](../skills/hl-flow-eval/SKILL.md)

## Experimental stage recording

Recording is opt-in. Each experimental group gets one private directory for its ledger, outside the execution repos. Use a common operator-owned switch directory across groups. The trusted hook host needs write access to its ledger and switch read access. Grant evaluators read access to their own group. Use host filesystem isolation so execution sessions cannot read the ledger, other groups, grader materials, future Git objects or another thread's transcripts. Separate Git clones alone grant no filesystem isolation. Verify those boundaries with synthetic canaries on the selected agent surface before enrolling an experiment.

## Operator setup

Run `factory` from the pinned checkout, using the project's configured Python. Choose a different exact first line per stage in the same work directory. Both groups may use identical opening lines in separate workspaces.

```text
factory debug arm --work WORK --group-dir GROUP --stage STAGE --marker "OPENING LINE"
factory debug hook-config --group-dir GROUP --switch SWITCH
factory debug on --switch SWITCH
```

Install the emitted JSON in the trusted runtime hook configuration for the enrolled workspace. Review the generated hook commands through the runtime's normal hook-trust flow. Preserve existing hooks when installing in an existing profile. Select the corresponding stage by placing its exact opening line at the beginning of a fresh session's first prompt. A stage binds once. Agents that have not enrolled continue normally. The switch defaults off and a new switch epoch never resumes a prior enrollment.

Use synthetic or approved inputs whose visible messages and tool results are permitted in the private ledger. The process records tool arguments and output verbatim. Keep credentials and production data outside the enrolled workload. A trusted host writes the SQLite ledger even where the model's tool sandbox cannot read it. Model-visible tool events and hook tool payloads are separately identified. Opaque binary/media outputs and unavailable fields should be assessed only to the extent actually observed.

## Handoff and grading

Preserve each stage's first delivery, Git revisions and any uncommitted changes at handoff, before repair; record assistance and product decisions independently. A failed handoff can be evaluated with no downstream session. After the session ends and the runtime has flushed its transcript, seal the named stage and disable the switch when all intended stages are complete.

```text
factory debug seal --group-dir GROUP --switch SWITCH --stage STAGE
factory debug off --switch SWITCH
factory debug report --group-dir GROUP --stage STAGE --events
factory debug content --group-dir GROUP --sha256 DIGEST
```

Sealing reads any remaining timestamped rows from the already identified transcript, including late usage. Sealed stages ignore future hooks. Exact content references resolve inside the same group. The recorder accepts visible assistant messages, tool calls and returned results, and runtime token counts. It skips private reasoning and system/developer messages. Recorded event span is an observation window. Report known usage and actors without counts; a missing runtime field is unknown, and a truncated tool return supplies only the visible part. Capturing a path or tool call alone does not establish that an agent saw a specific rule. The grader independently runs the real entry point and captures stdout, stderr and exit status separately when the recording contains a combined stream.
