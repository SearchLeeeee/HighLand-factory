---
name: hl-feature-profile-generate
description: Use when a Leaf Feature's conclusions and domain implementation documents are confirmed and directly executable Code AI subagent profiles are needed under the feature workspace. Composes generic constraints from the code-ai profile library by relative-path reference, adds feature-specific boundaries, tests and acceptance criteria, and emits an index plus reading, implementation, review and verification profiles.
---

# Feature Profile Generate

## Step 0 — Load factory context

Run this before anything else, including reading the feature documents.

1. Resolve `WORK_ROOT`: the git top-level that contains `.factory/`, or the directory that holds `.factory/`. Every path below is relative to it.
2. Read `WORK_ROOT/.factory/local.yaml` (machine-scoped, gitignored) and take:
   - `factory_root` → `FACTORY_ROOT`
   - `python` → `PYTHON`, an interpreter with PyYAML available

   If the file is missing, unreadable, or either value is empty, stop and tell the user to run `$hl-factory-init` (`factory init --work <WORK_ROOT>`). Never guess a checkout path.
3. Read `WORK_ROOT/wiki/governance/workflow-profile.md`. It is generated from `.factory/factory.yaml` and is the only source for project language, layout, owners, commands, verification, gates, security boundaries and packs. If it is missing, or it disagrees with `.factory/factory.yaml`, stop and run `$hl-factory-doctor`; never hand-edit it.
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

## Purpose

Turn confirmed feature requirements into a set of Code AI profiles that can be handed straight to subagents.

Core principle: **compose by reference, never copy**. Generic constraints — startup order, safety boundaries, doc sync, review gate, agent notes, README sync, commit granularity, handoff structure — live in `wiki/code-ai/`. Generated feature profiles reference those documents by relative path and contain only feature-specific business logic, implementation boundaries, test requirements and acceptance criteria. Copying a generic block into a feature profile is forbidden because it creates drift.

## Inputs

These must already exist, normally produced by `$hl-feature-discuss`:

- `wiki/feature-workspace/initiatives/<initiative>/features/<feature>/discussion/workbench.md` — confirmed conclusions, domain classification, test cases, acceptance criteria
- `wiki/feature-workspace/initiatives/<initiative>/features/<feature>/<domain>/*.md` — domain implementation documents

Before generating anything, confirm:

- the owning `feature.yaml` carries a complete five-dimension `consistency_matrix`;
- every dimension has a legal status, a real owner, relative `source_refs` that exist, and long-term wiki `promotion_targets`;
- `factory gate workspace --work <WORK_ROOT>` passes.

If the documents are missing or acceptance criteria are unconfirmed, return to the discussion or documents phase. If the matrix is incomplete, stop and repair it through `$hl-feature-workspace`; do not generate profiles against a pending matrix.

## Output Structure

```text
<feature-root>/code-ai/
  README.md                                  # index: profiles, responsibilities, required reading, execution order, handoff expectations
  reading-agent-profile.md                   # optional: only when the touched modules have no prior survey
  <domain>-implementation-agent-profile.md   # one per implementation domain
  review-agent-profile.md
  verification-agent-profile.md
```

## Generation Flow

1. Read the workbench and every domain implementation document of the feature.
2. Re-validate the `consistency_matrix`; an incomplete matrix blocks generation.
3. Read the generic library to fix the reference set: `wiki/code-ai/README.md`, `wiki/code-ai/project-facts.md`, `wiki/code-ai/subagent-flow.md`, `wiki/code-ai/review-agent.md`, the relevant `<owner>-agent.md` profile for each domain, and the relevant files under `wiki/code-ai/_blocks/`.
4. Decide which owners the feature touches, using the profile owners table — never a remembered list of owners. One implementation profile per touched owner/domain.
5. Write each profile with the template below. Every in-repo reference is a relative path from the work repo root, for example `wiki/code-ai/project-facts.md`. Never use an absolute path or a machine token.
6. Write the `code-ai/README.md` index in `project.language.docs`: profile responsibilities, required reading, execution order and handoff expectations, following the fixed order in `wiki/code-ai/subagent-flow.md`.
7. Self-check against the quality gate below; fix before delivering.

