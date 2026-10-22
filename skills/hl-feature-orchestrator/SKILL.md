---
name: hl-feature-orchestrator
description: Use when one registered Leaf Feature has completed Code AI profiles and must be implemented through scoped owner subagents with plan approval, a fixed review gate, separate verification and governed lifecycle transitions. Explicit invocation with a feature workspace path or feature ID.
---

# Feature Orchestrator

## Step 0 — Load factory context

Run this before anything else, including reading the request.

1. Resolve `WORK_ROOT`: the git top-level that contains `.factory/`, or the directory that holds `.factory/`. Every path below is relative to it.
2. Read `WORK_ROOT/.factory/local.yaml` (machine-scoped, gitignored) and take:
   - `factory_root` → `FACTORY_ROOT`
   - `python` → `PYTHON`, an interpreter with PyYAML available

   If the file is missing, unreadable, or either value is empty, stop and tell the user to run `$hl-factory-init` (`factory init --work <WORK_ROOT>`). Never guess a checkout path.
3. Read `WORK_ROOT/wiki/governance/workflow-profile.md`. It is generated from `.factory/factory.yaml` and is the only source for project language, layout, owners, commands, verification, gates, security boundaries and packs. If it is missing, or it disagrees with `.factory/factory.yaml`, stop and run `$hl-factory-doctor`; never hand-edit it.
4. Keep these values for the rest of the session:
   - the **owners table** — owner ids, titles, owned paths, profile paths. Owner selection and write-scope enforcement read from here, never from memory.
   - the **commands table** — the only validation commands you may run or cite.
   - `verification.baseline_evidence`, `verification.evidence_root`, `verification.isolated_env`.
   - `workflow.review_required`, `workflow.verification_separate`, `workflow.merge_requires_authorization`, `workflow.max_parallel_features`.
   - `security.forbidden_operations`, `security.sensitive_classes`.
   - `packs.enabled` — whether an optional commit or remote-verify policy exists at all.
   Section titles are rendered in the project document language: locate sections by topic.
5. Run the gates through the engine instead of composing paths:
   ```bash
   <PYTHON> <FACTORY_ROOT>/engine/factory.py doctor --work <WORK_ROOT>
   <PYTHON> <FACTORY_ROOT>/engine/factory.py gate workspace --work <WORK_ROOT>
   ```
   A failing gate blocks dispatch. Do not weaken a gate to make progress; configuration disputes route to `$hl-workflow-governance`.

## Scope

Use this skill only when the user explicitly invokes `$hl-feature-orchestrator` and names a registered Leaf Feature — a feature ID, or the `code-ai/` profile directory of that feature.

If the invocation carries no resolvable feature, ask for it before dispatching any implementation subagent. Never infer a default feature or a default profile folder from another project, the current directory, or memory.

The Feature's Code AI profiles live under its feature root:

```text
wiki/feature-workspace/initiatives/<initiative>/features/<feature>/code-ai/
```

The review gate is the fixed exception and is not discovered dynamically: `wiki/code-ai/review-agent.md`, resolved relative to `WORK_ROOT`. If it is not readable when review is required, stop and report that the review gate cannot run instead of substituting another review profile.

## Source Discovery

At the start of each orchestration task:

1. Resolve the feature root from the user's invocation and confirm it is a Leaf Feature, not an Initiative or a container.
2. List the `*.md` files directly under the feature `code-ai/` directory.
3. Exclude `README.md` from worker candidates.
4. Exclude non-profile drafts only when their own content says they are not agent profiles.
5. Read `code-ai/README.md` when present and treat it as the live routing table.
6. If it is missing or stale, still consider the discovered profiles by reading each relevant one and inferring scope from title, headings and body.
7. Say in the main thread when the routing README looks missing or out of sync.

Do not rely on a hard-coded owner list. New owner profiles become available when they appear in the profile library or the feature `code-ai/` directory. This discovery rule never applies to the review gate.

## Preflight Gate

Before dispatching:

- Resolve the owning `feature.yaml`; reject Initiatives and non-Leaf containers.
- Require phase `code-ai-profiles` completed, a passing Scope Gate, no blocking child, and satisfied dependencies.
- Confirm the owner ids used by the profiles exist in the profile owners table and their write scopes do not overlap.
- Treat `wave` as a scheduling hint only; parallelism is also capped by `workflow.max_parallel_features`.
- Read the authority pages that exist before dispatch: `wiki/00-spec.md`, `wiki/02-file-authority-map.md`, `wiki/03-current-decisions.md`, plus any page covering the touched contract or risk.
- If one of those pages is absent, continue with what exists and mention the gap only when it affects routing, contract safety or validation.

## Main Agent Responsibilities

Own coordination and quality gates:

- Decide whether the task should be split, sequenced, or kept in the main thread.
- Enforce the preflight gate before dispatch.
- Read the minimum required authority and profile sources; fully read only selected profiles.
- Keep documentation decisions ahead of code or contract changes.
- Select the right owner from the owners table.
- Create subagents with narrow scope, explicit allowed files, forbidden files, acceptance criteria and validation expectations.
- Require every implementation subagent to return a plan first and wait for main-agent approval before changing files; batch-approve independent plans when scopes do not overlap.
- Prevent two agents from touching the same files or redefining the same contract unless explicitly sequenced.
- Maintain or update documents before contract, schema, API, state, security, workflow or ownership changes.
- Integrate outputs in the main thread and resolve cross-owner boundaries through documented contracts, not ad hoc edits.
- Run final verification, or state the exact reason a check cannot run.
- Trigger the review gate and the separated verification before claiming completion.
- Report true status: completed, blocked, validation results, remaining risk, decisions needed.

Do not delegate final acceptance. Subagents produce owner work; the main agent decides whether it is integrated and acceptable.

## Owner Selection

Use this order of authority:

1. An explicit user instruction naming a specific owner or profile.
2. Routing guidance in the feature `code-ai/README.md` when present and current.
3. The discovered profile's own content.
4. The owners table in `workflow-profile.md`, then the authority map and current decisions.

When an existing Code AI profile library under `wiki/code-ai/` contains a profile for the owner, reference it (`wiki/code-ai/<owner>-agent.md`) instead of restating its boundaries.

Do not select the reviewer from the feature worker set. Review always uses the fixed review profile.

If a task crosses owner boundaries, document or confirm the shared contract first, then dispatch in a safe order. Prefer one primary owner at a time unless files and contracts are clearly independent.

## Dispatch Protocol

Apply the preflight gate, then send a compact packet:

```text
You are <Owner Agent Name>.
Profile: <path to the selected profile>
Code AI profile directory: <feature code-ai directory>
Wiki root: <wiki root>
Implementation root: <implementation root>
Task objective:
Required startup reads:
- <authority and profile files relevant to this task>
Allowed files:
Forbidden files:
Expected documentation updates:
Acceptance criteria:
Validation commands:
Output required:
1. First reply with a plan only. Do not modify files until the main agent approves.
2. After approval, work only inside the allowed scope.
3. Stop and escalate before changing an API, schema, state, security, workflow, file ownership or published contract not already covered by this packet.
4. Final handoff must include modified files, validation results, doc-sync status, review needs, remaining risks and open questions.
```

Approve, revise or reject the plan before implementation starts, and record the approved file scope in the main thread.

## Monitoring and Stall Handling

Check progress at declared checkpoints, after validation commands, when dependencies complete, and when the main thread resumes.

Check first by reading available artifacts, messages, diffs or declared outputs. Do not interrupt an agent that shows visible progress.

If no progress is visible, ask for a short status:

```text
Status check: I see no recent artifact or handoff. Are you working, blocked, waiting for approval, or uncertain about scope? Reply with current state, last completed step, blocker if any, and next intended action.
```

If the reply shows the subagent is blocked, confused about boundaries, inactive, repeatedly off-scope, or unable to produce a plan or artifact, stop it, summarize the failure mode, preserve useful artifacts, and hand off to a fresh subagent built from the same or a corrected profile. The fresh subagent receives the original task, approved scope, known blockers and usable partial output, and re-plans before editing.

Never let two agents edit overlapping files at once. On handoff, state clearly that the previous subagent is no longer the active owner.

## Documentation and Contract Gate

Documentation precedes contract changes. Before any change to an API, schema, runtime protocol, state model, checkpoint behaviour, permission, safety boundary, plugin contract, file authority or cross-owner workflow:

1. Identify the authoritative wiki document.
2. Update or draft the decision, ADR, open question or contract document first.
3. Only then allow implementation against the updated documented contract.
4. If the decision is not clear enough to document, ask the user or record an open question instead of guessing.

The main agent owns this gate even when a subagent writes the draft.

## Review Gate

For any code or behaviour change, run the fixed review gate before claiming completion:

`wiki/code-ai/review-agent.md`

Resolve it relative to `WORK_ROOT`. Do not replace it with a discovered profile. If it is unreadable and `workflow.review_required` is on, stop and report that the gate cannot run.

Give the review subagent:

- Affected owners
- Changed files
- Contract, API, schema, runtime, state and security implications
- Owner-specific review focus
- Validation already run
- Remaining risk areas

Blocker findings must be fixed and re-reviewed. High-severity findings should be fixed and re-reviewed unless the user explicitly accepts the risk. Warnings and nits are surfaced in the final report.

## Acceptance and Verification Separation

When `workflow.verification_separate` is on, verification runs in a session separate from implementation, and the implementer never accepts its own work. Use `verification.isolated_env` for how isolation is achieved. When it is off, record that the project deliberately weakened the gate; do not describe a self-check as independent verification.

Classify acceptance criteria before implementation. An externally dependent or unprovable item needs an approved evidence mode or a scope decision. Unsupported API or contract conflicts pause the affected work and return to the workbench; keep the goal active.

