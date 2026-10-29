# Worktree Lifecycle And Cleanup

Load factory context first: read `.factory/local.yaml` and `wiki/governance/workflow-profile.md`
before using this file. The worktree path and branch name are the ones the implementation session
recorded; `repo.mode`, `repo.default_branch` and `workflow.merge_requires_authorization` come from
the profile.

This reference is the **only** rule source for retiring a dedicated git worktree and its Feature
branch after implementation. Other skills reference it and never restate the conditions. Cleanup is
an operational action, not a workflow phase: it adds no lifecycle state, no schema value, no
manifest field and no state-machine branch, and it never edits `feature.yaml`. The lifecycle
authority stays `feature_workspace.py` plus the feature-workspace README and schema.

## Reclaim Preconditions

Every condition must hold before a worktree or branch is reclaimed:

1. The Feature is `ready-to-merge / ready`, or already `merged / completed`.
2. Its code is merged into `repo.default_branch`. When `workflow.merge_requires_authorization` is
   true, the explicit authorization is recorded.
3. `git status` inside the worktree is clean.
4. The branch is merged and holds no commit that is not already reachable from `repo.default_branch`,
   so no unpushed or unmerged commit is lost.

A `ready-to-merge / ready` Feature becomes reclaimable only after its worktree merge-back is complete.
Until then the worktree still holds the implementation that review, verification and acceptance
evidence name.

## Never Reclaim

- Uncommitted changes in the worktree. Stop and wait for a human decision; never `stash`, discard,
  reset or delete on your own initiative.
- Unmerged commits on the Feature branch.
- A Feature that is `blocked` or `abandoned`.
- Commits by someone else on the branch.
- Anyone still using the worktree: an active subagent, an open editor, or a running service whose
  path resolves inside it.

When any of these is uncertain, keep the worktree and branch and report what blocks cleanup. A
skipped cleanup is cheap; lost work is not.

## Reclaim Order

1. Confirm before touching anything: `git worktree list`, `git -C <worktree> status --porcelain`, and
   `git -C <worktree> log --oneline <repo.default_branch>..HEAD`. An empty range means no unmerged
   commits. Compare the result with the merge commit recorded for the Feature.
2. Prove the branch is merged into `repo.default_branch` before deleting it, using the repository's
   own merge check rather than a recollection of the merge.
3. Remove the worktree with `git -C <owning repository> worktree remove <worktree path>`. Do not force
   the removal past a dirty tree, a registered lock or a path that is still in use.
4. Delete the branch with the safe form that refuses an unmerged branch (`git branch -d`). A forced
   delete (`-D`), a reset or a forced push needs explicit human authorization and a stated reason.

Run the steps in that order. Deleting a branch before its merge is proven, or removing the worktree
before capturing what it contains, is the failure this order exists to prevent.

## Report

Report both sides, not only the deletions:

- Reclaimed: every worktree path, its branch, the Feature id it belonged to, and the commit that
  merged it into `repo.default_branch`.
- Retained: every worktree, branch or Feature left in place, with the concrete reason (uncommitted
  change, unmerged commit, blocked or abandoned state, foreign commit, or active user).
- Authorization: the recorded merge authorization when `workflow.merge_requires_authorization` is
  true.

A missing or unreadable worktree registration is reported as a gap; it is not evidence that the
directory was already cleaned up.

## Boundaries

- Cleanup is never a lifecycle transition and is never recorded in `feature.yaml`.
- Cleanup is not a workflow phase, milestone or acceptance criterion.
- Cleanup is not a commit boundary. If the project wants a provenance commit for a cleanup record,
  the ordinary rules in `references/commit-boundaries.md` apply.
- A worktree is code isolation only. Removing it says nothing about the Feature's review,
  verification, acceptance or wiki-merge state, and never changes any of them.
- The worktree and its branch belong to one Feature. A shared or reused worktree is outside this
  file; keep it in place and report it instead of inventing a lifecycle rule for it.
