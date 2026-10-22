# Init Questionnaire

`$hl-factory-init` asks only what it cannot detect or safely default. This document is the question bank and the rationale; the skill may compress or reorder it, but it must not silently skip a P0 item.

## 0. Design rule

Three tiers, progressive disclosure:

| Tier | When | Budget | Items |
| --- | --- | --- | --- |
| P0 | always, one decision at a time | ~20 questions, 10-20 minutes | identity, topology, migration, runnable baseline, architecture, owners, security, authorization, evidence, workflow parameters, naming, git |
| P1 | "全量模式" or when a P0 answer leaves a gap | ~15 questions | CI/CD, issue tracker, MCP, model tiers, agent platforms, docs topology, license, contribution, glossary, fixtures, observability, release/versioning, dependency policy, performance baseline |
| P2 | later, via `$hl-workflow-governance` | unlimited | anything that can change without invalidating the skeleton |

Rules:

- Ask one decision at a time; each question carries why it matters, the realistic options, a recommended default, and one sentence of trade-off.
- Detect before asking. Stack, commands, existing docs, git remotes, folder structure and licenses are auto-discovered and shown as a proposal to confirm.
- Record every answer and every assumption in `wiki/governance/init-record.md`.
- Anything answered "unknown / decide later" becomes an explicit assumption with a re-check trigger, not a silent default.
- Never ask a question whose answer the factory does not consume. A dead config field is a defect.

## 1. Why "requirements + architecture" is not enough

Requirements and architecture answer **what to build**. A workflow also needs:

1. **How "done" is proven** — real commands, a green baseline, evidence format, isolated verification environment.
2. **What must never happen** — security boundaries, sensitive data classes, redaction, irreversible operations.
3. **Who authorizes** — merge, commit, push, delete, production writes; role separation between implement/review/verify.
4. **Where truth lives** — wiki authority map, domain taxonomy, owner map, profile composition.
5. **How the workflow itself evolves** — factory version pinning, upgrade path, drift handling, customization ownership.

These are the items most often missing from a first initialization, and the ones that cause silent workflow decay later.

## 2. P0 question bank

| # | Topic | Question | Why it is P0 | Recommended default |
| --- | --- | --- | --- | --- |
| 1 | Mode | New repo, adopt an existing repo, or attach to an already initialized repo? | Changes the whole write plan and safety rules | `new` for greenfield; `adopt` for existing |
| 2 | Identity | Project name, slug, one-liner, license, visibility? | Appears in config, wiki, README, commit scopes | derive slug from name; license MIT; visibility private |
| 3 | Goals | Target users, core scenarios, success signals, explicit non-goals? | Drives `00-spec` / product authority and feasibility review | must be answered; non-goals at least 3 |
| 4 | Language | Doc language, code/comment language, commit language? | Every generated artifact and skill prompt inherits it | docs = user language; code/identifiers English |
| 5 | Repo mode | `mono` (code/ + wiki/ in one repo) or `split` (wiki repo + external code repo)? | Controls topology and compatibility with existing two-repo projects | `mono`; use `split` when visibility differs or repos already exist |
| 6 | Code source | Empty `code/`, existing path to move/copy, existing external repo, or submodule? | Determines history strategy and whether anything may be rewritten | empty for new; external reference for adopt |
| 7 | Wiki source | Fresh wiki or existing docs to import/migrate? | Existing docs must be mapped, not regenerated | fresh for new; import-map for adopt |
| 8 | Stack | Languages, frameworks, runtimes, package managers, versions? | `project-facts.md`, review boundaries, command detection | detect from manifests and confirm |
| 9 | Commands | install/build/lint/typecheck/test/e2e/dev/verify commands? | Without real commands acceptance is impossible | must run each once and capture a green baseline |
| 10 | Runtime | Which Python has PyYAML for the engine; Node/pnpm/uv availability? | The engine cannot run without it | detect `uv`/venv and verify `import yaml` |
| 11 | Services | Local services, ports, databases, migrations, env files? | Dev-runtime pack, acceptance and health checks | detect; declare in config if used |
| 12 | Architecture | System shape, modules, dependency direction, data stores, external systems, deployment topology, trust boundaries? | Feeds `architecture/` authority and owner boundaries | must be answered; record open questions |
| 13 | Owners | Which implementation owners exist (id, title, owned paths, profile file)? | Drives profile generation, write scopes and review routing | one `core` owner for tiny projects; else backend/frontend/devops |
| 14 | Security | Forbidden operations, sensitive data classes, redaction rules, secret storage? | Agents write code and docs; irreversible/vendor/money actions must fail closed | explicit list; secrets only in gitignored local config |
| 15 | Authorization | Who authorizes commit, push, merge, delete, production writes? Are review and verification roles independent? | Gates are meaningless without a decision owner | user authorizes all outward actions; review/verify independent |
| 16 | Verification | Baseline evidence path, evidence root, isolated-environment policy, reproducibility requirements? | Defines what evidence a future session can trust | local evidence root under feature workspace; no isolation for v0.1 unless needed |
| 17 | Workflow gates | Keep default Scope Gate thresholds? Enable quick-change? Max parallel features? Require initiative integration testing? | These are policy, not code; wrong defaults silently weaken gates | keep all gates on; quick-change on; max parallel 1 |
| 18 | Naming | Initiative/Feature ID prefixes, slug rules, wiki taxonomy, file naming? | ID schemes and paths are load-bearing in scripts and docs | `I###` / `I###-F##`, kebab-case slugs, standard taxonomy |
| 19 | Git | Default branch, commit format and granularity, PR policy, initial commit now? | Commit gate and history hygiene depend on it | `main`, conventional commits, one concern per commit, initial commit only after doctor passes |
| 20 | Packs | Enable `commit`, `dev-runtime`, `remote-verify`? | Packs add machine-specific behaviour and need config | `commit` on; others off unless the project has a dev server / remote verifier |
| 21 | Factory version | Pin engine version range and decide upgrade policy? | Prevents silent drift between work repo and factory | pin `>=0.1 <0.2`; upgrade only through `factory upgrade` |

