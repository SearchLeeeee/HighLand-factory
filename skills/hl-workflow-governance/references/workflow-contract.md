# Workflow Contract

Load factory context first: read `.factory/local.yaml` and `wiki/governance/workflow-profile.md`
before using this file. Policy switches quoted here are read from that profile, not assumed.

This reference is an operational index, not a second state machine. Executable and schema
authority stays with the feature-workspace tools and documentation named by
`references/entry-point.md`.

## Invariants

- Initiative creation is followed by a complete initial Feature inventory, dependency and wave
  registration, a per-candidate Scope Gate, mandatory splitting, and `finalize-decomposition`;
  only then may the first dependency-ready Leaf enter discussion.
- A broad F01 must not represent the whole Initiative during discussion. `must-split` is never
  discussion-admissible; `split-default` requires a recorded `indivisibility_reason`.
- Leaf Feature lifecycle changes and Initiative decomposition finalization use the shared
  state-machine command, never ad hoc YAML edits.
- A ready dependency is usable only when its acceptance and closure are complete.
- Acceptance `passed` is boolean and only `true` passes. Acceptance and ready closure evidence
  are non-empty relative file lists resolved from their owning manifest and checked for existence.
  This checks records, not their substantive quality; independent review and verification remain.
  Canonical promotion targets need not exist before promotion. A registry-backed transition checks
  the complete candidate registry before atomic replacement; rejected or failed writes retain the
  original manifest. Standalone Leaf readiness cannot replace Initiative preflight.
- An Initiative is not mergeable until all active Leaf Features are ready and new Initiative-level
  integration evidence has passed.
- Integration evidence is local, bound to one immutable run, and distinct from per-Feature sealed
  evidence.
- Feature merges happen only after `initiative-merge-ready` passes and, when
  `workflow.merge_requires_authorization` is true, after explicit user authorization is obtained,
  in dependency-topological order.
- For each Feature the fixed order is: semantic wiki merge, affected-MOC updates, full long-term
  wiki validation excluding registered process workspaces, retained-history transformation
  after PASS, `merged/completed`, then authority switch and external routing-record update.
- The full long-term wiki validator is a `$hl-wiki-merge` machine gate
  (`<FACTORY_ROOT>/skills/hl-wiki-merge/scripts/validate_llm_wiki.py`); it is not a lifecycle field.
- Validator failure leaves the Feature `ready-to-merge / ready` and forbids tombstone or
  routing-record creation, authority switch, retained-history transformation and
  `merged/completed` closure.
- Only after validator PASS are merged Feature source directories transformed and retained as
  non-authoritative provenance, excluded from active manifest references, default discovery and
  reporting, and from new Feature `context_refs`; the canonical wiki then becomes the sole current
  authority.
- Future discussions and open questions stay in the feature workspace; canonical current facts go
  into the current or domain authority document.
- A topic MOC is created when its first canonical document is added. Do not create or link empty
  topic MOCs from the default wiki home; all existing canonical Markdown must remain reachable from
  the root home within the validator's depth limit.
- Historical lookup starts from a concrete question and canonical path, runs in a fresh isolated
  subagent through the external routing record and the retained `history-route.yaml`, and returns
  only a compact handoff to the main session.
- Quick-change records are process material. A fired hard gate escalates to the feature workflow
  instead of widening the lightweight record's authority.
- Manual refactoring starts only on an explicit request after every effective Initiative and
  Leaf reaches its proper terminal condition. It keeps its own run, selection and evidence and
  never reopens completed work. A selected handoff to new Feature work requires maintenance to
  pause or finish before that work starts.
- Full and latest-Initiative scans disclose coverage and exclusions, then require user selection
  before editing. Changed behavior needs explicit item-level selection; ordinary implementation
  choices within the selected cost/risk boundary do not require repeated confirmation.
- Current Wiki excludes the exact built-in and explicitly registered process-workspace roots.
  Check business claims against current implementation and important implementation facts against
  Wiki in both directions, with time/version/configuration evidence. Separate structural PASS,
  semantic consistency, business correctness and deployment observations.
- A baseline Wiki structural failure may be diagnosed by an explicitly requested read-only
  refactor scan. Preserve the failure; selected implementation cannot close without Wiki PASS.
  This narrow diagnostic exception does not waive lifecycle validation or normal merge gates.
- A refactor scan may recommend workflow improvements, but runtime changes to generic skills,
  templates, dispatch or governance belong to another user-directed session. Current project
  capability, module responsibility and contract documentation remain in-scope when selected.
- Every user-facing question follows `references/socratic-questioning.md`, including initialization,
  optional packs and batch workbench review. Ground neutral questions in the user's answers to
  clarify concepts, probe assumptions and evidence, examine alternatives and trace consequences.
  Recommendations stay conditional; existing authorization gates remain binding.
