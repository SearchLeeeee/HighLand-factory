---
name: hl-feature-workspace
description: Use when a workflow skill needs to create, validate, transition, split, close or inspect an Initiative or Leaf Feature in the shared feature workspace. Wraps the single lifecycle state machine and its schema gate; it is the only skill allowed to change lifecycle state.
---

# Feature Workspace

`wiki/feature-workspace/README.md` and `schema/feature-workspace-schema.md` are the workflow
authority. YAML manifests are lifecycle-state authority only; they never override product facts in
the long-term wiki.

Run `<FACTORY_ROOT>/skills/hl-feature-workspace/scripts/feature_workspace.py` through the Python
interpreter recorded in `.factory/local.yaml`, which must have PyYAML available. If the interpreter
cannot import `yaml`, stop and report the missing dependency instead of guessing manifest state. The
registry may reference Initiative and Feature manifests by relative path; validation and reporting
resolve those references recursively.

## Step 0 — Load factory context

1. Read `<work>/.factory/local.yaml`. If missing or unreadable, stop and tell the user to run
   `$hl-factory-init` (or `factory init`); never guess a path or interpreter.
2. Resolve `FACTORY_ROOT` (`factory_root`), `PYTHON` (`python`), and `WORK_ROOT` (the git
   top-level, or the directory containing `.factory/`).
3. Read `wiki/governance/workflow-profile.md` under `WORK_ROOT`. It defines language, layout,
   owners, commands, the evidence root, gate switches and security boundaries. If it is missing or
   unreadable, stop and tell the user to run `$hl-factory-doctor`.
4. Run gates through the engine rather than composing paths:
   `factory gate workspace --work <WORK_ROOT>` (this runs `validate` against the registry) and
   `factory gate wiki --work <WORK_ROOT>`.
5. Take the scope-gate switches, max parallel features, review and verification policy, evidence
   root and the feature-workspace root from the profile. The default registry path is
   `wiki/feature-workspace/registry.yaml`; if the profile declares a different workspace root, use
   that instead.
6. If the profile or config contradicts the request, route to `$hl-workflow-governance` instead of
   improvising.

Fail closed: missing config, missing profile, a failing gate, or an unresolved language policy stops
the skill with one concrete repair instruction.

## Commands

```bash
<PYTHON> <FACTORY_ROOT>/skills/hl-feature-workspace/scripts/feature_workspace.py validate --registry wiki/feature-workspace/registry.yaml
<PYTHON> <FACTORY_ROOT>/skills/hl-feature-workspace/scripts/feature_workspace.py report --registry wiki/feature-workspace/registry.yaml
<PYTHON> <FACTORY_ROOT>/skills/hl-feature-workspace/scripts/feature_workspace.py finalize-decomposition --registry wiki/feature-workspace/registry.yaml --initiative <Ixxx>
<PYTHON> <FACTORY_ROOT>/skills/hl-feature-workspace/scripts/feature_workspace.py merge-ready --feature <feature.yaml>
<PYTHON> <FACTORY_ROOT>/skills/hl-feature-workspace/scripts/feature_workspace.py initiative-merge-ready --registry wiki/feature-workspace/registry.yaml --initiative <Ixxx>
```

Transition and integration commands take the same registry/feature/initiative arguments, plus
`--output` for the handoff and `--evidence` for the integration result. Run `validate` after every
manifest change; its exit status is the gate.

## Formal Context References

Use `context_refs` when a future session must inherit decisions or authority documents that the
lifecycle manifest does not contain.

```yaml
context_refs:
  - path: feasibility/confirmed-constraints.md
    kind: prior-constraints
    required: true
```

- Resolve `path` relative to the manifest that declares it.
- Keep every reference inside the feature-workspace root. Use relative paths only.
- Set `required: true` for prior constraints, accepted decisions, or other inputs without which the
  next workflow must not proceed.
- Put conclusions shared by several Leaf Features into one Initiative-level authority document and
  reference it from the Initiative and every affected active Leaf Feature; do not duplicate those
  conclusions per Feature.
- Keep confirmed conclusions separate from recommendations and open questions.
- Persist human-readable content in the configured document language (or the user's language when
  the profile leaves it open) while keeping IDs, keys, paths, lifecycle enums, skill names and
  verdict labels in their stable ASCII form.
- Do not persist next-session prompts; generate them from current manifests and formal references
  with `$hl-feature-progress`.
- Treat a malformed reference, a required missing file, or a path outside the workspace as a
  blocking validation error.
- Never put retained `merged/completed` Feature source documents into an active Initiative or
  Feature `context_refs`; they are provenance only and the validator rejects them. Use canonical
  long-term wiki authority instead.

## Initiative Intake And Discussion Gate

After creating an Initiative, build the complete initial Feature inventory before any detailed
business discussion. Allocate stable F IDs, record `depends_on` and `wave`, and run Scope Gate for
every candidate. Split every `must-split` candidate immediately. A `split-default` candidate may
remain only with a non-empty `scope_gate.indivisibility_reason`.

When every initial active candidate is confirmed as a Leaf Feature, run `finalize-decomposition`.
Only then route the first dependency-ready Leaf to the discussion skill. Do not create a broad F01
for the Initiative, do not ask whether a mandatory split should happen, and do not use detailed
discussion to discover the initial decomposition.

The validator rejects active Features in `discussion` or a later phase when the Initiative
decomposition is incomplete, the Feature is not a Leaf, the Scope Gate requires splitting, or a
`split-default` exception lacks its reason. Transitioning into discussion requires `--registry` so
the state machine can verify the parent Initiative gate.

When `workflow.scope_gate.enabled` is false, record the policy reason in the Initiative manifest and
still run the structural split checks: a candidate that spans several independently valuable loops
or redefines several core contracts must not enter discussion as one Feature.

Update lifecycle state only at skill boundaries: skill start, skill completion, blocked, scope split,
acceptance and merge. Do not write question-level progress.

Never:

- treat an Initiative as an implementable Leaf Feature;
- enter detailed discussion before the Initiative initial decomposition is finalized;
- retain a `must-split` candidate as a discussion target;
- defer a current-loop requirement as a naked TODO;
- bypass the scope gate because a feasibility review was skipped;
- delete staged Feature documents during or after merge; retain them as historical,
  non-authoritative material;
- let retained source documents or lifecycle YAML compete with the long-term wiki after merge.

Stop on duplicate IDs, dangling or cyclic dependencies, illegal lifecycle values, missing next
actions, or closure-gate failures.

## File I/O Routing

Lifecycle changes belong to this skill's state machine and must be invoked through the configured
Python interpreter; never edit `phase` or `state` with generic write operations. Run `validate` after
every manifest change and retain the audit receipt. Manifest prose may be edited directly, but a
change that alters lifecycle meaning must go through a transition command instead.
