---
name: hl-feature-discuss
description: Use when exactly one dependency-ready Leaf Feature is ready to be refined into confirmed conclusions, domain implementation documents and executable Code AI profiles inside the feature workspace. Reuses explicitly chosen, applicable discussion and development preferences; automatically continues from completed documents to profile generation without another user confirmation, advances lifecycle state only at skill boundaries and hands off to `$hl-feature-orchestrator` in a new session, because discussion and code implementation never share a session.
---

# Feature Discuss

On an initialized work repo run `factory resolve --work <WORK_ROOT> --json`, read `<wiki>/README.md` first, then the current responsibility’s page in `<role_memory>/` if present. Use the returned paths and follow `<FACTORY_ROOT>/skills/hl-workflow-governance/references/wiki-memory.md` for role routing and task experience.

## Questioning Style

All user-facing questions must use Socratic questioning. Before asking, read
`<FACTORY_ROOT>/skills/hl-workflow-governance/references/socratic-questioning.md`
(relative to the located factory checkout during bootstrap). Follow that shared policy for
chat, choice panels and workbench questions; preserve existing explicit authorization gates.

## Step 0 — Load factory context

Run this before anything else, including reading the feature request.

1. Resolve `WORK_ROOT`: the git top-level that contains `.factory/`, or the directory that holds `.factory/`. Every path below is relative to it.
2. Read `WORK_ROOT/.factory/local.yaml` (machine-scoped, gitignored) and take:
   - `factory_root` → `FACTORY_ROOT`
   - `python` → `PYTHON`, an interpreter with PyYAML available

   If the file is missing, unreadable, or either value is empty, stop and tell the user to run `$hl-factory-init` (`factory init --work <WORK_ROOT>`). Never guess a checkout path.
3. Read `<workflow_profile>`. It is generated from `.factory/factory.yaml` and is the only source for project language, layout, owners, commands, verification, gates, security boundaries and packs. If it is missing, or it disagrees with `.factory/factory.yaml`, stop and run `$hl-factory-doctor`; never hand-edit it.
4. Keep these values for the rest of the session:
   - `project.language.docs` — language of the implementation documents you will write. Never hardcode one.
   - the owners table — the real implementation domains of this project.
   - the commands table — the only commands you may cite as verification.
   - `workflow.scope_gate.*`, `workflow.review_required`, `workflow.verification_separate`.
   Section titles are rendered in the project document language: locate sections by topic, not by an English literal heading.
5. Run the gates through the engine instead of composing paths:
   ```bash
   <PYTHON> <FACTORY_ROOT>/engine/factory.py doctor --work <WORK_ROOT>
   <PYTHON> <FACTORY_ROOT>/engine/factory.py gate workspace --work <WORK_ROOT>
   ```
   A failing gate blocks this skill. Do not weaken a gate to keep discussing; lifecycle repairs go through `$hl-feature-workspace`.

For nested skills in the same session, reuse loaded context and successful doctor/gate results
only while their relevant inputs remain unchanged. A new skill name alone is not a reason to
repeat preparation. Required gates after configuration, source or lifecycle changes still run.

## Purpose

Turn one registered Leaf Feature into a durable feature workspace: a conclusion-only workbench, then domain implementation documents, then executable Code AI profiles.

The core pattern is: verify that the parent Initiative's initial Feature decomposition is finalized, take exactly one dependency-ready Leaf Feature, classify its domains, list every known question before detailed questioning, resolve applicable discussion and parallel development preferences, confirm conclusions, derive the acceptance scope and consolidate the workbench at discussion wrap-up, ask for explicit confirmation that discussion is complete, then write the implementation documents in `project.language.docs`, automatically finish the profile phase through `$hl-feature-profile-generate` without another user confirmation, and hand off to `$hl-feature-orchestrator` in a new session.

Discussion and code implementation never share a session. This session owns the workbench, the domain implementation documents and the Code AI profiles; it never writes application code, never dispatches owner implementation subagents, and never runs review or acceptance.

## Discussion Mode (resolve before detailed questions)

After Step 0, confirm the single Leaf target. For a fresh request such as “继续 F02 的讨论”,
resolve its full ID from the validated registry and perform the read-only flow lookup in
`hl-feature-progress/SKILL.md` for that target. Reuse a lookup already performed for this
request. A match resumes the existing recording using its returned records root; a miss
continues normally. This lookup also applies when discussion was invoked directly.

