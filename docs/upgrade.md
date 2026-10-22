# Upgrade and Drift

## 1. Version pinning

`.factory/factory.yaml` pins a compatible engine range:

```yaml
factory:
  version: ">=0.1.0 <0.2.0"
```

`factory doctor` fails when the installed engine does not satisfy the range. Upgrade the range deliberately, not implicitly.

## 2. What counts as generated

`.factory/state.json:generated_files` records the SHA-256 of every file written by `factory init`/`upgrade`. A file is "generated" only if it is in that map.

- **Generated**: `wiki/governance/workflow-profile.md`, `wiki/code-ai/<owner>-agent.md` (initial), `wiki/code-ai/_manifests/<owner>.yml`, plus template-rendered files.
- **Project-owned after init**: authority docs, discussion records, feature manifests, project facts, code.
- **Machine-owned**: `.factory/local.yaml`, `.factory/state.json`.

## 3. Normal upgrade

```bash
git -C <factory> pull --ff-only
<factory>/install/upgrade.ps1                 # Windows; POSIX: install/upgrade.sh
<factory>/install/upgrade.ps1 -Work <work> -ApplyWorkUpgrade
factory doctor --work <work> --strict
factory gate all --work <work>
```

The upgrade script (v0.1):

1. optionally runs `git pull --ff-only` with `-Pull` / `--pull`;
2. refreshes the factory venv and `bin/factory` shim;
3. re-links `skills/` and `packs/` into the detected agent skill roots, adds new
   links, removes links whose source skill was deleted, and leaves links owned by
   other managers untouched;
4. with `-Work` / `--work`, refreshes each work repo's `local.yaml`, runs
   `factory upgrade --check`, and with `-ApplyWorkUpgrade` applies the refresh and
   runs `factory doctor`.

Restart the agent session after the script so it reloads the refreshed skills. If
another tool manages your agent skill roots (for example a central skill manager),
run the script with `-NoSkills` / `--no-skills` and register `<factory>/skills` there
instead.

Classification:

| Action | Meaning | Safe? |
| --- | --- | --- |
| `create` | new generated file | yes |
| `overwrite` | generated file unchanged since last generation | yes |
| `skip` / "locally modified" | project edited a generated file | no — decide manually |
| `skip` / "exists" | init-time collision with an existing project file | expected |

## 4. Drift

Three kinds of drift are detected:

1. **Config ↔ digest drift** — `workflow-profile.md` hash differs from the recorded hash (`PROFILE_DRIFT`). Fix: edit `factory.yaml`, run `factory upgrade --apply`; never hand-edit the digest.
2. **Engine ↔ config drift** — version range mismatch (`FACTORY_VERSION`). Fix: upgrade the factory, or adjust the range with the user.
3. **Template ↔ work repo drift** — new template files, or changed generated files. Fix: `factory upgrade --check`, review, apply.

## 5. Locally modified generated files

If a project deliberately customizes a generated file (for example an owner profile):

1. Record the decision in `wiki/governance/` (why this file is project-owned).
2. Remove it from `state.generated_files` so future upgrades stop trying to refresh it (edit state only through the documented upgrade flow; never hand-edit casually).
3. Prefer moving the customization into `factory.yaml` and regenerating when possible.

## 6. Breaking upgrades

A breaking upgrade (schema change, removed config key, changed lifecycle enum) must ship:

- a `CHANGELOG.md` entry with the migration steps,
- a config migration in the engine (accept old key, warn, write new key),
- a doctor check that detects the old shape and prints the exact repair.

If the migration cannot be automated, the release notes must say so explicitly and the upgrade command must refuse rather than write a half-migrated repo.

## 7. Rollback

The work repo is git. Before a major upgrade, commit or tag the current state:

```bash
git -C <work> tag pre-upgrade-<factory-version>
```

Rollback = restore the tag, then pin `factory.version` back to the previous range. `.factory/local.yaml` is gitignored; re-run `install` for the machine if the factory checkout changed.

## 8. Managed by an external skill manager

If agent skill roots are managed by another tool (for example a central agent-config
repository), do **not** let `install`/`upgrade` write the agent directories directly.
Register the factory once as an external skill root instead:

```yaml
# manager's source file
external_skill_roots:
  - id: highland-factory-skills
    root: ${FACTORY_ROOT}
    skills_subdir: skills
  - id: highland-factory-packs
    root: ${FACTORY_ROOT}
    skills_subdir: packs
```

```yaml
# manager's machine-local config (not committed)
vars:
  FACTORY_ROOT: /path/to/HighLand-factory
```

The manager junctions each `hl-*` skill into the agent roots and reads it in place, so
normal updates are:

```bash
git -C <factory> pull --ff-only
<factory>/install/upgrade.ps1 -NoSkills      # engine + venv only, agent dirs untouched
<manager>/tools/sync.ps1                     # only needed for added/removed/renamed skills
<manager>/tools/doctor.ps1                   # verify the agent sees the skills
```

Content-only changes are picked up immediately through the junction. Work-repo generated
files still upgrade with `install/upgrade.ps1 -Work <work> -ApplyWorkUpgrade` or
`factory upgrade --work <work> --apply`. Because every skill carries the `hl-` prefix, the
factory skills do not collide with skills managed elsewhere; retire old equivalents in the
manager whenever the project no longer needs them.

