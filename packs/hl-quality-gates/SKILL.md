---
name: hl-quality-gates
description: "Opt-in pack for quantitative quality signals: runs configured crapper (CRAP score), dryer (structural duplication report) and mutator (mutation testing) commands with exact exit-code semantics, writes reproducible evidence under verification.evidence_root and fails closed on missing config, unsupported stack or a failed mutator symlink preflight. dryer has no pass/fail gate. Enable with packs.enabled: [quality-gates]; core skills work with this pack disabled."
---

# Quality Gates (pack)

## Questioning Style

All user-facing questions must use Socratic questioning. Before asking, read
`<FACTORY_ROOT>/skills/hl-workflow-governance/references/socratic-questioning.md`
(relative to the located factory checkout during bootstrap). Follow that shared policy for
chat, choice panels and workbench questions; preserve existing explicit authorization gates.

## Pack status

This directory is an **optional pack**, not a core skill. Core workflow must run with
`packs.enabled: []`; no core skill may require these tools, their evidence, or this pack.

- Enable: install or link `<factory>/packs/quality-gates/` into the agent skill root, then add
  the id and the tool groups to the work repo config:

  ```yaml
  packs:
    enabled: [quality-gates]
    quality-gates:
      evidence_dir: <path-relative-to-work-root-inside-verification-evidence-root>
      crap:
        command: [<argv>, <argv>]
        paths: [<path-relative-to-work-root>]
      dry:
        command: [<argv>, <argv>]
        paths: [<path-relative-to-work-root>]
      mutate:
        command: [<argv>, <argv>]
        paths: [<path-relative-to-work-root>]
        max_workers: <integer>
        note: <free-form-fact-for-a-human-decision>
  ```

  Then run `factory upgrade --work <work>` and `factory doctor --work <work>`.
- Disable: remove `quality-gates` from `packs.enabled`; the core workflow must still work, and
  the project's documented testing/quality policy governs instead. Do not run these tools by
  hand under this pack's contract while it is disabled.
- Tools, argv, paths and thresholds are **data**. This pack contains no tool name spelled as a
  fixed installation path, no default threshold, and no assumed directory layout.

## When to use

Use this pack when a change needs a quantitative signal beyond "tests pass": a worst-case CRAP
score against a configured threshold, a list of structurally similar code candidates for a
reviewer, or the number of mutants that survived the test suite. It turns three external tools
into reviewed evidence with a fixed interpretation of their exit codes.

Do not use it as a replacement for the configured `commands.test` / `commands.lint` /
`commands.verify`, and do not let its output decide that work is complete. Do not use it on a
stack the tools do not support, or on a change whose tests are currently failing — a mutation or
coverage run over a red suite measures nothing. If a tool group is not configured, that tool was
**not run**; say so, never infer its result.

Tool facts this pack is built on (do not re-derive, do not contradict):

| Tool | Input | Output | Gate? |
| --- | --- | --- | --- |
| `crapper` | source plus a real test run it starts itself | CRAP score per unit; writes `.metrics/crap.edn` | yes, by exit code only |
| `dryer` | source only, Jaccard structural fingerprints (default threshold 0.82) | report of candidate clusters; writes `.metrics/dry.edn` | **no gate at all** |
| `mutator` | source plus a baseline test run | per-namespace mutation results under `.metrics/mutate/<namespace>.edn` | yes, by exit code only |

All three support exactly Clojure, Java, Go, TypeScript-JS, Rust and Python; output is **EDN, not
JSON**; they have no configuration file, only CLI flags. A project outside those six stacks is
unsupported: stop and report it, do not emulate the tool or invent a substitute metric.

## Step 0 — mandatory preamble

Every run of this pack starts here, even when it only reads config.

1. Resolve `WORK_ROOT` — the work repo root (git top-level, or the directory containing
   `.factory/`). Read `<WORK_ROOT>/.factory/local.yaml` and resolve:
   - `FACTORY_ROOT` = `local.yaml:factory_root`
   - `PYTHON` = `local.yaml:python`

   If `local.yaml` is missing or unreadable, stop: "machine config missing — run `factory init`
   (or `$hl-factory-init`) for this work repo, then retry." Never guess an interpreter path.