Resolve the discussion mode before
writing detailed questions or conclusions. Prefer the current workbench's recorded choice. If
absent, inherit a mode the user explicitly chose for the same Initiative when that choice is
available in a formally referenced workbench or authorized handoff. State its source and continue;
do not re-ask merely because this is another Leaf. Without an explicit recorded choice, ask one
startup question:

- **Interactive (default)** — one decision at a time, highest implementation impact first. Best for ambiguous, security-sensitive or contract-changing features.
- **Batch review** — write the complete initial question inventory and detailed question blocks into `discussion/workbench.md` in one pass, let the user answer, accept or defer them in bulk, then process the batch and continue with another batch or switch to interactive for the remaining high-risk items.

When a choice is needed, use the structured choice panel when the platform provides one; otherwise ask one concise question with these two options and allow a custom answer. Retain the selected or inherited choice and its source in the conversation and include it under `## Discussion mode` at the next workbench save. The user may change it at any time. A mode preference never supplies product decisions or authorization.

Both modes are equal in rigor: the same inventory, the same confirmation rule, the same phase gates and the same lifecycle transitions. Batch mode changes the interaction order, not the evidence standard.

### Batch review rules

- Write every known question before asking the user to review; each block carries context, one
  neutral Socratic question, the assumption or evidence being examined, implementation impact,
  and test or acceptance impact where relevant. Add options for actual decisions and conditional
  recommendations only when justified. Dependent follow-ups wait for the user's answer.
- Keep each batch reviewable: group by domain and impact, at most about 10-12 questions per batch. If the inventory is larger, send the next batch after processing the first.
- The user may answer by Q ID, explicitly accept a recommendation, defer a question with a reason, or ask to switch to interactive mode.
- Agent recommendations and silence are not confirmation. Only an explicit answer, or an explicit "accept recommendation for Q-xxx", becomes a confirmed conclusion.
- Security, irreversible-operation, contract-changing, permission and cross-owner boundary questions require an explicit per-question answer; they cannot be covered by a blanket "accept all".
- After processing a batch: retain confirmed conclusions and statuses in the conversation, re-inventory newly discovered questions, and continue in the selected mode unless the user requests a change or the next decision needs clarification. Save the answers together with the next batch or at discussion wrap-up.
- Batch mode resolves behaviour, ownership and contract decisions and uses the same wrap-up rules and phase confirmation as interactive mode.

## Parallel Development Mode (check applicability at startup)

This skill still discusses exactly one Leaf Feature. Before the first detailed question, after
resolving the discussion mode, check whether other Leaf Features of the same Initiative can be
developed at that moment. A prior development choice is reusable only when its explicit
authorization covers this Feature and current owner, file, contract and isolation conditions
still apply; do not infer worktree authorization from a discussion-mode preference.

1. Read the workspace `README.md` section on ordering and parallelism and the schema section on dependencies and wave.
2. Enumerate the sibling Leaf Features from the registry and the Initiative manifest. A sibling counts as parallelizable at this moment only when all of these hold:
   - it is a Leaf, and not `cancelled` or `superseded`;
   - every `depends_on` entry is satisfied: `completed`, or `ready-to-merge / ready` with passed acceptance and complete closure;
   - it has no blocking child;
   - its implementation file scope does not overlap this Feature's, and it does not change the same contract.
   Owner IDs identify responsibility; sharing an owner ID alone does not block parallel work.
   There is no numeric concurrency cap: the disjointness test above plus worktree code isolation is what makes concurrent work safe. Coordinate shared work-root files and Git merge/index operations as necessary.
3. Run `feature_workspace.py report` and use its ready and next-action lines as evidence. Never infer parallelism from numbering or from `wave` alone; `wave` is only a scheduling hint.
4. If at least one sibling qualifies and no applicable authorized choice exists, ask one startup question before writing detailed questions: develop in the shared checkout sequentially, or open a dedicated git worktree for this Feature so the other Features can be developed in parallel. Use the structured choice panel when the platform provides one, put the worktree option first with its tradeoff (isolation buys parallel throughput, at the cost of a later merge-back), and accept a custom answer. When reusing a choice, state its source and applicability. If no sibling qualifies, state that in one line and continue without asking.
5. Retain the answer in the conversation and include it under `## Parallel development` at the next workbench save.
6. Recheck a recorded parallel development choice against current dependencies and scope; continue it when still applicable and authorized. Resolve a concrete conflict before proceeding rather than repeating the whole startup interview.

