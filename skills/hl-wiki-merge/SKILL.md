---
name: hl-wiki-merge
description: Use when staged Markdown must be folded semantically into the long-term wiki authority documents and the staged source retained as non-authoritative history. Covers preflight, inventory, semantic apply, affected-MOC updates, the full wiki validator gate, retained-history transformation and the authority switch.
---

# Wiki Merge

Use this skill to absorb useful staged documentation into the long-term wiki at `wiki/`. The merge
is semantic: update existing authority documents in their current style and structure, and create a
new wiki document only for a genuinely new topic.

The staged source path is retained after a successful merge as historical, non-authoritative
material. Never delete it as part of this skill. Agent-profile content under `code-ai` and discussion
content under `discussion` or `discussions` is never merged and is also retained. Retained-history
marker files are metadata, not merge candidates, so reruns cannot re-import their own tombstone.

## Step 0 — Load factory context

1. Read `<work>/.factory/local.yaml`. If missing or unreadable, stop and tell the user to run
   `$hl-factory-init` (or `factory init`); never guess a path or interpreter.
2. Resolve `FACTORY_ROOT` (`factory_root`), `PYTHON` (`python`), and `WORK_ROOT` (the git
   top-level, or the directory containing `.factory/`).
3. Read `wiki/governance/workflow-profile.md` under `WORK_ROOT`. It defines language, layout,
   owners, commands, the evidence root, the merge-authorization switch and security boundaries. If
   it is missing or unreadable, stop and tell the user to run `$hl-factory-doctor`.
4. Run gates through the engine, not by composing paths: `factory gate wiki --work <WORK_ROOT>` and
   `factory gate workspace --work <WORK_ROOT>`.
5. Use `project.language.docs` for the wiki prose you write, and take the merge-authorization and
   Initiative-integration switches from the profile. Never assume them.
6. If the profile or config contradicts the request, route to `$hl-workflow-governance` instead of
   improvising.

Fail closed: missing config, missing profile, a failing gate, or an unresolved language policy stops
the skill with one concrete repair instruction.

## Required Input

Require a staged source path: a Markdown file, or a directory containing Markdown files. The
canonical wiki root is `wiki/` under `WORK_ROOT`, resolved from the profile's layout section rather
than assumed.

## Exclusion Rules

Never merge Markdown files whose path contains any segment named:

- `code-ai`
- `discussion`
- `discussions`

Also skip the retained-history marker files `RETAINED_HISTORY.md`, `history-route.yaml` and
`history-checksums.sha256`. Apply path-segment checks case-insensitively. Leave excluded files in
the retained source path and report them as skipped. A Feature whose `feature.yaml` has
`phase: merged` is historical input and must not be re-imported.

## Workflow

Five explicit phases. Keep JSON receipts in a per-run evidence directory outside both the supplied
source and the canonical wiki. For a registered Feature, durable closure evidence belongs in the
governed feature workspace where its contract requires it.

### 1. Preflight

1. Resolve `PYTHON` and `FACTORY_ROOT` from `.factory/local.yaml`. Verify the inventory script, the
   validator script and `feature_workspace.py` exist before writing anything.
2. Resolve the source path and capture its kind, Markdown SHA-256, and the starting version-control
   status. For a registered Feature, pass `initiative-merge-ready` through `$hl-feature-workspace`
   before inventory.
3. Stop if the Feature is already `phase: merged`. Check the canonical wiki root, planned target
   paths, target conflicts, and whether required parent directories can be created.
4. Write a preflight receipt with resolved paths, tool paths, source hash, wiki root, baseline
   version-control status, and planned output files. Do not edit anything during preflight.

### 2. Inventory And Mapping Plan

1. Run the inventory script and save its output as the inventory receipt:

```bash
<PYTHON> <FACTORY_ROOT>/skills/hl-wiki-merge/scripts/inventory_llm_wiki_merge.py --source <staged-path> --format json
```

2. Read the current wiki overview documents (`wiki/README.md`, `01-reading-guide.md`,
   `02-file-authority-map.md`), then inspect only likely target documents and nearby style examples.
3. Map every eligible source to exactly one canonical target and disposition before editing:

```text
source -> canonical target -> action (update/create/skip) -> reason -> conflict
```

