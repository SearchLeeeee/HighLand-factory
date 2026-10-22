---
name: hl-workflow-governance
description: Use when governing the feature workspace lifecycle rules, dependency and ready-to-merge gates, Initiative integration-test handoffs and results, merge eligibility, routing between workflow skills, or maintenance of the workflow itself.
---

# Workflow Governance

Use this skill to decide which workflow skill owns a request, to check a governed
transition against policy, and to maintain the workflow itself. It restates the contract;
it never replaces the owning machine gate. The durable authority remains
`wiki/feature-workspace/README.md` and `schema/feature-workspace-schema.md`, and
`<FACTORY_ROOT>/skills/hl-feature-workspace/scripts/feature_workspace.py` is the only
lifecycle state machine.

## Step 0 — Load factory context

1. Read `<work>/.factory/local.yaml`. If missing or unreadable, stop and tell the user to run
   `$hl-factory-init` (or `factory init`); never guess a path or interpreter.
2. Resolve `FACTORY_ROOT` (`factory_root`), `PYTHON` (`python`), and `WORK_ROOT` (the git
   top-level, or the directory containing `.factory/`).
3. Read `wiki/governance/workflow-profile.md` under `WORK_ROOT`. It defines project language,
   layout, owners, commands, verification evidence root, gate switches and security boundaries.
   If it is missing or unreadable, stop and tell the user to run `$hl-factory-doctor`.
4. Run gates through the engine rather than composing paths by hand:
   `factory gate workspace --work <WORK_ROOT>` and `factory gate wiki --work <WORK_ROOT>`.
5. Take policy values (scope gate, split default, quick change, review required, verification
   separate, merge authorization, Initiative integration required, max parallel features,
   evidence root) from `workflow-profile.md` / `.factory/factory.yaml`. Never assume a default.
6. If the profile or config disagrees with what the user is asking for, treat the config as
   truth and route the change through **Workflow Maintenance** below.

Fail closed: missing config, missing profile, a failing gate, or an unresolved language policy
stops the skill with one concrete repair instruction.

## Route The Request

| Request | Owning skill |
| --- | --- |
| Progress, blockers, next actions, stale work, next-session handoff | `$hl-feature-progress` (read-only) |
| Feature or Initiative lifecycle state, dependency, closure, validation, split, merge eligibility | `$hl-feature-workspace` |
| Initiative-level cross-Feature integration after all Leaf Features are ready | `$hl-initiative-merge` |
| Semantic wiki merge after preflight and authorization, including MOC updates, full validator, retained-history transformation, authority switch | `$hl-wiki-merge` |
| Provenance / why / history question while reading canonical authority | `$hl-history-trace` (isolated subagent) |
| Bounded bugfix or detail adjustment that may escalate | `$hl-quick-change` |
| A change to these rules themselves | **Workflow Maintenance** below |

Never treat a narrative report, a chat summary or a directory guess as state authority. Resolve
`wiki/feature-workspace/registry.yaml`, the current manifests and every required `context_refs`,
and run `validate` before and after any manifest or workflow change.

## User Choice Panels

When the workflow needs a decision among two or more viable alternatives, use the structured
choice-panel tool when the client offers one instead of asking for a number or free-form prose.

- Ask one decision at a time unless up to three decisions are tightly coupled.
- Offer 2-3 mutually exclusive options. Put the recommended option first, mark it
  `(Recommended)`, and state the material impact of each in one short sentence.
- Do not add an explicit `Other` option; the client supplies it. Treat a custom answer as the
  selected proposal and ask again only when a material ambiguity remains.
- Without a panel, ask one concise plain-text question, list the same options, and allow a
  custom proposal.
- A choice panel never weakens an authorization, lifecycle, validation, merge, deletion, commit
  or push gate.

## Tiered Delegation

The main session owns intent, scope, authority, lifecycle decisions, cross-agent synthesis and
final verification. When the platform exposes a lower-cost model tier, delegate bounded low-risk
work to protect main-session context; if that tier is unavailable, use another permitted
low-cost model or do the work in the main session without weakening the responsibility boundary.

Good delegation targets: file inventory, reference search, concise summaries, draft matrices,
read-only local checks, log collation, handoff drafts, and mechanical edits with an explicit file
boundary. Parallelise only tasks with disjoint ownership and no ordering dependency.

Do not delegate product decisions, security or privacy judgements, lifecycle transitions, merge
gates, integration PASS registration, retained-source authority changes, commit/push, or final
acceptance. Every delegated task states paths, allowed mutation scope, acceptance criteria and a
structured handoff. The main session inspects the result and reruns material checks; a delegated
answer is never authority by itself.