Recorded worktree mode is an implementation decision carried to the implementation session; it is not a lifecycle value. The worktree is created and used by `$hl-feature-orchestrator`, which works in it and does not propose merging it back to `repo.default_branch` before the Feature reaches `ready-to-merge / ready`.

## Workspace Rules

Use the registered Leaf path; do not invent a parallel location:

```text
<feature_workspace>/initiatives/initiative-iNNN-<initiative-slug>/features/feat-iNNN-fNN-<feature-slug>/
```

- Directory names are lowercase kebab-case and carry both the stable ID and a short summary.
- The authoritative identifiers, numbering rules and directory format are defined in `<feature_workspace>/schema/feature-workspace-schema.md`; read it before creating anything and never restate a conflicting rule.
- During discussion maintain only the workbench:

```text
feat-<slug>/
  discussion/
    workbench.md
```

- Treat `code-ai/` and `code-ai/README.md` as planned targets during discussion. Create them only after the user confirms the discussion is complete.
- After confirmation, create only the domain folders this feature actually needs, named after the project's real domains from the profile owners table. Prefer a project-native taxonomy over a generic list; a longer-lived `wiki/` taxonomy wins over an invented one.

## Phase Gate Rules

Treat discussion, implementation documents and Code AI profiles as separate recorded phases. After discussion approval, document production and profile generation run continuously in the same session; the documents-to-profiles boundary needs no additional user confirmation.

During the discussion phase:

- Within the work repo, create or update only the feature root and `discussion/workbench.md`.
- Do not create final domain implementation documents.
- Do not create Code AI profile files.
- Use implementation-document targets and profile targets as planned paths only.
- Before asking detailed questions, enumerate every known question with stable IDs. Interactive mode keeps this inventory in the conversation until the workbench save; batch review writes the inventory and reviewable question blocks before user review.
- For frontend page changes in either mode, start with the [frontend page design discussion](../hl-workflow-governance/references/frontend-page-design.md). Resolve the Penpot proposal or the user's choice to skip before taking up dependent implementation questions.
- In interactive mode keep asking one unresolved question at a time until material decisions about behaviour, domain ownership and contracts are confirmed or explicitly deferred. In batch-review mode write reviewable batches of pending questions and wait for the user's bulk review; never treat silence or your own recommendation as confirmation.
- Summarize behavior added, preserved, removed, or degraded relative to the current system. A high-impact removal or degradation requires explicit per-item confirmation, even in batch review; do not bury it in blanket acceptance of recommendations.
- For behavior, contract, or compatibility changes, use `<current topic index linked from the Wiki home>` to identify relevant current authority documents and check them for semantic conflict. Resolve or explicitly route any conflict before implementation documents and profiles are produced. Do not scan unrelated wiki areas.
At discussion wrap-up in either mode, derive the acceptance scope, required test cases and observable pass/fail criteria from confirmed requirements, existing system behavior and project constraints. Incorporate any acceptance requirements the user has already stated. If a check exposes a material unresolved product requirement, resolve or explicitly defer that requirement before closing the discussion.

- Classify visual/interaction impact when deriving the criteria. When in scope, require persistent evidence tied to the tested build, route/state, and viewport. When not applicable, record why.
- For required criteria that depend on an external source, check available evidence for the required sample, window and inputs. Use an existing authorized read-only probe when evidence is insufficient and the probe can resolve the question. Record a concrete passing scenario, any acceptable substitute evidence and what remains unverified without a real sample. Resolve a material ambiguity at the existing discussion boundary.

Save the accumulated workbench in one pass. Summarize confirmed conclusions, behavior changes, relevant authority documents checked for material changes, visual/interaction evidence requirements or the reason they do not apply, pending or deferred questions, planned document and profile targets, and the derived acceptance scope, required test cases and criteria. The sole routine wrap-up question asks for explicit confirmation to enter the implementation-documents phase.

Only after explicit confirmation may you create domain folders, final documents, `code-ai/README.md` and profile files.

That discussion-completion confirmation covers both implementation documents and Code AI profiles. Do not ask the user to approve the completed documents or confirm the profile phase again. Honor an explicit documents-only scope or pause instruction.

