---
name: hl-commit
description: "Opt-in pack for git policy: repo-mode aware granular commits, one concern per commit, docs-before-code ordering, no unrelated dirty changes, commit only when the workflow authorizes it, and push only with explicit authorization. Enable with packs.enabled: [commit] and configure repo.* / project.language.commit; core skills work with this pack disabled."
---

# Commit (pack)

## Pack status

This directory is an **optional pack**, not a core skill. Core workflow must run with
`packs.enabled: []`; nothing in `skills/` may require this pack.

- Enable: install or link `<factory>/packs/commit/` into the agent skill root, then add the id
  to the work repo config:

  ```yaml
  packs:
    enabled: [commit]
  ```

  Then run `factory upgrade --work <work>` (regenerates the workflow profile) and
  `factory doctor --work <work>`.
- Disable: remove `commit` from `packs.enabled`, rerun the two commands. No repair is needed;
  the core workflow must still work.
- When enabled, this pack is the only commit path for this work repo. Do not run an ad-hoc
  commit flow beside it.

## When to use

Use this pack when the user asks to commit, stage, or persist changes, or when a workflow
reaches a commit boundary and the change set is ready. Use it for the commit **and** the
optional push, because both carry the same authorization and scope discipline.

Do not use it to inspect history, to review a diff as its primary goal, or to commit work no
workflow authorized. If the pack is disabled, or the repo topology is not `mono`/`split`, stop
instead of improvising a different commit flow.

## Step 0 — mandatory preamble

1. Read `<work>/.factory/local.yaml` and resolve `factory_root` and `python`.
   If missing or unreadable, stop: "machine config missing — run `factory init`
   (or `$hl-factory-init`) for this work repo, then retry." Never guess interpreter paths.
2. Read `<work>/wiki/governance/workflow-profile.md`.
   If missing, stop: "workflow profile missing — run `factory upgrade --apply --work <work>`,
   then `$hl-factory-doctor`; do not hand-write the profile."
3. Confirm the pack is enabled: `packs.enabled` in `<work>/.factory/factory.yaml` contains
   `commit`. If not, stop and give the exact enable snippet plus the two commands above.
4. Resolve the config keys below. Any required key missing, empty or unknown stops the pack
   with a repair instruction. Never substitute a silent default.
5. Run `factory doctor --work <work>`. A failing doctor stops the pack before any `git add`.

## Config contract

| Key | Required | Use |
| --- | --- | --- |
| `repo.mode` | yes | `mono` or `split`; any other value stops the pack |
| `repo.default_branch` | yes | branch that receives the commits |
| `repo.remote` | yes | remote name used for status and push |
| `repo.commit.format` | yes | `conventional` or `plain`; empty/unknown stops the pack |
| `project.language.commit` | yes | commit subject/body language |
| `repo.code_path` | mono | code root inside the work repo |
| `repo.wiki_path` | yes | wiki/authority root inside the work repo |
| `repo.code_external` | split | code repo root, relative to the work repo or absolute |
| `security.forbidden_operations` | no | paths/content classes that must never be staged |

This pack declares no `packs.commit.*` keys: enabling it is the whole switch, and the policy
values live in the core sections above.

Empty-config behaviour (fail closed): no `.factory/factory.yaml`, no `repo` section, or any
required key above absent/empty means the pack cannot run. Stop with:

```text
commit pack cannot run: <key> is missing in .factory/factory.yaml.
Add it, run factory doctor --work <work>, then retry.
```

## Step-by-step flow

### 1. Check authorization

Commit only when the governing workflow or the user authorized committing this change.
Otherwise stop at "changes ready", list them, and hand off. Push required its own explicit
authorization — a commit authorization is not a push authorization.

### 2. Scan every target repo

Run `git -C <repo> status --short -uall` for each repo in the current mode (`mono`: the work
repo; `split`: the wiki repo and the code repo). Read enough diff to attribute each path.
A dirty tree is not evidence that every dirty file belongs to this task.

### 3. Attribute changes

- Map each dirty path to the owner, feature/spec, or quick-change record that authorized it,
  using the owners table in the workflow profile and the authoritative docs.
