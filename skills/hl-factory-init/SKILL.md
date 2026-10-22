---
name: hl-factory-init
description: Use when a user wants to create a new HighLand-factory work repo or attach the factory to an existing project. Runs a guided conversation to determine requirements, architecture, verification, security, governance and agent policy, calls the deterministic `factory init`/`factory adopt` engine, and for adopt mode dispatches read-only code-analysis subagents to fill the long-term wiki baseline before declaring init complete. This is the only skill allowed to bootstrap a work repo.
---

# Factory Init

## What this skill is for

Turn a project idea (or an existing code + docs pair) into a **valid HighLand-factory work repo**:

- one git repo, `code/` + `wiki/` two folders (or `split` mode with an external code repo),
- `.factory/factory.yaml` project config + `.factory/local.yaml` machine config,
- a complete wiki authority skeleton, `feature-workspace/`, `quick-workspace/`, `code-ai/`,
- `wiki/governance/workflow-profile.md` digest,
- `AGENTS.md` / `CLAUDE.md` agent entry,
- a green baseline and `factory doctor` PASS.

This skill is the **conversation**. The engine (`factory init` / `factory adopt`) is the **writer**. Never hand-create the skeleton: it drifts from templates and fails the doctor.

## Hard rules

1. Ask one decision at a time. Each question includes: why it matters, 2-3 realistic options, the recommended option first (marked `(Recommended)`), and one sentence of trade-off.
2. Detect before asking. Inspect the existing directory, git remotes, package manifests, CI files, existing docs, and licenses; present the detection as a proposal to confirm.
3. Never silently skip a P0 item. If the user says "decide later", record it as an explicit assumption in `wiki/governance/init-record.md` and tell them the consequence.
4. Never store secrets, tokens, account numbers or private keys in committed files. Only references and policy go into `factory.yaml`.
5. Do not implement product features during init. Init ends at a valid baseline; the first change goes through `$hl-feasibility-grill` or `$hl-quick-change`.
6. Do not create a placeholder Initiative "for the project". The feature workspace starts empty and valid.
7. Every write is planned first. Run `factory init --dry-run` (or `adopt --dry-run`), show the plan summary, and get explicit confirmation before applying.
8. Initial git commit and any push happen only after the doctor passes and only with explicit authorization.
9. For adopt mode, init is not complete until the code-analysis phase has filled the wiki baseline (see `references/adopt-code-analysis.md`). Analysis is read-only for code; only the wiki and `code-ai/project-facts.md` are written.

## Step 0 — locate the factory

1. Find the factory checkout: `factory --version` works if the installer ran; otherwise read `FACTORY_ROOT` from the work repo `.factory/local.yaml` if it exists, or ask the user for the checkout path.
2. Read `<factory>/docs/init-questionnaire.md` — it is the authoritative question bank and definition of done.
3. Run `factory --version` and confirm it satisfies the intended engine range.
4. If `<work>/.factory/factory.yaml` already exists, stop: this repo is initialized. Route to `$hl-factory-doctor` (or ask whether they intend a forced re-init, which requires `--force`).

## Step 1 — choose the mode

Ask which situation applies:

- **New project** — empty directory or a directory with only a README. Use `factory init --mode new`.
- **Adopt existing** — an existing docs/wiki repo plus an existing code repo (possibly two repos). Use `factory adopt --work <docs-repo> --code <code-repo>`. After the skeleton is valid, this mode also runs a read-only code-analysis phase that fills the long-term wiki baseline.
- **Attach** — already initialized; route to `$hl-factory-doctor`.

For adopt, first freeze the current state: record the current branch, commit SHA and a tag name in the init record. Init must not rewrite authoritative docs.

## Step 2 — interview (P0)

Follow the P0 order in `docs/init-questionnaire.md`. For each item, detect → propose → confirm. At minimum:

1. mode; identity (name, slug, one-liner, license, visibility)
2. target users, core scenarios, success signals, explicit non-goals
3. doc / code / commit language
4. repo mode (`mono` vs `split`) and code source
5. wiki source (fresh vs existing docs to import)
6. stack and runtime versions
7. real commands: setup, build, lint, typecheck, test, e2e, dev, verify
8. Python interpreter with PyYAML (for the engine), Node/uv availability
9. services, ports, databases, migrations, env files (if any)
10. architecture: shape, modules, dependency direction, data stores, external systems, deployment, trust boundaries
11. owner map (id, title, owned paths) — one `core` owner is acceptable for small projects
12. security: forbidden operations, sensitive data classes, redaction, secret storage
13. authorization: who approves commit/push/merge/delete/production writes; whether review and verification are independent
14. verification: baseline evidence path, evidence root, isolation policy, reproducibility
15. workflow gates: keep defaults? quick-change? max parallel features? initiative integration?
16. naming: ID prefixes, slug rules, wiki taxonomy
17. git: default branch, commit format, initial commit now?
18. packs: commit / dev-runtime / remote-verify
19. factory version pin and upgrade policy

