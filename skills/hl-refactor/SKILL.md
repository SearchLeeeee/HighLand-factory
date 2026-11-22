---
name: hl-refactor
description: Use only on an explicit user request for a manual full-project or latest-completed-Initiative scan and controlled refactoring of code, tests and current business Wiki. Require every effective Initiative to be closed, present evidence with benefit, cost and risk, then implement only user-selected items with independent review and verification. Also use for an explicit request to resume a recorded refactor run. Never trigger automatically on Initiative completion, a schedule, or an incidental code smell.
---

# Manual Refactor

On an initialized work repo run `factory resolve --work <WORK_ROOT> --json`, read `<wiki>/README.md` first, then the current responsibility’s page in `<role_memory>/` if present. Use the returned paths and follow `<FACTORY_ROOT>/skills/hl-workflow-governance/references/wiki-memory.md` for role routing and task experience.

## Step 0 — Load factory context

1. Resolve `WORK_ROOT` from the directory containing `.factory/`. Read
   `<WORK_ROOT>/.factory/local.yaml`; obtain `FACTORY_ROOT` and `PYTHON`. Missing or unreadable
   values require `$hl-factory-init`; do not guess an interpreter or project path.
2. Read the generated `<workflow_profile>` under the resolved Wiki layout and
   `.factory/factory.yaml`. Obtain language, code/Wiki roots, owners, real commands, verification
   policy, security constraints, enabled packs and registered process-workspace exclusions.
   Missing/stale configuration requires `$hl-factory-doctor`; do not edit generated files.
3. Run the existing engine checks:

   ```bash
   <PYTHON> <FACTORY_ROOT>/engine/factory.py doctor --work <WORK_ROOT>
   <PYTHON> <FACTORY_ROOT>/engine/factory.py resolve --work <WORK_ROOT> --json
   <PYTHON> <FACTORY_ROOT>/engine/factory.py gate workspace --work <WORK_ROOT>
   <PYTHON> <FACTORY_ROOT>/engine/factory.py gate wiki --work <WORK_ROOT>
   ```

   Invalid configuration, lifecycle/registry state or unresolved language policy blocks entry.
   Preserve a Wiki structural baseline failure as a finding: this skill alone may continue
   **read-only diagnosis** of that failure. Implemented maintenance still requires the existing
   Wiki gate to pass before completion. Never report a failed baseline as PASS.
4. Read `<FACTORY_ROOT>/skills/hl-workflow-governance/references/entry-point.md` for the shared
   workflow boundaries, and the project's formal entry/role-required material. Preserve those
   startup reads. Before any user question read the shared `socratic-questioning.md` beside that
   entry point. Reuse settled answers and authorization; use concentrated candidate review.
5. Read [run-protocol.md](references/run-protocol.md) before operating a run, and
   [scan-guide.md](references/scan-guide.md) before scanning or reviewing. Use the same helper
   throughout: `<PYTHON> <FACTORY_ROOT>/skills/hl-refactor/scripts/refactor.py`.

## 1. Establish the manual run

Use the user's requested `full` or `latest` mode and cost boundary. If the mode is absent,
ask one focused choice after gathering available scope facts. Separate scan coverage, selected
edit scope and total effort; do not impose an arbitrary file-count limit. An unspecified budget
is not a license for extensive cleanup: show actual proposed work and cost before selection.

For `latest`, establish the most recently completed Initiative incorporated into the current
baseline from trustworthy closure/merge evidence. Include every effective Leaf, integration fix
and final Wiki update. Supply its ID, code base/head and range evidence; split repositories
also need Wiki base/head. The helper checks refs and ancestry, not recency or semantic completeness.
If the range cannot be recovered, show the concrete gap and request a reliable range or `full`.
Never substitute the last commit, greatest ID or only the final Leaf.

Start with a distinct implementing session/agent identity:

```bash
<PYTHON> <FACTORY_ROOT>/skills/hl-refactor/scripts/refactor.py start --work <WORK_ROOT> --mode full --actor <implementer-id> --budget <cost-boundary>
```

