# Customization

The factory is designed so that most customization happens in **one file**: `<work>/.factory/factory.yaml`. Change code only when the workflow itself must change.

## 1. Change project values

Edit `factory.yaml`, then:

```bash
factory upgrade --work . --apply    # refresh generated digest/profiles
factory doctor --work . --strict
```

Never hand-edit `wiki/governance/workflow-profile.md` or generated owner manifests; they are regenerated and the doctor checks their hash.

## 2. Add or remove an owner

1. Add an entry to `owners`:

```yaml
owners:
  - id: mobile
    title: Mobile
    paths: [code/mobile]
```

2. Run `factory upgrade --work . --apply` — this generates `wiki/code-ai/mobile-agent.md` and `wiki/code-ai/_manifests/mobile.yml`.
3. Link the new profile from `wiki/code-ai/README.md` if the generated link block did not already include it (the template uses `{{generated:owner_links}}`, so it usually does).
4. Run `factory doctor --work . --strict`.

Removing an owner: remove the config entry, then delete the generated profile and manifest (upgrade does not delete files). Update `02-file-authority-map.md` if it lists the owner.

## 3. Add a wiki domain

The long-term wiki is a normal MOC tree: root `wiki/README.md` → domain `README.md` → documents, all within three hops.

1. Create `wiki/<domain>/README.md` with a one-line purpose.
2. Add a link from `wiki/README.md`.
3. Add the domain to `02-file-authority-map.md` (topic authority table) and, if relevant, to `00-spec.md` archiving rules.
4. Run `factory gate wiki --work .`.

Do not create `moc/`, `maps/`, `decisions/`, `discussions/` or ADR directories — the validator treats them as legacy routes.

## 4. Add a real command

Commands live in `factory.yaml:commands`. Add one line per command; the profile and the baseline template pick them up after `factory upgrade --apply`. Then run the command once and record the result in `wiki/validation/init-baseline.md`.

## 5. Change workflow gates

`workflow.*` switches are policy, not code. Changing them does not require editing skills:

- `scope_gate.enabled` — keep Scope Gate checks on by default; turning it off is a deliberate risk.
- `quick_change` — allow the bounded quick-change on-ramp.
- `review_required` / `verification_separate` — require independent review / verification roles.
- `merge_requires_authorization` — require explicit user authorization before wiki merge.
- `initiative_integration_required` — require Initiative-level integration evidence before any merge.
- `max_parallel_features` — scheduling hint, not a lock.

If a gate needs new behaviour (not just on/off), that is workflow maintenance, not configuration: see section 7.

## 6. Add or remove a pack

Packs are optional capabilities that read the same config but declare extra keys.

1. Install the pack directory under `<factory>/packs/hl-<id>/` with a `SKILL.md` and, if needed, scripts. The config id stays `<id>`; the installed skill name is `hl-<id>`.
2. Enable it in `packs.enabled`.
3. Run `factory doctor` and follow the pack's documented config requirements.

A pack must never be required by a core skill; core skills must work with all packs disabled.

## 7. Change the workflow itself

When the rule itself changes (new lifecycle phase, new gate, changed evidence format):

1. Write the rule, compatibility impact and fail-closed behaviour first.
2. Update the owning surface: state machine and tests, validator and tests, schema doc, or the skill prose — whichever actually owns the behaviour.
3. Update every skill that restates the rule. Prose and code must not diverge.
4. Run `python tools/check_no_leakage.py`, the full test suite, and a real `factory init` smoke test.
5. Bump `VERSION` and `CHANGELOG.md`; run `factory upgrade --check` against an example work repo.

Never fork a second state machine, never duplicate a validator, never let a skill invent a lifecycle rule in prose that the state machine does not enforce.

## 8. Template ownership

| Path | Owner | Safe to edit per project? |
| --- | --- | --- |
| `wiki/00-spec.md`, `01-reading-guide.md`, `02-file-authority-map.md`, `03-current-decisions.md` | project | yes — these become project authority after init |
| `wiki/<domain>/**` | project | yes |
| `wiki/code-ai/project-facts.md`, owner profiles | project | yes after first generation |
| `wiki/code-ai/_blocks/**`, `_manifests/**`, `subagent-flow.md`, `review-agent.md` | factory | extend via a project block or a pack; keep upstream shape |
| `wiki/governance/workflow-profile.md` | generated | no |
| `wiki/feature-workspace/schema/**` | factory | no — change the factory, not one project |

Project-specific additions belong in new files or project-owned docs, not by rewriting factory-owned generic rules in place. That keeps upgrades possible.
