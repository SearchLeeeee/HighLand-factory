---
name: hl-initiative-merge
description: Use when an Initiative's active Leaf Features are all ready. Runs the governed cross-Feature integration acceptance in one immutable evidence root, registers the result, then hands off to an authorized semantic wiki merge.
---

# Initiative Integration And Merge

Use this skill after every active, non-cancelled, non-superseded Leaf Feature is
`ready-to-merge / ready`. It owns the boundary between Feature completion and current wiki
authority. It does not replace feasibility, feature discussion, Feature acceptance,
`$hl-feature-workspace`, or `$hl-wiki-merge`.

Read before acting: `wiki/feature-workspace/README.md` and
`schema/feature-workspace-schema.md`; `$hl-feature-workspace`; `$hl-workflow-governance` with its
`references/entry-point.md`; `$hl-wiki-merge`; the Initiative manifest, every active Feature
manifest, their required `context_refs`, and the generated integration handoff.

The lifecycle state machine is the only authority for lifecycle changes. Use
`feature_workspace.py`; never hand-edit `phase`, `state`, acceptance, closure or
`integration_testing` fields.

## Step 0 — Load factory context

1. Read `<work>/.factory/local.yaml`. If missing or unreadable, stop and tell the user to run
   `$hl-factory-init` (or `factory init`); never guess a path or interpreter.
2. Resolve `FACTORY_ROOT` (`factory_root`), `PYTHON` (`python`), and `WORK_ROOT` (the git
   top-level, or the directory containing `.factory/`).
3. Read `wiki/governance/workflow-profile.md` under `WORK_ROOT`. It defines language, layout,
   owners, commands, verification evidence root, gate switches and security boundaries. If it is
   missing or unreadable, stop and tell the user to run `$hl-factory-doctor`.
4. Run gates through the engine, not by composing paths:
   `factory gate workspace --work <WORK_ROOT>` and `factory gate wiki --work <WORK_ROOT>`.
5. Take the evidence root, integration-required switch, verification-separate switch and merge
   authorization policy from the profile / `.factory/factory.yaml`. Never assume them.
6. If the profile or config contradicts the request, route to `$hl-workflow-governance` instead of
   improvising.

Fail closed: missing config, missing profile, a failing gate, or an unresolved language policy
stops the skill with one concrete repair instruction.

## Fixed Boundary

Keep these states separate and never report one as another:

1. **Feature acceptance** — one Leaf Feature's implementation, review, verification and closure.
2. **Initiative integration acceptance** — one immutable cross-Feature run proving the dependency
   chain, shared contracts, negative paths, safety boundaries and required user-visible behaviour.
3. **Wiki merge** — a semantic authority switch performed only after Initiative merge readiness,
   the required authorization, affected-MOC updates and the full long-term wiki validator.

A passing Feature is not an Initiative integration pass. An integration pass is not a wiki merge.

## Phase A: Intake And Freeze

Run read-only validation and reporting first:

```bash
factory gate workspace --work <WORK_ROOT>
<PYTHON> <FACTORY_ROOT>/skills/hl-feature-workspace/scripts/feature_workspace.py report --registry wiki/feature-workspace/registry.yaml
```

Then require:

```bash
<PYTHON> <FACTORY_ROOT>/skills/hl-feature-workspace/scripts/feature_workspace.py initiative-merge-ready --registry wiki/feature-workspace/registry.yaml --initiative <Ixxx>
```

If it fails because integration evidence is absent, generate the handoff exactly once:

```bash
<PYTHON> <FACTORY_ROOT>/skills/hl-feature-workspace/scripts/feature_workspace.py initiative-integration-handoff --registry wiki/feature-workspace/registry.yaml --initiative <Ixxx> --output <initiative-dir>/integration-testing/integration-test-handoff.md
```

Freeze before testing:

- Capture the registry/manifest revision or working-tree identity, the build identity, the runtime
  configuration identity, the state-store identity, and external-dependency session identity where
  applicable.
- Define the acceptance matrix before executing anything. Each row names the user trigger, the
  path actually exercised, the expected durable result, the evidence artefact, and whether it
  blocks PASS.
- Classify every criterion as required for PASS, optional diagnostic, or unavailable external
  observation. Do not silently change a required criterion after a failure.