- Discussion persistence follows the same shared questioning reference: accumulate answers in the
  conversation and save at wrap-up or an earlier required boundary. Interactive question delivery
  does not require per-answer file writes. Batch-review questions remain available in the workbench;
  required lifecycle, scope-registration and authorization actions are not deferred.
- When the user must choose among two or more viable alternatives, use the structured choice panel
  when available: 2-3 mutually exclusive options, the recommended one first, the client-provided
  `Other` for custom input, and one concise plain-text question only as a fallback. This
  interaction rule never weakens an authorization or machine gate.
- User authorization is required for actual merge, deletion, commit and push operations whenever
  the profile requires it.
- Starting a registered Leaf through `$hl-feature-orchestrator` supplies standing authorization
  for its local implementation, documentation sync, review fixes and closure evidence commits at
  passed boundaries, as defined in `references/commit-boundaries.md`. Preserve it across handoffs
  and resumes without asking again. Explicit restrictions and stricter project policy prevail;
  initialization, Quick Change, unrelated changes, push and merge are outside this grant.
- Commit boundaries are governed by `references/commit-boundaries.md`, not scattered through prose.
  Commits happen only behind a passing gate, at one of the named boundaries; a commit authorization
  is never a push authorization. Identify reviewed/tested sources using an existing revision
  and the relevant diff/new files. New freeze commits are needed only for a concrete immutable
  artifact or acceptance requirement, with authorization; evidence-only changes do not invalidate
  unchanged source results. Commit boundaries add no lifecycle state,
  manifest field or state-machine branch, and the core workflow must still run with
  `packs.enabled: []`.
- Parallel development mode — shared checkout sequentially, or one dedicated git worktree per
  Feature — is an implementation decision recorded in the discussion workbench, never a lifecycle
  value. A worktree isolates code only: manifests, evidence and the workspace gate stay in the work
  root, `.factory/worktrees/` stays gitignored, and the worktree is never merged back into
  `repo.default_branch` before the Feature reaches `ready-to-merge / ready`. That merge is a
  separate operation with its own explicit authorization.
- Batch discussion makes behavior added, preserved, removed or degraded explicit; high-impact
  removals or degradations need individual user confirmation. Material behavior, contract or
  compatibility changes require a semantic conflict check against the relevant documents in the
  authority map, not an indiscriminate whole-Wiki scan.
- UI/interaction scope is classified during discussion. Applicable visual evidence is persistent
  and bound to build, route/state and viewport; non-applicability is recorded with a reason.
- Discussion-completion confirmation covers implementation documents and Code AI profiles.
  `$hl-feature-discuss` records `implementation-docs / completed` through the state machine and,
  after the workspace gate passes, automatically invokes `$hl-feature-profile-generate` in the
  same session. No document approval, profile-phase confirmation or separate user invocation is
  required. Honor explicit documents-only scope or pause instructions. Missing inputs, failed
  gates or new unresolved requirements block the affected continuation; resolve the concrete gap
  without adding a generic permission question. Existing lifecycle phases and gates remain intact.
- Review conclusions bind to identifiable source changes and applicable criteria. Git revision
  plus relevant diff/new files is the default; per-file hashes, receipts, extra clones and clean-tree
  freeze commits are not mandatory. Changes invalidate affected conclusions only; metadata or an
  unrelated HEAD change does not automatically invalidate review. Broaden checks when real impact
  requires it, and preserve applicable unaffected results with their provenance.
- Quick Change records test impact, selected commands and reasons for omitted commands. Shared contracts, persistence/migration, security/permissions and cross-module changes require
  coverage of the affected compatibility and safety boundaries; broaden verification when impact
  cannot be bounded, without automatically rerunning unrelated suites. Context compaction is required only for a real session
  transfer, substantial context or a needed handoff; a short same-session path records its scope and
  criteria without a no-op handoff block.
- The implementation session carries one continuous goal: advance the Feature to
  `ready-to-merge / ready`. Update it once when new evidence changes the status, never create a
  second goal, never emit a next-session handoff mid-workflow, and complete it only after the
  transition is recorded and the workspace gate passes.
- Discussion and code implementation never share a session. The discussion session owns the
  workbench, the domain implementation documents and the Code AI profiles, ends at
  `code-ai-profiles / completed`, and hands off exactly one copyable prompt that starts
  `$hl-feature-orchestrator` in a new session; that prompt carries the workspace paths, the
  must-read documents, the confirmed conclusions and the parallel development choice, so the
  implementation session needs no chat history. Starting implementation in the discussion session,
  or reopening product discussion in the implementation session, is invalid.
- Minimum sufficient verification is the default: reuse applicable evidence and environments,
  rerun affected checks, preserve actual failures, and repair gaps locally. Independent roles do
  not require duplicate full execution. Coordinators inspect decisive evidence and sample by risk;
  they do not recursively re-prove every record. Keep logs outside tool-cleaned output, permit noted
  non-semantic corrections, and stop at the agreed delivery boundary. Extra work needs a concrete
  risk reason in the normal handoff, not a new configuration or approval process. Safety, required
  machine gates and explicit authorization remain binding.
