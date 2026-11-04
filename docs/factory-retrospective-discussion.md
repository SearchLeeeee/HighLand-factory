# Factory Retrospective Discussion

## File Role

This is a conclusion-only discussion workbench for reviewing HighLand-factory against its use in qqq-radar. It records confirmed conclusions, pending decisions, and later sync targets. It is not the workflow authority or an implementation checklist.

## Goal

Decide which reusable workflow improvements are justified by the qqq-radar development history, then identify the factory authorities, machine gates, tests, and generated work-repository surfaces that would need synchronization.

## Discussion Rules

- Discuss one question at a time.
- Record confirmed conclusions only; keep unresolved items pending.
- Do not change workflow authority or implementation during this discussion phase.
- After discussion completion, obtain confirmation before syncing formal docs or creating Code AI artifacts.

## Known Constraints

- The qqq-radar records show both successful safeguards and process gaps; project-specific product decisions must not be copied into generic factory rules.
- Existing factory authorities include workflow skills, feature-workspace lifecycle tools, templates, tests, and generated work-repository guidance. Changes must be routed to the correct authority after discussion.
- Git-history review: F04's presentation tradeoff was an approved product decision; its dark palette was an implementation deviation. F06's review record reports changes to reviewed files and commits during the review window.
- Complexity review: six topic folders started with only short README files; the wiki validator accepts a root README as a valid minimal wiki, so topic indexes can be created when needed. Governance entry-point prose overlapped the governance skill/contract. The template root README collided with the generated workspace README.
- The 15 F06 review rounds were costly but not automatically idle: later rounds closed concrete negative-test detection gaps. Prefer narrower delta-based re-review over a round cap that could leave a real finding unresolved.
- Preserve the distinct Feature/Quick Change workspaces, independent review, independent acceptance and authority-switch gate: the qqq-radar history shows each caught a different class of issue. Simplify duplicated instructions and unused default scaffolding before removing those boundaries.
- Code AI follow-up scope: the final implementation agent may be a weaker model, so planning, task boundaries, dependencies, tests and stop conditions need to be explicit before it edits. Existing orchestration already requires worker plans before edits; this review is about whether those plans are sufficiently complete, integrated and easy for a weaker model to execute.

## Confirmed Conclusions

### Q-001: Make material user-visible losses explicit in batch review

- In batch review, present a clear summary of behavior added, preserved, removed, or degraded.
- Require separate user confirmation for high-impact removals or degradations; lower-impact changes may remain in batch approval.
- Later sync targets: `skills/hl-feature-discuss/` and the generated workspace discussion guidance.

### Q-002: Check relevant authority documents for material conflicts

- For behavior, contract, or compatibility changes, check the relevant documents identified through the authority map for semantic conflicts before implementation and acceptance.
- Do not require every Feature to scan the entire Wiki.
- Later sync targets: Feature discussion/profile instructions and the existing consistency-matrix source/promotion references; no new lifecycle field.

### Q-003: Declare visual and interaction evidence needs during Feature discussion

- At discussion time, classify whether visual or interaction behavior is in scope.
- When applicable, require persistent evidence bound to the tested build, route/state, and viewport; when not applicable, record the reason.
- Later sync targets: discussion, profile-generation and acceptance instructions; existing evidence references carry the visual/interaction result without a new lifecycle field.

### Q-004: Bind review evidence to an immutable reviewed snapshot

- Record the revision and fingerprints for reviewed implementation/design/acceptance files at review start.
- Recheck before accepting the review; any change in the reviewed set invalidates that review run.
- Exclude the reviewer's own report output from the reviewed-file fingerprint set.
- Later sync targets: Feature orchestrator, review evidence format, and review gate tests.

### Q-005: Use risk-based verification for Quick Change

- Select final verification suites based on documented change impact and risk.
- Record affected suites and why omitted suites cannot be affected.
- Require full verification for shared contracts, persistence, security, and cross-module changes.
- Later sync targets: Quick Change skill, quick-record schema/template, and applicable validation tests.

### Q-007: Require a risk-scaled Feature-level implementation plan

- Every Feature implementation has one integrated plan before file changes begin.
- Plan depth scales with risk: a short ordered checklist is enough for bounded work; multi-owner, contract-changing or otherwise high-risk work requires detailed dependencies and integration steps.
- The plan does not introduce a Feature lifecycle state.
- Later sync targets: profile generation, orchestration plan gate and Code AI flow guidance.

### Q-008: Use a short core plan format with conditional detail

- Every plan uses a concise common structure; contract, data/migration, compatibility, security, visual evidence and cross-owner details are included when relevant.
- Mark conditional sections not applicable with a reason instead of copying full requirements into the plan.
- Later sync targets: the plan template and the orchestrator's plan completeness check.

