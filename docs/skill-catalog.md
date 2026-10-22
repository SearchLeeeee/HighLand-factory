# Skill Catalog

Every skill is self-contained and starts with **Step 0 — Load factory context** (read `.factory/local.yaml`, then `wiki/governance/workflow-profile.md`, then run gates through the engine). No skill contains project facts.

All skill directories and their `name:` fields carry an `hl-` prefix (the agent skill spec requires lowercase kebab-case, so it is written `hl-`; it means the same as an `HL-` prefix) to avoid collisions with other workflows installed in the same agent.

## Core skills

| Skill | Role | Produces | Calls |
| --- | --- | --- | --- |
| `hl-factory-init` | Guided bootstrap of a work repo (new/adopt), requirements → architecture → verification → security → governance → agent policy | `.factory/factory.yaml`, wiki skeleton, digest, baseline | `factory init/adopt`, `factory doctor` |
| `hl-factory-doctor` | Diagnose config/layout/digest/gates and drive repairs | repair plan | `factory doctor`, `factory gate` |
| `hl-factory-upgrade` | Refresh generated files safely after a factory update | refreshed digest/manifests | `factory upgrade`, `factory doctor` |
| `hl-feasibility-grill` | Technical feasibility stress test before decomposition; verdict and handoff | verdict, Initiative creation routing | `factory gate workspace` |
| `hl-feature-workspace` | The only lifecycle state machine and schema gate | `registry.yaml`, `initiative.yaml`, `feature.yaml`, integration handoff, progress report | `feature_workspace.py` |
| `hl-feature-discuss` | Discuss exactly one dependency-ready Leaf Feature to confirmed conclusions | workbench, domain implementation docs, profile targets | `$hl-feature-workspace`, `factory gate workspace` |
| `hl-feature-profile-generate` | Compose executable Code AI profiles by relative-path reference | feature `code-ai/` profiles + index | `factory gate workspace` |
| `hl-feature-orchestrator` | Dispatch owners, plan approval, implementation → review → acceptance | code changes, review/acceptance evidence, lifecycle transitions | `feature_workspace.py`, `factory gate` |
| `hl-feature-progress` | Read-only progress, blockers, parallelizable work, next-session prompt | report | `feature_workspace.py report` |
| `hl-workflow-governance` | Routing and durable invariants entry point | decisions, maintenance | all of the above |
| `hl-initiative-merge` | Initiative-level cross-Feature integration acceptance before merge | frozen evidence, PASS record | `feature_workspace.py`, `factory gate` |
| `hl-wiki-merge` | Semantic long-term wiki merge, validator gate, retained history | merged authority, MOC updates, retained-history bundle | `validate_llm_wiki.py`, `inventory_llm_wiki_merge.py` |
| `hl-history-trace` | Isolated provenance lookup through tombstones and history routes | compact handoff | `trace_feature_history.py` |
| `hl-quick-change` | Bounded bugfix/adjustment on-ramp with hard-gate escalation | quick record, evidence | `$hl-feasibility-grill` on escalation |

## Packs (opt-in)

Enable with `packs.enabled: [<id>]` in `.factory/factory.yaml`, then `factory upgrade --apply` and `factory doctor`. Pack **config ids stay unprefixed**; the installed skill is `hl-<id>`.

| Pack id | Skill | Role | Required config |
| --- | --- | --- | --- |
| `commit` | `hl-commit` | Repo-mode aware granular commits; commit only when authorized, push only on separate authorization | `repo.*`, `project.language.commit` |
| `dev-runtime` | `hl-dev-runtime` | Start/stop/restart configured local services with health verification | `packs.dev-runtime.services[]` |
| `remote-verify` | `hl-remote-verify` | Run one commit through an isolated/remote clone and return a machine verdict | `packs.remote-verify.{host,user,clone_path,entry,evidence_root}` |

## Adding a skill

1. Create `skills/hl-<name>/SKILL.md` with YAML frontmatter (`name: hl-<name>`, `description`).
2. Start with the Step 0 preamble from [skill-contract](skill-contract.md).
3. Use work-repo-relative paths and `<FACTORY_ROOT>/skills/...` for scripts; never a machine token or absolute path.
4. Reference other skills by `$hl-<name>`.
5. Run `tools/check_no_leakage.py` and the test suite.

## Adding a pack

1. Create `packs/hl-<id>/SKILL.md`; declare it opt-in and list its config keys. The pack config id stays `<id>` (`packs.enabled: [<id>]`), while the installed skill is `hl-<id>`.
2. Fail closed with a named-key message when config is missing.
3. Core skills must keep working with the pack disabled.
4. Add the pack to the installer documentation (`install --with-packs`).
