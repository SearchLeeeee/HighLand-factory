# Wiki memory and task experience

## Entry and routing

On an initialized work repo load the machine configuration and run `<PYTHON> <FACTORY_ROOT>/engine/factory.py resolve --work <WORK_ROOT> --json`. Use the returned Wiki and process paths throughout the task, including delegated prompts. Read the resolved Wiki's `README.md` first. Select the current responsibility from the assignment or Code AI profile, then read the corresponding page in `role_memory` if present. A missing role page is an ordinary skip. Follow the current topic links needed for this task and read the resolved `workflow_profile` for configuration and gates. A role page can change what to inspect or how to act under stated conditions. The Code AI profile remains binding for responsibility, write scope and handoffs.

New work repos use `factory.template: workspace-v2`. The Wiki contains current knowledge. The sibling process tree is resolved through `workflow.workspace_root`. Resolve `feature_workspace`, `quick_workspace`, `refactor_workspace` and `registry` separately, including for legacy projects. Existing process roots, task paths and sealed histories retain their locations across Wiki redesign. Treat placeholders in skill commands as resolved paths, including where the work repo uses a customized Wiki name.

Place product intent, business rules and accepted behavior under `product/`; place engineering implementation, operations and maintenance under `engineering/`. Give each fact one authoritative body. Role pages link across roles or into the shared body where that changes a role's action. Put guidance on the home only if reading it in advance changes actions for **every** responsibility. Use `by-type.md` for cross-cutting lookup: each topic appears once with a link to its canonical page, without reproducing its body. Use MOCs for navigation, or an explicit `## 子页导航` on a topic or role page for its direct child links. Keep canonical pages reachable from the home in at most three navigation links. Ordinary references undergo broken-link checking and do not shorten the navigation route.

## Capture at work time

When a project explicitly separates a former process root, the resolver also returns
`retained_*` paths. New tasks and current writes use the active paths. Use retained paths
only on an explicit history lookup. Keep the active Feature number counter continuous and
move any open work to the active root before registering the former root as retained. The
active registry may declare `canonical_path_aliases` from old Wiki-relative paths to
their current targets for history lookup without rewriting sealed tombstones. A string target
applies to all matching Feature records. For an old page split across new topics, use a
mapping from the real retained Feature IDs to one target or a list of targets. Each target
can include a section anchor.

```yaml
canonical_path_aliases:
  validation/baseline.md:
    I007-F02:
      - engineering/baseline.md#coverage
      - product/area-a/README.md#behavior
    I007-F03: engineering/baseline.md#setup
```

Register an ID only when its retained record cites the old path and supports the new topic.
A new page lookup includes the Features mapped to its sections. A lookup with an anchor
requires that anchor. Initiative evidence without a Feature routing record keeps its own
evidence reference.

When an observation could change a future action, use the existing task's writable process root. Write `experience.md` or, for independent subtasks, `experience-<subtask>.md` only as needed. Use a few lines identifying the observed fact and evidence reference, any hypothesis separately, and a suggested check. Feature and Initiative owners use the relevant Feature or Initiative root, refactoring owners the run root, and Quick owners `<quick_workspace>/tasks/<id>/` even when the status record moves. There is no shared intake directory. A read-only answer or a conversation with no task workspace reports the observation to the user, who decides whether to save it. Never modify a sealed task.

## Assess and adopt

For a targeted merge, run `factory memory-scan --work <WORK_ROOT> --task <task-root>` once per distinct task root resolved by `$hl-wiki-merge`. The targeted scan reads one directory at a time, so an Initiative root and its in-scope Leaf roots are separate scans. Run `factory memory-scan --work <WORK_ROOT>` for incremental whole-Wiki maintenance. With no valid bookmark start with dirty, untracked and explicitly identified clues; do not traverse all committed history. Review candidates against evidence and current contracts. Experience is an input to judgment; never import its file as a product authority. A verified observation may be adopted on its first occurrence. State the applicable condition and what the next person should do; preserve relevant exceptions. Keep unverified hypotheses pending with the suggested check, and avoid turning observations into stronger claims, general mandates or new product commitments. If a conflict remains, invoke `$hl-history-trace` with the specific authority and question to inspect the relevant workspace decision, evidence or acceptance. Ask only about the unresolved conflict and continue independent work.

For accepted experience keep provenance on the history side in an existing writable task record or in the ordinary change's Git commit message. Sealed sources stay intact. Carry `Wiki-Experience-Reviewed-Through: <sha>` in a normal Git commit only for a completely reviewed incremental range; a targeted merge never advances past other unreviewed tasks. Use the scan's reviewed source revision, not the commit being created. Without an ordinary change, do not create a bookmark-only commit. Do not add a report file or a reciprocal link from current authority into excluded process history.

## Scheduling and retirement

At scheduling time check whether a Wiki merge or manual maintenance is underway for the same Wiki and arrange the other operation after it. Recheck before starting canonical edits. This is coordination between these two operations; it does not impose a project-wide lock. During merge, review only facts, role lessons, links and retirements actually affected by the source. Apply confirmed long-term facts and affected lessons in the same authority switch, then run the standard full-Wiki gate. Whole-Wiki maintenance also looks for historical leftovers. When evidence establishes retirement, remove obsolete text or narrow its conditions in this pass. Preserve live exceptions, applicable links and necessary old entry points. Git and process workspaces retain history.