### Q-009: Plan dependencies, parallelism and integration points

- The plan records task dependencies and integration checkpoints.
- Parallelize only when both file and contract scopes are non-overlapping and dependencies are satisfied.
- Keep integration and verification checkpoints in the plan; the main agent remains responsible for integration.
- Later sync targets: Code AI flow, orchestrator dispatch and integration checks.

### Q-010: Use risk-based execution checkpoints

- Keep planned small-step verification in the implementation flow.
- Same-model, single-agent work does not produce a duplicate report after every step.
- Use compact explicit checkpoints at meaningful milestones, multi-agent integration points, high-risk changes or material deviations.
- Scope, contract, security and product decisions still stop and escalate; in-scope implementation adjustments can be captured at the next checkpoint.
- Later sync targets: plan/profile checkpoint guidance and integration handoff; no lifecycle state or duplicate command list.

### Q-011: Keep complete role-appropriate startup reading

- Retain the current required startup reading; the intended model has enough context capacity to read the complete set.
- Keep the approved plan and current task easy to find in the entry/dispatch, while preserving source-document reading and authority links.
- Later sync: no reduction to the startup reading set; check the plan is prominently routed without duplicating authority text.

### Q-012: Persist one canonical implementation plan

- Save the integrated Feature plan as one durable file under the Feature's `code-ai/` directory.
- The orchestrator creates it before implementation after inspecting the actual code and reconciling the worker plans; workers and reviewers reference the same plan.
- Update the same plan when approved scope, assumptions, dependencies or execution order materially change; do not create one plan file per worker.
- Later sync targets: plan template, profile index/generation guidance and orchestrator plan/replan gate.

## Question Inventory

| ID | Topic | Question | Why it matters | Status |
| --- | --- | --- | --- | --- |
| Q-001 | Decision quality | Should user-visible removals or degradations require explicit per-item confirmation even during batch review? | Makes compatibility costs salient and reduces accidental approval by blanket acceptance. | confirmed |
| Q-002 | Authority consistency | Should Feature readiness require a semantic conflict check against all relevant current authority documents, beyond listing promotion targets? | Prevents implementation and acceptance from overlooking conflicting canonical docs. | confirmed |
| Q-003 | Visual acceptance | Should UI-affecting Features classify visual evidence as required or not applicable, with a reason, before implementation? | Makes visual regressions testable and keeps visual verification tied to the intended scope. | confirmed |
| Q-004 | Review integrity | Should review evidence bind to a revision and invalidate automatically if reviewed files change during review? | Prevents a review result from being applied to a different implementation state. | confirmed |
| Q-005 | Verification cost | Should Quick Change use risk-based targeted checks during iteration and reserve full-suite checks for the final gate or high-risk changes? | Reduces routine verification cost without weakening checks for contracts or cross-module changes. | confirmed |
| Q-006 | Quick Change overhead | Should the context-compaction block and compaction/handoff action be mandatory for every Quick Change, including short work continued in the same session? | Avoids repeating the same context in a record and the active session when no handoff is needed. | confirmed |
| Q-007 | Code AI plan gate | Is the current per-worker plan-before-edit gate sufficient, or should Code AI require a feature-level implementation plan before any code changes? | A weaker model benefits from an approved end-to-end map before it starts editing. | confirmed |
| Q-008 | Plan contents | Which concrete fields must every implementation plan contain, and which should be required only for higher-risk work? | A plan must be actionable without duplicating the business and domain documents. | confirmed |
| Q-009 | Execution sequencing | How should the plan govern sequential work, parallel owner agents, dependencies and integration checkpoints? | Uncoordinated local plans can conflict or leave integration until the end. | confirmed |
| Q-010 | Progress and deviations | What evidence or checkpoint should be required after each implementation slice, and when must a deviation stop and return for replanning? | Weaker agents need short feedback loops and a clear boundary against silent scope drift. | confirmed |
| Q-011 | Startup context | Should Code AI retain broad mandatory startup reading, or use a compact core plus task-specific authority/profile reads? | Long, overlapping instructions consume attention and make it harder to find the approved plan. | confirmed |
| Q-012 | Plan persistence | Should the approved feature-level implementation plan be a durable workspace artifact or remain in the orchestration session/handoff? | The plan must remain available to implementation agents, reviewers and any resumed session. | confirmed |

## Pending Questions

No pending questions.

Q-001–Q-012 are confirmed. No questions remain pending.

## Sync Targets

Approved synchronization plan, implemented below:

| Conclusion | Candidate authority surfaces |
| --- | --- |
| Q-001: behavior loss summary and high-impact separate confirmation | `skills/hl-feature-discuss/SKILL.md`, its discussion templates/references, relevant tests, and generated work-repository discussion guidance |
| Q-002: semantic conflict check against relevant authority documents | consistency-matrix guidance in `skills/hl-feature-discuss/`, Feature Workspace schema/README and lifecycle checks if the rule becomes machine-gated, plus merge/acceptance handoff guidance |
| Q-003: visual/interaction impact and evidence classification | discussion and profile-generation skills, Feature evidence/schema guidance, Initiative evidence requirements, and validation tests |
| Q-004: revision and file fingerprint for review | `skills/hl-feature-orchestrator/SKILL.md`, review evidence format, and review gate/verification tests |
| Q-005: risk-based Quick Change verification | `skills/hl-quick-change/SKILL.md`, quick-record schema/template, and validation tests |
| Q-006: conditional Quick Change context compaction | `skills/hl-quick-change/SKILL.md`, quick-record schema/template |
| Cross-cutting consistency | `skills/hl-workflow-governance/SKILL.md`, `skills/hl-workflow-governance/references/entry-point.md`, and `references/workflow-contract.md`; generated workspace guidance under `templates/workspace/` |
| Code AI planning and weak-model execution (Q-007–Q-012) | `skills/hl-feature-profile-generate/SKILL.md`; `skills/hl-feature-orchestrator/SKILL.md`; new `templates/workspace/wiki/code-ai/implementation-plan-template.md`; `templates/workspace/wiki/code-ai/README.md.tmpl`; `templates/workspace/wiki/code-ai/subagent-flow.md`. Keep one plan authority; retain full startup reading. |

### Code AI Follow-up Sync Plan

The discussion is complete. The next step is factory-side workflow documentation only. It will define where the plan is created, who approves it, how workers and reviewers use it, and how risk-based checkpoints work. After those rules are stable, the generated Code AI template artifacts require a separate explicit confirmation.

| Phase | Files | Planned change | Review |
| --- | --- | --- | --- |
| Factory workflow docs | `skills/hl-feature-orchestrator/SKILL.md` | Require the orchestrator to inspect the implementation repository, create one Feature-level plan from the approved template before edits, integrate worker plans into it, gate file changes on approval, bind dispatch/review to its current revision, update it on material approved changes, and use risk-based checkpoints. Keep existing lifecycle states and escalation boundaries. | Check sequencing against preflight, dispatch, review, verification and closure; confirm no same-model per-step handoff is added. |
| Profile generation contract | `skills/hl-feature-profile-generate/SKILL.md` | Make generated Feature `code-ai/README.md` point to the reserved canonical `implementation-plan.md` path and require implementation/review/verification profiles to use it. The orchestrator fills it after code survey; profile generation must not create a premature empty plan. | Verify generated profile reading order and role responsibilities agree with the orchestrator. |
| Generated Code AI templates — separate phase | New `templates/workspace/wiki/code-ai/implementation-plan-template.md`; `templates/workspace/wiki/code-ai/README.md.tmpl`; `templates/workspace/wiki/code-ai/subagent-flow.md`; `docs/workspace-template.md` | Add one canonical risk-scaled plan format; link it from the library entry and define the plans gate, dependencies, conditional parallelism and milestone checkpoints. Clarify that Code AI templates have their own approved maintenance phase. Preserve the full startup reading set and expose the approved plan prominently. Avoid changing unrelated blocks or adding lifecycle states. | Check links, source-of-truth ownership, and template rendering behavior. |

No pending discussion questions remain. The user separately confirmed the factory documentation sync and Code AI artifact phases; both are now complete.

Validation: `git diff --check` passed. The plan path, profile-generation contract, dispatch sequence, source discovery, review snapshot inputs, risk-based checkpoints, template links and maintainer scope guidance were manually cross-checked. No automated tests were run for these documentation/template-only edits.

### Complexity And Wiki Structure Findings

- Preserve distinct workflow boundaries that caught real issues in the retrospective: discussion vs implementation, independent review, independent acceptance, and authority switch. Avoid eliminating these as a cost-saving shortcut.
- Reduce idle handoff ceremony in Quick Change using Q-006 and verification cost using Q-005.
- Keep semantic wiki areas such as product, domain, architecture, implementation, features and testing distinct, but stop pre-creating short topic-only README files and root-MOC links for areas with no content. Add a topic MOC when its first authority document is introduced. The wiki validator already accepts a root-only wiki, so this can be done without a new wiki mode/configuration.
- Shorten the workflow-governance entry point to session bootstrap and authority routing; keep operational invariants in their owning skill and the shared contract rather than repeating the full daily flow in three places.
- Move the template-maintainer guide out of `templates/workspace/README.md` and remove the `SKIP_TEMPLATE_FILES` renderer exception if the path collision can be resolved cleanly.