### Workbench save timing

Follow the shared discussion-persistence policy in `references/socratic-questioning.md` under
`$hl-workflow-governance`. In interactive mode, keep answers, inventory changes, mode choices
and document/profile targets in the conversation; create or update the workbench at wrap-up.
Keep that state in the conversation while waiting for a reply, after a wait timeout, and across
turn endings. Save only at wrap-up or at an explicit boundary below.
Do not read or rewrite it after each answer. Read an existing workbench once at entry and
inspect additional authority pages only when the next decision needs new evidence.

Save earlier for the shared policy's pause, handoff, compaction, user-requested save or governed
scope-change boundaries. Reconcile any concurrent file edits before saving. If the final
confirmation adds or changes a conclusion, save that delta before advancing. The discussion-completion
confirmation, lifecycle transitions and gates still apply.

### Session boundary

- This session ends at `code-ai-profiles / completed`. It never starts implementation, never writes application code, never dispatches an implementation subagent, and never runs review or acceptance — those belong to a new session running `$hl-feature-orchestrator`.
- Before ending, record the boundary through the state machine with `--next-skill hl-feature-orchestrator` and an instruction naming the feature root, then emit the copyable startup prompt from `## Handoff Prompt`.
- If the user asks to implement in this same session, decline and point at the startup prompt instead: mixing discussion and implementation makes the discussion conclusions unverifiable and loses the independent review and separated acceptance boundary.

## Discussion Workbench

The workbench is conclusion-only. It is not a chat transcript and not the final authority document.

```markdown
# <Feature> Discussion Workbench

## File role
[One paragraph: conclusion-only workbench; records the question inventory, confirmed decisions, open questions, domain classification, document targets and profile targets.]

## Feature summary
[One paragraph in user/business language.]

## Domain classification
- Primary domain:
- Supporting domains:
- Rationale:

## Discussion mode
- selected: interactive | batch-review
- recorded at: <date or step>

## Parallel development
- selected: sequential | worktree
- parallel features considered: <feature IDs, or none>
- recorded at: <date or step>

## Discussion rules
- Follow the mode chosen at startup: interactive asks one question at a time; batch-review writes a reviewable batch of pending questions and waits for the user's bulk review.
- Every question carries context, a neutral Socratic question, the assumption or evidence being
  examined, implementation impact, and test or acceptance impact when relevant. Include options
  only for actual choices and conditional recommendations only when supported by evidence.
- Wait for confirmation before recording a conclusion.
- Record only confirmed conclusions and still-open questions.
- Keep answers in the conversation during questioning; consolidate this workbench at wrap-up or an earlier required save boundary.
- Keep unresolved questions until answered or explicitly deferred.
- Record the acceptance scope, test cases and criteria derived at wrap-up.
- Include the behavior-change, authority-consistency, and visual/interaction acceptance summaries required above; high-impact behavior loss needs individual confirmation.

## Known constraints
[Confirmed boundaries, dependencies, compatibility requirements, excluded scope.]

## Confirmed conclusions
[Grouped by topic or domain.]

## Behavior change summary
- Added:
- Preserved:
- Removed or degraded:
- High-impact removals confirmed individually:

## Authority consistency check
- Relevant authority documents from `<current topic index linked from the Wiki home>`:
- Semantic conflicts and resolution:

## Acceptance scope
- Covered behavior and regression risks:
- Required test cases and observable pass/fail criteria:

## Visual and interaction acceptance
- In scope: yes | no
- For page changes: confirmed Penpot boards/version and covered states, or the scope for which the user chose to proceed without a mockup.
- Evidence required or reason not applicable:

## Question inventory
[All known questions, stable IDs, kept until answered, deferred or split.]

| ID | Domain | Question | Why it matters | Status |

## Pending questions
### Q-001: <question>
Context:
Assumption or evidence to examine:
Decision and acceptance impact:
Options (only for a concrete choice):
Conditional recommendation (if supported):
Decision status: pending

## Implementation document targets
- `<domain>/<doc>.md`:

## Code AI profile targets
- `code-ai/README.md`:
- `code-ai/<domain>-implementation-agent-profile.md`:
```

If a workbench already exists, read it first and continue from its pending questions and confirmed conclusions rather than restarting the inventory.

## Question Loop

Run this loop until the feature is stable enough to document:

