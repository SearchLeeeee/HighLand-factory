---
name: hl-feature-profile-generate
description: Use when a Leaf Feature has confirmed conclusions and completed domain implementation documents and needs executable Code AI subagent profiles. Runs automatically after document completion in `$hl-feature-discuss` without another user confirmation, or directly to resume generation. Composes generic constraints by relative-path reference and emits an index plus reading, implementation, review and verification profiles.
---

# Feature Profile Generate

On an initialized work repo run `factory resolve --work <WORK_ROOT> --json`, read `<wiki>/README.md` first, then the current responsibility’s page in `<role_memory>/` if present. Use the returned paths and follow `<FACTORY_ROOT>/skills/hl-workflow-governance/references/wiki-memory.md` for role routing and task experience.

## Questioning Style

All user-facing questions must use Socratic questioning. Before asking, read
`<FACTORY_ROOT>/skills/hl-workflow-governance/references/socratic-questioning.md`
(relative to the located factory checkout during bootstrap). Follow that shared policy for
chat, choice panels and workbench questions; preserve existing explicit authorization gates.

## Step 0 — Load factory context

Run this before anything else, including reading the feature documents.

1. Resolve `WORK_ROOT`: the git top-level that contains `.factory/`, or the directory that holds `.factory/`. Every path below is relative to it.
2. Read `WORK_ROOT/.factory/local.yaml` (machine-scoped, gitignored) and take:
   - `factory_root` → `FACTORY_ROOT`
   - `python` → `PYTHON`, an interpreter with PyYAML available

   If the file is missing, unreadable, or either value is empty, stop and tell the user to run `$hl-factory-init` (`factory init --work <WORK_ROOT>`). Never guess a checkout path.
3. Read `<workflow_profile>`. It is generated from `.factory/factory.yaml` and is the only source for project language, layout, owners, commands, verification, gates, security boundaries and packs. If it is missing, or it disagrees with `.factory/factory.yaml`, stop and run `$hl-factory-doctor`; never hand-edit it.
4. Keep these values for the rest of the session:
   - `project.language.docs` — language of the generated index and profile prose. Never hardcode one.
   - the owners table — owner ids, titles, owned paths, profile paths. Profiles and owner-boundary text must match it.
   - the commands table — the only commands a profile may cite. Never invent a command.
   - `workflow.review_required`, `workflow.verification_separate`, `security.sensitive_classes`.
   Section titles are rendered in the project document language: locate sections by topic.
5. Run the gates through the engine instead of composing paths:
   ```bash
   <PYTHON> <FACTORY_ROOT>/engine/factory.py doctor --work <WORK_ROOT>
   <PYTHON> <FACTORY_ROOT>/engine/factory.py gate workspace --work <WORK_ROOT>
   ```
   A failing gate blocks profile generation. Never write profiles against a failing workspace.

When invoked by the discussion skill in the same session, reuse its loaded context and applicable
successful doctor/gate results. Re-run only checks whose configuration, manifests or checked
sources changed, including the required gate at the profiles-completed boundary. Nested entry
does not require a fresh environment or another approval.

## Purpose

Turn confirmed feature requirements into a set of Code AI profiles that can be handed straight to subagents.

Core principle: **compose by reference, never copy**. Generic constraints — startup order, safety boundaries, doc sync, review gate, maintenance records, README sync, commit granularity, handoff structure — live in `<code_ai>/`. Generated feature profiles reference those documents by relative path and contain only feature-specific business logic, implementation boundaries, test requirements and links to acceptance criteria. Copying a generic block into a feature profile is forbidden because it creates drift.

## Inputs

These must already exist, normally produced by `$hl-feature-discuss`:

- `<feature_workspace>/initiatives/<initiative>/features/<feature>/discussion/workbench.md` — confirmed conclusions, domain classification, test cases, acceptance criteria
- `<feature_workspace>/initiatives/<initiative>/features/<feature>/<domain>/*.md` — domain implementation documents

Before generating anything, verify:

- the owning `feature.yaml` carries a complete five-dimension `consistency_matrix`;
- every dimension has a legal status, a real owner, relative `source_refs` that exist, and long-term wiki `promotion_targets`;
- the workbench summarizes added, preserved, removed or degraded behavior and individually confirms any high-impact removal;
- for behavior, contract or compatibility changes, the relevant current authority documents from `<current topic index linked from the Wiki home>` were checked for semantic conflict and any conflict has a recorded resolution or route;
- the workbench marks visual/interaction impact and, when applicable, names persistent evidence bound to build, route/state and viewport;
- `factory gate workspace --work <WORK_ROOT>` passes.

If the documents are missing or lack executable acceptance criteria, return to the discussion or documents phase. If the matrix is incomplete, stop and repair it through `$hl-feature-workspace`; do not generate profiles against a pending matrix.