### Approved File-By-File Sync Plan

This plan keeps the discussion findings small and avoids new lifecycle states or manifest fields. It includes one focused review-snapshot helper because Q-004 explicitly requires an automatic stale-review check.

| Area | Files | Planned change | Check needed |
| --- | --- | --- | --- |
| Q-001–Q-003 | `skills/hl-feature-discuss/SKILL.md` | Make behavior-loss summaries, relevant authority conflict checks for material changes, and visual/interaction impact classification required discussion outputs. Use existing workbench and acceptance sections; add no new Feature lifecycle field. | Documentation consistency only. |
| Q-002–Q-003 | `skills/hl-feature-profile-generate/SKILL.md`; `skills/hl-feature-orchestrator/SKILL.md` | Carry the authority conflict check and applicable visual evidence requirements into generated profiles and separate acceptance. Do not scan unrelated wiki areas or require screenshots for non-visual work. | Documentation consistency only. |
| Q-004 | `skills/hl-feature-orchestrator/SKILL.md`; new `skills/hl-feature-orchestrator/scripts/review_snapshot.py`; new `skills/hl-feature-orchestrator/tests/test_review_snapshot.py` | Capture the target revision and SHA-256 for the reviewed file set before review; verify the same set before accepting the report; return stale/fail if a reviewed file or target revision changed. Keep the review report output outside the fingerprint set. This is a review evidence tool, not a second lifecycle state machine. | Targeted helper tests plus an end-to-end capture/change/verify check. |
| Q-005–Q-006 | `skills/hl-quick-change/SKILL.md`; `skills/hl-quick-change/references/quick-record-template.md`; `templates/workspace/wiki/quick-workspace/schema/quick-record-schema.md` | Keep a concise impact-based list of tests run and omitted with reasons; keep full-suite verification for shared contracts, persistence, security, and cross-module work. Make compaction/handoff conditional on session transfer or substantial context; short same-session work proceeds from recorded scope and acceptance. Add no status values or separate quick-change state machine. | Template/schema consistency; existing quick path must remain valid. |
| Cross-cutting policy | `skills/hl-workflow-governance/SKILL.md`; `skills/hl-workflow-governance/references/entry-point.md`; `skills/hl-workflow-governance/references/workflow-contract.md` | Keep only a compact summary in governance entry points, route each procedure to its owning skill, and avoid repeating the full workflow in all three documents. | Cross-reference and authority consistency review. |
| Topic MOC simplification | `templates/workspace/wiki/README.md.tmpl`; remove the six topic-only README files in `architecture/`, `domain/`, `features/`, `implementation/`, `product/`, and `testing/`; `skills/hl-factory-init/references/adopt-code-analysis.md`; `skills/hl-wiki-merge/SKILL.md`; `docs/init-questionnaire.md`; `docs/architecture.md` | Keep the core root Wiki documents and semantic topic taxonomy, but create a topic MOC when that topic gets its first authority document. Update adopt and merge instructions to create/link a MOC when first needed. Do not add a compact/full config switch. The current wiki gate accepts a root-only wiki and still enforces link integrity/orphan coverage. | Template smoke and a generated minimal-workspace wiki gate. |
| Template path exception | Move `templates/workspace/README.md` to `docs/workspace-template.md`; `engine/factorylib/render.py`; `engine/tests/test_init.py` | Remove the same-output-path collision with `README.md.tmpl` and delete only the obsolete README skip entry; keep the separate `.factory/factory.yaml.tmpl` exception. Update template inventory and rendering documentation. | Init rendering test and template smoke. |
| User-facing workflow handbook | `templates/workspace/wiki/feature-workspace/README.md` | Align its process guide with the new confirmed rules, but replace repeated generic detail with pointers to the owner skills/schema where possible. | Link, scope, and consistency check. |

Not in this sync: do not merge semantic wiki domains such as product/domain/architecture/implementation/testing; do not remove independent review, independent acceptance, Feature/Quick Change isolation, Initiative integration, or authority-switch gates; do not introduce a wiki profile/configuration knob.

The user approved this file-level plan and its targeted verification. The workflow documents, template structure, and snapshot helper are implemented. The targeted initialization/template gate and snapshot tests pass: 20 passed. No full factory test suite was run. Code AI review-agent templates remain outside this approved sync and require the separate confirmation described below.

## Code AI Artifact Rule

The original retrospective sync and the separately confirmed Code AI follow-up artifact sync are complete. Future changes to these reusable Code AI templates still require their own explicit phase confirmation.
