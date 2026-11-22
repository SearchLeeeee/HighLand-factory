---
name: hl-workflow-governance
description: Use when governing the feature workspace lifecycle rules, dependency and ready-to-merge gates, Initiative integration-test handoffs and results, merge eligibility, routing between workflow skills, or maintenance of the workflow itself.
---

# Workflow Governance

## Questioning Style

All user-facing questions must use Socratic questioning. Before asking, read
`<FACTORY_ROOT>/skills/hl-workflow-governance/references/socratic-questioning.md`
(relative to the located factory checkout during bootstrap). Follow that shared policy for
chat, choice panels and workbench questions; preserve existing explicit authorization gates.

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
   separate, merge authorization, Initiative integration required, evidence root) from
   `workflow-profile.md` / `.factory/factory.yaml`. Never assume a default.
6. If the profile or config disagrees with what the user is asking for, treat the config as
   truth and route the change through **Workflow Maintenance** below.

Fail closed: missing config, missing profile, a failing gate, or an unresolved language policy
stops the skill with one concrete repair instruction.

## Minimum Sufficient Verification

Use the smallest set of checks that can decide the current requirements and real risks. Reuse
applicable results for unchanged sources and conditions; choose reruns by impact, not by phase,
agent count or a desire for more evidence. A brief reason in the normal handoff is enough when
additional work is necessary; do not add configuration, approval steps or a separate proof process.

Ordinary source identity is a Git revision plus the relevant diff and new-file contents. Keep the
reviewed sources stable. Do not default to per-file hashes, whole-tree snapshots, extra freeze
commits, fresh clones or repeated environment provisioning. Use extra identity or isolation only
when a concrete source ambiguity, state contamination, concurrency conflict, artifact-integrity
requirement or explicit acceptance criterion needs it. Existing strictly bound receipts remain
usable for the scope and identity they actually record.

Independent review and verification require independent judgement. They do not automatically
require repeating every successful check. The coordinator inspects the findings and decisive
evidence and samples or reruns checks where a concrete risk warrants it; final acceptance remains
the coordinator's responsibility.

On failure or missing evidence, preserve the observation, diagnose the affected part and repair
only the resulting gap. Keep unaffected valid results with their provenance. Missing or ambiguous
results are not passes, but formatting, metadata changes or a lost record do not automatically
invalidate every other result. Preserve failure facts; harmless presentation corrections may be
noted without recreating a run. Keep raw logs separate from output directories tools may clean.
Do not hash every log or add multiple summaries to prove the same fact. Stop once the stated
acceptance and delivery boundary is satisfied. Safety and authorization boundaries still apply.

Within one session, nested skills reuse the already resolved context and successful doctor/gate
results while their inputs remain unchanged. Reload changed configuration and rerun the affected
checks; lifecycle mutations still require their boundary validation. A new independent role reads
the necessary current inputs and judges evidence independently, without automatically reprovisioning
an equivalent healthy environment. Use existing project toolchains, caches and maintained synthetic
test entry points. Check required external-client availability early through an already supported
client, without prescribing a particular product or GUI. Preserve data, process and session isolation
where the acceptance contract requires it; keep credentials and raw sensitive logs out of scripts.

For execution work, apply [Execution Preparation And Handoff](references/execution-preparation.md)
to make that reuse operational: assign one preparation owner, check cheap prerequisites before
expensive work, carry resources/results in the existing plan and handoff, overlap safe preparation,
and diagnose stalled tasks before retrying. Keep only applicable details; this adds no mandatory
report, configuration, lifecycle state or approval.

Cross-session handoffs use that reference's continuity and evidence-source rules: state the
critical inherited conditions, actual evidence scope and continuation entry, and remaining
required checks. If sources change, synchronize the existing plan and result mapping with the
affected claims; a recreated scenario is not automatically the original chain continued.
This is an execution check, not another user confirmation or a change to phase boundaries.

Carry explicit discussion and handoff preferences within the same Initiative when a current
workbench, formal context reference or handoff records their source and scope. A new Leaf does not
by itself require the user to choose the same mode again. Missing or conflicting preferences need
clarification only for the affected choice. Preferences never grant authorization: discussion
completion, new-session creation, merge and push keep their existing explicit boundaries. Handoff
to implementation still waits for completed profiles and a passing workspace gate.

## Route The Request

| Request | Owning skill |
| --- | --- |
| Progress, blockers, next actions, stale work, next-session handoff | `$hl-feature-progress` (read-only) |
| Feature or Initiative lifecycle state, dependency, closure, validation, split, merge eligibility | `$hl-feature-workspace` |
| Initiative-level cross-Feature integration after all Leaf Features are ready | `$hl-initiative-merge` |
| Semantic wiki merge after preflight and authorization, including MOC updates, full validator, retained-history transformation, authority switch | `$hl-wiki-merge` |
| Provenance / why / history question while reading canonical authority | `$hl-history-trace` (isolated subagent) |
| Bounded bugfix or detail adjustment that may escalate | `$hl-quick-change` |
| Explicit manual full or latest-Initiative code/test/current-Wiki scan after all Initiatives close, followed by user-selected maintenance | `$hl-refactor` |
| Cleaning up a finished or residual worktree and its Feature branch | `references/worktree-lifecycle.md` |
| A change to these rules themselves | **Workflow Maintenance** below |

Never treat a narrative report, a chat summary or a directory guess as state authority. Resolve
`wiki/feature-workspace/registry.yaml`, the current manifests and every required `context_refs`,
and run `validate` before and after any manifest or workflow change.

## User Choice Panels

Apply `references/socratic-questioning.md` to every workflow question. First clarify any unresolved
premise through a neutral Socratic question. When the workflow then needs a decision among two or
more viable alternatives, use the structured choice-panel tool when the client offers one. Keep
open exploration in free text rather than forcing it into premature alternatives.

