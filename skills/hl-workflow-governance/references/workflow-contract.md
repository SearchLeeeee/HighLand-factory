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
- An Initiative is not mergeable until all active Leaf Features are ready and new Initiative-level
  integration evidence has passed.
- Integration evidence is local, bound to one immutable run, and distinct from per-Feature sealed
  evidence.
- Feature merges happen only after `initiative-merge-ready` passes and, when
  `workflow.merge_requires_authorization` is true, after explicit user authorization is obtained,
  in dependency-topological order.
- For each Feature the fixed order is: semantic wiki merge, affected-MOC updates, full long-term
  wiki validation excluding the feature and quick workspaces, retained-history transformation
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
- When the user must choose among two or more viable alternatives, use the structured choice panel
  when available: 2-3 mutually exclusive options, the recommended one first, the client-provided
  `Other` for custom input, and one concise plain-text question only as a fallback. This
  interaction rule never weakens an authorization or machine gate.
- User authorization is required for actual merge, deletion, commit and push operations whenever
  the profile requires it.
- Commit boundaries are governed by `references/commit-boundaries.md`, not scattered through prose.
  Commits happen only behind a passing gate, at one of the named boundaries; a commit authorization
  is never a push authorization; the freeze-then-seal order means implementation is committed to
  obtain the revision that review, verification and Initiative integration run against, and the
  evidence naming that revision is committed afterwards. Commit boundaries add no lifecycle state,
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
- Review conclusions bind to a frozen revision and the SHA-256 fingerprints of the reviewed source
  set. A changed revision or reviewed file invalidates that run; remediation re-review is limited to
  changed files and affected findings unless the contract, scope or dependency direction changes.
- Quick Change records test impact, selected commands and reasons for omitted commands. Full
  verification remains required for shared contracts, persistence/migration, security/permissions,
  cross-module changes or unbounded impact. Context compaction is required only for a real session
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
| `verification.evidence_root` | `workflow-profile.md` | where immutable integration evidence is written |

## Change Surface

| Concern | Authority to update |
| --- | --- |
| Initiative intake, decomposition, discussion-entry behaviour | feature-workspace README/schema, `feature_workspace.py`, affected feasibility, discussion and progress skills |
| Lifecycle status and transition behaviour | `<FACTORY_ROOT>/skills/hl-feature-workspace/scripts/feature_workspace.py` |
| Lifecycle behaviour tests | `<FACTORY_ROOT>/skills/hl-feature-workspace/tests/test_feature_workspace.py` |
| Long-term wiki merge validator and inventory | `<FACTORY_ROOT>/skills/hl-wiki-merge/scripts` and its tests |
| Provenance lookup | `<FACTORY_ROOT>/skills/hl-history-trace/scripts` and its tests |
| Operator process | feature-workspace README/schema for lifecycle changes; affected workflow skills plus this skill's `references/entry-point.md` and `references/workflow-contract.md` |
| Commit boundaries and commit packaging | this skill's `references/commit-boundaries.md`, the opt-in `packs/hl-commit` skill, and the generated `wiki/code-ai/_blocks/commit-granularity.md` block |
| Worktree and branch cleanup | this skill's `references/worktree-lifecycle.md` and the affected skill's cleanup steps |
| Actual Feature status | Feature and Initiative manifests, updated only through approved workflow boundaries |
