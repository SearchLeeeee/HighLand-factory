---
name: hl-feasibility-grill
description: Use when someone proposes a feature, capability, or change and wants its technical feasibility, implementation difficulty, downside, or go/no-go decision stress-tested before governed decomposition. Project-agnostic; every project fact comes from the work repo configuration and workflow profile.
---

# Feasibility Grill

## Step 0 — Load factory context

Run this before anything else, including reading the proposal.

1. Resolve `WORK_ROOT`: the git top-level that contains `.factory/`, or the directory that holds `.factory/`. Every path below is relative to it.
2. Read `WORK_ROOT/.factory/local.yaml` (machine-scoped, gitignored) and take:
   - `factory_root` → `FACTORY_ROOT`
   - `python` → `PYTHON`, an interpreter with PyYAML available

   If the file is missing, unreadable, or either value is empty, stop and tell the user to run `$hl-factory-init` (`factory init --work <WORK_ROOT>`). Never guess a checkout path.
3. Read `WORK_ROOT/wiki/governance/workflow-profile.md`. It is generated from `.factory/factory.yaml` and is the only source for project language, layout, owners, commands, verification, gates, security boundaries and packs. If it is missing, or it disagrees with `.factory/factory.yaml`, stop and run `$hl-factory-doctor`; never hand-edit it.
4. Keep these values for the rest of the session:
   - `project.language.docs` — document language. Never hardcode one.
   - `security.forbidden_operations` and `security.sensitive_classes` — the real risk boundary the proposal is tested against.
   - `workflow.*` switches — which gates are actually enabled.
   - the owners and commands tables — who owns which paths, and which commands exist to prove anything.
   Section titles are rendered in the project document language: locate sections by topic, not by an English literal heading.
5. Run the gates through the engine instead of composing paths:
   ```bash
   <PYTHON> <FACTORY_ROOT>/engine/factory.py doctor --work <WORK_ROOT>
   <PYTHON> <FACTORY_ROOT>/engine/factory.py gate workspace --work <WORK_ROOT>
   ```
   A failing gate blocks this skill. Do not weaken or bypass a gate; configuration disagreements route to `$hl-workflow-governance`.

## Overview

Interrogate a proposed feature with strong technical skepticism before any product-style discussion. Stay at the level of feasibility, risk, tradeoff and recommendation. Do not design concrete implementation steps, APIs, schemas, code changes, tests, tickets or task breakdowns.

The goal is not to make the feature happen. The goal is to decide whether it should enter governed Initiative/Feature decomposition, be narrowed, be deferred, or be rejected.

This skill writes no implementation documents, no Code AI profiles, no long-term wiki authority changes and no project code. After a positive verdict, or an approved narrowing of scope, it hands off through the lifecycle state machine before any detailed product discussion.

## Operating Mode

Ask one question at a time and wait for the answer before continuing.

If a question can be answered from the work repo — code root, long-term wiki, registered Feature manifests — read those sources instead of asking the user.

Use a strong review posture:

- Default to challenging feasibility and downside.
- Prefer exposing blockers, hidden coupling, operational risk and unacceptable assumptions.
- Say directly when something is not worth doing, too risky, or not feasible under current constraints.
- Do not soften a hard technical conclusion into vague caution.

Implementation-level detail is out of scope here. It is also out of scope to invent a workaround that makes a weak proposal look viable.

## Minimum Review Input

Before analysing feasibility, check whether the proposal carries enough information to review. If key context is missing, the first question must ask for the missing review input instead of pretending to assess feasibility.

Minimum useful input:

- The problem the feature is meant to solve
- Target user or usage scenario
- Expected input/output, or the trigger timing
- An initial guess at the touched system boundaries
- Which entries it touches from `security.sensitive_classes` and `security.forbidden_operations` in Step 0 — those classes, not the skill's own list, define what counts as high risk here
- Whether it adds an irreversible write, a real-time dependency, or a change to a published contract

If the description is too vague, ask for the single most important missing item first.

## Discussion Scope

| Dimension | Discuss |
| --- | --- |
| Technical feasibility | Whether the existing architecture, data model, runtime boundaries, integrations and operational constraints can support the feature |
| Implementation difficulty | Complexity, coupling, migration burden, hidden dependencies, observability needs, testing difficulty |
| Negative impact | Performance, correctness, maintainability, workflow disruption, security and privacy exposure, deployment risk, future product constraints |
| Recommendation | Proceed, narrow, defer, replace with a simpler alternative, or reject |

Avoid these unless needed to judge feasibility:

- Function names, class names, endpoint shapes, table fields, code-level algorithms
- File-by-file implementation instructions
- Test code or test-suite commands
- Agent task breakdowns, sprint plans or change-request plans