Evidence lands under `verification.evidence_root`, baseline evidence is compared against `verification.baseline_evidence`, and every criterion is recorded as pass, fail, blocked or not verified.

Git merge, `ready-to-merge / ready`, and long-term wiki authority merge are three separate operations. A git merge requires an explicit request; only `$hl-wiki-merge` changes long-term wiki authority.

## Lifecycle Transitions

Update the owning `feature.yaml` only through the state machine, never by hand-editing `phase`/`state`:

```bash
<PYTHON> <FACTORY_ROOT>/skills/hl-feature-workspace/scripts/feature_workspace.py transition \
  --feature <WORK_ROOT>/wiki/feature-workspace/initiatives/<initiative>/features/<feature>/feature.yaml \
  --phase <phase> --state <state> \
  --next-skill <skill> --next-instruction "<instruction in project.language.docs>" \
  --registry <WORK_ROOT>/wiki/feature-workspace/registry.yaml
```

| Boundary | Phase | State |
| --- | --- | --- |
| Orchestration starts | `implementation` | `in-progress` |
| All approved owner implementation and validation complete | `implementation` | `completed` |
| Fixed review starts | `review` | `in-progress` |
| Review passes after required fixes and re-review | `review` | `completed` |
| Independent acceptance starts | `acceptance` | `in-progress` |
| All acceptance criteria pass and the handoff package is complete | `acceptance` | `completed` |
| Closure gate passes and the Feature is ready to merge | `ready-to-merge` | `ready` |

The final transition is mandatory. Do not leave a successfully implemented and accepted Feature at `code-ai-profiles / completed`, `implementation / completed` or `review / completed`.

At every transition:

1. Preserve all existing required `context_refs`.
2. Add formal references to new implementation, review, verification and acceptance evidence.
3. Set `next_action` to the next workflow skill and a concrete instruction.
4. Run `factory gate workspace --work <WORK_ROOT>` immediately after writing the manifest.
5. If it fails, repair the manifest before continuing; never report a transition as successful from prose alone.

If implementation, review or acceptance is incomplete, failed or not verified, keep the truthful current phase with `in-progress`. Use `blocked` only under the workspace rules. Never mark `acceptance / completed` while any required acceptance item is failing, blocked or unverified.

## Commit Boundary

Commit only when all of the following hold:

- the Feature is at `ready-to-merge / ready`;
- the user explicitly authorized a commit in this session;
- the optional commit pack is enabled in `packs.enabled` — if it is not, follow the project's documented policy and do not invent one.

Do not commit before `ready`. Never push without an explicit instruction. Report the commit result, including its identifier, in the final handoff.

## Final Handoff

The visible handoff is the last step, not a substitute for lifecycle maintenance:

1. Complete implementation, documentation sync, fixed review, main-thread validation and independent acceptance.
2. Build the human-readable acceptance checklist, reproducible steps and remaining-risk section.
3. Confirm every required criterion is passing.
4. Record acceptance evidence and required references in the feature workspace.
5. Advance the manifest to `acceptance / completed` with the correct `next_action`.
6. Run `factory gate workspace --work <WORK_ROOT>` and confirm it passes.
7. Advance to `ready-to-merge / ready` through the closure gate.
8. Commit only if the commit boundary above is satisfied.
9. Then send the final handoff and state the actual completion boundary.

If steps 3-7 do not succeed, send a truthful incomplete or blocked handoff and do not claim completion.

## Acceptance Checklist

Produce the checklist in the user's language, usable without reading subagent transcripts. Match a different language only when the user explicitly asks.

For every requirement or acceptance criterion include:

- Feature ID and a short requirement name.
- What was implemented, and where.
- Preconditions: fixtures, services, accounts, permissions, test data.
- The exact automated command or the manual UI/API procedure.
- The expected observable result.
- The evidence already obtained.
- Status: passing, failing, blocked, or not verified.
- Known limitations, safety boundaries and cleanup steps.

Order entries by dependency and user workflow, not by file path or completion time. Separate automated checks from manual acceptance steps. Never mark a manual step as passed unless it was actually performed.

## Reproducible Acceptance Steps

After the checklist, give a numbered procedure:

1. State the implementation root and required runtime.
2. Start required services with exact commands.
3. Prepare fixtures or safe test data.
4. Run the automated validation commands.
5. Perform the manual, user-visible checks in workflow order.
6. Inspect relevant logs, traces, reports or persisted artifacts.
7. Restore or clean temporary state.
8. State the final pass/fail rule.

Commands must be directly runnable. UI steps name the page, control, input, action and expected result. Where `security.sensitive_classes` or `security.forbidden_operations` apply, preserve the read-only and safety constraints and never imply that a real, irreversible action was tested unless it was explicitly authorized.

## Final Response Order

The final response uses this order:

1. True implementation status.
2. Human-readable acceptance checklist.
3. Reproducible acceptance steps.
4. Remaining risks and anything unverified.

Do not claim completion before all four exist, with evidence and the `ready-to-merge / ready` transition recorded. If a commit was explicitly requested, report its result.