- Nested skills in one session reuse unchanged context and successful doctor/gate results. Changed
  inputs invalidate affected results, and lifecycle boundaries still validate their mutations.
  Independent roles judge current inputs and evidence without automatically rebuilding equivalent
  environments. Use existing supported toolchains, caches and maintained synthetic test entry
  points; check required external-client availability early. Preserve isolation required by the
  contract and never embed credentials or sensitive runtime data in reusable scripts.
- Execution preparation and handoff follow `references/execution-preparation.md`: one preparation
  owner, minimal prerequisite checks before expensive work, reuse at the tool/build/runtime/state
  level actually justified, and concise updates in the existing plan/handoff. Safe preparation may
  overlap; final review and separated acceptance retain their judgement order. Reuse current
  source surveys/owner proposals, supplement missing input, and diagnose stalls before retrying.
  This adds no preparation report, registry, configuration switch or lifecycle gate.
- Cross-session handoffs explicitly carry the critical sourced constraints, actual evidence scope
  and continuation entry, and outstanding required checks. The receiver checks applicability in
  normal execution, without an acknowledgement turn. Recreated or substituted evidence records
  the reason, old/new provenance, retained/lost continuity and affected rows in the existing plan
  and acceptance/result mapping; unaffected valid results remain. Capability alone does not prove
  a required original-chain continuation. Source changes within existing scope add no approval;
  actual criterion or permission changes keep the existing authorization boundary.
- Same-Initiative discussion and handoff preferences may be inherited from an explicitly sourced
  current workbench, formal reference or handoff. Re-ask only unresolved or conflicting choices;
  mode/model preferences do not authorize creating a session or performing a merge/push. The
  discussion-completion confirmation and profiles-completed boundary still govern implementation.
- Integration matrices inherit all confirmed same-object, artifact, session and continuous-sequence
  requirements. Reused evidence must satisfy the linked conditions together. Separate capability
  runs cannot silently weaken a required continuous path; preserve valid results and execute only
  the missing affected path.
- Main-session responsibility cannot be delegated: a lower-cost model tier may prepare bounded
  work, but the main session owns authority, lifecycle decisions, gates and final verification.

## Policy Values Read, Never Assumed

| Value | Read from | Effect |
| --- | --- | --- |
| `workflow.scope_gate.enabled` | `workflow-profile.md` | whether Scope Gate blocks discussion entry |
| `workflow.scope_gate.split_default` | `workflow-profile.md` | whether a `split-default` score defaults to splitting |
| `workflow.quick_change` | `workflow-profile.md` | whether the bounded quick-change path exists at all |
| `workflow.review_required` | `workflow-profile.md` | whether independent review is mandatory |
| `workflow.verification_separate` | `workflow-profile.md` | whether verification runs in a separate session |
| `workflow.merge_requires_authorization` | `workflow-profile.md` | whether merge needs explicit user authorization |
| `workflow.initiative_integration_required` | `workflow-profile.md` | whether Initiative integration evidence is a merge precondition |
| `workflow.process_workspaces` | `workflow-profile.md` | explicit additional Wiki-relative process roots; built-in roots stay excluded |
| `verification.evidence_root` | `workflow-profile.md` | where immutable integration evidence is written |

## Change Surface

| Concern | Authority to update |
| --- | --- |
| Initiative intake, decomposition, discussion-entry behaviour | feature-workspace README/schema, `feature_workspace.py`, affected feasibility, discussion and progress skills |
| Lifecycle status and transition behaviour | `<FACTORY_ROOT>/skills/hl-feature-workspace/scripts/feature_workspace.py` |
| Lifecycle behaviour tests | `<FACTORY_ROOT>/skills/hl-feature-workspace/tests/test_feature_workspace.py` |
| Long-term wiki merge validator and inventory | `<FACTORY_ROOT>/skills/hl-wiki-merge/scripts` and its tests |
| Provenance lookup | `<FACTORY_ROOT>/skills/hl-history-trace/scripts` and its tests |
| Manual maintenance run, candidate selection and recovery | `<FACTORY_ROOT>/skills/hl-refactor` and its tests; existing lifecycle reader remains state authority |
| Shared process-workspace exclusions | `<FACTORY_ROOT>/engine/factorylib/workspaces.py`, layout/config generation and existing Wiki consumers |
| Operator process | feature-workspace README/schema for lifecycle changes; affected workflow skills plus this skill's `references/entry-point.md` and `references/workflow-contract.md` |
| Commit boundaries and commit packaging | this skill's `references/commit-boundaries.md`, the opt-in `packs/hl-commit` skill, and the generated `wiki/code-ai/_blocks/commit-granularity.md` block |
| Worktree and branch cleanup | this skill's `references/worktree-lifecycle.md` and the affected skill's cleanup steps |
| Actual Feature status | Feature and Initiative manifests, updated only through approved workflow boundaries |