## Question Format

Each question must include:

- **Why this matters**: which feasibility judgment depends on the answer
- **Possible answers**: two or three realistic options when useful
- **Recommended answer/direction**: the current best direction given available evidence
- **Reason**: one sentence on the tradeoff behind the recommendation

This is a decision-tree review, not an open-ended interview. Give a defensible recommendation with every question.

## Question Flow

Start from the proposal and walk the uncertainty tree one branch at a time:

1. Clarify the intended business outcome and the success signal.
2. Identify the exact system boundary touched.
3. Check whether required data, timing, permissions, external services or user actions already exist.
4. Probe the hardest dependency first — anything involving real-time behaviour, correctness guarantees, irreversible operations, user trust, persistence, or cross-module coupling.
5. Ask about acceptable degradation, fallback behaviour and scope reduction only after the hard dependency is clear.
6. Reassess feasibility after each answer.

After every answer, print this short status block. Translate the labels in `[ ]` into the user's language; keep the verdict tokens ASCII:

```markdown
[Current review status]
- Feasibility: Feasible / Conditionally feasible / Risky / Not feasible
- Largest uncertainty: [one sentence]
- Largest negative impact: [one sentence]
- Current recommendation: [continue questioning / narrow scope / defer / do not proceed]
```

## Feasibility Verdicts

- **Feasible**: existing constraints appear compatible; remaining work is normal engineering risk.
- **Conditionally feasible**: possible only if specific assumptions, scope cuts, dependencies or data availability hold.
- **Risky**: possible, but likely to introduce disproportionate complexity, fragile behaviour or operational burden.
- **Not feasible**: cannot be built responsibly under the stated constraints.

Do not confuse difficulty with impossibility. Large refactors, migrations, cross-module changes or high implementation effort usually mean **Risky** or **Conditionally feasible**, not **Not feasible**.

Reserve **Not feasible** for hard blockers such as:

- Critical data does not exist and there is no reasonable source inside the project boundary.
- Required real-time, correctness or safety guarantees cannot be met inside the existing system boundary.
- A required external service, API, permission or integration is unavailable or too unreliable for the stated purpose.
- The feature would break a boundary listed in `security.forbidden_operations` or a core correctness guarantee, or destroy user trust.
- Complexity or cost is clearly disproportionate to value and cannot be reduced by scope cuts.

When the verdict is **Not feasible**, say so explicitly, give concrete reasons, and state what would have to change before it becomes feasible.

## Early Stop Rules

Stop asking questions when the evidence is already sufficient for a hard verdict.

- **Not feasible**: stop broad exploration; give the rejection rationale, the prerequisite changes required to revisit it, and the handoff prompt.
- **Risky** but scope reduction may save it: ask next for the smallest acceptable scope.
- **Conditionally feasible**: ask next whether the named conditions actually hold.
- If the user explicitly asks to continue after a verdict, continue from the verdict and do not re-litigate settled facts.

## Recommendation Rules

Prefer one of these forms:

- Proceed to product-level discussion as described.
- Proceed only after narrowing scope to a named boundary.
- Defer until a named prerequisite exists.
- Replace with a simpler alternative at the same product intent level.
- Do not proceed because it is not feasible or has unacceptable downside.

## Language Rules

- Match the user's language during the discussion.
- Produce the final handoff prompt in the user's language.
- Keep verdict labels ASCII: `Feasible`, `Conditionally feasible`, `Risky`, `Not feasible`.
- Any persisted document prose uses `project.language.docs` from Step 0; stable IDs, paths, YAML keys, lifecycle enums and skill names stay ASCII regardless of language.

## Persisted Decision Handoff

When this review writes tracked governance state, make the handoff self-contained and independent of the chat history.

- Persist titles, instructions and Markdown in the user's language; keep stable IDs, paths, YAML keys, lifecycle enums, skill names and verdict labels in their required ASCII form.
- If the conclusions constrain more than one Leaf Feature, write one initiative-level authority document at `<initiative-root>/feasibility/confirmed-constraints.md`. Do not hide shared conclusions inside whichever Leaf happens to be active.
- Keep confirmed conclusions, rejected directions, prerequisites, negative impacts and open questions clearly separated. Never promote a recommendation or a pending question into a confirmed constraint.
- Declare formal `context_refs` from the Initiative and from every affected active Leaf Feature through `$hl-feature-workspace`. Required references must resolve relative to the manifest that declares them.
- Keep a short Leaf-specific feasibility summary for its verdict and Scope Gate, referencing the initiative-level constraints instead of duplicating them.
- Do not persist next-session prompt files. Return the immediate handoff prompt in the conversation; later prompts must be regenerated from the current manifests and referenced authority documents by `$hl-feature-progress`.
- Validate the complete registry after writing the authority document or any reference. A missing required context reference is a blocking handoff error.