2. Read `<WORK_ROOT>/wiki/governance/workflow-profile.md`. If missing, stop: "workflow profile
   missing — run `factory upgrade --apply --work <WORK_ROOT>`, then `$hl-factory-doctor`; do not
   hand-write the profile."
3. Confirm `packs.enabled` in `<WORK_ROOT>/.factory/factory.yaml` contains `quality-gates`. If
   not, stop with the enable snippet above and the two commands.
4. Read `<WORK_ROOT>/.factory/factory.yaml` and resolve the whole `packs.quality-gates` block
   below, plus `verification.evidence_root` (the workflow profile lists enabled packs, not their
   configuration).
5. Run the engine gates and stop the pack if any fails:

   ```bash
   <PYTHON> <FACTORY_ROOT>/engine/factory.py doctor --work <WORK_ROOT>
   <PYTHON> <FACTORY_ROOT>/engine/factory.py gate workspace --work <WORK_ROOT>
   ```

6. If the resolved config and what the user is asking for disagree (for example a tool the
   project never configured, or a language the tools do not support), say so and route the
   decision to `$hl-workflow-governance`; do not improvise a gate.

A skill must fail closed: any missing, empty or malformed key stops the pack with a concrete
repair instruction.

## Config contract

`packs.quality-gates` — all keys below; the config id stays unprefixed, the skill is
`hl-quality-gates`.

| Key | Required | Meaning |
| --- | --- | --- |
| `evidence_dir` | yes | directory that receives evidence files, **relative to the work repo root**, and it must resolve inside `verification.evidence_root` |
| `crap.command` | yes when `crap` present | non-empty argv list invoked exactly as written to run `crapper` |
| `crap.paths` | no | path list describing the scope of a `--changed` style selection |
| `dry.command` | yes when `dry` present | non-empty argv list invoked exactly as written to run `dryer` |
| `dry.paths` | no | path list describing the scope of a `--changed` style selection |
| `mutate.command` | yes when `mutate` present | non-empty argv list invoked exactly as written to run `mutator` |
| `mutate.paths` | no | path list describing the scope of a `--changed` style selection |
| `mutate.max_workers` | no | integer worker count passed through the configured `command`, not appended by the pack |
| `mutate.note` | no | free-form note a human must read; data for a decision, not a command |

Rules:

- `evidence_dir` is a relative path: an absolute path, a drive letter, a `..` segment or a value
  that escapes `verification.evidence_root` stops the pack. Evidence belongs inside the
  repository; machine paths never appear in project config.
- `command` is an argv list, not a shell string. The pack must not compose a shell command line,
  must not rewrite or reorder a configured argument, and must not append flags the config does
  not carry. Thresholds, formats and `--no-coverage` style switches are configuration, never
  pack defaults.
- `paths` is descriptive data: it states which changed paths are in scope for this run and is
  quoted in the evidence and report. It is not a glob to execute, and it never changes
  `command`.
- `mutate.note` is read for human context. It is never executed blindly, and its presence is not
  a substitute for a valid `command`.
- Throwaway artifacts (the `.metrics/` tree, temporary overlay directories) must stay ignored
  by the repository; if they are not ignored, report that before running and do not add them to
  a commit.

Empty-config behaviour (fail closed) — all three tool groups are absent, empty or not mappings:

```text
quality-gates pack cannot run: packs.quality-gates.crap, packs.quality-gates.dry and
packs.quality-gates.mutate are all missing or empty, and packs.quality-gates.evidence_dir
must be set.
Enable packs.enabled: [quality-gates], set packs.quality-gates.evidence_dir to a path inside
verification.evidence_root, declare at least one of crap / dry / mutate with a non-empty
command argv list, then run factory upgrade --work <work> and factory doctor --work <work>.
```

At least one tool group must be usable. A partially valid group (mapping present, `command`
missing, empty or not a list) stops the whole pack — a half-configured gate is not a gate. Never
silently drop an unusable group and report on the remaining ones.

