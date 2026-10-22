# FAQ

## Why one work repo with `code/` and `wiki/`?

Because two folders are the smallest contract that lets every skill use relative paths without token rendering. If code and docs need different visibility or already live in separate repositories, use `repo.mode: split` — the work repo tracks the wiki and points at an external code repo. `mono` is the default; `split` is first-class, not a hack.

## Why not keep the `${TOKEN}` rendering approach?

Token values are machine-scoped, so one machine could only serve one project configuration, and any skill containing a token stopped being a single physical copy. HighLand-factory instead fixes the layout and moves variable values into `.factory/factory.yaml`, read through the generated `wiki/governance/workflow-profile.md`. Skills stay single-copy and upgradeable.

## Does the factory repo ever contain project content?

No. It contains engine, skills, templates, installer and docs. CI runs `tools/check_no_leakage.py` over generic assets to keep it that way. Project content belongs to the work repo (or to an opt-in pack for vendor-specific behaviour).

## How do agents find the skills?

`install/install.ps1` (Windows) or `install/install.sh` links `skills/*` into the detected user-level skill roots (`~/.dsh/skills`, `~/.claude/skills`, `~/.codex/skills`). The same installer creates `<factory>/bin/factory`. If your agent uses a different root, link the directories manually; the skills have no machine-specific content.

## Which Python does the engine need?

Python ≥ 3.10 with PyYAML. `install` creates `<factory>/.venv` and installs PyYAML there; `factory init` records that interpreter in `.factory/local.yaml`. If you prefer another interpreter, pass `--python <path>` to `factory init` or update `local.yaml`.

## Why does `factory doctor` fail even though the wiki looks fine?

The validator enforces navigation, not completeness: a one-file wiki can pass. The doctor additionally checks config, layout, generated digest, owner profiles, baseline and both gates. Run `factory doctor --work <work>` and follow the hints; never weaken a gate to get a green result.

## Can I rename `code/` or `wiki/`?

Only `repo.code_path` and `repo.wiki_path` are configurable, and the wiki-internal structure stays fixed. Renaming internal paths (`feature-workspace/`, `code-ai/`) is a factory change because the state machine and validator treat those segments as load-bearing. Keep the contract; it is what makes upgrades and skills portable.

## How do I migrate an existing two-repo project?

Use adopt mode with the docs repo as the work repo:

```bash
factory adopt --work <docs-repo> --code <code-repo> --wiki <existing-wiki-folder>
```

Freeze the pre-adopt state with a git tag first. Adopt never rewrites existing authoritative docs; it adds `.factory/`, the digest, missing skeleton files and owner profiles, then reports every skipped path. See `examples/adopt-existing-project/` for a configuration example.

## Where do secrets go?

Never in `factory.yaml`, `wiki/` or skills. Use the project's secret store; `security.secrets_file` names the gitignored file or reference. `local.yaml` may hold machine paths but not credentials.

## What if my agent cannot run subagents or a choice panel?

The workflow degrades gracefully: skills ask one plain-text question at a time and execute roles in the main session. Role separation is a policy (`workflow.review_required`, `workflow.verification_separate`); if the platform cannot provide independent agents, record the limitation and do not pretend the gate was independently satisfied.

## Can I use this for a non-software project?

The lifecycle, wiki authority and feature workspace are generic, but the code-ai profiles and command/verification model assume a code repository. For document-only work, set `repo.mode: mono` with an empty `code/` and configure verification commands that validate the documents; the heavy implementation chain is optional.

## Why does init ask about security and authorization?

Because agents write code and docs. Without an explicit forbidden-operation list and a named authorization owner, the workflow cannot fail closed on irreversible actions. These are the two items most often missing from a first initialization.

## How do I contribute a change to the factory itself?

Treat it as workflow maintenance: rule first, then owning surface (script + tests, validator + tests, schema, or skill prose), then affected skills, then full test suite plus a real `factory init` smoke test. Update `CHANGELOG.md` and `VERSION`. See `docs/customization.md` §7.
