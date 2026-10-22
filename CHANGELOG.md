# Changelog

All notable changes to HighLand-factory are documented here. Format: Keep a Changelog; versioning: SemVer.

## [0.1.0] - 2026-10-22

First usable version: greenfield init + split-mode adopt, core feature lifecycle, machine gates, doctor/upgrade, installer and CI guards.

### Added
- **Engine CLI** (`engine/factory.py`): `init`, `adopt`, `doctor`, `upgrade`, `status`, `resolve`, `gate`.
  - config validation, template rendering with scalar/generated placeholders, custom wiki/code folder mapping, owner profile overrides, generated-file hashing, version-range checks.
  - `init`/`adopt` write `.factory/factory.yaml`, `.factory/local.yaml`, `.factory/state.json`, `wiki/governance/init-record.md`, baseline evidence; adopt preserves existing docs, appends `.gitignore` machine-state entries and links generated files into the nearest MOC so the wiki gate stays valid.
- **Workspace templates** (`templates/workspace/`): wiki authority skeleton (README/00–03, domain MOCs, governance digest, feature workspace + schema, quick workspace, code-ai profiles/blocks/manifests), root README/AGENTS/CLAUDE, `.factory` docs, `code/` seed.
- **Adopt code-analysis phase** (`hl-factory-init` + `references/adopt-code-analysis.md`): read-only subagents analyze the existing codebase in slices (repo map, core logic, data contracts, operations, tests, security/privacy, domain glossary); the main session synthesizes an evidence-based wiki baseline (`architecture/overview.md`, `domain/overview.md`, `implementation/overview.md`, `testing/overview.md`, `governance/runtime-and-operations.md`), updates `project-facts.md` and the authority map, and validates the wiki gate. Analysis notes stay gitignored under `.factory/analysis/`.
- **Generic skills** with the `hl-` prefix (collision-safe): `hl-factory-init`, `hl-factory-doctor`, `hl-factory-upgrade`, `hl-feasibility-grill`, `hl-feature-workspace`, `hl-feature-discuss`, `hl-feature-profile-generate`, `hl-feature-orchestrator`, `hl-feature-progress`, `hl-workflow-governance`, `hl-initiative-merge`, `hl-wiki-merge`, `hl-history-trace`, `hl-quick-change`.
- **Machine gates** (project-agnostic): feature-workspace state machine, long-term wiki validator, merge inventory, history trace.
- **Packs**: config ids `commit`, `dev-runtime`, `remote-verify`; installed skills `hl-commit`, `hl-dev-runtime`, `hl-remote-verify` (opt-in, config-driven).
- **Installer** (`install/install.ps1`, `install/install.sh`): bootstraps a PyYAML venv, writes `bin/factory`, links skills/packs into agent roots, refreshes `local.yaml`, supports `--no-skills` / `--skills-root` / `--with-packs`.
- **Upgrade script** (`install/upgrade.ps1`, `install/upgrade.sh`): optional `git pull --ff-only`, engine refresh, agent skill/pack re-link with stale-link cleanup, optional work-repo refresh and generated-file upgrade.
- **Docs**: architecture, skill contract, init questionnaire, customization, upgrade/drift, FAQ, skill catalog, adopt example.
- **CI**: leakage guard over generic assets, engine tests (init smoke + both gates), machine-gate script tests.

### Verified
- `factory init` → `doctor` → `gate all` green on a scratch work repo (engine test suite).
- Split-mode adopt dry-run and full adopt on a **temporary copy** of an existing two-repo project: 0 gate errors, generated files linked into existing MOCs, existing docs preserved. No existing repository was modified by the factory during verification.
- 25 engine tests + 49 machine-gate tests pass; leakage guard clean.
