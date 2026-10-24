# Commit Boundaries

Load factory context first: read `.factory/local.yaml` and `wiki/governance/workflow-profile.md`
before using this file. Commit format and language come from `repo.commit.format` and
`project.language.commit`; push policy and authorization come from the profile.

This reference names **when** a commit is allowed in the workflow. It is process guidance executed
by the opt-in commit pack (`$hl-commit`), not a lifecycle mechanism: it adds no phase, no state, no
manifest field and no state-machine branch. The only lifecycle authority stays
`feature_workspace.py` plus the feature-workspace README and schema. A commit never records a
transition, and a transition is never inferred from a commit.

When `packs.enabled` does not contain `commit`, follow the project's documented commit policy; do
not invent one and do not treat this file as that policy.

## The Two Rules Behind The List

1. **Commit only behind a passed gate.** Every boundary below names the check that must already be
   green. Committing a red gate, or an implementation that review or acceptance has not yet passed
   as if it were complete, is the failure this list exists to prevent.
2. **A commit authorization is not a push authorization.** Push remains a separate explicit
   instruction at every boundary. No boundary in this file implies a push.

## Required Boundaries

| # | Boundary | Gate that must pass first | Commit contains | Why it must be atomic |
| --- | --- | --- | --- | --- |
| 1 | Initialization or adoption complete | `factory doctor` plus the workspace and wiki gates | Rendered skeleton, generated config, init record, baseline evidence | This is the only chance to start repository history from a reproducible baseline; an adopted repo is tagged before the mechanical generation so its original state stays recoverable |
| 2 | Initial decomposition sealed | `finalize-decomposition` plus a passing `validate` | Registry, Initiative manifest, every candidate Feature manifest with `depends_on`, `wave` and Scope Gate | Discussion admissibility and dependency release are derived from these manifests; an uncommitted edit can silence a `must-split` verdict with nothing in history showing it |
| 3 | Discussion conclusions and implementation documents complete | `gate workspace` passes with the discussion documents written | Workbench, confirmed conclusions, domain implementation documents | The orchestrator's preflight reads these as the contract; the implementation session starts fresh and can only trust what is on disk |
| 4 | Code AI profiles complete | `gate workspace` passes at `code-ai-profiles / completed` | Feature `code-ai/` profiles and their routing README | This is the exact input the implementation session is dispatched from |
| 5 | Implementation frozen | Implementation work complete and `gate workspace` passes | Code, documentation sync, and anything else that will be reviewed | Review, verification and the Initiative integration run must all point at one revision; an unfrozen tree makes every later result unreproducible |
| 6 | Review passed, including its fixes | The fixed review gate passes after required fixes and re-review | Review evidence and the remediation it demanded | Findings and their fixes must be reviewable and revertable together |
| 7 | Acceptance and closure complete | Acceptance criteria all pass, closure recorded, and `ready-to-merge / ready` is recorded through the state machine | Acceptance evidence, closure data, final `feature.yaml` | A dependency counts as satisfied only when this state is real on disk for the downstream Feature |
| 8 | Initiative integration evidence sealed | Handoff generated, the run executed at the frozen revision on a clean tree, and the result registered | Handoff, new immutable evidence root, Initiative integration status | Integration evidence must name a revision and a clean worktree, or it cannot be compared against any later run |
| 9 | Per-Feature wiki merge closure | Full long-term wiki validation passes, then retained history, `merged / completed` and authority switch complete | Canonical wiki edits, affected MOCs, validator receipt, tombstone and routing record, retained-history marker, route and checksums | The authority switch is a multi-file state change; if it is not atomic, "which version is current" stops being auditable. One commit per Feature, in `depends_on` topological order |
| 10 | Quick change completed | Its required repeatable verification artefact exists and the record reaches `completed` | Quick record, fix, verification evidence | The lightweight path needs one revertible point so its evidence stays comparable with the Feature path |

## Advisory Boundaries

Commit these when the project wants the provenance, not because a gate demands it:

| Boundary | Note |
| --- | --- |
| Feasibility conclusions | Worth a commit when the confirmed constraints become `context_refs` for downstream work; otherwise absorb them into boundary 3 |
| Workflow maintenance (skills, engine, schema, tests, prose) | Must follow its own green checks, and must never be mixed into a business Feature commit |
| `factory upgrade --apply` | Commit the generated files with their digest together so the upgrade is one revertible step |

## Two Packaging Modes

Choose the mode per boundary; never mix them inside one boundary.

- **State wrapper** (2, 3, 4, 6, 7, 9, 10): the gate passes, then the state and the evidence that
  justify it go into one commit.
- **Freeze → verify → seal** (5, 7, 8): commit the implementation state first to obtain revision A,
  run review, verification and the Initiative integration run against A with a clean worktree, then
  commit the evidence that names A. Because the evidence root lives inside the repository, running
  the checks first necessarily dirties the tree and invalidates the next run — the order is not
  negotiable.

A commit may be cited as evidence only when the worktree was clean at that revision.

## Repository Mode And Worktrees

- `mono`: code, wiki and evidence share one repository. Documentation commits precede code commits
  inside the same boundary.
- `split`: the wiki repository and the code repository are committed separately and never combined.
  A wiki-only boundary leaves the code repository untouched, and the handoff names both revisions
  and their correspondence.
- Worktree mode splits boundaries 5 and later into two commit lines: code lands on the Feature
  branch inside the worktree, while manifests, evidence and the workspace gate stay in the work
  root. Report the correspondence, and never merge the worktree back before the Feature is
  `ready-to-merge / ready`.

## Never A Boundary

- The end of each discussion question. Lifecycle state is written at skill boundaries only, and
  question-level progress is not recorded.
- Each validator or gate re-run. Reruns produce receipts, not commits.
- Any failing gate. Fix the cause, then commit.
- Unreviewed or unaccepted implementation, presented as done.
- Any push. Push needs its own authorization and is never bundled into a boundary.
- An amend, rebase or force-push of shared history, without explicit user authorization.

## Interaction With Other Gates

Automatic commits are never authorized by this file; each one still needs the commit authorization
the profile or the user provides. When a boundary and an authorization disagree, the authorization
wins and the boundary stays open. Escalation, merge, deletion and push authorizations are separate
and are not granted here.