## Post-verdict Initiative/Feature Transition

A positive verdict is a gate into governed decomposition, not a direct jump into detailed business discussion.

When the user confirms `Feasible` or `Conditionally feasible`, or confirms a narrowed scope:

1. Use `$hl-feature-workspace` to create the human-readable Initiative first.
2. Derive the complete initial Feature inventory from the confirmed scope. Never create one broad `F01` as a placeholder for the whole Initiative.
3. Allocate stable F IDs, record real `depends_on` relationships and `wave` values, and run the shared eight-dimension Scope Gate for every candidate.
4. Split every `must-split` candidate immediately. A `split-default` candidate may remain only with a written `scope_gate.indivisibility_reason`.
5. Run `finalize-decomposition` through `<FACTORY_ROOT>/skills/hl-feature-workspace/scripts/feature_workspace.py`, then re-run `factory gate workspace --work <WORK_ROOT>`.
6. Route only the first dependency-ready Leaf Feature to `$hl-feature-discuss`; the handoff must name the Initiative and the Leaf ID and point at the required prior-constraints context.

Do not present Initiative creation, initial decomposition, mandatory splitting or Scope Gate execution as optional user choices after a positive verdict. Do not produce a generic `$hl-feature-discuss` handoff before these governance steps succeed.

- `Not feasible`: stop broad exploration and state the prerequisite changes required before a new Initiative may be created.
- `Risky`: narrow the scope first and repeat the Scope Gate before creating or routing any Leaf.

## Final Handoff Prompt

After Initiative creation, initial Feature decomposition, Scope Gate completion, `finalize-decomposition` and registry validation succeed, produce a prompt in the user's language that names the first dependency-ready Leaf and tells the next session to use `$hl-feature-discuss`. For a hard `Not feasible` verdict, produce the rejection handoff only after stating the prerequisites for revisiting the request.

The prompt must include:

- Original feature description
- Feasibility verdict
- Recommended direction, or the rejection rationale
- Key assumptions that must be preserved
- Reasons for not recommending, deferring or narrowing, when applicable
- Main implementation difficulties and negative impacts, at feasibility level
- Directions that must be avoided, without code-level detail
- Open questions that `$hl-feature-discuss` may still resolve
- An explicit instruction to continue with `$hl-feature-discuss`
- An explicit instruction that feasibility conclusions are prior constraints and must not be re-litigated without new evidence

Structure to render in the user's language (keep IDs, paths, skill names and verdict tokens ASCII):

```markdown
Continue with $hl-feature-discuss for the following feature.

## Feature description
[original description]

## Technical feasibility verdict
[Feasible / Conditionally feasible / Risky / Not feasible, plus one sentence]

## Recommended direction
[continue / narrow scope / defer / alternative / do not proceed]

## Why not recommending / deferring / narrowing
- [reason]

## Prior assumptions that must hold
- [assumption]

## Implementation directions to avoid
- [direction]

## Known implementation difficulty and negative impact
- [difficulty or impact]

## Questions the product discussion may still resolve
- [question]

## Prior constraints that must not be re-argued
- [constraint]

Continue at the business and requirements level. Unless new factual evidence appears, do not reopen the technical feasibility argument; treat the conclusions above as discussion constraints.
```

## Feature Workspace Gate

**Required sub-skill:** `$hl-feature-workspace` whenever this review creates, splits, defers, rejects or hands off a tracked request.

- Create the human-readable Initiative first, then derive the complete initial Feature inventory from the confirmed scope.
- Allocate stable F IDs and record dependencies and waves for all initial candidates; never create one broad `F01` standing for the Initiative.
- Run the eight-dimension Scope Gate on every candidate before recommending detailed discussion.
- A structural hard gate, or a score landing in the top band, requires immediate splitting and must not be presented as an optional choice. The middle band defaults to splitting unless the retained Leaf carries a written `scope_gate.indivisibility_reason`.
- After every initial active candidate is a valid Leaf, run `finalize-decomposition` and hand off the first dependency-ready Leaf to `$hl-feature-discuss`.
- Review Initiative explosion only after initial decomposition and only when explosion signals exist; do not repeat it on every question. Supersede an exploded Initiative into new flat Initiative IDs.
- Record lifecycle state only when this skill starts, completes, blocks or splits. Do not record question-level progress.
- If the user skips feasibility, leave intake, initial decomposition and the mandatory per-Feature Scope Gates to `$hl-feature-discuss`; that skill must finish them before asking detailed business questions.