Stop and ask when authority cannot be inferred or the mapping contains unresolved conflicts. Never
begin a partial merge.

### 3. Canonical Apply

1. For a registered Feature, confirm explicit authorization before the first canonical write when
   `workflow.merge_requires_authorization` is true.
2. Apply only the completed mapping to canonical wiki documents and affected MOCs. Record
   before/after hashes in the apply receipt.
3. Keep integration semantic and concise. Do not modify source Feature manifests, retained-history
   files, tombstones or registry routing during this phase.

### 4. Validate

1. Verify that every eligible source fact has a canonical target or an explicit duplicate, obsolete
   or excluded disposition.
2. Confirm the source hash still matches the preflight receipt, then run the full long-term wiki
   validator and save its exit code, scan counts, errors and warnings in the validator receipt:

```bash
<PYTHON> <FACTORY_ROOT>/skills/hl-wiki-merge/scripts/validate_llm_wiki.py --wiki-root wiki --format json
```

3. Any validator error stops the workflow. Leave the Feature `ready-to-merge / ready`; do not
   transform retained history or switch authority.

### 5. Close And Retain History

For an ordinary staged path, record the retained source path and leave it intact. For a registered
Feature, only after valid full-wiki validation, transform the complete source into routed retained
history, update lifecycle through `feature_workspace.py`, generate checksums last, remove active
manifest discovery, and write a close receipt.

Generate the final report from the phase receipts and the version-control status delta against the
preflight baseline. Distinguish `canonical_apply=complete`, `validator=valid` and
`feature_close=complete`; a valid validator alone does not mean the Feature merge is complete.

## Merge Quality Rules

Do not append the staged document to the end of an existing wiki file unless that target is
explicitly an append-only log.

Prefer precise integration:

- Convert staged decisions into the existing decision or authority sections.
- Convert staged requirements into the matching product, domain, architecture, implementation,
  testing or runtime documents.
- Fold examples and edge cases into the relevant section instead of preserving staging order.
- Remove duplicated wording while preserving distinct constraints, acceptance criteria and test
  expectations.
- Preserve source meaning even when rewriting the prose.

When staged content conflicts with current wiki content, do not silently overwrite and do not route
the conflict into deleted legacy decision, discussion or open-question roots. Stop the merge and ask
the user when authority cannot be inferred.

## Source Retention And Authority

After the semantic merge, the affected-MOC updates and a successful full-wiki validation:

- Do not delete, move, truncate or repurpose the supplied source path.
- Retain eligible and excluded source documents for audit, provenance and historical reconstruction.
- Treat the retained source as historical and non-authoritative. The merged long-term wiki is the
  sole authority for current product and implementation facts.
- Remove its active manifest reference when replacing the Feature with the external merged routing
  record. Default registry loading, progress reports, new Initiative/Feature creation and ordinary
  context discovery must not scan the retained directory.
- Never add a retained merged source document to an active Initiative or Feature `context_refs`; the
  validator rejects this. Use canonical long-term wiki documents instead.
- Read retained source only for an explicit provenance or historical-audit request, reached through
  the merged routing record. Do not load it by default into a new session.
- Do not keep editing a merged Feature source to introduce new requirements. Create a new Feature
  that reads the canonical wiki baseline.
- A retained source path does not make a partial or failed merge successful. If the semantic merge
  or validation fails, do not mark the Feature merged.

## Retained History Transformation

Before replacing a registered Feature's active manifest reference with its merged routing record:

1. Set the retained `feature.yaml` to `phase: merged`, `state: completed`.
2. Add `RETAINED_HISTORY.md` stating that the directory is historical, non-authoritative, excluded
   from default discovery, and readable only through an explicit history audit.
3. Add `history-route.yaml` following
   `<FACTORY_ROOT>/skills/hl-history-trace/references/history-route-schema.md`. Build semantic question
   routes to narrow source files and headings, and to canonical targets. Feature and Initiative IDs
   may exist inside this retained bundle and the routing record, but never inside canonical wiki
   documents and never as reverse-history links.
4. Generate `history-checksums.sha256` after every retained-history file is final:

```bash
<PYTHON> <FACTORY_ROOT>/skills/hl-history-trace/scripts/trace_feature_history.py checksum --root <retained-feature-root> --output <retained-feature-root>/history-checksums.sha256
```

