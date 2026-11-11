# Workflow Governance — Entry Point

Load factory context first: read `.factory/local.yaml`, then
`wiki/governance/workflow-profile.md`. If either is missing, stop and route to `$hl-factory-init`
or `$hl-factory-doctor`; do not reconstruct values from memory, chat history or directory guesses.

This page is a fresh-session map. It does not restate every procedure. `$hl-workflow-governance`
owns routing and workflow maintenance; the skill named for the current action owns its detailed
steps; executable and schema authorities below own machine-enforced behavior.

## Fresh-session entry

1. Read `wiki/feature-workspace/README.md` and
   `wiki/feature-workspace/schema/feature-workspace-schema.md`.
2. Read `$hl-feature-workspace/SKILL.md` for lifecycle commands and the
   `$hl-workflow-governance/SKILL.md` for request routing and maintenance.
3. Run `factory gate workspace --work <WORK_ROOT>`. Use the registry and current manifests as
   lifecycle authority; narrative reports are not state.

## Route

Use `$hl-workflow-governance/SKILL.md`'s request table to select the owner: Feature workspace,
Feature discussion/orchestration, Initiative integration, wiki merge, history trace, Quick Change,
or workflow maintenance. Do not carry out a Feature transition in the routing skill.

## Shared invariants

- Use minimum sufficient verification: one identifiable source target, applicable evidence reuse,
  affected checks and risk-based sampling. Do not default to layered hashes, repeated freezes, fresh
  clones or full reruns. Repair evidence gaps locally, retain failure facts, and keep safety,
  independent judgement, machine gates and authorization. No new mode or approval is required.

- Complete Initiative inventory, dependency/wave registration and Scope Gate before Leaf discussion.
- Dependencies count as satisfied only after acceptance and closure are complete.
- An Initiative merge requires every active Leaf ready, new Initiative integration evidence, a
  passing merge-ready gate, and the required authorization.
- Per Feature, merge semantic content, update affected MOCs, pass the full long-term wiki
  validator, retain the source, then switch authority and close the Feature.
- Wiki content validation is not a lifecycle state. A failed validator keeps the Feature ready and
  blocks authority switch and closure.
- Keep future work in the Feature or Quick Change workspace; keep the canonical wiki as current
  authority. Retained sources are history only.
- Before workflow maintenance, state compatibility and fail-closed behavior, update every owning
  surface, and keep generic documents free of project-specific facts.

Detailed commit and worktree rules live in `references/commit-boundaries.md` and
`references/worktree-lifecycle.md`. Shared policy details and change-surface ownership live in
`references/workflow-contract.md`.

## Authorities

- Lifecycle state machine: `<FACTORY_ROOT>/skills/hl-feature-workspace/scripts/feature_workspace.py`
- Long-term Wiki validator: `<FACTORY_ROOT>/skills/hl-wiki-merge/scripts/validate_llm_wiki.py`
- Semantic merge workflow: `$hl-wiki-merge/SKILL.md`
- Provenance resolver: `<FACTORY_ROOT>/skills/hl-history-trace/scripts/trace_feature_history.py`