- Read the candidate records rather than inferring ownership from a filename.
- A path that cannot be attributed to the authorizing change is **unrelated**: exclude it,
  leave it dirty, and report it. Never sweep it in to "clean the tree".
- A spec-only change (documents/profiles, no implementation) is committed as documents; do not
  invent matching code for it.

### 4. Group into one-concern commits

Use the configured format's types where it applies: `docs`, `feat`, `fix`, `chore`,
`refactor`, `test`. Never lump unrelated topics. If the grouping needs five or more commits,
present the grouping and get confirmation before committing.

### 5. Order the commits

1. Constraints/facts/contract documents before implementation.
2. `mono`: docs before code within the same concern. `split`: wiki repo before code repo,
   never combined.
3. Config/cleanup before content inside the same concern.
4. Deletes before adds when restructuring.
5. Independent additions before edits that depend on them.

### 6. Stage selectively

Use explicit paths: `git add <path> ...`. Never `git add -A`, `git add .` or a pathspec wide
enough to catch unrelated files, unless every dirty path belongs to that single commit.
Before each commit verify the staged scope with `git status --short` and
`git diff --cached --stat`.

Never stage generated or local artifacts (build output, dependency caches, logs, local
machine config, secrets, database dumps, editor state) unless the user explicitly asks and the
project tracks them.

### 7. Reconcile totals

Count dirty entries from `git status --short -uall` (`M` + `D` + `??`) before the first
commit, then sum the file counts of the commits created (`git log --shortstat` for exactly
those commits). The numbers must match.

- Shortfall: a dirty file was never committed. Stop, find it, commit or explain it.
- Excess: a file was counted twice. Stop and re-group.
- Phantom modification: `git status` reports `M` but `git diff -- <file>` is empty and the
  index blob hash equals the worktree blob hash. Nothing to commit — leave it alone and
  subtract it from the expected total. Never `git add` it to fix the count.

### 8. Write the message

- `repo.commit.format: conventional` → `<type>(<scope>): <summary>` or `<type>: <summary>`.
- `repo.commit.format: plain` → `<summary>`.
- Language: `project.language.commit`. Stable identifiers, paths and type prefixes stay ASCII.
- Summary imperative, at most 72 characters, no vague words like `updates` or `misc`.
- Body bullets start with `-`, one logical change each, say what changed and why.

### 9. Commit

Run `git commit` only after step 6 and step 7 pass. Do not amend, rebase, force, or rewrite a
shared branch without explicit user authorization. If the sandbox blocks writes to `.git`,
request escalation for that exact git command and say why — do not move the repo.

### 10. Push

Push only with explicit push authorization, only after all intended commits exist, and only
when the repo has no unexpected dirty state. Push to `repo.remote` / `repo.default_branch`.
On a transient network failure retry at most three times with a short backoff; if it still
fails, report that the commits are local and give the exact command. Never place a credential
in a remote URL or on the command line.

### 11. Report

Per repo: commit hash and subject, whether it is now clean, every path still dirty and why,
and which checks already ran (do not rerun expensive checks for the report). In `split` mode
report both commit ids and their correspondence. Match the user's language.

## Failure handling

| Situation | Action |
| --- | --- |
| Config missing / key empty | stop before staging; print the fail-closed message above |
| Doctor fails | stop; route to `$hl-factory-doctor` |
| Unrelated dirty paths | exclude, leave untouched, report by path |
| Total reconciliation mismatch | stop, re-inspect; never report success over a mismatch |
| Stage/commit blocked by sandbox | escalate that one git command with a reason; no workaround commits |
| Hook failure | fix the cause, or report it; `--no-verify` only with explicit authorization |
| Push rejected non-fast-forward | stop; do not force-push; surface the divergence |
| User interrupts | stop; on resume rescan every repo and continue only from the newest request |

## What this pack must never do

- Never commit unrelated dirty changes or "clean up" a tree that spans several concerns.
- Never push without explicit authorization; never force-push or rewrite shared history.
- Never mix wiki-repo and code-repo changes in one commit in `split` mode.
- Never infer ownership from a filename or directory.
- Never stage secrets, credentials, local machine config, or generated runtime artifacts.
- Never invent a repo, branch, remote or commit format when config is empty.
- Never claim a commit covers the tree while the reconciliation totals disagree.
