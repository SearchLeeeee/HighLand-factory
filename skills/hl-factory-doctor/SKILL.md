---
name: hl-factory-doctor
description: Use when a HighLand-factory work repo may be misconfigured or broken — after init/adopt, after editing .factory/factory.yaml, after a factory upgrade, when a skill fails its step 0, or when the user asks to check the workflow. Runs the deterministic doctor plus both machine gates and returns a repair plan. Read-only by itself; it never weakens a gate.
---

# Factory Doctor

## What this skill is for

Diagnose a work repo against the factory contract and produce a concrete repair plan:

- config validity and required values
- machine values (factory checkout, Python with PyYAML)
- fixed layout (`code/`, `wiki/`, feature/quick workspace, code-ai)
- generated `workflow-profile.md` hash vs recorded state
- agent entry files, git state, baseline evidence
- both machine gates: long-term wiki validator and feature-workspace state machine

The engine command is authoritative; this skill explains results and drives repairs.

## Step 0 — locate config

1. Resolve the factory checkout and Python: read `<work>/.factory/local.yaml`; fall back to `factory --version` or ask the user.
2. Run:

```bash
factory doctor --work <work> --json
```

3. If the engine cannot even load config, report the exact error and route to `$hl-factory-init`.

## Interpreting results

| Level | Meaning | Action |
| --- | --- | --- |
| `fail` | A contract violation; downstream skills must not proceed | repair before any implementation |
| `warn` | Acceptable temporarily, risky long term | surface it; fix in the same session when cheap |
| `ok` | Verified | no action |

Never downgrade a `fail` to a warning, never edit the doctor output, never bypass a gate to "make progress". If a gate is wrong, the correct route is `$hl-workflow-governance` (workflow maintenance), not a local workaround.

## Repair routing

| Failure | Repair |
| --- | --- |
| `CONFIG_MISSING` / `CONFIG_INVALID` | route to `$hl-factory-init` or fix `.factory/factory.yaml` with the user |
| `LOCAL_*` / `PYTHON_YAML` | re-run `install/install.ps1|install.sh --work <work>`, or set `python` in local.yaml |
| `FACTORY_VERSION` | update `factory.version` in factory.yaml, or upgrade the factory checkout |
| `LAYOUT_MISSING` / `PROFILE_MISSING` | `factory upgrade --apply`; if still missing, `factory init --force` after reviewing the plan |
| `PROFILE_DRIFT` | edit `factory.yaml`, then `factory upgrade --apply`; never hand-edit the profile |
| `GATE_WIKI` | read validator output; fix links/home/isolation; create missing authority docs |
| `GATE_WORKSPACE` | read state-machine output; fix manifests through `$hl-feature-workspace` transitions |
| `BASELINE_PENDING` | run configured commands once and record evidence |
| `COMMANDS_*_EMPTY` | ask the user for the real command and persist it |
| `GIT_MISSING` | `git init -b <default_branch>` after doctor passes |

## Verification

After repairs, rerun:

```bash
factory doctor --work <work> --strict
factory gate all --work <work>
```

`--strict` turns warnings into a non-zero exit; use it before starting an implementation session and before a merge. Report the final pass/fail counts and any remaining warnings with their consequence.

## Language and output

Match the user's language. Keep the report short: status, failures, repairs applied, remaining risks. Quote exact engine messages for failures.
