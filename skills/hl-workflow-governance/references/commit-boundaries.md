# Workflow Commit Checkpoints

At the checkpoints below, the coordinating agent commits the completed, verified work locally
within the task scope, before the next handoff or final report. Local staging and commits at these
checkpoints require no separate user authorization or handoff permission. Honor an explicit request
to defer commits. This rule supersedes earlier factory-generated guidance on commit approval.
Plan approval, work selection, session creation, merge and push follow their own rules.

## When to commit

| Checkpoint | Required evidence | Commit scope |
| --- | --- | --- |
| Leaf implementation handoff | Profiles complete and workspace gate passes | Confirmed decisions, implementation documents, Code AI profiles and their handoff manifest |
| Leaf delivery | Fixed review and separated acceptance pass, closure reaches `ready-to-merge / ready`, workspace gate passes | Reviewed implementation with its regression tests, documentation sync, and tracked closure evidence |
| Initiative integration | Required integration checks pass and PASS is registered against the actual sources | Tracked integration result and the evidence references needed to reproduce or understand it |
| Wiki merge closure | Full Wiki validator passes and the authorized authority switch is complete | Canonical changes, navigation and applicable retained-history routing and closure for the same Feature |
| Quick change or selected refactor delivery | Its existing verification and closure requirements pass | Verified change, affected documents or tests, and applicable tracked decision/evidence references |

Group work by one logical concern. A review finding corrected before delivery normally belongs with
the verified implementation it changed. Skip empty checkpoints and avoid commits for individual
discussion answers, gate reruns, intermediate edits and scan-only refactor outcomes. Review and
testing can identify uncommitted sources using a revision plus the relevant diff and new files.
Only an explicit immutable-source requirement warrants an earlier commit, with the same scope and
staging rules and an accurate statement of what is still pending.

## How to commit

- Use `$hl-commit` when enabled. Otherwise follow the project's Git policy and these shared rules.
  Use `repo.commit.format` and `project.language.commit` and honor stricter
  project restrictions. Push, merge and history rewrites require their own applicable authorization.
- Inspect the actual staged diff and include only the current concern. Isolate same-file changes
  only when their scope can be proven. Preserve unrelated staged and unstaged work, and exclude
  credentials, machine-local data and runtime artifacts. Compare staged sources with the reviewed
  and tested target. Recheck affected conclusions if the staged content changes the verified scope.
  Apply the repository and ordering rules in
  `<code_ai>/_blocks/commit-granularity.md`. In worktree mode, commit the code on the active Feature
  branch and the workspace records in the work repo. Report corresponding revisions for split repos
  or worktrees in the existing handoff.
- Record each actual commit ID and its scope in the handoff. If task scope, Git access or a
  required check blocks a commit, report the concrete reason and leave that work uncommitted.
  Continue unaffected work allowed by existing gates. A commit never advances lifecycle state or
  proves that a check passed. Reuse applicable evidence when committed content matches what was checked.

## Write messages for maintainers

Use a precise subject naming the affected capability and the resulting change. Include a short
body on every workflow checkpoint commit. A maintainer reading Git history should be able to find:

- The problem, decision or constraint that explains why the change was made.
- The substantive change and affected behavior, contracts or paths. Include compatibility,
  migration or rollback implications when relevant.
- The checks actually run and their results, or a stable tracked evidence reference. Identify
  material gaps and any reliance on previously verified results.
- A stable Feature, Initiative or Quick Change ID, tracked document or acceptance criterion when
  available and appropriate to the repository's visibility. Keep private paths and sensitive data
  out of commit messages. Use stable repository-relative references where possible.

Use only details that help explain the change. A stage name, a file inventory or a bare claim that
tests pass does not explain the decision or establish which source and behavior were checked.