## Required Initiative Intake Gate

Creating an Initiative is followed by initial decomposition, not by an Initiative-wide discussion
in a broad F01. Before any detailed Feature discussion:

1. Register the complete initial Feature inventory with stable F IDs, `depends_on` and `wave`.
2. Run Scope Gate for every candidate.
3. Split every `must-split` candidate before discussion. Retain `split-default` only with a
   non-empty `scope_gate.indivisibility_reason`.
4. Run `feature_workspace.py finalize-decomposition`.
5. Route only the first dependency-ready Leaf into discussion.

The validator and transition commands fail closed when decomposition is incomplete, the candidate
is not a Leaf, or the candidate is not discussion-admissible. Mandatory splitting is a workflow
action performed now, not a question deferred into business discussion.

## Required Initiative Preflight

Before any merge, every non-cancelled, non-superseded Leaf Feature must reach
`ready-to-merge / ready` through its normal review, acceptance and closure gate. Then generate the
Initiative integration-test handoff, execute only the remaining cross-Feature tests in a new
immutable evidence root under the configured evidence root, record PASS with
`initiative-integration-result` and an existing local evidence file, and require
`initiative-merge-ready` to pass. Do not reuse or reseal individual Feature evidence as
Initiative evidence.

A `ready-to-merge / ready` dependency counts as satisfied only when its acceptance passed and its
closure is complete. Any partial ready state stays fail-closed.

## Required Merge And Authority Gate

After the Initiative preflight, follow this order without exception for each Feature in
`depends_on` topological order:

1. Require `initiative-merge-ready` to pass. When `workflow.initiative_integration_required` is
   false, the initiative-local equivalent recorded in the profile still governs.
2. Obtain explicit authorization for the merge when `workflow.merge_requires_authorization` is
   true.
3. Perform the semantic wiki merge into current or domain authority documents.
4. Update every affected MOC.
5. Run the full long-term wiki validator owned by `$hl-wiki-merge`
   (`<FACTORY_ROOT>/skills/hl-wiki-merge/scripts/validate_llm_wiki.py`), which excludes the feature
   and quick workspaces.
6. Only after validator PASS, perform the retained-history transformation. Preserve the complete
   staged source; never delete it.
7. Record the Feature as `merged / completed`.
8. Switch authority to the canonical wiki and update the external routing record, removing active
   manifest references and default discovery paths, and rejecting active `context_refs` into
   retained history.

The validator is a `$hl-wiki-merge` machine gate, not a lifecycle field. On validator failure, stop:
keep the Feature `ready-to-merge / ready`, and do not create a tombstone or routing record, switch
authority, transform retained history, or mark the Feature merged/completed. Open questions stay
in the feature workspace; current canonical facts belong in the current or domain authority doc.

## Provenance And Quick-Change Boundaries

- Historical lookup starts from a concrete question plus a canonical path, runs inside a fresh
  isolated subagent through the external routing record and the retained `history-route.yaml`, and
  returns only the compact handoff. The main session must not load retained material.
- Canonical authority documents never contain feature/initiative IDs, retained paths or reverse
  history links.
- A quick-change record is process material, never lifecycle authority. When a hard gate fires,
  the record escalates to the feature workflow instead of stretching its own boundary.
- When `workflow.quick_change` is false, do not open the lightweight path at all; route the
  request through intake and decomposition.

## Workflow Maintenance

Update every authority that owns the changed behaviour, in one change:

1. State the new rule, its compatibility impact and its fail-closed behaviour before editing.
2. Lifecycle status or transition changes go through `feature_workspace.py`, its tests, and the
   feature-workspace README/schema.
3. Merge-content machine gates stay in `$hl-wiki-merge` scripts and tests; they must never be
   represented as lifecycle fields, status values or state-machine branches.
4. Keep the affected workflow skills, this skill, `references/entry-point.md` and
   `references/workflow-contract.md` consistent; prose and code must not diverge.
5. Run the checks owned by every affected surface: the state-machine tests plus a real workspace
   `validate` for lifecycle changes, and the validator positive/negative tests plus a full wiki
   validation for merge-gate changes.
6. Preserve unrelated dirty worktree changes. Do not merge, create tombstones, switch authority,
   transform retained history, commit or push unless the applicable gate and a separate
   authorization have passed.

## Language

Write instructions and internal reasoning in English. Match the user's language when talking to
them, and use `project.language.docs` for any document this skill helps produce. Keep IDs, keys,
paths, lifecycle enums, skill names and verdict labels in their stable ASCII form.