0. Before detailed questions, list all known questions with stable IDs in the conversation; retain inventory and pending-section changes until the save boundary.
1. Reuse the workbench and relevant authority context read at entry; inspect additional pages only when a decision needs new evidence.
2. Pick the unresolved decision with the highest implementation impact.
3. Ask one neutral Socratic question grounded in the user's latest answer and known evidence.
4. Explain why this uncertainty matters.
5. Probe a relevant concept, assumption, evidence, alternative or consequence; use options only
   when an actual choice is ready to be made.
6. If supported, state a conditional recommendation separately from the question and name its
   tradeoff. When the user requests a recommendation for every question, put the recommendation
   and its conditions in the same question card, following the shared questioning policy.
7. Wait for the answer; follow up only on a remaining material uncertainty, then confirm the conclusion.
8. Retain the explicit conclusion and question status in the conversation; ask the next unresolved question without a routine file write.
9. Retain document-target and profile-target changes for the same consolidated save.
10. Follow the shared wrap-up rules to derive and record acceptance coverage and request phase confirmation.
11. At the discussion-to-documents boundary, initialize and validate the complete five-dimension `consistency_matrix` before creating documents or advancing lifecycle state.

When the user asks what remains, summarize unresolved decisions and risks only.

## Batch Review Loop

Use this loop instead of the interactive loop when batch-review mode is selected.

1. Build or refresh the complete question inventory (stable IDs, domain, why it matters).
2. Write independent Socratic pending-question blocks for the next reviewable batch: context, one neutral question, the premise or evidence under examination, implementation impact, and test or acceptance impact. Add alternatives or a conditional recommendation only where useful; dependent follow-ups wait.
3. Tell the user which batch is ready and how to answer: by Q ID, explicitly accept a recommendation, defer with a reason, or ask to switch to interactive mode.
4. Wait. Do not record any conclusion from silence or from your own recommendation.
5. Process the answers in the conversation: retain explicit conclusions, deferred items with their reasons, inventory statuses and targets; do not save each individual answer.
6. Re-inventory newly discovered questions; either prepare the next batch, saving accumulated answers with it in one pass, or switch to interactive mode for the remaining high-risk items and save at wrap-up.
7. Repeat until material decisions about behaviour, ownership and contracts are confirmed or explicitly deferred, then follow the shared wrap-up rules to derive and record acceptance coverage and request phase confirmation.

## Implementation Documents Phase

Before creating documents, initialize the feature manifest `consistency_matrix` with all five required dimensions: `business`, `architecture`, `contract`, `code`, `testing`. For each dimension record a real owner, relative `source_refs` that exist, and long-term wiki `promotion_targets`; use `pending` or `in-progress` while evidence is missing. Persist that manifest change through `$hl-feature-workspace` and re-run `factory gate workspace --work <WORK_ROOT>`; stop if it fails. The matrix is a lifecycle gate, not a conclusion to infer later.

When discussion is stable and the user explicitly confirms entry into the documents phase, create or update one implementation document per needed domain. Documents are written in `project.language.docs`; code identifiers, file paths, API names, schema field names and quoted source terms stay as they are. Each document contains:

- Purpose and scope.
- Confirmed behaviour.
- Inputs, outputs, and user/system flows.
- Data contracts, API contracts, or state transitions where relevant.
- Files or modules likely to change, if known.
- Cross-domain dependencies.
- Edge cases and failure behaviour.
- Required test cases: normal flow, edge cases, failure paths, regression checks.
- Acceptance criteria as observable pass/fail outcomes.
- For affected pages, include the agreed design reference and its covered states in the owning frontend criterion. For skipped or uncovered states, specify the agreed written behavior and visual checks.
- Test and verification expectations, citing only commands from the profile commands table.
- Open questions explicitly deferred out of implementation.

Give each acceptance criterion a stable ID in its owning implementation document. That entry is the current executable criterion. The workbench retains the decision and, once the document exists, refers to the criterion by ID and relative path. Use the same ID in plans and role handoffs.

Keep each document authoritative for its own domain; do not paste the workbench into every document.

## Code AI Profile Phase

After the documents are ready, record `implementation-docs / completed` through `$hl-feature-workspace` with `--next-skill hl-feature-profile-generate`, and run `factory gate workspace --work <WORK_ROOT>`. On PASS, immediately follow `$hl-feature-profile-generate` in this same session. Do not end with a documents-only delivery, ask for another confirmation, or require a separate user invocation. Do not maintain a second set of profile-generation rules here.

