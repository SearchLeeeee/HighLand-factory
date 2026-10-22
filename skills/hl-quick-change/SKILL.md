---
name: hl-quick-change
description: Handle bounded bugfixes and detail adjustments with a hard-gate scope check, lightweight feasibility review, one-question-at-a-time grilling, repeatable verification, and automatic escalation when the work outgrows the lightweight path.
---

# Quick Change

Use this skill as the single entry point for small maintenance requests. It owns the lightweight
record and the routing decision. It never creates or modifies a second lifecycle state machine.

## Step 0 — Load factory context

1. Read `<work>/.factory/local.yaml`. If missing or unreadable, stop and tell the user to run
   `$hl-factory-init` (or `factory init`); never guess a path or interpreter.
2. Resolve `FACTORY_ROOT` (`factory_root`), `PYTHON` (`python`), and `WORK_ROOT` (the git
   top-level, or the directory containing `.factory/`).
3. Read `wiki/governance/workflow-profile.md` under `WORK_ROOT`. It defines language, layout, the
   quick-workspace root, `workflow.quick_change`, review and verification policy, and security
   boundaries. If it is missing or unreadable, stop and tell the user to run `$hl-factory-doctor`.
4. Run gates through the engine rather than composing paths: `factory gate workspace --work
   <WORK_ROOT>` and `factory gate wiki --work <WORK_ROOT>`.
5. If `workflow.quick_change` is false, do not open this path at all: route the request through
   Initiative intake and decomposition with `$hl-feature-workspace` and `$hl-feature-discuss`.
6. If the profile or config contradicts the request, route to `$hl-workflow-governance` instead of
   improvising.

Fail closed: missing config, missing profile, a failing gate, or an unresolved language policy stops
the skill with one concrete repair instruction.

## Required Reading

At the start of a new request, read:

1. The long-term wiki entry point: `wiki/README.md`.
2. `wiki/feature-workspace/README.md` when judging escalation or handing off to the heavy workflow.
3. The grilling skill for the one-question-at-a-time behaviour.
4. The feasibility or feature-discussion skill only when routing to that heavy workflow.

The quick workspace is process material. Exclude it from long-term memory, default context discovery,
indexes, graph and MOC navigation, and routine wiki searches, exactly as the feature workspace is
excluded. Do not treat a quick record as current system authority.

## Entry And Routing

Create `wiki/quick-workspace/active/<id>.md` immediately at intake, resolving the path from
`WORK_ROOT` and the profile's quick-workspace root. Use an ID such as `quick-YYYYMMDD-###` and
preserve it for the request lifetime.

Run a hard-gate scope check before implementation. Escalate immediately if any of these apply:

- multiple independent business goals, domains, modules, or independently releasable changes;
- data migration, a public or shared API or contract change, a permission or security boundary
  change, or shared infrastructure change;
- a lifecycle, workflow-governance or long-term authority-rule change;
- Initiative-level integration testing, or a change that cannot be proved by local repeatable
  verification;
- unresolved value, behaviour, compatibility or failure semantics that require broad discovery.

If the hard gate is clear, run the lightweight feasibility review. Use a small complexity score as
supporting evidence, never as a waiver for a hard gate. Keep the request lightweight only when it is
one coherent bugfix or adjustment with a bounded file or module surface and local verification.

When escalation is required:

1. Stop lightweight implementation.
2. Complete the record's `Scope Gate`, `Escalation Handoff` and evidence sections.
3. Move the same record from `active/` to `escalated/`.
4. Set `status: escalated`, `scope_verdict: escalate`, and `next_skill` to the feasibility or
   feature-discussion skill.
5. Route technical or value uncertainty first to feasibility review; route an already-understood but
   oversized change to feature discussion; chain them when both conditions apply.

The heavy workflow owns all Initiative and Feature state, Scope Gate re-evaluation, dependency and
wave registration, and subsequent authority decisions. The quick record is a handoff, never a
lifecycle authority.

## Feasibility And Grill

The lightweight feasibility review must cover value and problem reality, available code and data,
impact and compatibility, security, privacy and project-specific risk categories named in the
profile, repeatable testing, rollback and failure handling, and continued lightweight eligibility.

