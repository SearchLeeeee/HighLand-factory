---
name: hl-feature-progress
description: Use when the user asks for feature progress, remaining work, blockers, parallelizable work, next actions, stale work, merge readiness, workspace maintenance instructions, or a copyable next-session prompt. Strictly read-only.
---

# Feature Progress

Remain strictly read-only. Do not create, edit, transition, repair or delete workspace files. Work
correctly in a fresh session without relying on chat history.

## Step 0 — Load factory context

1. Read `<work>/.factory/local.yaml`. If missing or unreadable, stop and tell the user to run
   `$hl-factory-init` (or `factory init`); never guess a path or interpreter.
2. Resolve `FACTORY_ROOT` (`factory_root`), `PYTHON` (`python`), and `WORK_ROOT` (the git
   top-level, or the directory containing `.factory/`).
3. Read `wiki/governance/workflow-profile.md` under `WORK_ROOT`. It defines language, layout,
   owners, commands, the evidence root, gate switches and security boundaries. If it is missing or
   unreadable, stop and tell the user to run `$hl-factory-doctor`.
4. Run gates through the engine rather than composing paths: `factory gate workspace --work
   <WORK_ROOT>`.
5. Take the docs language, feature-workspace root, parallel-feature cap and gate switches from the
   profile. Never assume them.
6. If the profile or config contradicts the manifests, report the contradiction instead of
   improvising a repair; repairs route to `$hl-workflow-governance` or `$hl-feature-workspace`.

A report may read state; it may never change it. A failing gate is reported verbatim, not worked
around.

## Reporting Procedure

1. Resolve the default registry at `wiki/feature-workspace/registry.yaml`, unless the user supplies
   another feature-workspace path.
2. Read the workspace `README.md`, the registry, referenced Initiative manifests, referenced active
   Feature manifests, and `migration-candidates.yaml`.
3. Follow every formal `context_refs` entry declared by the target Initiative or Feature. Resolve
   each path relative to the manifest that declares it. Treat `required: true` references as
   blocking inputs.
4. Do not discover prior decisions by guessing sibling directories, filenames or chat context. If a
   required reference is missing, unreadable or not formally linked, report the handoff gap and do
   not invent the missing constraints.
5. Run the shared validator and report command:

```bash
<PYTHON> <FACTORY_ROOT>/skills/hl-feature-workspace/scripts/feature_workspace.py validate --registry wiki/feature-workspace/registry.yaml
<PYTHON> <FACTORY_ROOT>/skills/hl-feature-workspace/scripts/feature_workspace.py report --registry wiki/feature-workspace/registry.yaml
```

6. If validation fails, report the inconsistencies first. Do not infer replacement state from prose.
7. Separate formal Features from unclassified migration candidates.
8. Before reporting a Leaf discussion as the next action, verify the parent Initiative's
   `initial_decomposition.status: completed`, its frozen `feature_ids`, and each candidate's Scope
   Gate. If decomposition is incomplete, report `finalize-decomposition` or the required split as
   the next action; never route a broad or `must-split` Feature to discussion.
9. For active work, report the current skill and phase, state, remaining workflow stages, blockers,
   dependency-ready parallel work, next skill, target manifest, and required referenced inputs.
10. For merged work, report the tombstone and canonical long-term wiki targets as authority. Do not
    scan unreferenced retained source directories. Mention or read one only when the user explicitly
    asks for provenance or history; never use it as current requirements, `context_refs`, or input to
    new Initiative/Feature creation.
11. Explain maintenance ownership: name the workflow skill responsible for the next state change and
    the manifest it will maintain. Never recommend manual phase advancement.
12. State that `wave` is only a scheduling hint; parallel execution also requires completed
    dependencies and non-overlapping owner, file and contract scope, within
    `workflow.max_parallel_features`.

## Next-Session Prompts

When the user asks for a next-session prompt:

- Generate it in the response; never persist prompt files.
- Include the Feature ID and title, current phase and state, next skill, target manifest, dependency
  status, and every required context reference as an explicit must-read path.
- Carry confirmed conclusions and prior constraints from the referenced authority documents. Keep
  open questions clearly separate; do not promote recommendations or pending questions into settled
  facts.
- Tell the next workflow skill to preserve split boundaries and to maintain the owning manifest.
- If formal references are incomplete, output a blocker prompt that requests the missing authority
  instead of pretending the handoff is complete.
- Produce one fenced, copyable prompt per requested Feature.

## Language

Match the user's language in the report. Use `project.language.docs` for any quoted document prose.
Keep IDs, keys, paths, lifecycle enums, skill names and verdict labels in their stable ASCII form.
Clearly label missing or inconsistent data as unknown rather than guessing.
