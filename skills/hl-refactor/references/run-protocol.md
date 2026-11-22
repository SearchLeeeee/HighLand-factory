# Manual Maintenance Run Protocol

Use this reference to operate `scripts/refactor.py`. The helper enforces admission,
selected file boundaries and evidence provenance. The agent remains responsible
for truthful scope, user decisions, semantic inspection and independent review.

## Contents

- [Command entry and identity](#command-entry-and-identity)
- [Start and range evidence](#start-and-range-evidence)
- [Candidate input](#candidate-input)
- [Selection and implementation](#selection-and-implementation)
- [Evidence and closure](#evidence-and-closure)
- [Pause, resume and changed sources](#pause-resume-and-changed-sources)
- [Authority and guarantee limits](#authority-and-guarantee-limits)

## Command entry and identity

Prefix every command below with:

```text
<PYTHON> <FACTORY_ROOT>/skills/hl-refactor/scripts/refactor.py
```

Use `--help` or `<command> --help` to inspect the installed parser. Every command takes
`--work <WORK_ROOT>`; every command except `start` also takes `--run <run-id>`.
Use resolved paths from Step 0 and a unique, honest implementing session identity for `--actor`.
An actor label is an audit assertion, not proof of agent independence.

`start` returns the run ID, record path, status and scope information. Retain the run ID for
subsequent commands; do not hand-edit the run record. `resume` and selection application return
status and scope information for the current run.

Keep `run.json` as the canonical aggregate in
`<refactor_workspace>/runs/<run-id>/`. It includes source snapshots, candidates,
decisions, resolutions and checks. `events.jsonl` preserves the operation trail; `evidence/`
holds copied evidence. Other compact working notes in this same process area are allowed,
but must not become a second candidate ledger or current-capability catalogue.

## Start and range evidence

Full scan:

```text
start --work <WORK_ROOT> --mode full --actor <implementer-id> --budget <requested-cost-boundary>
```

Latest completed Initiative:

```text
start --work <WORK_ROOT> --mode latest --actor <implementer-id> --budget <cost-boundary> --initiative <id> --base <code-base> --head <code-head> --range-evidence <evidence-summary>
```

Add `--wiki-base <wiki-base> --wiki-head <wiki-head>` when Wiki has a separate Git identity,
including an explicit equal base/head if it truly had no changes. In a shared repository
the Wiki range defaults to the code range; override it only with evidence.

`--budget` may be omitted when the user has not supplied one; settle a concrete cost boundary
in candidate selection. `latest` requires the named completed Initiative, both code refs and
nonempty range evidence. Refs must be commits, base must precede/equal head, and head must be
incorporated into the current checked-out baseline. Old and new paths are retained for renames.

The range explanation must establish **recency and completeness**: all effective Leaves,
integration repairs and final Wiki changes. Cite closure/merge evidence or a reliable explicit
change inventory. The helper verifies only mechanically decidable range facts, not whether the
chosen Initiative really is latest. Do not guess missing refs or present a partial range as full.
Current uncommitted content is recorded separately and must be considered in the scan.

Startup validates lifecycle admission and captures current source identities.
A blocked start preserves a diagnostic record. Resolve the named
problem and start a new manually requested run; do not edit the blocked record to continue.

## Candidate input

Write a JSON file in the run's process area, then call:

```text
candidates --work <WORK_ROOT> --run <run-id> --input <candidate-json-file>
```

The following is an illustrative schema example. Replace all findings, paths and claims with
actual project evidence before using it:

```json
{
  "coverage": {
    "checked": ["Named source area and current Wiki scenes actually inspected"],
    "limitations": ["No deployment observation; the result concerns checked source/configuration"]
  },
  "candidates": [
    {
      "id": "R001",
      "title": "Unify one shared policy rule",
      "kind": "refactor",
      "problem": "The same effective business rule has two separately maintained owners",
      "evidence": ["Exact source and contract references with the observed duplication"],
      "proposed_action": "Use the existing policy entry from both actual callers",
      "benefit": "One rule owner and a discoverable reuse entry",
      "cost": "Low: inspect both callers, change the call sites, run affected checks and sync the capability entry",
      "risk": "Preserve existing accepted inputs and error outcomes; list unresolved assumptions",
      "recommendation": "Implement if the caller/contract evidence confirms one responsibility",
      "paths": ["code:src/policy.py", "code:tests/test_policy.py", "wiki:capabilities/policy.md"],
      "acceptance": ["Actual caller outcomes remain unchanged and the authority names the reuse entry"],
      "depends_on": []
    }
  ]
}
```

Required candidate fields are the fields shown. IDs match `R001` style; `evidence` and
`acceptance` are nonempty string arrays. `coverage.checked` must contain actual coverage even
when `candidates` is empty. `coverage.limitations` may be empty only when justified.

| `kind` | Meaning | Extra requirements |
| --- | --- | --- |
| `refactor` | Preserve observable behavior while improving structure | Exact edit paths and preservation evidence |
| `test` | Delete, merge or rewrite tests | Nonempty `original_protection` and `continued_protection`; identify retired requirements or retained/replacement checks |
| `wiki` | Repair evidenced current authority or discovery | Exact Wiki paths and semantic mapping |
| `investigate` | Bounded read-only inquiry into an uncertain finding | State question, stopping evidence and cost; grants no source edit permission |
| `behavior` | Change observable behavior, compatibility or failure semantics | Explicit old/new effect and user acknowledgement of this ID |
| `handoff` | Investigate/package work for a separate workflow/session | State unsolved gap and destination; grants no source edit permission |

List exact canonical files as `code:<relative-file>`, `wiki:<relative-file>` or
`work:<relative-file>`. Use the most specific resolved root. Include necessary tests,
documentation and exact new filenames; no directories, wildcards, traversal, symlink escape,
Git internals, ignored untracked files or process-workspace edit targets. Investigation and
handoff paths may name read targets but **never** enter the source edit allowlist.

`depends_on` contains other candidate IDs and must form an acyclic graph. Explain the dependency
in the proposal. Store alternatives, uncertainty and documentation/test sync effort in the
action/cost/risk/acceptance fields. Distinguish pure investigation cost from an unapproved fix.

## Selection and implementation

After presenting the evidence and receiving an actual user selection:

```text
select --work <WORK_ROOT> --run <run-id> --ids <selected-ids-csv> --decision <recorded-user-decision>
```

Include all required dependent IDs. Add `--ack-behavior <behavior-ids-csv>` only for behavior
items the user explicitly selected with their effects visible. The decision records selected
scope, cost boundary and retained/deferred items. Selecting `--ids ""` retains all candidates.
An empty candidate list needs no manufactured approval.

Before each selected unit:

```text
begin --work <WORK_ROOT> --run <run-id> --id <selected-id>
```

`check` performs the same ongoing lifecycle/source/scope checks without starting a unit. `begin`
authorizes no action beyond the already recorded selection. Keep read-only investigations
read-only. Execute selected implementation within exact paths and existing project permissions.

Before first edits, replacing candidates clears the old selection. After edits begin, existing
candidates are immutable: append any newly evidenced candidate, present its material decision,
and record an expanded selection containing prior IDs before writing its new paths. A scope
check failure cannot be repaired by retrospectively approving an already made external edit.

An exact-file extension for a necessary supporting test, document or helper may reuse the
user's existing authorization when goal, observable behavior, cost and risk remain within the
approved boundary. Record it as a supporting item dependent on the original selected goal;
name that standing authorization in `--decision` and expand the allowlist before writing.
Do not ask again for this routine implementation detail. An unrelated finding or a material
scope/behavior/cost/risk increase requires a new concentrated user decision. Carry previously
given behavior acknowledgements forward rather than asking for them again.

Record each selected outcome with a nonempty evidence file and actual effort:

```text
resolve --work <WORK_ROOT> --run <run-id> --id <candidate-id> --outcome <fixed-or-investigated-or-transferred> --evidence <file> --note <result-and-limits> --actual-cost <actual-work-and-budget-comparison>
```

Implementation candidates resolve as `fixed`; investigations as `investigated` or `transferred`;
handoffs as `transferred`. A handoff is not a fixed business problem. One concise evidence file
can cover several related items; name each criterion and result. Preserve unsatisfied items as
incomplete and pause if needed instead of falsely resolving them.

## Evidence and closure

After the actual relevant checks, use:

```text
record-check --work <WORK_ROOT> --run <run-id> --kind <test-or-wiki-or-review-or-handoff> --evidence <file> --verdict <pass-or-fail-or-blocked> --actor <actual-actor>
```

| Kind | Required evidence content | Additional arguments |
| --- | --- | --- |
| `test` | Actual applicable command, source/configuration, result/log and preserved test protection; explain relevant reused evidence or omissions | `--command <actual-command> --exit-code <actual-exit-code>` |
| `wiki` | Bidirectional scenes/claims checked, time/version/configuration, evidence types, semantic conclusions and remaining differences | Actor required; command/exit code optional if relevant |
| `review` | Independent assessment of selected changes, behavior, scope, test protection, caller impact and fixes | Actor must differ from the implementing actor |
| `handoff` | Read-only continuation exercise from formal entry and all role-required reads; actual capability/reuse/authority/impact/verification paths | Actor must differ from the implementing actor; may share the review file |

For `wiki`, PASS means **the selected goals and their affected semantic scope were checked
successfully**, with remaining outside-scope findings explicit. It does not mean every scanned
claim matches code, all business behavior is correct, or anything was deployed. A diagnostic
scan may honestly record `fail` or `blocked` when consistency cannot be established. Never label
a selected unresolved semantic defect PASS just because its mapping table is complete.

Run the actual existing structural gate separately:

```text
verify-wiki --work <WORK_ROOT> --run <run-id>
```

This creates a `wiki-structure` receipt from `factory gate wiki`; it never substitutes a new
validator. A failed command cannot be recorded as PASS. Copied evidence has an integrity hash
and source correspondence; its contents still require honest inspection. Evidence or process
notes changing do not count as project implementation edits.

Record final checks against the final implementation. If later source changes invalidate a
receipt, assess affected conclusions and reuse still-applicable results with an explanation;
do not rerun every check solely to obtain a new receipt. Review and handoff must be genuinely
independent, not the same implementer with a different invented label.

```text
finish --work <WORK_ROOT> --run <run-id> --summary <outcome-benefit-cost-coverage-remaining-findings>
```

For implemented maintenance, resolve all selected items and provide current passing evidence
for independent review/handoff, applicable verification, semantic Wiki checks and the actual
Wiki structure gate. Recheck the affected area and synchronize tests/current Wiki first.
For a scan-only result, add `--scan-only`: the outcome is `scan-completed` with
`closure_type: diagnostic-scan`, rather than `completed / verified-maintenance`. No source edits
or `fixed` resolutions are permitted. Semantic and actual structural receipts are still
required, but may retain `fail`/`blocked`. Known failures require an explicit `select --ids ""`
decision identifying the residuals; selected investigation/handoff still requires its resolved
outcome and independent review/continuation. Zero worthwhile candidates with no failures needs
no artificial selection. The helper preserves residual IDs.

## Pause, resume and changed sources

```text
show --work <WORK_ROOT> --run <run-id>
pause --work <WORK_ROOT> --run <run-id> --reason <incomplete-work-and-reason>
resume --work <WORK_ROOT> --run <run-id>
```

`show` is read-only and remains available for completed/paused runs. Pause records the best
available source identity. Before resuming, stop any previous writer for that run, inspect the
run and unresolved items, then let `resume` recheck lifecycle admission, selected scope and
evidence validity.

If relevant source/authority changed before edits and the run is still active, refresh only
after reviewing the changed paths and maintaining the correct range:

```text
refresh --work <WORK_ROOT> --run <run-id> --reason <changed-evidence-and-recheck-plan>
```

For `latest`, also provide `--range-evidence <fresh-recency-and-completeness-evidence>` for the
unchanged explicit code/Wiki ranges. Lifecycle, configuration or repository-root changes require
pause and a new manually scoped run; `refresh` cannot accept those authority changes.

Refresh preserves prior candidates/selection as history, then clears current approval and
requires a new scan/selection. It cannot erase an implementation baseline after edits. If an
already paused source changed, `resume` rejects the stale basis and `refresh` does not bypass
that check: preserve the incomplete record and start a new explicit scan of the actual remaining
work after resolving the divergence. Do not reset source files or rewrite historical Initiative
state to make a receipt current.

For an interrupted run, inspect `show`, retain its evidence and unresolved outcomes, and use
`resume` to recheck lifecycle, sources and selected scope before continuing. Do not hand-edit
status fields or repeat completed work. Preserve an incomplete record when source divergence
requires a new explicitly scoped scan.

## Authority and guarantee limits

The helper borrows the existing Feature/Initiative reader. It
creates no new Feature phase or Initiative state and never changes their historical closure.
Source identity uses Git to enumerate sources and records their actual available working-tree
bytes, consistently across clean/staged files, Windows line-ending conversion, `assume-unchanged`
and `skip-worktree`. Reading those bytes at each checkpoint resolves the concrete ambiguity
between normalized Git objects and the files actually reviewed; no freeze commit or extra
evidence artifact is required. `dirty_paths` reports Git-visible changes and untracked files;
the byte inventory also detects changes hidden by index flags. Content-equivalent revision
changes do not alone invalidate evidence. Inventory limitations,
such as nested submodule content or ignored files, remain visible and must not be reported as
covered. Use project-specific checks for a genuinely needed untracked/generated/runtime surface.

Source rechecks detect changes within the recorded local source inventory. Coordinate shared
work-root files and Git merge/index operations as necessary when other work is in progress.
The parser can validate recorded selection and actor fields but cannot establish actual human
authorization, semantic correctness or independent judgment. Those remain the coordinator's
responsibility. Commit, push, deployment and new workflow initiation retain their own existing
authorization boundaries.
