---
name: hl-wiki-maintain
description: Use when explicitly asked to organize the whole current Wiki, review incremental task experience or migrate the authority layout of a named existing project.
---

# Manual Wiki maintenance

For user-facing questions apply the shared Socratic questioning guidance in `<FACTORY_ROOT>/skills/hl-workflow-governance/references/socratic-questioning.md`.

1. Resolve the work repo with `factory resolve --work <WORK_ROOT> --json`. Read the Wiki home, current role memory when present and the generated profile. Follow `<FACTORY_ROOT>/skills/hl-workflow-governance/references/wiki-memory.md` for evidence, navigation, scheduling and bookmarks. Coordinate with any Wiki merge before starting.
2. Survey the whole Wiki for structure, current links, duplicates, retired claims and missing routes. Run the normal Wiki gate for a baseline. Read incremental experience with `factory memory-scan --work <WORK_ROOT>`; use existing evidence before requesting any additional work. A small, clearly bounded uncertainty may use an existing verification path. Keep unsupported hypotheses pending.
3. Repair demonstrated problems. Add an omitted topic only when an existing effective contract **and** acceptance evidence support it. Code observations can document implementation; they cannot establish product commitments. Resolve conflicts through targeted history tracing first and continue unrelated items.
4. Run the standard full `factory gate wiki --work <WORK_ROOT>` after applying edits. Explain affected topics, retained exceptions and any unresolved questions. Record provenance and incremental coverage according to the shared reference in normal changes.

## Explicit migration of an existing project

Start only when the user names the existing work repo for migration. Ordinary upgrade preserves its home and role memories. Run the read-only `factory migrate-wiki --work <WORK_ROOT>` preflight. Record the original revision and inventory old authority, inbound links, aliases and actual process roots. Stage the new authority layout separately from the effective entry point. Preserve existing process locations and sealed history.

Independently reread the old originals against the candidate layout. For each rule compare its conditions, exceptions, scope and acceptance boundary in both directions; record omitted or broadened meaning in the current working discussion. Use targeted workspace history to investigate genuine conflicts and ask only where evidence cannot decide. Correct the candidate before switching. Confirm the resolved paths still reach the original registries, process records and history, and retain necessary entry points. Prepare and independently review the actual replacement pages first. After semantic equivalence without expansion and structural validation, activate the reviewed layout with `factory migrate-wiki --work <WORK_ROOT> --apply`. Activation preserves prepared pages, old process roots and the resolved profile location. Check the full Wiki and workspace gates against the effective layout before closing. Do not manufacture task reports, rewrite archived evidence or reinitialize the project.