The helper uses the existing lifecycle reader to require
all effective Initiatives and Leaves properly terminal. `ready-to-merge / ready`, an intermediate
`completed`, or integration PASS alone does not qualify. Cancelled/superseded work follows the
existing semantics; report it accurately and never describe cancellation as implementation.
An initialised project without Initiatives may use `full`.

Retain the returned run ID and use the helper's `pause`, `resume` and `finish` commands to
manage the run. Never create, resume, cancel or rewrite an Initiative to gain admission.
Source changes require rechecks.

Keep one authoritative `run.json` under the resolved `refactor-workspace/runs/<run-id>/`.
The helper maintains events and evidence references. Place working scan/decision/review evidence
in this process area; do not create a second long-term description of the project's capabilities.

## 2. Scan without implementation edits

Follow the scan guide across current code, tests, relevant configuration and current-state Wiki:

- Discover existing capability/reuse points, responsibilities, dependency direction, shared
  mutable state and abstractions whose cost exceeds their value.
- Distinguish necessary boundary defenses/compatibility from redundant or ineffective checks.
  Unknown purpose becomes a bounded investigation candidate, never assumed deletion permission.
- Inspect obsolete/duplicate/implementation-coupled tests while preserving their valid behavioral
  protection. A long-passing regression test is not automatically obsolete.
- Check business scenes in both directions: Wiki claim to implementation and important implemented
  capability/constraint to Wiki. Bind conclusions to time/timezone, code/Wiki identity and relevant
  configuration. Distinguish source existence, executed tests and runtime/deployment observations.

Exclude only the exact registered process roots from current-fact discovery, including this
run's workspace. Necessary lifecycle/range metadata remains readable. Incremental analysis may
read related callers, shared contracts and Wiki beyond its seed diff; disclose that extension
and never imply whole-project coverage. If budget leaves a full scan incomplete, label partial
coverage explicitly.

Parallelise independent read-only questions when useful. Keep code, tests and canonical Wiki
unchanged during scanning; only process records may be written. Validate findings
against source evidence and combine duplicates before presenting them.

## 3. Present candidates and record the user's batch selection

Record candidates through `candidates --input <json-file>` using the protocol schema. For each
stable ID show the problem/evidence, proposed action and affected paths, expected benefit,
investigation/implementation/verification/synchronisation cost, risk/uncertainty, dependencies,
acceptance and recommendation. Include the actual checked coverage and limitations even when
there are no candidates. Record the cost boundary and disposition of every found issue.

Apply the design, dependency and test-protection rules in the scan guide. A third-party proposal
needs several real uses and clear net engineering benefit. Similar code with different semantics
may remain separate. State how any deleted or rewritten test's protection retires or survives.

Use `investigate` for unknown defenses and `behavior` for changes to observable compatibility,
validation, error/fallback semantics, side effects or contracts. An investigation selection does
not authorize its possible follow-up edit. Explicitly enumerate each behavior change for the
user; `select --ack-behavior` records that item-level decision.

Request one batch choice: implement IDs, investigate IDs, retain/defer others, and any necessary
cost tradeoff. Only the user's actual answer or existing explicit instruction supplies selection;
recommendations and silence do not. Then run `select --ids <csv> --decision <decision>` with any
behavior acknowledgements. Select required dependencies together. `--ids ""` records retaining
all candidates. With no worthwhile candidates, proceed to honest scan-only closure.

The explicit edit allowlist contains exact code/Wiki/work files, including necessary tests,
documentation and planned new files. Material additional scope/cost/risk or behavior returns as
a concentrated new decision **before** the extra write. After implementation starts, append a
new candidate and expand selection; do not mutate the meaning of an already selected item.
Necessary supporting test/doc/helper files within the already approved goal, cost and behavior
may use that existing authorization: record their dependency and scope extension before writing,
without another user question. This never authorizes an unrelated new finding. Carry existing
behavior acknowledgements forward unchanged. Routine choices within the selected boundary
proceed autonomously.