## 3. P1 question bank (defaults are fine)

- CI/CD platform, required checks, path filters for mono repos.
- Issue tracker / backlog integration (and whether feature IDs must link to it).
- MCP servers the workflow may use (wiki query, indexer, tracker).
- Agent platforms in use and their skill installation method.
- Model tier mapping for owner / review / verification / delegation.
- Wiki taxonomy additions and which domains get their own MOC.
- Decision record policy (this template defaults to "current decisions doc + git history", no ADR directory).
- Glossary / ubiquitous language terms.
- Fixture and test-data policy (synthetic vs captured, metadata requirements).
- Observability conventions (trace/correlation IDs, log redaction).
- Release/versioning policy for the project.
- Dependency update policy.
- Performance / load baseline requirements.
- Contribution guide and code of conduct (for public projects).
- Documentation review owner and staleness policy.

## 4. Adopt-mode specifics

Adopt must additionally determine:

- Which existing repository is the work repo (usually the wiki/docs repo) and which is the code repo.
- Where the long-term wiki root is today (`wiki/`, `docs/`, or a project-specific folder name) and whether init may create a `wiki/` alias or must use the existing path.
- Which existing files are authoritative vs stale; init never rewrites authoritative docs.
- Whether an old Feature Workspace exists and must be preserved at its current path (set `layout.feature_workspace` compatibility override) or migrated later.
- Which old skills/rules remain valid and which are replaced; produce a migration mapping in `init-record.md`.
- A freeze tag/branch before the first adopt run, so the pre-adopt state is recoverable.

## 5. Init definition of done

`factory doctor --strict` must pass, and the following must exist:

- `.factory/factory.yaml` valid; `.factory/local.yaml` with a working Python (PyYAML); `.factory/state.json`.
- `wiki/` skeleton valid under `validate_llm_wiki.py` (not merely a one-file wiki).
- `wiki/feature-workspace/registry.yaml` valid under `feature_workspace.py validate`.
- `wiki/governance/workflow-profile.md` matching config hash.
- `wiki/code-ai/` entry, blocks, manifests and one owner profile per configured owner.
- `AGENTS.md` / `CLAUDE.md` bootstrap instructions.
- Green baseline: every configured build/lint/test/verify command executed once, results recorded in `wiki/validation/init-baseline.md`.
- `wiki/governance/init-record.md` with answers, assumptions, detected facts and generated-file hashes.
- Git initialized on the configured default branch; initial commit only after doctor passes and only with explicit authorization.

## 6. What init must not do

- Do not implement a product Feature. Init stops at a valid baseline; the first real change enters through `$hl-feasibility-grill` or `$hl-quick-change`.
- Do not create a broad placeholder Initiative to "represent the project".
- Do not rewrite or delete existing authoritative documents in adopt mode.
- Do not ask P2 questions to look thorough.
- Do not store secrets, tokens or credentials in committed files.