The complete enablement snippet — five keys, copied verbatim into
`<WORK_ROOT>/.factory/factory.yaml`, with only the groups you actually want to run:

```yaml
packs:
  enabled: [quality-gates]
  quality-gates:
    evidence_dir: <path-relative-to-work-root-inside-verification-evidence-root>
    crap:
      command: [<argv>, <argv>]
      paths: [<path-relative-to-work-root>]
    dry:
      command: [<argv>, <argv>]
      paths: [<path-relative-to-work-root>]
    mutate:
      command: [<argv>, <argv>]
      paths: [<path-relative-to-work-root>]
      max_workers: <integer>
      note: <free-form-fact-for-a-human-decision>
```

An unconfigured group is skipped by design; the fail-closed case above is *all three* missing or
*no* valid group, never "the user chose not to measure duplication".

### Evidence files

`evidence_dir` is resolved once, created before the first tool runs (so even an early failure has
somewhere to write), and each run writes one file per tool:

```text
<evidence_dir>/quality-<tool>-<UTC-timestamp>.md
```

`<tool>` is `crap`, `dry` or `mutate`; `<UTC-timestamp>` is UTC, `YYYYMMDDThhmmssZ`. The same
tool run twice produces two files; never overwrite or edit an existing evidence file. A run that
cannot write its evidence file did not happen — do not report a result for it.

Each evidence file records exactly:

1. the tool and the resolved `command` argv, one argument per line, verbatim;
2. the working directory used and the resolved time window;
3. the exit code;
4. the last lines of stdout/stderr as a short summary (a bounded tail, not the whole log);
5. every produced artifact path under `.metrics/` with its SHA-256;
6. the classification taken from the exit-code contract below, plus everything that was skipped;
7. nothing else — no EDN content, no secrets, no tokens.

## Exit-code contract (per tool, do not renumber, do not reinterpret)

The exit code is the only verdict channel. Do not parse a result out of a data file to overrule
it, and do not reclassify a result after the fact.

### crap — `crapper`

| rc | Class | Meaning | Required action |
| --- | --- | --- | --- |
| 0 | pass | worst score is within the configured threshold | this is the only rc that may be reported as a CRAP pass |
| 2 | High finding | worst score exceeded `--threshold` | record a High finding; the change is **not** complete; hand it to review |
| other non-zero | environment | tool missing, test run failed, interpreter or dependency broken | stop; this is an environment failure, never a quality conclusion |

- With `--no-coverage`, coverage and CRAP are `N/A`. An `N/A` result is **not** a pass; the run
  proves nothing and must be reported as inconclusive.
- The pack owns no threshold. The threshold lives in the configured `command`.

### dry — `dryer`

| rc | Class | Meaning | Required action |
| --- | --- | --- | --- |
| 0 | report produced | the tool ran and wrote its report; **this is not a judgement** | attach the candidate list to the report as review input |
| 1 | usage error | wrong flags, unreadable target | stop; fix the configured `command` |
| 2 | unknown `--format` | the format value is not accepted | stop; fix the configured `command` |
| other non-zero | environment | stop; classify as environment | stop; do not report a verdict |

`dryer` has **no pass/fail gate of any kind**. Its output is candidate clusters of heuristic
similarity (Jaccard structural fingerprints), not a semantic duplication verdict; the pack does
not decide that anything should be deleted or merged — that decision belongs to review. Never
present "dryer rc 0" as "no duplication" or as a green quality gate.

### mutate — `mutator`

| rc | Class | Meaning | Required action |
| --- | --- | --- | --- |
| 0 | pass | every executed mutant was killed | the only rc that may be reported as a mutation pass; state how many mutants executed |
| 2 | environment | the baseline test run failed | stop immediately; fix the suite/environment, write no quality conclusion |
| 3 | Blocker | at least one mutant survived | record a Blocker; the change is not complete until triaged with review |
| other non-zero | environment | tool missing, worker crashed, permissions or overlay failure | stop; classify as environment |