## Output Structure

```text
<feature-root>/code-ai/
  README.md                                  # index: profiles, responsibilities, required reading, execution order, handoff expectations
  reading-agent-profile.md                   # optional: only when the touched modules have no prior survey
  <domain>-implementation-agent-profile.md   # one per implementation domain
  review-agent-profile.md
  verification-agent-profile.md
```

The generated `README.md` also states that the orchestrator creates one canonical
`implementation-plan.md` in this directory after surveying the actual code and before any
implementation edit. Do not create an empty or speculative plan during profile generation. The
orchestrator dispatches the completed plan to implementation, review and verification roles.

## Generation Flow

When resuming profile generation in a fresh session, use the resolved Leaf ID for
the read-only recording lookup in `hl-feature-progress/SKILL.md`. When called from
the current discussion, reuse its recording decision and coordinates.

1. Read the workbench and every domain implementation document of the feature.
2. Re-validate the `consistency_matrix`; an incomplete matrix blocks generation.
3. Read the generic library to fix the reference set: `<code_ai>/README.md`, `<project_facts>`, `<code_ai>/subagent-flow.md`, `<code_ai>/review-agent.md`, the relevant `<owner>-agent.md` profile for each domain, and the relevant files under `<code_ai>/_blocks/`. `<code_ai>/_blocks/coding-discipline.md` is always part of that set for implementation and review profiles: it owns the implementation order and the code-quality discipline, and a profile that restates those rules instead of referencing them is a defect.
4. Decide which owners the feature touches, using the profile owners table — never a remembered list of owners. One implementation profile per touched owner/domain.
5. Write each profile with the template below. Write every in-repo reference as a path relative to the work repo root, including the path resolved for `<project_facts>`. Never use an absolute path or a machine token.
6. Write the `code-ai/README.md` index in `project.language.docs`: profile responsibilities, required reading, execution order, handoff expectations and the implementation-plan gate, following the fixed order in `<code_ai>/subagent-flow.md`. State where the orchestrator creates the plan and that no implementation starts before it is ready; do not link a not-yet-created plan file.
7. Self-check against the quality gate below; fix before delivering.

## Profile Template

Every profile uses this skeleton and stays thin — generic content is always a reference:

```markdown
# <Feature> <Role> Agent

## Identity and responsibility
[One sentence: what this agent does in this feature, and what it does not do.]

## Required reading (in order)
1. <resolved Wiki home>
2. <current responsibility’s role-memory page, when present>
3. <current authority pages for the touched topic, reached from the Wiki home>
4. <project_facts>
5. <code_ai>/<owner>-agent.md
6. <code_ai>/subagent-flow.md
7. <feature-root>/discussion/workbench.md
8. <feature-root>/<domain>/<doc>.md
[Add or remove by role; do not list unrelated documents.]

## Feature business boundary
- Target behaviour / explicit non-goals
- Behavior change summary: added, preserved, removed or degraded behavior; individual confirmation for high-impact loss
- Relevant authority documents checked for material behavior, contract or compatibility changes
- Allowed paths / forbidden paths, down to directories or files
- Documents that must be updated first

## Tests and acceptance
- Required test cases, including negative and guardrail cases
- Reference each applicable acceptance criterion by stable ID and relative link to its owning implementation document. Add role-specific checks and evidence steps that follow the criterion without duplicating its pass/fail wording.
- Visual/interaction impact and evidence requirements; if not applicable, the recorded reason
- For page changes, point the frontend implementation, review and verification profiles to the design reference and covered states in the owning criterion. Use the written checks where no mockup was agreed.
- Verification commands taken from the profile commands table — never invented
- Reference the existing plan/handoff's prepared entry points, conditions and remaining checks; do not copy local configuration or create a second environment inventory.

## Handoff
- Reading and verification agents use the fixed handoff structure in <code_ai>/subagent-flow.md
- Implementation agents use <code_ai>/_blocks/handoff-output.md, including the review-gate summary
- Keep material observations in the role handoff and check README impact per <code_ai>/_blocks/agent-notes-rule.md and <code_ai>/_blocks/readme-sync-rule.md.
- Carry critical sourced constraints, evidence scope/identity/continuation entry and required unverified work through those existing handoffs. A source replacement updates the affected plan and acceptance mapping; rebuilding a scenario does not by itself prove original-chain continuation.

## Plan Gate
- The orchestrator supplies the current canonical Feature implementation plan and assigns a plan item before implementation, review or verification.
- Implementation agents change only the files and behaviour assigned by that plan item; they stop if the plan is missing or no longer matches the task.
- Review and verification agents use the same current plan to check implementation scope, integration points and acceptance evidence.
```

## Role Differences