## Profile Template

Every profile uses this skeleton and stays thin — generic content is always a reference:

```markdown
# <Feature> <Role> Agent

## Identity and responsibility
[One sentence: what this agent does in this feature, and what it does not do.]

## Required reading (in order)
1. wiki/00-spec.md
2. wiki/02-file-authority-map.md
3. wiki/03-current-decisions.md
4. wiki/code-ai/project-facts.md
5. wiki/code-ai/<owner>-agent.md
6. wiki/code-ai/subagent-flow.md
7. <feature-root>/discussion/workbench.md
8. <feature-root>/<domain>/<doc>.md
[Add or remove by role; do not list unrelated documents.]

## Feature business boundary
- Target behaviour / explicit non-goals
- Allowed paths / forbidden paths, down to directories or files
- Documents that must be updated first

## Tests and acceptance
- Required test cases, including negative and guardrail cases
- Acceptance criteria as observable pass/fail
- Verification commands taken from the profile commands table — never invented

## Handoff
- Reading and verification agents use the fixed handoff structure in wiki/code-ai/subagent-flow.md
- Implementation agents use wiki/code-ai/_blocks/handoff-output.md, including the review-gate summary
- Code changes maintain agent notes and READMEs per wiki/code-ai/_blocks/agent-notes-rule.md and wiki/code-ai/_blocks/readme-sync-rule.md
```

## Role Differences

**Reading agent profile** — given a scope (list of module paths) and focus points; may add or update agent notes, must not change business logic; produces the fixed reading handoff. Generate only when the touched modules have no prior survey or agent notes are missing.

**Implementation agent profile** — one per domain. It references the matching owner profile for boundaries and review focus, and writes only the feature's business logic, file-level allowed and forbidden scope, TDD order, mandatory test list and acceptance criteria. Definition of done references `wiki/code-ai/_blocks/common-definition-of-done.md` plus feature-specific additions.

**Review agent profile** — must state this six-step procedure:

1. Read the feature profile and the domain documents — the requirements and acceptance criteria.
2. Read the generic constraints: `wiki/code-ai/review-agent.md` and the affected owner profile's review focus.
3. Check the change against the business requirements and acceptance criteria.
4. Check that agent notes for modified files are maintained.
5. Check whether a README needs syncing and was synced.
6. Check test coverage including negative and guardrail cases, that the verification commands were actually run, and that risk boundaries from `security.sensitive_classes` are preserved.

The output follows the format in `wiki/code-ai/review-agent.md`, including the doc-sync review. Findings must be actionable: file or area, why, required fix.

**Verification agent profile** — independently re-verifies, separate from the implementer: walk every acceptance criterion, re-run the verification commands, check handoff completeness and documentation sync, and produce the fixed verification handoff. It must not reuse the implementer's self-assessment.

## Quality Gate

All six must hold before delivery:

- [ ] Every reference path in every profile resolves to a file that exists.
- [ ] No block or generic profile content was pasted into a feature profile.
- [ ] Generic constraints and feature content are cleanly separated: each constraint is either feature-specific or a relative-path reference.
- [ ] Each profile is directly executable: identity, required reading, boundary, tests, acceptance and handoff are all present; no empty section, no placeholder.
- [ ] Agent notes, README sync, test and verification, and commit granularity requirements are all present via reference.
- [ ] `code-ai/README.md` lists every profile, the execution order and the handoff expectations.

## Orchestration Boundary

Profiles describe owner scope only. Preflight, goal, lifecycle state and commit timing belong to `$hl-feature-orchestrator` and the generic flow. Until work is complete, a handoff may only report `in-progress`, `blocked` or `not verified`.

## Relationship to Other Skills

`$hl-feature-discuss` owns the discussion phase and the domain implementation documents. Once the user confirms the profile phase, generation follows this skill. Do not maintain two sets of profile-generation rules across skills.