- A surviving mutant is evidence that the tests do not constrain that behavior — it is a
  Blocker, not a style note, and it is never converted into a pass by "the tests are green".
- rc 2 never becomes "the code is broken"; the baseline suite could not even run.

## Step-by-step flow

### 1. Resolve and validate config (no tools executed yet)

1. Apply Step 0, then resolve `packs.quality-gates` and `verification.evidence_root`.
2. Reject `evidence_dir` that is absolute, carries a drive letter, contains `..`, or resolves
   outside `verification.evidence_root`.
3. Reject any present group whose `command` is missing, empty, or not a list of non-empty
   strings; reject `mutate.max_workers` that is not a positive integer.
4. Confirm the project language/stack is one the tools support. Unsupported stack → stop with
   "not measurable by this pack"; do not fake a metric.
5. Print the resolved plan before executing anything:

   ```text
   tool=<crap|dry|mutate> cwd=<relative-path> argv=<space-joined argv> evidence=<relative-evidence-path>
   ```

### 2. Reserve evidence before running

Create `evidence_dir` and confirm it is writable. If it cannot be created or written, stop — a
run whose result cannot be recorded must not start.

### 3. Capability check without side effects

For each configured group, confirm the executable named by `command[0]` resolves and is
runnable, and that `PYTHON` is the interpreter the tool needs. Do this without triggering the
tool's install or test phases. A missing tool is an environment failure for that group: stop, do
not silently skip the group, and do not report the remaining groups as an overall pass.

### 4. Run the configured groups serially

Run each configured group in the order `dry` → `crap` → `mutate` (cheapest and read-only first,
then the run that installs coverage support and executes the suite, then the most expensive is
last), one at a time. Do not run two groups concurrently: they share the `.metrics/` tree and
may share the project environment.