5. Put `path`, `marker`, `route` and `checksum_manifest` in the external merged routing record.

Historical lookup happens only through `$hl-history-trace`, which delegates the lookup to a fresh
isolated subagent. Ordinary sessions must not open the retained bundle.

## Machine Gates

Use the inventory script only for discovery and JSON receipt generation; it never modifies files and
never decides semantic targets.

After the semantic merge and the affected-MOC updates, run the independent validator before any
retained-history transformation. It uses only the Python standard library, always scans the complete
long-term wiki, and excludes every path under the feature and quick workspaces. It fails on
Obsidian-style wikilinks, broken local Markdown links or ASCII anchors, Markdown files unreachable
from the wiki home, shortest MOC routes deeper than three links, feature-workspace traversal,
deleted legacy-root references, and a competing root-level home. It existence-checks local image
targets without treating images as navigation edges, strips URL query and fragment components when
resolving files, accepts platform separators and URL-encoded paths, ignores fenced and inline code
for link syntax and default-discovery references, allows existence-checked links within the
repository root without adding them to the wiki graph, and never fetches external URLs. Non-ASCII
heading anchors are warning-only in this version.

Navigation edges are same-line inline Markdown links to `.md` files originating only from MOCs named
`README.md`, `index.md` or `_index.md`; leaf-to-leaf links are validated but do not establish
reachability. ATX headings and explicit HTML `id` or `name` anchors are recognised. Reference-style
links, HTML navigation, setext headings and generated-site route rewriting are not interpreted; use
explicit inline Markdown links for governed MOC routes.

Any validator error leaves a registered Feature at `ready-to-merge / ready`. Do not create a
tombstone, switch authority, transform retained history, or mark it merged/completed. Correct the
semantic merge or the MOC routing and rerun the complete validator.

## Registered Feature Closure Gate

When the source is a registered feature workspace, use `$hl-feature-workspace` before inventory or
merge.

Before the first Feature merge for an Initiative, require:

```bash
<PYTHON> <FACTORY_ROOT>/skills/hl-feature-workspace/scripts/feature_workspace.py initiative-merge-ready --registry wiki/feature-workspace/registry.yaml --initiative <Ixxx>
```

This rejects an Initiative until every non-cancelled, non-superseded Leaf Feature is
`ready-to-merge / ready` and Initiative-level integration testing passed with local evidence. If the
handoff does not exist yet, generate it once with `initiative-integration-handoff` through
`$hl-feature-workspace`, and let the integration owner register PASS with
`initiative-integration-result`. After the Initiative preflight passes, merge Features individually
in `depends_on` topological order.

For each Feature, require:

- a Leaf Feature in `ready-to-merge / ready`;
- passed acceptance;
- closure data naming validation evidence and intended canonical wiki targets;
- no blocking child;
- a valid feature-workspace dependency graph.

The five phases apply to each Feature. During the close phase, also:

1. Verify every durable requirement, contract, test expectation, limitation and operations fact has
   a canonical long-term wiki target.
2. Record the Feature as `merged / completed`; upsert the tombstone into the parent
   `initiative.yaml` and the global `registry.yaml` with canonical paths, merge evidence, source
   relationships and retained-source routing.
3. Switch authority to the validated wiki, update the Initiative aggregate state, validate the
   feature workspace, and remove the retained Feature from active manifest references and default
   context discovery.

The tombstone stays compact historical routing data; it does not imply the source directory was
deleted. The retained source is provenance only, and the validated long-term wiki is the sole
product and implementation authority. Never require excluded discussion or agent-profile content to
understand merged behaviour. If the semantic merge or the full-wiki validation fails, the Feature
stays `ready-to-merge / ready`: do not add a tombstone, switch authority, transform retained history,
or mark it merged/completed. This gate introduces no lifecycle state and no manifest field.

## File I/O Routing

Inventory and inspect staged and current wiki files with read tools. Make semantic document and MOC
edits with file-edit tools, preserving UTF-8 and recording before/after hashes. Never use generic
writes for lifecycle manifests; route Feature transitions through `feature_workspace.py`. Keep phase
receipts with the run evidence. Run the full long-term wiki validator only at the governed merge
gate, after all affected MOCs are updated, and save its JSON result.
