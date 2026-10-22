# Pre-Flight And Verification Techniques

Load factory context first: read `.factory/local.yaml` and
`wiki/governance/workflow-profile.md` before running any recipe here. Commands come from the
profile's `commands` section; evidence goes to the configured evidence root. If a command is not
configured, do not invent one and do not claim verification.

Every item below is a recipe: run it, record the output.

## Classify Blockers Before Freezing The Matrix

Do this before the run, not during it: who owns the ports the criteria name, whether privilege
escalation exists, whether logs are readable by the test user, whether the deployment root exists at
all. A handful of read-only checks decides several rows at once, and finding a blocker after writing
the matrix forces a re-freeze.

## Dependency Provisioning

A frozen or lockfile install usually brings base dependencies only. Inspect the dependency extras
section of the project manifest before recording a provider as `dependency_missing`; the project's
own install documentation may require an extra. A provider the application treats as the runtime
default but ships as an extra will report a missing dependency on a freshly provisioned host — that
is an environment prerequisite, not a code defect.

## Proving A Failure Is Pre-Existing

Export the last commit into a temporary directory (`git archive HEAD | tar -x -C <tmp>`) and run the
same test selection there before accepting a "pre-existing failure" claim. Running only the changed
files cannot separate new breakage from old.

## Verifying A Fix Without Disturbing The Frozen Tree

Verify in a separate clone, never in the frozen read-only clone: copy the changed files elsewhere,
run with the module search path pointed at the code under test, then confirm the frozen clone still
reports its recorded revision with zero dirty entries.

A mode-only version-control fix is provable: `git update-index --chmod=+x` plus
`git diff --cached --numstat` showing zeros for every touched path.

## Regenerating An Inherited Artefact

Before promising to regenerate evidence at the frozen revision, confirm the harness exists and is
obtainable: the generator script, the fixture sources, and the runtime it needs. "Re-run the
evidence" is not a plan when the generator was never committed or the isolated runtime is
undocumented and absent — that is a freeze-time blocker to report, not a step to improvise mid-run.

When the only way the work actually ran was an ad hoc driver, copy that driver and its normaliser
into the evidence root so the run is reproducible, and record the missing version-controlled
harness as a follow-up that does not change the gate.

## Files, Transport And Release Trees

- A delegated edit to a tracked data or configuration file can arrive with the wrong line endings.
  Reread the diff after accepting it: an edit made on a different platform turns a line-feed file
  into a carriage-return file, which shows up in the diff as whitespace churn or a full-file
  rewrite. Normalise to the repository's declared policy (check the attributes file) before
  committing.
- A staging or release directory that a deploy tool made read-only refuses recursive removal with
  `Permission denied` on every file. Make the tree writable first, then remove: the refusal is the
  tool enforcing immutability, not a permissions bug.
- When a long-lived process must be started on another host, ship the sequence as a script file and
  run that file; an inline command that starts a server can trip a command-text guard that reads
  the invocation rather than the effect.

## Cross-Platform Casing

A cross-platform row cannot be proven on a case-insensitive filesystem alone. A path assembled from
a symbolic name or id passes on one platform and fails on a case-sensitive filesystem, and the
symptom is empty results rather than a file-not-found error, so a green run on one platform is not
portability evidence. Detect it by exercising the exact path on the case-sensitive platform, and
keep producer/consumer casing identical.