- A material re-scope of one criterion is a formal decision: the owner authorizes it, the
  authorization is quoted in the frozen run identity, the withdrawn wording is named, the row is
  marked `RE-SCOPED` with the new wording, and the result is reported as a pass of the new wording
  only. Never present a re-scoped row as a pass of the original criterion, and never let one
  decision relax its neighbours — unmentioned rows keep their wording or become `BLOCKED`.
- Revising a Feature's own frozen acceptance text is a second, separate authorization: update the
  Feature's testing or acceptance documents with a dated note naming the authorization and the
  disproving run, keep the original verdict visible and mark the row `REVISED`, and leave the
  lifecycle YAML alone. The earlier acceptance evidence is stale against the revised criterion and
  the revised row stays unverified until something re-executes it on the new contract.
- Define baseline semantics once. When a clean-state run is required, record the pre-run state,
  preserve only explicitly required configuration, establish and verify the clean baseline once,
  and do not repeat destructive resets inside the same run. A reset invalidates prior evidence; it
  does not repair it.
- Landing a fix moves the baseline. Open a new run with a new run id, leave the previous evidence
  root untouched as history, record the predecessor run id in the new run identity, and re-establish
  every row against the new revision. Never carry a prior run's passing rows forward and never
  re-stamp the old root as current. A follow-up run scoped to the repaired Feature alone leaves the
  matrix straddling two revisions; that state cannot be registered — either re-execute the whole
  matrix at the final revision or report the matrix as blocked on that consolidation.
- Create a new immutable evidence root. Do not reseal old Feature evidence as Initiative evidence.
- Re-derive, at the frozen revision, every inherited factual claim a required row depends on.
  Acceptance documents, review and verification reports, and handoff summaries are claims, not
  facts: check the artefact itself and record any divergence as a finding instead of inheriting
  the claim.
- Freeze the evidence-root layout before running: one `frozen/` directory holding the run identity
  and the pre-execution matrix with its own hash manifest, one directory per Feature, plus
  cross-Feature, safety and raw-log areas. Keep the frozen matrix immutable and publish results
  separately so a later reader can prove the criteria were not rewritten after the outcome was
  known. Layout and binding rules: `references/evidence-root-layout.md`.
- Record which observations are current-run evidence, historical capability evidence,
  replay/idempotency evidence, or diagnostic evidence. Only the categories the matrix allows may
  satisfy a criterion.

If a required Feature is not ready, required context is missing, or the handoff cannot be
generated, stop as blocked and report the exact gate. Do not begin exploratory acceptance.

## Phase B: One Integration Run

Execute only the matrix rows, and use the real user-facing or operator-facing path whenever a
criterion names one.

Evidence substitution rules:

- A lower-layer replay may diagnose a failure, but cannot prove a higher-layer entry path, user
  action, end-to-end persistence, or presentation criterion.
- A unit, contract or component test may support a shared contract, but cannot prove cross-Feature
  runtime behaviour.
- A prior successful run may establish historical capability, but cannot prove the current run
  unless the criterion explicitly permits historical evidence.
- A prior-run artefact is admissible only when its recorded revision **and** its recorded worktree
  cleanliness both match the frozen baseline. Evidence produced at a different revision, or on a
  dirty tree, makes the comparison invalid and the row failed; do not re-run only the missing half
  to manufacture agreement. The same holds for a cross-platform pair — mismatched revision, fixture
  hashes, runner identity or runtime version invalidates the comparison even when both results look
  right alone.
- When a required row cannot be executed inside the stated safety boundary, record `BLOCKED` with
  its smallest prerequisite and continue with the independent rows. Do not substitute a nearby
  environment (another port, a developer entry point, a mocked layer) for the named surface and call
  it a pass. A substitute run may be recorded as an explicitly optional diagnostic and can never
  flip a required row.
- A replay, retry or idempotency case proves replay behaviour only. It cannot prove first-run
  behaviour or clean-state ingestion.
- A state-store row, API response, log or internal projection is not presentation evidence.
  Required visual or interaction evidence must come from the required surface, be persisted, and be
  bound to the same run identity with viewport, route, timestamp and relevant state metadata.
- When a criterion spans layers, bind the evidence across layers with a correlation or run
  identifier. Never infer the missing layer from a neighbouring artefact.
- External dependencies must retain source, request scope, completion signal, session identity and
  error or degraded state. A healthy connection returning an empty, partial, stale or unknown-scope
  response is not proof of a complete empty result.