After feasibility is viable, grill the user one question at a time until shared understanding is
reached. Do not impose a fixed number of questions. Even a one-file change enters this gate. Code
inspection and agent inference do not count as user confirmation. Resolve at minimum:

- observed behaviour, reproduction conditions, and desired behaviour;
- exact change points and explicit non-goals;
- affected files, modules and ownership boundaries;
- failure paths, compatibility and rollback behaviour;
- acceptance criteria and repeatable verification commands;
- the intended wiki target domain or document, and residual risks.

If answers reveal a hard-gate condition, stop the grill as a lightweight activity and escalate. Do
not change code before the user and the agent share the same change boundary. If the user has not
answered the current grill question, remain in `grilling`; never proceed on silence or on an assumed
recommendation. The record must identify which required points the user explicitly confirmed and
which were marked not applicable with a reason.

At grill completion, write the required `context_compaction` block into the record, then perform one
context compaction or handoff action when the host supports it. Record a non-empty ISO-8601 timestamp
and the method (`native` or `fixed-block`). If native compaction is unavailable, treat the fixed block
as the mandatory implementation handoff and record that method explicitly. A blank timestamp or an
unrecorded method is a verification failure: remain in `grilling` or `blocked`. The implementation
phase reads the compact block first and uses the full grill record only for audit detail.

## Record Contract

Use `references/quick-record-template.md`. The frontmatter `status` is a document progress marker
only; it is not a replacement for `feature_workspace.py` or any other lifecycle authority.

Allowed `status` values:

`draft`, `grilling`, `ready-for-implementation`, `implementing`, `verification`, `completed`,
`escalated`, `blocked`.

Track `wiki_merge_readiness` separately: `ready`, `needs-target`, or `blocked`. `completed` means
implementation and verification are complete; it does not mean the wiki merge has happened.

Create the record at intake, append decisions and evidence as the work proceeds, and move it to
`completed/` only after verification. Move it to `escalated/` when the heavy workflow takes over.
After `completed` or `escalated`, use append-only addenda; never rewrite the original decision or
evidence. Every terminal record ends with one explicit `Final State` addendum containing the current
`status`, `scope_verdict` and `wiki_merge_readiness`; earlier stale values are superseded there.

## Implementation And Verification

When the user asked for a fix or adjustment, implementation may begin automatically after the grill
compaction handoff. Analysis-only requests stop after discussion.

Every request needs at least one repeatable verification artefact:

- bugfix: a failing reproduction or regression test plus the passing result;
- detail adjustment: a targeted test, static check, or reproducible manual verification;
- interaction change: the viewport and interaction path, with screenshots or equivalent persistent
  evidence when useful;
- documentation or configuration: format, reference, schema or consistency checks;
- environment limitation: the exact steps, environment, observation and residual risk; keep
  `blocked` when the result is not sufficient.

On failure, remain in `verification` or `blocked`. If implementation reveals new scope, stop and
escalate. Never mark `completed` with missing or failed evidence. Use the profile's configured
commands; never invent a command and claim verification.

## Wiki Handoff

Before completion, record at least the target domain and the candidate authoritative document in
`wiki_targets`. If the target is undecided, use `wiki_merge_readiness: needs-target`; do not create a
new authority document in this skill.

The quick skill produces staged source only. A user-authorized wiki update must run through
`$hl-wiki-merge` for the semantic merge, MOC updates, full validation, retained-history handling and
authority switch. A validator failure leaves the staged record intact and does not switch authority.
Escalated requests are merged through the heavy Feature workflow instead of directly from the quick
record. If the merge would require changing a validator, an exclusion rule, a lifecycle rule or any
other governance behaviour, stop the quick change and route that maintenance through
`$hl-workflow-governance`; never modify governance machinery as part of a quick merge.

## Authorization Boundaries

A user request to fix or adjust authorizes ordinary local implementation after the grill handoff. It
does not authorize the wiki merge, commit, push, deletion, broad refactoring, or heavy-workflow
implementation. Obtain the applicable authorization and follow the owning skill for those actions.

## Language

Talk to the user in their language. For any persisted document, use `project.language.docs` when the
profile sets it, otherwise match the user's language. Keep IDs, keys, paths, status values, verdict
labels and skill names in their stable ASCII form.
