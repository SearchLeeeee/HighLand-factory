---
name: hl-history-trace
description: Use while reading canonical authority documentation when a user or an agent asks why a rule exists, what prior decision or evidence led to it, or requests provenance or history. Spawns an isolated subagent to route an explicit question from the current authority document through the external merged routing record into one retained non-authoritative Feature source, without loading historical context into the main session or leaking identifiers into canonical documents.
---

# History Trace

Operate read-only, and keep historical lookup out of the main session.

## Step 0 — Load factory context

1. Read `<work>/.factory/local.yaml`. If missing or unreadable, stop and tell the user to run
   `$hl-factory-init` (or `factory init`); never guess a path or interpreter.
2. Resolve `FACTORY_ROOT` (`factory_root`), `PYTHON` (`python`), and `WORK_ROOT` (the git
   top-level, or the directory containing `.factory/`).
3. Read `wiki/governance/workflow-profile.md` under `WORK_ROOT` for layout, language, gate switches
   and security boundaries. If it is missing or unreadable, stop and tell the user to run
   `$hl-factory-doctor`.
4. Confirm the registry path from the profile layout; the default is
   `wiki/feature-workspace/registry.yaml`.
5. If the profile or config contradicts the request, route to `$hl-workflow-governance` instead of
   improvising.

Fail closed: missing config, missing profile or a failing gate stops the lookup with one concrete
repair instruction. An audit that cannot resolve its inputs reports a gap; it never scans the
workspace to improvise one.

## Mandatory Isolation

The main session must spawn a fresh subagent for every history lookup. Prefer an actually available
lower-cost model tier for this bounded read-only task. Never claim a requested model tier was used
when it was unavailable.

The main session passes only:

- the user's exact question;
- the canonical authority document path and the relevant current section, if known;
- the registry path;
- this skill's path;
- the fixed handoff contract below.

The main session must not run the locator, open tombstones, read `history-route.yaml`, search
retained directories, or read historical source files. If subagents are unavailable, stop and report
that isolated history lookup is unavailable; do not absorb the lookup into the main context.

## Subagent Procedure

1. Read the canonical section first and preserve it as current authority.
2. Locate the routing candidate:

```bash
<PYTHON> <FACTORY_ROOT>/skills/hl-history-trace/scripts/trace_feature_history.py locate --registry wiki/feature-workspace/registry.yaml --authority-doc <canonical-doc> --question "<question>"
```

3. If no candidate is returned, report a provenance-routing gap. Do not scan every retained
   directory.
4. Route the question inside the selected candidate:

```bash
<PYTHON> <FACTORY_ROOT>/skills/hl-history-trace/scripts/trace_feature_history.py route --route-file <history-route.yaml> --question "<question>"
```

5. Read only the returned relative source files and headings.
6. Expand within that one retained root only when the route is incomplete, and disclose the fallback
   in the handoff.
7. Verify integrity when a checksum manifest is present:

```bash
<PYTHON> <FACTORY_ROOT>/skills/hl-history-trace/scripts/trace_feature_history.py verify --root <retained-feature-root> --manifest <retained-feature-root>/history-checksums.sha256
```

8. Return the fixed compact handoff. Do not return raw document dumps or unrelated history.

Read `references/history-route-schema.md` only when diagnosing a route or a post-validator retained
bundle.

## Fixed Handoff

Return at most 700 words with exactly these fields:

```text
AUTHORITY: <canonical path + current authoritative conclusion>
HISTORICAL_RATIONALE: <question-specific explanation, explicitly non-authoritative>
SOURCE_REFS: <retained relative file + heading only>
INTEGRITY: <PASS/FAIL/UNKNOWN + checksum manifest>
CONFLICTS_OR_GAPS: <none or concise list>
LOOKUP_SCOPE: <candidate count, files/headings read, fallback used yes/no>
```

The main session answers from `AUTHORITY` first and may use `HISTORICAL_RATIONALE` only as labelled
provenance. It must not ingest or reproduce raw retained material.

## Isolation Rules

- Never add Feature or Initiative IDs, retained paths, tombstone links or history routes to canonical
  wiki documents.
- Never add retained material to active Initiative or Feature `context_refs`.
- Never use retained material to override current authority or seed a new Feature or Initiative; new
  work reads the canonical wiki baseline.
- Never mutate lifecycle state, retained material, tombstones, canonical documents, commit state or
  merge state during an audit.
- Include historical IDs and paths only in the transient subagent handoff or an explicitly requested
  audit artefact outside canonical authority documents.
- Write the handoff in the user's language and use `project.language.docs` for any quoted canonical
  prose; keep verdict labels and paths ASCII.