- If an external dependency is required by the criterion and its scope or completeness is unknown,
  the criterion fails or stays blocked. Do not change the product claim after the observation to
  obtain PASS.
- If the product contract explicitly permits degraded external state, record the
  implementation-path result and the external limitation as separate statuses instead of one
  unqualified PASS.
- Never perform irreversible or production-impacting actions unless the matrix explicitly
  authorizes them and the applicable safety policy permits them.

Use delegation for bounded evidence collection only. A delegated agent may inventory, run disjoint
tests, or draft evidence; it may not decide lifecycle state, register integration PASS, authorize a
merge, switch authority, or close the goal. The main session inspects material outputs and makes the
final gate decision.

Default the mechanical legs to subagents and keep this session for coordination, gating and final
verification. Long runs drown the coordinating session in tool output, and a context full of log
tails makes worse gate decisions. Hand the fixing and the disjoint testing to children, run them in
parallel when their file scopes do not overlap, and keep here only the frozen matrix, the acceptance
verdict, the review of each child's diff, and the user-facing report.

Provisioning is the exception: build the environment yourself and hand the child a base that already
answers its health check. A child asked to install a runtime and repair its own toolchain tends to
stall before running a single test, and re-dispatching repeats the same failure.

Disjoint file scopes are not enough when children share one host: they collide on runtime resources.
Partition ports, state-store paths, service names and log directories explicitly in each brief —
otherwise one child's cleanup tears down a sibling's service, and two children initialising the same
store contradict each other's evidence.

Treat every child's completion message as a self-report, including claims like "all tests pass",
"mode fixed", "nothing committed" or "leak removed". Before accepting work that touches the
repository, re-run the decisive query yourself and read the diff. Row ids do not survive delegation:
give each child the exact row ids with criterion text, and map results back by criterion text rather
than by id. Counts a child writes into an acceptance document need re-executing; they are claims
until your own run reproduces them.

An interrupted child runs no cleanup. Stopping one that started services leaves its process still
listening until you sweep the port, the process table and the container list yourself. Do the sweep
before reporting, and never leave a delegated service listening on a network address across a
session break. Then inspect what actually landed before re-dispatching: an interrupted child may
have written complete and valid edits, or nothing at all.

When delegated work moves a real secret out of the codebase (account id, token, key, credential),
require synthetic values in every fixture, comment and docstring, then grep the whole tree for the
real value and require zero hits before accepting. An agent asked to fix a leak will readily paste
the leaked value into a fixture as its expected constant, which converts a runtime leak into a
permanent one in history. Redaction is a multi-surface property, not a patch to one return value:
check every logging path and every passthrough structure, and re-grep the raw value before claiming
the evidence is sanitised.

## Pre-Flight And Verification Techniques

Classify environment blockers before freezing the matrix — port ownership, privilege escalation,
log readability, deployment-root existence — because a handful of read-only checks decides several
rows at once, and finding a blocker after the freeze forces a re-freeze.

Concrete recipes live in `references/preflight-and-verification.md`: dependency extras, proving a
failure is pre-existing, verifying a fix outside the frozen clone, mode-only version-control fixes,
harness availability before promising regeneration, line-ending churn from delegated edits,
read-only release trees, and cross-platform path casing.

## Workflow Anti-Patterns

Before declaring PASS, check for these failure modes:

- Layer substitution: a lower-layer result reported as proof of a higher-layer workflow.
- Evidence borrowing: old, unrelated or differently configured evidence filling a current-run gap.
- Replay confusion: retry, duplicate or idempotency evidence reported as first-run evidence.
- Moving baseline: state reset, partially restored or changed until the result looks favourable.
- Unknown-state laundering: an external dependency's unknown scope, incomplete response or degraded
  status rewritten as success.
- Unbound visuals: screenshots or visual checks not tied to the tested build, state, route, viewport
  or run.
- Gate collapse: implementation acceptance, integration PASS, merge authorization, validator PASS
  and lifecycle closure reported as one action.
- Handoff loop: each subtask emits a new handoff while the same goal continues, creating
  contradictory intermediate "finished" states.

If any anti-pattern is present, keep the affected criterion failed or blocked, explain the evidence
gap, and continue only with a bounded repair or a fresh invalidated run.

## Goal And Handoff Discipline

