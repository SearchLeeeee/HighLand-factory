---
name: hl-factory-upgrade
description: Use when the factory checkout has been updated (git pull), when factory.doctor reports a version mismatch or generated-file drift, or when the user asks to upgrade the workflow of an existing work repo. Refreshes generated files safely, never overwrites project-owned documents, and finishes with doctor + gates.
---

# Factory Upgrade

## What this skill is for

Keep an existing work repo in sync with a newer HighLand-factory checkout without losing project edits.

Upgrade touches **generated** artifacts only:

- `wiki/governance/workflow-profile.md`
- `wiki/code-ai/_manifests/<owner>.yml`
- initial owner profiles (only if unchanged since generation)
- other files recorded in `.factory/state.json:generated_files`

Project-owned authority documents, discussion records, feature manifests, code and `.factory/factory.yaml` are never rewritten by upgrade.

## Step 0 — Load factory context

1. Read `<work>/.factory/local.yaml`. If missing, stop and route to `$hl-factory-init` (the work repo is not initialized) or ask the user to run `install` again.
2. Resolve `FACTORY_ROOT` (`factory_root`) and `PYTHON` (`python`), and confirm `factory --version` runs with that interpreter.
3. Read `wiki/governance/workflow-profile.md`; if it is missing or unreadable, run `$hl-factory-doctor` first — upgrade on a broken repo cannot distinguish new breakage from old.
4. Run `factory status --work <work>` before planning anything.

Fail closed: missing local config, missing profile, or an already-failing doctor stops the upgrade with one concrete repair instruction.

## Flow

1. Confirm the factory checkout is updated: `factory --version`, and check `git -C <factory> log -1`.
2. Read the current work repo state:

```bash
factory status --work <work>
factory upgrade --work <work> --check --json
```

3. Explain the classification to the user:
   - `create`: new generated file from a newer template
   - `overwrite`: generated file unchanged since last generation; safe to refresh
   - `skip` with "locally modified": the project edited a generated file; upgrade will not touch it — decide whether to keep the edit or revert it
4. Confirm `factory.version` in `.factory/factory.yaml` allows the new engine. If not, ask the user to choose: pin back, or update the range and accept the upgrade.
5. Apply:

```bash
factory upgrade --work <work> --apply
factory doctor --work <work> --strict
factory gate all --work <work>
```

6. If a locally modified generated file matters (for example an owner profile the project customized), record the decision: keep the local edit and mark the file as project-owned, or move the customization into `factory.yaml` and regenerate.

## Rules

- Never run upgrade with `--force` to blow through a locally modified file. `--force` is an init-time recovery flag, not an upgrade strategy.
- Never hand-edit `.factory/state.json`.
- Never upgrade a work repo whose doctor is already failing for unrelated reasons; fix those first, otherwise you cannot tell new breakage from old.
- If the new template set requires a config key that does not exist, the doctor will report it; add the key through `$hl-workflow-governance` (or by editing `factory.yaml` with the user) and rerun upgrade.
- Preserve unrelated dirty git changes; upgrade must not commit.

## Handoff

Report: old version → new version, files refreshed, files skipped because locally modified, doctor result, gate result, and any follow-up decisions. Match the user's language.