If required inputs are missing, a gate fails, or an unresolved requirement changes the confirmed scope or acceptance criteria, repair or route that specific gap before generating profiles. Ask only for the unresolved decision when user input is needed; do not replace the removed phase confirmation with a generic permission question.

That skill produces, under the feature root's `code-ai/`, an index plus reading, per-domain implementation, review and verification profiles. Profiles compose generic constraints from `<code_ai>/` by relative-path reference and carry only feature-specific business logic, implementation boundaries, test requirements and acceptance criteria.

Profiles must instruct the future implementer to work from the matching domain document, and not to reopen product discussion unless it hits a documented blocker.

## Quality Bar

A complete discussion first produces only the workbench. After discussion-completion confirmation, the complete package produces:

- A registered feature workspace under `<feature_workspace>/`.
- A concise `discussion/workbench.md` with domain classification, confirmed decisions, pending questions and targets.
- Domain implementation documents in `project.language.docs`, each covering required test cases and acceptance criteria.
- A `code-ai/README.md` index under `code-ai/`.
- Executable profiles under `code-ai/`, generated per `$hl-feature-profile-generate`, referencing `<code_ai>/` by relative path.
- One copyable startup prompt for a new session running `$hl-feature-orchestrator`, per `## Handoff Prompt`.

Do not finish with chat discussion only when the user asked for durable files.

## Feature Workspace Protocol

**Required sub-skill:** `$hl-feature-workspace`. It is the only lifecycle state machine and the only schema gate.

At skill start, resolve the parent Initiative. If feasibility was skipped, record the skip reason.

Before creating a workbench or asking any detailed business question:

1. Build the complete initial Feature inventory from the confirmed Initiative scope.
2. Allocate all initial F IDs and record `depends_on` plus `wave`.
3. Run or verify the Scope Gate for every candidate.
4. Split every `must-split` candidate immediately; do not ask whether a mandatory split should happen.
5. Default `split-default` candidates to splitting; retaining one requires a written `scope_gate.indivisibility_reason`.
6. Run `finalize-decomposition` through `<FACTORY_ROOT>/skills/hl-feature-workspace/scripts/feature_workspace.py`.
7. Select the first dependency-ready Leaf as the sole discussion target.

If `initial_decomposition.status` is not `completed`, stop detailed discussion and finish decomposition first. A broad placeholder `F01` must never carry Initiative-wide discussion. Only a registered Leaf with an admissible Scope Gate may enter discussion, and that transition must pass the registry-backed machine gate (`factory gate workspace --work <WORK_ROOT>`).

When discussion discovers new scope, classify it before continuing:

- current-loop required: absorb and rescore; split if the Leaf no longer passes;
- prerequisite: create a blocking Feature and block the current Leaf;
- adjacent enhancement: create a non-blocking Feature with a stable ID;
- new business goal: create a new Initiative.

Naked TODO, deferred prose and unregistered "future support" are invalid handoffs. After initial decomposition, review Initiative explosion only when explosion signals exist — not on every question.

Update `feature.yaml` only at skill boundaries: start, blocked or split, discussion complete, documents complete, profiles complete. Do not write question-level status. Before profiles, verify that the feature is still a complete Leaf, required tests and acceptance criteria exist, and no blocking child remains.

Transitions go through the state machine, never by hand-editing `phase`/`state`:

```bash
<PYTHON> <FACTORY_ROOT>/skills/hl-feature-workspace/scripts/feature_workspace.py transition \
  --feature <feature_workspace>/initiatives/<initiative>/features/<feature>/feature.yaml \
  --phase <phase> --state <state> \
  --next-skill <skill> --next-instruction "<instruction in project.language.docs>" \
  --registry <registry>
```

Then re-run `factory gate workspace --work <WORK_ROOT>`. Never report a transition as successful from prose alone.

## Handoff Prompt

Discussion and code implementation never share a session. This skill ends at `code-ai-profiles / completed`; the implementation runs in a new session started by one copyable prompt.

Before ending:

