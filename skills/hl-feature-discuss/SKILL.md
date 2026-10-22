---
name: hl-feature-discuss
description: Use when exactly one dependency-ready Leaf Feature is ready to be refined into confirmed conclusions, domain implementation documents and Code AI profile inputs inside the feature workspace. Runs a rubber-duck, one-question-at-a-time discussion with a conclusion-only workbench and advances lifecycle state only at skill boundaries.
---

# Feature Discuss

## Step 0 — Load factory context

Run this before anything else, including reading the feature request.

1. Resolve `WORK_ROOT`: the git top-level that contains `.factory/`, or the directory that holds `.factory/`. Every path below is relative to it.
2. Read `WORK_ROOT/.factory/local.yaml` (machine-scoped, gitignored) and take:
   - `factory_root` → `FACTORY_ROOT`
   - `python` → `PYTHON`, an interpreter with PyYAML available

   If the file is missing, unreadable, or either value is empty, stop and tell the user to run `$hl-factory-init` (`factory init --work <WORK_ROOT>`). Never guess a checkout path.
3. Read `WORK_ROOT/wiki/governance/workflow-profile.md`. It is generated from `.factory/factory.yaml` and is the only source for project language, layout, owners, commands, verification, gates, security boundaries and packs. If it is missing, or it disagrees with `.factory/factory.yaml`, stop and run `$hl-factory-doctor`; never hand-edit it.
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

## Purpose

Turn one registered Leaf Feature into a durable feature workspace: a conclusion-only workbench, then domain implementation documents, then inputs for executable Code AI profiles.

The core pattern is: verify that the parent Initiative's initial Feature decomposition is finalized, take exactly one dependency-ready Leaf Feature, classify its domains, create the workbench, list every known question before asking any, discuss one decision at a time, record confirmed conclusions only, ask for explicit confirmation that discussion is complete, then write the implementation documents in `project.language.docs` and hand the profile phase to `$hl-feature-profile-generate`.

## Workspace Rules

Use the registered Leaf path; do not invent a parallel location:

```text
wiki/feature-workspace/initiatives/initiative-iNNN-<initiative-slug>/features/feat-iNNN-fNN-<feature-slug>/
```

- Directory names are lowercase kebab-case and carry both the stable ID and a short summary.
- The authoritative identifiers, numbering rules and directory format are defined in `wiki/feature-workspace/schema/feature-workspace-schema.md`; read it before creating anything and never restate a conflicting rule.
- During discussion maintain only the workbench:

```text
feat-<slug>/
  discussion/
    workbench.md
```

- Treat `code-ai/` and `code-ai/README.md` as planned targets during discussion. Create them only after the user confirms the discussion is complete.
- After confirmation, create only the domain folders this feature actually needs, named after the project's real domains from the profile owners table. Prefer a project-native taxonomy over a generic list; a longer-lived `wiki/` taxonomy wins over an invented one.

## Phase Gate Rules

Treat discussion, implementation documents and Code AI profiles as separate phases.

During the discussion phase:

- Create or update only the feature root and `discussion/workbench.md`.
- Do not create final domain implementation documents.
- Do not create Code AI profile files.
- Use implementation-document targets and profile targets as planned paths only.
- Before asking individual questions, enumerate every known question and write it into the workbench.
- Keep asking one unresolved question at a time until behaviour, domain ownership, test cases and acceptance criteria are confirmed or explicitly deferred.

Before leaving the discussion phase, summarize: confirmed conclusions, pending or deferred questions from the full inventory, planned document targets, planned profile targets, required test cases, and acceptance criteria. Then ask for explicit confirmation to enter the implementation-documents phase.

Only after explicit confirmation may you create domain folders, final documents, `code-ai/README.md` and profile files.

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

## Discussion rules
- One question at a time unless the user asks for a batch.
- Every question carries context, concrete options, a recommendation, implementation impact, and test or acceptance impact when relevant.
- Wait for confirmation before recording a conclusion.
- Record only confirmed conclusions and still-open questions.
- Keep unresolved questions until answered or explicitly deferred.
- Treat test cases and acceptance criteria as required topics before documents are stable.

## Known constraints
[Confirmed boundaries, dependencies, compatibility requirements, excluded scope.]

## Confirmed conclusions
[Grouped by topic or domain.]

## Question inventory
[All known questions, stable IDs, kept until answered, deferred or split.]

| ID | Domain | Question | Why it matters | Status |

## Pending questions
### Q-001: <question>
Context:
Options:
Recommendation:
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

0. Before detailed questions, list all known questions into the inventory and pending sections.
1. Read the workbench and the relevant long-term wiki pages.
2. Pick the unresolved decision with the highest implementation impact.
3. Ask one concrete question.
4. Explain why the decision matters.
5. Give two to four realistic options.
6. Recommend one and name the tradeoff.
7. Wait for confirmation.
8. Update `discussion/workbench.md` with the confirmed conclusion only.
9. Update document targets and profile targets.
10. Before leaving discussion, discuss required test cases and acceptance criteria explicitly.
11. At the discussion-to-documents boundary, initialize and validate the complete five-dimension `consistency_matrix` before creating documents or advancing lifecycle state.

When the user asks what remains, summarize unresolved decisions and risks only.

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
- Test and verification expectations, citing only commands from the profile commands table.
- Open questions explicitly deferred out of implementation.

Keep each document authoritative for its own domain; do not paste the workbench into every document.

## Code AI Profile Phase

After the documents are ready and the user explicitly confirms the profile phase, follow `$hl-feature-profile-generate`. Do not maintain a second set of profile-generation rules here.

That skill produces, under the feature root's `code-ai/`, an index plus reading, per-domain implementation, review and verification profiles. Profiles compose generic constraints from `wiki/code-ai/` by relative-path reference and carry only feature-specific business logic, implementation boundaries, test requirements and acceptance criteria.

Profiles must instruct the future implementer to work from the matching domain document, and not to reopen product discussion unless it hits a documented blocker.

## Quality Bar

A complete discussion first produces only the workbench. After explicit phase confirmation, the complete package produces:

- A registered feature workspace under `wiki/feature-workspace/`.
- A concise `discussion/workbench.md` with domain classification, confirmed decisions, pending questions and targets.
- Domain implementation documents in `project.language.docs`, each covering required test cases and acceptance criteria.
- A `code-ai/README.md` index under `code-ai/`.
- Executable profiles under `code-ai/`, generated per `$hl-feature-profile-generate`, referencing `wiki/code-ai/` by relative path.

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
  --feature <WORK_ROOT>/wiki/feature-workspace/initiatives/<initiative>/features/<feature>/feature.yaml \
  --phase <phase> --state <state> \
  --next-skill <skill> --next-instruction "<instruction in project.language.docs>" \
  --registry <WORK_ROOT>/wiki/feature-workspace/registry.yaml
```

Then re-run `factory gate workspace --work <WORK_ROOT>`. Never report a transition as successful from prose alone.

## Handoff Prompt

When discussion and documents are complete, hand off in the user's language, naming the feature root, the documents to read first, and the profile targets, and instruct the next session to use `$hl-feature-profile-generate`. Keep IDs, paths, YAML keys, lifecycle enums and skill names ASCII.
