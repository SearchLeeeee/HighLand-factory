# Workflow Governance — Entry Point

Load factory context first: read `.factory/local.yaml`, then
`wiki/governance/workflow-profile.md`. If either is missing, stop and route to `$hl-factory-init`
or `$hl-factory-doctor`; do not reconstruct values from memory, chat history or directory guesses.

This page is a fresh-session map. It does not restate every procedure. `$hl-workflow-governance`
owns routing and workflow maintenance; the skill named for the current action owns its detailed
steps; executable and schema authorities below own machine-enforced behavior.

## Fresh-session entry

1. Read `wiki/feature-workspace/README.md` and
   `wiki/feature-workspace/schema/feature-workspace-schema.md`.
2. Read `$hl-feature-workspace/SKILL.md` for lifecycle commands and the
   `$hl-workflow-governance/SKILL.md` for request routing and maintenance.
3. Run `factory gate workspace --work <WORK_ROOT>`. Use the registry and current manifests as
   lifecycle authority; narrative reports are not state.

## Route

Use `$hl-workflow-governance/SKILL.md`'s request table to select the owner: Feature workspace,
Feature discussion/orchestration, Initiative integration, wiki merge, history trace, Quick Change,
explicit manual refactoring, or workflow maintenance. Do not carry out a Feature transition in
the routing skill. `$hl-refactor` requires a user request and all effective Initiatives closed;
Initiative completion never invokes it automatically.

## Project write lease

Before the first project write, use the shared engine lease; checking once without acquiring
does not protect the interval before a later write. This applies to code, tests, Wiki, profiles,
process records, Initiative creation and workflow upgrades, including writes by subagents.

1. Inspect `factory maintenance-lock --work <WORK_ROOT> --action status`. If a coordinator
   explicitly delegated its live `FACTORY_MAINTENANCE_TOKEN`, borrow that lease and run
   `factory maintenance-check --work <WORK_ROOT>` with the token. Never copy an unrelated
   operation's token merely to bypass its occupancy.
2. Otherwise acquire `factory maintenance-lock --work <WORK_ROOT> --action acquire
   --owner <operation-id> --purpose <task-summary>` and retain the returned token in the
   execution environment as `FACTORY_MAINTENANCE_TOKEN` for governed commands. A conflicting
   lease blocks mutation with its owner and recovery instruction.
3. Pass the same token to delegated writers with explicit disjoint file ownership. Check access
   before each new implementation unit; keep the lease until those writers stop.
4. At completion or explicit pause, release a lease **this operation acquired** using
   `factory maintenance-lock --work <WORK_ROOT> --action release --token <owned-token>`.
   A borrower returns control to its coordinator and never releases the coordinator's lease.

`hl-refactor` acquires and releases its lease through its run helper and rechecks lifecycle
admission as well as access. Use that helper's `pause`/`resume`/`finish` commands for its runs.
Never steal a lease because it looks old; verify the owning operation has stopped and recover
with its recorded identity. If interrupted acquisition/release left missing peer lock files,
the exact owner's release token may recover the remaining locks; an unreadable or different-owner
lock still blocks release. The shared resolver covers work, code, Wiki and common Git worktree
resources. Cooperating factory writers are protected; arbitrary editors and remote processes
are detected through source rechecks, not physically prevented. Read-only progress and diagnosis
do not require a lease.

## Shared invariants

- All workflow questions follow [Socratic questioning](socratic-questioning.md): grounded,
  neutral inquiry into concepts, assumptions, evidence, alternatives and consequences, with
  direct explicit authorization at existing permission gates. The same reference owns discussion
  save timing: accumulate answers in the conversation, then consolidate at wrap-up or before a
  required boundary, without routine per-answer file reads and writes.

- Use minimum sufficient verification: one identifiable source target, applicable evidence reuse,
  affected checks and risk-based sampling. Do not default to layered hashes, repeated freezes, fresh
  clones or full reruns. Repair evidence gaps locally, retain failure facts, and keep safety,
  independent judgement, machine gates and authorization. No new mode or approval is required.