Maintain one continuous goal: complete the current Initiative integration and, if authorized, merge
it. Subagent completion is an internal event, not a user-facing handoff.

- Do not emit a next-session handoff after every subtask, partial result, retry or diagnostic.
- Do not declare the goal handed off and then continue executing it under the same goal.
- Summarise subagent results into the current acceptance matrix and continue without changing goal
  state.
- Emit one final handoff only when the workflow is complete, blocked, or needs a real user decision
  or authorization.
- Update the existing goal state once when new evidence changes the status; do not create a second
  goal or repeat a completed handoff.
- When waiting on agents, report meaningful changes only; do not narrate unchanged polling.
- A user decision is needed only for a material scope or criterion choice, or explicit merge
  authorization. Tooling retries and ordinary test failures are handled inside the current goal.

## Phase C: Register The Integration Result

After every required matrix row passes, inspect the evidence root and run:

```bash
<PYTHON> <FACTORY_ROOT>/skills/hl-feature-workspace/scripts/feature_workspace.py initiative-integration-result --registry wiki/feature-workspace/registry.yaml --initiative <Ixxx> --evidence <initiative-relative-evidence-file>
<PYTHON> <FACTORY_ROOT>/skills/hl-feature-workspace/scripts/feature_workspace.py initiative-merge-ready --registry wiki/feature-workspace/registry.yaml --initiative <Ixxx>
```

The evidence file must exist inside the Initiative directory, be immutable for this run, and
include:

- run identity and exact environment;
- the Feature and dependency chain covered;
- the acceptance matrix with per-row pass, fail or blocked status;
- exact commands and timestamps;
- cross-Feature contract assertions;
- negative-path and safety/redaction results;
- external source, scope, completion and completeness semantics where applicable;
- visual or interaction evidence references and viewport metadata where required;
- unresolved operational follow-ups that do not change the gate result.

If a required row is failed, blocked or unbound, do not register the result. Keep the Initiative
integration gate failed or blocked and preserve the evidence.

## Phase D: Authorized Wiki Merge

Do not merge merely because `initiative-merge-ready` passes. When
`workflow.merge_requires_authorization` is true, obtain explicit user authorization for the
authority switch after presenting the concrete merge scope and the validation result.

Then hand off to `$hl-wiki-merge` in dependency topological order. For each Feature:

1. Re-check `initiative-merge-ready` and the Feature's `merge-ready --feature` gate.
2. Semantically merge only eligible current documents; retain excluded discussion and agent-profile
   material untouched.
3. Update every affected MOC.
4. Run the complete long-term wiki validator, excluding the feature and quick workspaces.
5. Only after validator PASS perform the retained-history transformation, routing and tombstone
   updates, the authority switch, and the `merged / completed` lifecycle transition.
6. On any semantic conflict or validator failure, stop with the Feature still
   `ready-to-merge / ready`.

Never combine integration PASS registration, merge authorization, semantic content merge, validator
execution and lifecycle closure into one unreviewed action.

## Completion And Blocked Reports

The final report distinguishes:

- Feature gates: ready, or missing with the exact gate.
- Initiative integration: PASS, FAIL or BLOCKED, with one evidence root.
- Wiki merge: not started, in progress or completed, with the validator result.
- External operational follow-ups.
- The exact next action, only if one is genuinely required.

For a blocked run, preserve the goal as blocked and state the smallest prerequisite that would
allow resumption. Do not create a generic handoff while still performing the same work.

Give each prerequisite only the owner can clear as a recommendation, not a menu: the exact command
or action, why it beats the alternatives, and what the gate looks like if they skip it. Arrive at a
scope decision with a recommended choice and its trade-offs already weighed; a list of open options
hands the analysis back to the user, who asked for a decision. Say which residual risks the
recommendation accepts and record each accepted risk next to the relaxed criterion.

Never:

- treat a feasibility review as a substitute for integration acceptance;
- use old evidence to cover an unverified current criterion;
- use a lower-layer replay to claim a higher-layer path, or replay evidence to claim first-run
  behaviour;
- repeat baseline resets without invalidating and restarting the run;
- claim visual or interaction acceptance without persistent, run-bound evidence;
- reinterpret an external unknown, partial, stale or degraded result after the fact to obtain PASS;
- let an agent register PASS or authorize a merge;
- mark wiki authority switched before validator PASS;
- emit repeated handoffs while the same goal is still active.