1. Automatically finish the profiles phase through `$hl-feature-profile-generate` in this same session, then record the boundary through the state machine: `--phase code-ai-profiles --state completed --next-skill hl-feature-orchestrator` with an instruction naming the feature root and the objective. Re-run `factory gate workspace --work <WORK_ROOT>`. Emit the prompt after that skill finishes and the manifest reads `code-ai-profiles / completed`.
2. Apply the [Leaf handoff commit checkpoint](../hl-workflow-governance/references/commit-boundaries.md) to the completed discussion and profile package. Include the resulting revision or concrete commit blocker in the handoff.
3. Emit exactly one fenced, copyable prompt in the user's language, directly in the response.
4. If the user has explicitly authorized creating and starting the next implementation session,
   dispatch this prompt only after the profiles-completed boundary and workspace gate pass. Carry
   any applicable, explicitly chosen model and reasoning preference from the current workbench or
   authorized handoff, and report the actual session created. Otherwise say that the prompt must
   be pasted into a new session. Never create a session from a model preference alone, never hand
   off unfinished documents/profiles, and do not start implementation in this session.

For a prompt continuing the same enrolled `factory-flow` task, prepend its continuation marker per
`hl-workflow-governance/references/execution-preparation.md`. The self-contained task body follows in this order:

- the invocation: `$hl-feature-orchestrator <Feature ID>`, plus `FACTORY_ROOT`, `WORK_ROOT` and the feature root path;
- the current lifecycle position (`phase: code-ai-profiles`, `state: completed`) and the objective: advance this Feature to `ready-to-merge / ready`, keeping that one goal until it is recorded;
- the must-read paths: resolved Wiki home, the current responsibility’s role memory if present, `feature.yaml`, `discussion/workbench.md`, each domain implementation document, and `code-ai/README.md` with the profiles it indexes;
- the confirmed conclusions and constraints in short form, and the deferred questions marked explicitly as deferred so they are not reopened as discussion;
- for page changes, the frontend criterion and its confirmed design reference or recorded no-mockup scope;
- the critical inherited conditions with their formal source sections, stated directly rather
  than only hidden in the must-read list; include linked object/artifact/session/sequence conditions
  when applicable, without copying all background;
- any predecessor evidence the next step needs: its actual record, proven scope, relevant identity
  and continuation/configuration reference, reuse limits and missing entry points. List required
  checks still unexecuted/unverified/blocked; documentation completion is not application evidence;
- the recorded parallel development choice from `## Parallel development`. When it is `worktree`, add: create `<WORK_ROOT>/.factory/worktrees/<feature-id-lowercase>` on branch `feature/<feature-id-lowercase>` after the `check-ignore` precondition, work inside it, keep manifests and evidence in `WORK_ROOT`, and never propose merging back to `repo.default_branch` before the Feature is `ready-to-merge / ready`;
- the mandatory end state: recorded `ready-to-merge / ready` with passing fixed review, separated acceptance, complete closure and a passing `factory gate workspace`;
- the handoff commit revision or concrete blocker;
- the prohibitions: no product re-discussion, no hand-editing `phase`/`state`, no push or merge
  without separate explicit authorization.

Render section labels in the user's language; keep IDs, paths, YAML keys, lifecycle enums and skill names ASCII:

```text
Use $hl-feature-orchestrator <FEATURE_ID> in work repo <WORK_ROOT> to advance Leaf Feature <FEATURE_ID> (<title>).

- FACTORY_ROOT: <FACTORY_ROOT>
- WORK_ROOT: <WORK_ROOT>
- feature root: <feature_workspace>/initiatives/<initiative>/features/<feature>
- lifecycle: phase=code-ai-profiles, state=completed; profiles already generated
- goal: advance this Feature to ready-to-merge / ready (implementation and doc sync, fixed review,
  separated acceptance, closure gate, recorded transition with a passing factory gate workspace);
  keep this one goal until it is recorded
- read first: feature.yaml, discussion/workbench.md, <domain>/*.md, code-ai/README.md and the
  profiles it indexes
- confirmed conclusions: <short list>
- critical inherited constraints: <conditions + formal source sections>
- evidence to reuse/continue, when needed: <record, scope, identity, entry and limits; missing entry is a gap>
- required work not yet verified: <remaining checks/blockers; do not prefill PASS>
- deferred questions (do not reopen discussion): <short list>
- parallel development: sequential | worktree (<worktree path and branch when worktree>)
- local commits: <handoff revision or concrete blocker>
- do not: reopen product discussion, hand-edit phase/state, push or merge without separate
  explicit authorization
```