1. Execute the configured argv verbatim from the working directory the tool requires (the work
   repo root unless the config's paths make another directory meaningful).
2. Capture stdout/stderr to a bounded tail and the exit code; never edit the output.
3. Stop the sequence when a group fails closed in a way its exit-code class requires (crap
   environment failure, mutate rc 2, dry rc 1/2, any unknown rc). Report what did not run.
4. `crap` with coverage enabled runs the test suite itself; do not run a second suite in
   parallel with it.

### 5. mutator symlink preflight — mandatory, before any mutate run

`mutator` runs its workers behind a symlink overlay: the worker layer creates symlinks with no
fallback and no error translation. On Windows without symlink privileges this raises `OSError`.
Lowering `max_workers` to 1 does **not** avoid it, because the overlay is created per worker run.

So, whenever `mutate` is configured, before invoking it:

1. Create a throwaway probe directory (for example a uniquely named directory under the system
   temp root, never inside the repository tree).
2. Inside it, create one regular file and one symlink to that file; then read through the
   symlink and confirm the content matches.
3. Delete the probe directory and everything in it.

Outcome:

- Probe succeeds → the mutate run may proceed; record "symlink preflight: ok" in the evidence.
- Probe fails with a permission/`OSError`-class failure → **fail closed before touching the
  project**: print a short diagnosis and the exact remedies ("enable Windows Developer Mode, or
  run this session as an administrator, then retry"), mark `mutate` as not run, and do not
  present the traceback as the answer. Do not retry the probe in a loop, and do not weaken the
  preflight to "try and see".
- Probe fails for a non-permission reason (no temp space, unwritable temp root) → stop with that
  reason; it is an environment failure either way.

### 6. Capture evidence

For each tool that ran, write one `quality-<tool>-<UTC-timestamp>.md` file as specified in the
config contract. Include the preflight result for `mutate` and, for `crap`, whether coverage was
computed or `N/A`. Evidence must be complete and readable; a truncated or zero-byte file is
"evidence missing", never a pass.

### 7. Classify and report

Map each exit code through its tool's table, then report in the user's language:

- which tools ran, which were skipped, and the exact command that ran;
- the class per tool (pass / High finding / Blocker / report only / environment failure /
  inconclusive);
- the evidence paths and artifact paths;
- for `dry`, the candidate list explicitly framed as review input, not as a verdict.

### 8. Isolate the tools' own side effects

`crapper` changes the environment it measures: it installs `coverage` / `pytest` into the
project interpreter, installs `@vitest/coverage-v8` into `node_modules`, and injects a JaCoCo
plugin into `pom.xml`. Treat those as tool state, not as business change:

1. Before and after the run, compare the working tree and report the files the tool touched
   (`pom.xml`, dependency manifests, lock files, installed package metadata, `.metrics/`).
2. Keep the tool's changes separate from the change under review. Do not mix them in one
   commit, and do not leave an injected plugin or an added dependency unmentioned.
3. The pack never commits or pushes. It must state clearly that the tool's own edits must not be
   committed; if the user wants them reverted, that is their explicit decision — do not
   `git checkout --` or reset the tree on your own, and never revert business changes.

## Failure handling

| Situation | Action |
| --- | --- |
| `crap`, `dry`, `mutate` all missing/empty | fail closed with the message above; run nothing |
| `evidence_dir` missing, absolute, with `..`, or outside `verification.evidence_root` | fail closed; ask for a relative path inside the evidence root |
| A present group has an empty/non-list `command` | fail closed for the whole pack; do not drop the group |
| `verification.evidence_root` itself empty | stop; ask once, then route the value into config via `$hl-workflow-governance` |
| Stack outside the six supported languages | stop: "not measurable by this pack"; invent no metric |
| Tool executable not found / interpreter broken | environment failure; stop the affected group, report the rest as not run |
| `crap` rc 2 | High finding; not complete; hand to review |
| `crap` ran with `--no-coverage` | coverage and CRAP are `N/A`: inconclusive, never a pass |
| `crap` other non-zero | environment failure; never a quality conclusion |
| `dry` rc 1 or 2 | usage/format error: stop and fix the configured `command` |
| `dry` rc 0 | report produced, no verdict; present candidates as review input |
| `mutate` symlink preflight fails | fail closed before the run; give the Developer Mode / administrator remedies; `max_workers: 1` is not a workaround |
| `mutate` rc 2 | baseline suite failed: stop immediately, environment problem, no conclusion |
| `mutate` rc 3 | surviving mutants: Blocker |
| `mutate` other non-zero | environment failure; stop |
| Evidence file cannot be written or is truncated/empty | treat as not run; fix capture and rerun |
| `.metrics/` not ignored by the repository | report before running; do not commit artifacts |
| The tools touched `pom.xml`/dependency manifests/lock files | separate and report; do not commit tool edits |
| Any unknown exit code | treat as environment failure; do not guess a class from the output |

## What this pack must never do

- Never parse EDN. `.metrics/crap.edn`, `.metrics/dry.edn` and `.metrics/mutate/*.edn` are opaque
  artifacts: record their paths and SHA-256 only. Do not convert them to JSON, do not grep a
  score out of them, and do not overrule an exit code with their content.
- Never turn `dryer` into a gate: it reports candidates, it does not pass or fail. No deletion or
  merge decision is made here.
- Never report `--no-coverage` (`N/A`) as a pass, and never report a skipped tool as a pass.
- Never report an environment failure as a quality conclusion, and never report a High finding or
  a Blocker as "done".
- Never let the tools' own side effects (installed packages, an injected build plugin, generated
  `.metrics/`) be committed as if they were the change.
- Never run `mutate` before the symlink preflight passes, and never surface a raw traceback in
  place of a diagnosis.
- Never hardcode a tool, a threshold, a path, a port or a worker count; never rewrite a
  configured `command`.
- Never add lifecycle states, a second state machine, or a second wiki validator; never edit
  `feature.yaml` or any generated file; this pack only produces evidence and classifications
  inside the existing workflow.
- Never commit or push on its own authority.
- Never modify a test or a threshold to turn a failing classification green without explicit user
  approval that the test or threshold itself is wrong.
- Never run the three tools concurrently, and never leave a probe directory or a temporary
  overlay behind on success or failure.
