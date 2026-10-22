# Evidence Root Layout And Row Binding

Load factory context first: confirm `FACTORY_ROOT`, `PYTHON` and `WORK_ROOT` from
`.factory/local.yaml`, and confirm the evidence root from `wiki/governance/workflow-profile.md`
before creating any directory. The layout below is relative to the Initiative directory inside the
feature workspace.

One integration run = one immutable evidence root. Everything a gate decision rests on must be
resolvable from it without re-running tests.

## Layout

```text
wiki/feature-workspace/initiatives/<initiative>/integration-testing/evidence/<run-id>/
  frozen/            # written BEFORE any test row executes
    run-identity.md  # revisions, worktree state, platform, external sessions
    acceptance-matrix.md
    FROZEN.sha256.txt
  run-manifest.json  # machine-readable result
  INDEX.md           # row -> evidence file -> sha256
  EVIDENCE.sha256.txt
  f01/ f02/ ...      # one directory per Feature
  cross/ safety/
  logs/              # raw logs, sanitised
  harness/           # only when the run needed an unversioned driver to execute
```

`harness/` earns its place when the only way a row actually ran was a driver written ad hoc
because the repository ships no generator — copy the driver, the runner and the normaliser in, so
someone who was not there can reproduce the result. It is a reproducibility aid, not proof of a
product behaviour, and the missing version-controlled harness is recorded as a follow-up that does
not change the gate.

Name the run id from a UTC timestamp (`I011-IT-20261021T141150Z`), never from the outcome — an id
that says `pass` cannot honestly hold a failure.

## Cross-Run Index

When several runs accumulate, a single derived index at `evidence/STATUS.md` keeps a resuming
reader oriented. Keep it strictly subordinate: mark it derived, give it no verdict of its own, list
each run with its revision and its own verdict, and state the caveat when passing rows were
established across more than one revision. Never cite that index as evidence — the authority stays
each run's immutable root, and a summary that quietly becomes the record reintroduces exactly the
borrowing this discipline exists to prevent.

## Freeze, Then Never Touch

Write the matrix before the first test row, hash it, and keep the hash. Later writes go to
`run-manifest.json`, `INDEX.md`, or a per-Feature record — never back into `frozen/`. A reader must
be able to prove the pass criteria were not adjusted after the failures were known.

Each frozen row needs: id, class (`required` / `optional-diagnostic` / `unavailable-external`),
trigger (who or what acts), the real path exercised, the expected durable result, the evidence file,
and whether it blocks PASS. Fixed tolerances belong in the frozen file too, so widening them later
is visible.

## Bind Every Row To A File

An unbound row is not evidence. Generate `INDEX.md` from the manifest so the mapping cannot drift,
and fail the check if a row is unbound or a bound path is missing:

```python
rows = {r["id"]: r for r in manifest["rows"]}
assert all(rid in binding for rid in rows)                      # no unbound rows
assert all(os.path.exists(os.path.join(root, f)) for fs in binding.values() for f in fs)
```

Put the row status on the index line as well, so a reader sees status and artefact together.

## Manifest Shape

Keep declaration and evidence apart. Fields that earn their place:

- `run_id`, `initiative`, `verdict`, `verdict_reason`
- `revisions` — every repository plus worktree dirty counts and the handoff hash
- `environment` — OS, runtime versions, whether privileged
- `preflight` — the read-only gates and their results
- `rows[]` — id, class, status, one-line note
- `counts` — and they must be computed, not hand-written
- `findings[]` — blocker-class defects with the row they block
- `operational_followups[]` — real observations that do not change the gate
- `state_changes` — what this run did or did not mutate

## Verify The Totals Before Reporting

Recount from `rows[]`, assert against the declared `counts`, and assert that the statuses sum to
the row total. A hand-maintained total is the easiest number to get wrong and the number a reader
trusts most:

```python
from collections import Counter
c = Counter(r["status"] for r in rows)
assert c["PASS"] + c["FAIL"] + c["BLOCKED"] + c["NOT_EXECUTED"] == len(rows)
```

## Sanitise On The Way In

Raw logs move into `logs/` only after masking. Redaction is not done until a re-grep of the raw
value returns zero hits — a pattern with the wrong quantifier silently matches nothing, prints a
plausible masked count, and leaves the secret in place. Keep the masked copy as the artefact and
note in the Feature record that the live value stays on the host.
