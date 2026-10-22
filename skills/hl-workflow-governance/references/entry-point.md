# Workflow Governance — Entry Point

Load factory context first: read `.factory/local.yaml` and then
`wiki/governance/workflow-profile.md` before making any workflow decision. If either is missing,
stop and route to `$hl-factory-init` or `$hl-factory-doctor`; do not reconstruct values from memory,
chat history or directory guesses.

This file is the entry point for a fresh session. It governs Feature lifecycle, cross-Feature
dependencies, Initiative integration and documentation merge gates. It does not replace product
decisions and does not implement a business Feature.

## Scope

Use this skill for:

- creating, validating, transitioning, blocking and closing Initiatives and Leaf Features;
- `ready-to-merge` dependency rules and per-Feature merge-ready checks;
- the Initiative integration-test handoff, evidence registration and `initiative-merge-ready`
  after every Leaf Feature is ready;
- merging Feature documents one at a time in `depends_on` topological order once the Initiative
  gate passes;
- maintaining the workflow itself: rules, scripts, schema, tests and prose;
- isolating provenance lookup for already-merged Features while reading canonical authority.

Do not use it for product decisions, code implementation, feature testing or merge authorization
for a specific Feature. Those stay with the owning Feasibility, Discussion, implementation,
review, verification and acceptance skills, and with the user.

## Fresh-Session Entry

1. Read `wiki/feature-workspace/README.md`.
2. Read `wiki/feature-workspace/schema/feature-workspace-schema.md`.
3. Read `$hl-feature-workspace` (`<FACTORY_ROOT>/skills/hl-feature-workspace/SKILL.md`).
4. Read this skill's `SKILL.md`.

Then judge state only from `wiki/feature-workspace/registry.yaml`, the Initiative and Feature
manifests, and their `context_refs`. Chat records, folder guesses and old reports are not state.

Run the read-only checks first:

```bash
factory gate workspace --work <WORK_ROOT>
<PYTHON> <FACTORY_ROOT>/skills/hl-feature-workspace/scripts/feature_workspace.py report --registry wiki/feature-workspace/registry.yaml
```

`factory gate workspace` runs `validate` against the same registry; use the explicit form when you
need a human-readable report.

## Daily Flow

```text
create Initiative
  -> complete initial Feature inventory + depends_on + wave
  -> per-candidate Scope Gate and mandatory splitting
  -> finalize-decomposition
  -> first dependency-ready Leaf discussion
  -> implementation, independent review, Feature acceptance
  -> ready-to-merge / ready for every non-cancelled, non-superseded Leaf
  -> Initiative integration-test handoff
  -> new immutable integration evidence + PASS
  -> Initiative merge-ready
  -> explicit merge authorization (when policy requires it)
  -> semantic wiki merge per Feature in depends_on topological order
  -> affected MOC updates
  -> full long-term wiki validator excluding the feature and quick workspaces
  -> retained-history transformation after PASS
  -> Feature merged / completed
  -> authority switch and routing-record update
```

Rules:

- After an Initiative is created, complete the initial decomposition first; a broad F01 must not
  carry the whole Initiative's discussion.
- Every initial candidate gets a stable F ID, `depends_on`, `wave` and a Scope Gate. Split
  `must-split` immediately; keep `split-default` only with an `indivisibility_reason`.
- Only after `finalize-decomposition` succeeds may the first dependency-ready Leaf enter
  discussion. The validator and the transition command fail closed on this.
- A `ready-to-merge / ready` dependency is satisfied only with passed acceptance and complete
  closure; an incomplete ready state stays fail-closed.
- No merge starts before every non-cancelled, non-superseded Leaf in the Initiative is ready.
- After all Leaf Features are ready, generate the integration handoff and execute cross-Feature
  tests in a new immutable evidence root.
- `initiative-merge-ready` must pass before any merge. It requires an integration result of PASS
  and evidence files that exist on disk inside the Initiative directory.
- Feature merges follow `depends_on` topological order. Never fake completion or downgrade an
  upstream Feature to bypass a dependency.
- After the semantic merge, update every affected MOC, then run the full long-term wiki validator
  from `$hl-wiki-merge`. The validator covers the whole long-term wiki and excludes the feature and
  quick workspaces.
- That validator is a `$hl-wiki-merge` machine gate, not a Feature lifecycle field. Never add a
  status, schema field or state-machine branch for it.
- Only after validator PASS may you transform retained history, record `merged / completed`, and
  update the authority switch and the external routing record.