## 4. Implement the selected work

Run `begin --id <selected-id>` before each implementation or investigation unit. It rechecks the
lifecycle, source identity and allowed paths. Do not write when the check fails. Assign
disjoint files and concrete acceptance to any delegated writer; the coordinator retains final
responsibility.

For a behavior-preserving refactor, identify relevant current behavior, change structure, then
verify the preserved outcome. Keep selected behavior changes explicit and test their own
contract. Use project commands/environments and impact-based verification. Shared contracts,
cross-module paths, persistence and security changes require their affected boundary checks;
optional quality packs remain optional. Preserve failures and fix their causes rather than
deleting valid checks.

Update only selected current authority documents, capabilities/MOC entries, actual module
responsibilities and valid constraints. Distinguish stale documentation from implementation
defects; never change Wiki solely to make a bug look correct. Record unknown or partial support
honestly. Reuse the existing Wiki structural validator; do not replay `$hl-wiki-merge`'s Feature
closure, retained-history transformation, tombstone creation or authority switch.

For each selected item, use `resolve` with its evidence, outcome and actual cost. `investigated`
records what was learned, not an unapproved fix. `transferred` completes a handoff, not the product
gap: preserve the proposed scope and remaining work, then pause/finish maintenance
before opening a new Initiative. Workflow/skill/template/dispatch improvements discovered here
are recommendations for another user-directed session, not edits in this run.

## 5. Independently review and verify

Have an agent who did not implement the changes review the actual selected diff, behavior
boundaries, test protection, relevant callers and evidence. Include the short read-only Agent
continuation check from the scan guide: formal entry and required reads must lead to capability,
reuse, authority/constraints, impact and verification. One concise review file may cover both
review and continuation; no new feature or extra per-item report is required.

Run the existing Wiki gate through `verify-wiki`. Separately record semantic Wiki evidence using
`record-check --kind wiki`: it must name checked claims/scenes, both mapping directions,
source/test/runtime evidence, remaining differences and the exact conclusion. A successful
selected-scope check is not a claim that all Wiki is consistent or all product behavior is right.

Record actual test results, review and handoff through `record-check` with the required actor
and evidence. Reuse applicable evidence for unchanged behavior; record why it still applies at
the final source identity. Extra execution needs an impact/risk reason, not just another phase.
The helper verifies stored provenance and source correspondence; it cannot judge the truth of
agent-authored evidence. Do not turn a missing, failed or unverified result into PASS.

Address review findings within the selected scope. If new evidence materially expands the
decision, add and present that candidate first. Recheck the affected area for newly introduced
problems, preserve unaffected valid results and stop once selected goals are satisfied.

## 6. Close, pause or recover

Use `finish --summary <result>` only when its appropriate closure conditions are met. An
implemented run needs all selected items resolved, independent review/continuation, applicable
tests, current-Wiki semantic checks and actual structural PASS. A scan-only outcome may retain
documented baseline failures or unverified differences: use `finish --scan-only`, which records
`scan-completed / diagnostic-scan`, and preserve the required semantic/structural observations.
Known retained failures require an explicit disposition. Do not label that result a verified
refactor or hide a selected failure behind a completion claim.

Summarise the actual result, realized benefit and cost, source identities, verification,
Wiki coverage/time, remaining/deferred findings and separate-session workflow proposals. State
which items were fixed, investigated or handed off. No-change scans are valid outcomes.
Commit/push/deployment remain governed by existing
authorization; candidate selection supplies none of those permissions.

For interruption or a requested stop, preserve evidence, use `pause --reason <reason>`, then
report remaining work and the run ID. Resume the same run with `resume` and recheck its selected
scope/evidence before continuing. Use `show` for read-only inspection. Never repeat completed
edits. If sources changed, follow the protocol's
refresh/recovery path; preserve the incomplete result and identify the concrete recheck needed.