Do not ask P1/P2 items unless the user chooses the full mode or a P0 answer leaves a real gap.

## Step 3 — write the answers file

Write a temporary YAML file (outside the work repo, e.g. under the system temp dir) shaped like a partial `factory.yaml`:

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
  test: [...]
  verify: [...]
verification:
  isolated_env: local
workflow:
  quick_change: true
security:
  forbidden_operations: [...]
  sensitive_classes: [...]
```

Never put absolute machine paths or secrets in this file.

## Step 4 — plan and confirm

Run the dry-run and summarize:

```bash
factory init  --work <work> --answers <answers.yaml> --dry-run --json
factory adopt --work <docs-repo> --code <code-repo> --answers <answers.yaml> --dry-run --json
```

Show: number of files to create, files that will be skipped because they already exist, and any config warnings. Get explicit confirmation. If the plan looks wrong, fix the answers file — do not edit templates.

## Step 5 — apply

```bash
factory init  --work <work> --answers <answers.yaml>
factory adopt --work <docs-repo> --code <code-repo> --answers <answers.yaml>
```

Then immediately run:

```bash
factory doctor --work <work>
factory gate all --work <work>
```

Repair loop: if a gate fails, fix configuration or the existing docs. Do not weaken the gate, do not hand-edit generated files. If the wiki gate fails because the existing wiki is incomplete, create the missing skeleton files from the factory template shape (the doctor will name the missing paths).

## Step 5b — Adopt code analysis (existing projects only)

Skip this step for greenfield `init`: there is no code to analyze.

For adopt, after apply and a passing doctor/gate:

1. Read `references/adopt-code-analysis.md` completely.
2. Dispatch the analysis slices as **read-only subagents** — `repo-map`, `core-logic`, `data-contracts`, `operations`, `tests`, `security-privacy`, `domain-glossary`. Run them in parallel when the platform supports it. If the platform has no subagent facility, run the slices sequentially in the main session.
3. Each subagent writes only `<work>/.factory/analysis/<slice>.md` and never edits code, wiki or git. If it cannot write files, it returns the fixed handoff and the main session records it.
4. Synthesize the findings into the wiki baseline documents listed in the reference: `architecture/overview.md`, `domain/overview.md`, `implementation/overview.md`, `testing/overview.md`, `governance/runtime-and-operations.md`.
5. In the same pass update `wiki/02-file-authority-map.md`, `wiki/code-ai/project-facts.md`, all affected MOC links, and append the analysis summary to `wiki/governance/init-record.md`.
6. Never invent behaviour: cite relative source paths, mark unknowns, record conflicts between README and code instead of repeating the README. Never write secrets or absolute machine paths.
7. Run `factory gate wiki --work <work>` and `factory doctor --work <work>`; fix links until both pass.
8. Report the documents written and the unknowns that need an owner decision in the handoff.

## Step 6 — green baseline

For every configured command, run it once from the correct directory and record date, environment, command, expected and observed result in `wiki/validation/init-baseline.md`. Change `Status: pending` to `Status: passed` only when every configured build/test/verify command actually passes. If a command cannot run yet (greenfield), record that explicitly as a known gap and keep the status pending — doctor will keep warning.

## Step 7 — git and handoff

1. If the directory is not a git repo: `git init -b <default_branch>`.
2. `git add` and show the staged summary; make the initial commit only after the doctor passes and the user authorizes.
3. Do not push. Print the exact remote/push commands and let the user decide.
4. Produce a Chinese handoff prompt for the next session:

```markdown
工作仓库 <path> 已初始化完成（factory <version>，<mode>，<repo mode>）。

## 已确认
- 项目：<name>（<slug>）
- 代码：<code root>；Wiki：<wiki root>
- Owner：<ids>
- 门禁：<enabled gates>
- 基线：<passed / pending，原因>
- Wiki 基线（仅 adopt）：<analysis docs written>；未决未知：<items>

## 下一步
请先阅读 Wiki 基线文档，然后使用 $hl-feasibility-grill 评估第一个需求，或使用 $hl-quick-change 处理一个边界明确的小改动。
任何实现前先运行 factory doctor --work <path>。
```

## Failure handling

- Config invalid: show the exact engine error and ask for the missing value.
- Template missing: the factory checkout is incomplete; tell the user to `git pull` the factory repo and rerun install.
- Existing files block the plan: report each path; for adopt this is expected. Never force unless the user explicitly says so after seeing the list.
- Gate fails: fail closed, report the gate output verbatim, route repairs to the user.
- Interrupted run: safe to re-run; `factory doctor` reports residual state.