**Reading agent profile** — reports observations from its assigned module paths and focus points in the fixed reading handoff and leaves source files untouched. Generate only when a source investigation is needed and no applicable survey covers it.

**Implementation agent profile** — one per domain. It references the matching owner profile for boundaries and review focus, and writes only the feature's business logic, file-level allowed and forbidden scope, TDD order, mandatory test list and references to acceptance criteria. It requires the current approved plan and limits work to its assigned plan item. The TDD order is stated in the feature's own terms but derives from `<code_ai>/_blocks/coding-discipline.md`; the profile references that block rather than restating its rules. Definition of done references `<code_ai>/_blocks/common-definition-of-done.md` plus feature-specific additions.

**Review agent profile** — must state this seven-step procedure:

1. Read the feature profile, domain documents and relevant authority documents — including the behavior-change summary, any resolved authority conflict, and acceptance criteria.
2. Read the generic constraints: `<code_ai>/review-agent.md` and the affected owner profile's review focus.
3. Read the current canonical implementation plan and verify the reviewed work matches its approved scope, dependencies and integration points.
4. Check the target Git revision, relevant diff/new files and source scope. The orchestrator checks affected-source freshness before accepting the report. Separate hashes, receipts, freeze commits or clones are not defaults; never claim review of different or unidentified changes.
5. Check the change against business requirements and acceptance criteria, including any individually confirmed high-impact behavior loss.
6. Check that the handoff captures material observations and whether a README needs syncing. Do not require fixed source-file headers or per-file notes.
7. Check test coverage including negative and guardrail cases, that verification commands were actually run, that any required visual/interaction evidence is bound to build/state/viewport, and that `security.sensitive_classes` boundaries are preserved.

The output follows the format in `<code_ai>/review-agent.md`, including the doc-sync review. Findings must be actionable: file or area, why, required fix.

**Verification agent profile** — judges independently, separate from the implementer: use the same current plan and cover every criterion with sufficient applicable evidence. Execute missing or affected configured checks and independently assess the source/conditions of any reused results; do not accept the implementer's self-assessment as proof. Reuse suitable environments and caches, isolate state/data/processes as required, and do not default to fresh clones, all-command reruns or layered hashes. Apply `<FACTORY_ROOT>/skills/hl-workflow-governance/references/execution-preparation.md`: safe preparation may start early, final acceptance waits for required review to pass, and prepared resources are not acceptance evidence. Record actual results, limits, provenance and documentation sync in the existing handoff. Repair gaps locally, preserve failure facts and stop at the delivery boundary; no extra configuration or approval process.

## Quality Gate

All seven must hold before delivery:

- [ ] Every reference path in every profile resolves to a file that exists.
- [ ] No block or generic profile content was pasted into a feature profile.
- [ ] Generic constraints and feature content are cleanly separated: each constraint is either feature-specific or a relative-path reference.
- [ ] Each profile is directly executable: identity, required reading, boundary, tests, acceptance and handoff are all present; no empty section, no placeholder.
- [ ] Handoff observations, README sync, test and verification, and commit granularity requirements are all present via reference.
- [ ] Implementation and review profiles reference `<code_ai>/_blocks/coding-discipline.md` instead of restating its rules.
- [ ] `code-ai/README.md` lists every profile, the execution order, handoff expectations and the plan gate; profiles require the orchestrator-supplied plan without linking to a file that does not exist yet.

## Orchestration Boundary

Profiles describe owner scope only. The implementation plan, preflight, goal and lifecycle state belong to `$hl-feature-orchestrator` and the generic flow. Until work is complete, a handoff may only report `in-progress`, `blocked` or `not verified`.

## Relationship to Other Skills

`$hl-feature-discuss` owns the discussion phase and the domain implementation documents. When documents are complete and the workspace gate passes, it invokes this skill automatically in the same session. The discussion-completion confirmation already covers profile generation; do not request document approval, another phase confirmation or a separate user invocation. A direct invocation may resume generation from existing valid inputs. Honor an explicit documents-only scope or pause instruction. Do not maintain two sets of profile-generation rules across skills.

## Session Boundary

Discussion and code implementation never share a session, so this skill ends the discussion session.

- When generation finishes, the owning Feature must record `code-ai-profiles / completed` through `$hl-feature-workspace`, and `factory gate workspace --work <WORK_ROOT>` must pass.
- Then follow `$hl-feature-discuss` `## Handoff Prompt`, including its Leaf handoff commit checkpoint. The coordinating discussion agent owns the checkpoint and prompt in a nested call. On direct resume, complete the same steps here. Emit exactly one copyable prompt. Carry forward explicit permission to start the session with any applicable model/reasoning preference. Never dispatch before profiles are completed and the workspace gate passes.
- Do not start implementation, dispatch an implementation subagent, run review or run acceptance here, even when the profiles are complete and the code change looks small.