- Reuse unchanged context and successful checks across nested skills in one session; reload and
  recheck affected inputs after changes. Reuse supported toolchains and suitable healthy test
  environments while preserving required state/session isolation. Check required external clients
  early, without mandating a product or GUI.
  Use [Execution Preparation And Handoff](execution-preparation.md) for preparation ownership,
  suitability checks, safe overlap and concise role handoffs; no separate environment report.
  Its cross-session rules carry critical constraints, evidence scope/continuation entries and
  unverified work; source changes update the existing plan/result mapping without a new approval.
- Inherit explicit same-Initiative discussion/handoff preferences from a current workbench, formal
  reference or handoff. Do not repeat a settled choice merely for a new Leaf; preference is not
  authorization. Profiles and their gate must complete before implementation handoff.
- Acceptance requires boolean `true` and actual evidence files; ready closure also requires actual
  validation evidence. Registry-backed transitions validate the full candidate before atomic
  replacement, leaving the original unchanged on rejection. Planned canonical targets may be absent.
- Integration matrices preserve confirmed same-object/artifact/session/sequence requirements;
  historical capability evidence cannot relax those conditions.

- Complete Initiative inventory, dependency/wave registration and Scope Gate before Leaf discussion.
- After discussion approval, completed implementation documents lead automatically to Code AI
  profile generation in the same session, with no further phase confirmation. Preserve the
  state-machine boundaries, required inputs and workspace gate; honor explicit scope or pause
  instructions. Application-code implementation still starts in a new session after profiles.
- Dependencies count as satisfied only after acceptance and closure are complete.
- An Initiative merge requires every active Leaf ready, new Initiative integration evidence, a
  passing merge-ready gate, and the required authorization.
- Per Feature, merge semantic content, update affected MOCs, pass the full long-term wiki
  validator, retain the source, then switch authority and close the Feature.
- Wiki content validation is not a lifecycle state. A failed validator keeps the Feature ready and
  blocks authority switch and closure.
- Keep future work and maintenance evidence in their registered process workspaces; keep the
  canonical wiki as current authority. Retained sources are history only. Resolve exclusions
  from the shared workspace registry, never a directory-name heuristic.
- Manual refactoring records its own candidates, user selection and evidence. It never reopens
  completed Initiatives, repeats their historical authority switch, or relaxes Quick Change's
  hard gates. Future workflow-rule improvements belong to a separate session.
- Before workflow maintenance, state compatibility and fail-closed behavior, update every owning
  surface, and keep generic documents free of project-specific facts.

Detailed commit and worktree rules live in `references/commit-boundaries.md` and
`references/worktree-lifecycle.md`. Shared policy details and change-surface ownership live in
`references/workflow-contract.md`.
Starting a registered Leaf with `$hl-feature-orchestrator` grants scoped local commit authorization
under the commit reference. Preserve it in handoffs; do not ask again at each boundary. Explicit
restrictions and stricter project policy prevail; push and merge still require separate authorization.

## Authorities

- Lifecycle state machine: `<FACTORY_ROOT>/skills/hl-feature-workspace/scripts/feature_workspace.py`
- Long-term Wiki validator: `<FACTORY_ROOT>/skills/hl-wiki-merge/scripts/validate_llm_wiki.py`
- Semantic merge workflow: `$hl-wiki-merge/SKILL.md`
- Provenance resolver: `<FACTORY_ROOT>/skills/hl-history-trace/scripts/trace_feature_history.py`
- Manual maintenance run: `<FACTORY_ROOT>/skills/hl-refactor/scripts/refactor.py`
- Project lease: `<FACTORY_ROOT>/engine/factorylib/maintenance.py`
- Process-workspace registry: `<FACTORY_ROOT>/engine/factorylib/workspaces.py`