- Ask one focused question at a time; wait before asking a dependent follow-up.
- Offer 2-3 mutually exclusive options. Put the recommended option first, mark it
  `(Recommended)`, and state the material impact of each in one short sentence.
- Do not add an explicit `Other` option; the client supplies it. Treat a custom answer as the
  selected proposal and ask again only when a material ambiguity remains.
- Without a panel, ask one concise plain-text question, list the same options, and allow a
  custom proposal.
- A choice panel never weakens an authorization, lifecycle, validation, merge, deletion, commit
  or push gate.

Discussion records follow the save timing in `references/socratic-questioning.md`: retain answers
in the conversation and consolidate at wrap-up or an earlier required boundary. Question delivery
and file persistence are separate; required lifecycle and authorization gates still apply.

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
structured handoff. The main session inspects the result and decisive evidence, using targeted
checks when needed for an identified risk; delegation alone does not require rerunning every check.
A delegated answer is never authority by itself.

## Required Initiative Intake Gate

Creating an Initiative is followed by initial decomposition, not by an Initiative-wide discussion
in a broad F01. Before any detailed Feature discussion:

1. Register the complete initial Feature inventory with stable F IDs, `depends_on` and `wave`.
2. Run Scope Gate for every candidate.
3. Split every `must-split` candidate before discussion. Retain `split-default` only with a
   non-empty `scope_gate.indivisibility_reason`.
4. Run `feature_workspace.py finalize-decomposition`.
5. Route only the first dependency-ready Leaf into discussion.

Before that discussion, check whether other Leaf Features are parallelizable at that moment (satisfied
dependencies, no blocking child, clear ownership and disjoint implementation files and contracts); there is no numeric
concurrency cap — safety comes from that disjointness test plus worktree code isolation. When at
least one sibling is parallelizable, the operator chooses shared-checkout sequential work or a
dedicated git worktree, and the choice is recorded in the workbench. The implementation session
carries one continuous goal: advance the Feature to `ready-to-merge / ready`. A worktree is code
isolation only and never merges back to `repo.default_branch` before that state.

The validator and transition commands fail closed when decomposition is incomplete, the candidate
is not a Leaf, or the candidate is not discussion-admissible. Mandatory splitting is a workflow
action performed now, not a question deferred into business discussion.

## Required Documents-To-Profiles Continuation

After discussion completion is confirmed, `$hl-feature-discuss` writes the domain implementation
documents, records `implementation-docs / completed` through `$hl-feature-workspace`, and runs the
workspace gate. On PASS it invokes `$hl-feature-profile-generate` automatically in the same session,
without asking for document approval, another phase confirmation or a separate user invocation.
Honor an explicit documents-only scope or pause instruction. Missing inputs, failed gates and new
unresolved requirements block the affected continuation until repaired or resolved; they never
justify bypassing a gate. Preserve the existing phases and state-machine transitions without adding
an approval field or configuration switch. Code implementation still starts in a new session after
`code-ai-profiles / completed`.

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

Acceptance uses a boolean `passed`; only `true` qualifies. Passing acceptance and ready closure
require non-empty relative evidence-file lists resolved from their owning manifest. The machine
gate checks that those files exist; independent reviewers and verifiers judge their content.
Canonical promotion targets may still be planned. Registry-backed transitions validate the complete
candidate registry before atomically replacing the target manifest; rejection leaves the original
bytes unchanged. Standalone Leaf checks do not replace dependency or Initiative preflight.

Integration criteria inherit the confirmed acceptance contract, including any same-object,
same-artifact, same-session or continuous-sequence conditions. Reuse applies only when it satisfies
those conditions together; separate capability demonstrations cannot silently replace a required
continuous path. Repair only the missing path and retain applicable unaffected evidence.

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
   (`<FACTORY_ROOT>/skills/hl-wiki-merge/scripts/validate_llm_wiki.py`), which excludes the
   registered process workspaces through the shared resolver.
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

## Manual Refactoring Boundary

Invoke `$hl-refactor` only on an explicit user request, independently of Initiative closure.
Use the existing lifecycle reader to require all effective Initiatives and Leaves terminal
with their required closure; `ready-to-merge / ready` and integration PASS alone are insufficient.
Do not manufacture admission by cancelling work or editing historical state.

The skill scans read-only, presents evidence and total cost, then changes
only user-selected candidates. Full and latest-Initiative scanning share the same selection,
review and verification rules; scanning broadly does not authorize broad edits. Its run record
is process material under the resolved refactor workspace, not a second lifecycle authority.

Current-Wiki semantic consistency is checked in both directions and bound to time, source
versions and relevant configuration. Reuse the existing structural validator; a clean link
graph is not proof of business correctness. Keep completed Initiative history and tombstones
unchanged. Process-rule improvements discovered during a run are proposals for another session.
If a selected finding needs a new Feature, finish its investigation/handoff, then pause or close
the maintenance run before entering that workflow. A handoff does not mean the defect is fixed.

## Worktree Lifecycle And Cleanup

The conditions for retiring a dedicated git worktree and its Feature branch after implementation
live in `references/worktree-lifecycle.md`, which is the single rule source; do not restate them
here or in another skill.

- Trigger a cleanup review when the implementation session reaches `ready-to-merge / ready`, when
  the user asks whether disk space can be released, or when a residual worktree is found under the
  work root.
- This skill rules on whether cleanup is permitted and what must be retained. It performs no
  lifecycle transition for cleanup, edits no manifest, and never treats a removed worktree as a
  Feature state change.
- When the reference's preconditions do not hold, refuse the cleanup and report the worktree, its
  branch and the blocking reason instead of deleting anything.

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