- On validator FAIL the Feature stays `ready-to-merge / ready`; do not create a tombstone or
  routing record, switch authority, transform retained history, or mark it merged/completed.
- After the merge, retain the complete Feature source directory as non-authoritative provenance,
  but remove it from active manifest references, default discovery and reporting, and from new
  `context_refs`. Only an explicit history audit may read it. The long-term wiki is the sole
  current authority; later changes and open questions become a new Feature in the feature
  workspace.

Key commands:

```bash
# Seal the initial decomposition after inventory, dependencies, waves and Scope Gate
<PYTHON> <FACTORY_ROOT>/skills/hl-feature-workspace/scripts/feature_workspace.py finalize-decomposition --registry wiki/feature-workspace/registry.yaml --initiative <Ixxx>

# Single Feature closure
<PYTHON> <FACTORY_ROOT>/skills/hl-feature-workspace/scripts/feature_workspace.py merge-ready --feature <feature.yaml>

# Generate the handoff once every Leaf Feature is ready
<PYTHON> <FACTORY_ROOT>/skills/hl-feature-workspace/scripts/feature_workspace.py initiative-integration-handoff --registry wiki/feature-workspace/registry.yaml --initiative <Ixxx> --output <initiative-dir>/integration-testing/integration-test-handoff.md

# Register real integration evidence after tests pass
<PYTHON> <FACTORY_ROOT>/skills/hl-feature-workspace/scripts/feature_workspace.py initiative-integration-result --registry wiki/feature-workspace/registry.yaml --initiative <Ixxx> --evidence <initiative-relative-evidence-file>

# Final gate before merge
<PYTHON> <FACTORY_ROOT>/skills/hl-feature-workspace/scripts/feature_workspace.py initiative-merge-ready --registry wiki/feature-workspace/registry.yaml --initiative <Ixxx>
```

Documentation merge happens only after the last command passes and the user has authorized the
merge, and it runs through `$hl-wiki-merge`. Follow the fixed per-Feature order: semantic merge,
affected MOC updates, full wiki validation excluding the workspaces, retained-history
transformation after PASS, `merged / completed`, then the authority switch and routing-record
update.

## History Lookup

When a reader asks why a rule exists while reading the long-term wiki, call `$hl-history-trace` with
the concrete question and the current canonical document path. That skill must spawn a fresh
isolated subagent to resolve the tombstone, route, checksums and historical body; the main session
receives only the fixed compact handoff.

Canonical documents must not contain feature or Initiative IDs, retained paths or reverse history
links. Routing entries live only in the external merged record and in `history-route.yaml` inside
the retained directory. When no route exists, report a provenance gap instead of scanning the
workspace.

## Workflow Maintainer Guide

When the request is to change the workflow itself rather than to advance a Feature:

1. State the new rule, compatibility impact and fail-closed behaviour first. Never prove a rule
   with a hand-edited manifest.
2. Change `<FACTORY_ROOT>/skills/hl-feature-workspace/scripts/feature_workspace.py` only for
   lifecycle status or transition rules, and sync its tests with the feature-workspace README and
   schema.
3. Content-completeness gates for merges live in `<FACTORY_ROOT>/skills/hl-wiki-merge/scripts`; they
   never enter the lifecycle schema, status values or the state machine.
4. Sync the affected workflow skills (at least `$hl-feature-workspace` and `$hl-wiki-merge`) plus this
   skill's `SKILL.md`, `references/entry-point.md` and `references/workflow-contract.md`.
5. Run every affected check: state-machine tests plus a real workspace `validate` for lifecycle
   changes; validator positive/negative tests plus a full wiki validation for merge-gate changes;
   `$hl-factory-doctor` for configuration or generated-file changes.
6. Confirm no project fact leaked into the generic surface: no project names, no absolute paths,
   no machine tokens.

Unacceptable maintenance: a second state machine, a validator elevated into a lifecycle field,
prose changed without the matching machine gate, a validator changed without its tests, or a
merge skill that bypasses the Initiative integration gate.

## Authorities

- Entry and invariants: this file and `references/workflow-contract.md`.
- Lifecycle state machine: `<FACTORY_ROOT>/skills/hl-feature-workspace/scripts/feature_workspace.py`.
- Long-term wiki content gate: `<FACTORY_ROOT>/skills/hl-wiki-merge/scripts/validate_llm_wiki.py`.
- Provenance reader: `<FACTORY_ROOT>/skills/hl-history-trace/scripts/trace_feature_history.py`.
