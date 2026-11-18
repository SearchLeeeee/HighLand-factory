# Refactor Scan and Review Guide

Use this reference during the read-only scan, candidate preparation and independent review.
Keep findings in the run's existing candidate/evidence record; do not produce a parallel
architecture report or a second catalogue of all project capabilities.

## Contents

- [Scope and source identity](#scope-and-source-identity)
- [Code, dependencies and defensive behavior](#code-dependencies-and-defensive-behavior)
- [Test cleanup](#test-cleanup)
- [Current-Wiki business consistency](#current-wiki-business-consistency)
- [Candidate quality and decisions](#candidate-quality-and-decisions)
- [Independent review and Agent continuation](#independent-review-and-agent-continuation)

## Scope and source identity

Treat scan scope, selected change scope and budget as three different things. Full scanning
does not authorize full rewriting; a small maintenance task is small in total cost, not just
file count. Use the requested budget or state that it is unspecified. Never invent precise
hours or savings percentages without evidence.

For `full`, map current source, tests, important configuration/scripts, reusable capabilities,
responsibility boundaries and authoritative Wiki entry points. Then inspect likely complexity,
duplication, stale content and scene mismatches. Exclude generated/dependency/log material based
on project facts. Independent read-only analysis may run in parallel with disjoint questions;
the coordinator reconciles duplicates and preserves actual coverage limitations.

For `latest`, identify the latest completed Initiative incorporated into the current baseline.
Require evidence covering **all effective Leaves, integration fixes and final Wiki updates**;
track additions, removals and renames. An ID, directory timestamp, integration PASS or final
commit alone does not establish this range. A user-supplied range still needs an explanation
of how it covers the complete Initiative. Missing trustworthy boundaries require one concrete
scope decision or a switch to `full`, never a silently smaller scan.

Inspect the current surviving implementation. Read affected callers, contracts, similar
implementations and related Wiki outside the diff where needed to understand impact. Record
these expanded reads; they do not turn an incremental result into a whole-project verdict.
In split mode establish code and Wiki identities and ranges separately.

Bind observations to timestamp/timezone, code/Wiki revisions, relevant uncommitted changes and
configuration. A revision alone does not identify uncommitted content. The helper records source
identity and detects changes; the agent still decides which evidence supports which claim.
Recheck affected conclusions after relevant changes and reuse unchanged evidence when valid.

## Code, dependencies and defensive behavior

| Dimension | Seek evidence of | Decision rule |
| --- | --- | --- |
| Reuse | The same business rule maintained in several places; hard-to-find existing capability | Search existing project facilities before adding another; name concrete callers and ownership |
| Responsibility | Mixed reasons to change, dependency cycles, reverse dependencies, broad shared mutable state | Separate responsibilities when change patterns justify the boundary; assess caller impact |
| Simplicity | Forwarding-only layers, unused abstractions, unreachable branches, obsolete configuration or temporary scaffolding | Demonstrate redundancy and removal effect; line reduction is not the acceptance criterion |
| Design patterns | Repeated pressure that an established pattern can address | Explain the actual problem, boundary benefit and added concepts; no pattern for appearance |
| Similar code | Similar syntax with potentially different business meaning | Allow duplication when responsibility, semantics or future change direction differ |
| Structural stability | Proposed reversal of an earlier design | Require new usage/maintenance evidence; stylistic preference cannot justify repeated reorganisation |
| Dependencies | Proposed third-party capability | Name several real uses, the insufficiency of current facilities, and clear net efficiency after integration, upgrade, maintenance and diagnosis costs |

Distinguish real external-boundary validation, retry, idempotency and supported compatibility
from repeated checks, ineffective fallback or hidden failures. Missing explanation in the
current context is **not deletion evidence**. Trace callers, contracts, configuration, historical
questions through the authorised provenance path, and tests only as needed.

When purpose remains unclear, propose an `investigate` candidate: exact questions and read
targets, a bounded cost, what evidence ends the investigation, and the decision it will enable.
An investigation selection authorizes that investigation, not deletion discovered to be possible
later. Re-present consequential edits as candidates before writing them.

Classify removal of compatibility, changed error/fallback behavior, changed input acceptance,
side effects or exposed contracts as `behavior`. State old and proposed observable outcomes,
affected consumers and verification. Obtain the user's explicit selection of each such item;
never hide it inside an ostensibly behavior-preserving extraction.

## Test cleanup

For each proposed deletion, merge or rewrite, record:

1. The behavior or boundary the old test protects.
2. Whether that requirement remains effective, and the authority for any retirement.
3. If still effective, the retained/replacement checks that preserve that protection.
4. The actual checks needed to show that cleanup did not mask a defect.

Compare contract, input classes, failure paths and test layer. A unit test and integration test
with similar inputs can protect different boundaries. A long-passing historical regression
test is not obsolete merely because the failure has not recurred. Prefer observable behavior
over coupling to private implementation when the protected behavior remains valid.

Classify an existing failure as a real defect, environment failure or invalid expectation
before changing it. Do not delete a valid failing test or weaken its expectation to manufacture
PASS. Do not require a lower test count, mirror new implementation details in tests, or treat
coverage/complexity numbers as proof of correctness. Use optional quality tools only when
enabled and useful for an actual decision.

## Current-Wiki business consistency

### Identify authority and exclusions

Read the configured Wiki entry, reading guide and authority map. Use the shared resolver's
exact built-in and explicitly registered process roots. Exclude feature, quick, refactor and
configured process workspaces from current-fact discovery and canonical reachability. Do not
exclude a normal directory just because its name contains `workspace`.

Reuse the existing current-Wiki inventory when useful:

```text
<PYTHON> <FACTORY_ROOT>/skills/hl-wiki-merge/scripts/inventory_llm_wiki_merge.py --wiki-root <WIKI_ROOT> --format json
```

This lists current Markdown outside registered process roots, including applicable `code-ai`
material. It is discovery evidence, not semantic PASS. The existing `--source` mode remains
for staged Feature merge material; do not use it as a substitute for current-state inventory.

Read lifecycle/range metadata where necessary to establish scan scope; do not import historical
plans or discussion into current product truth. Current Wiki should distinguish implemented
capabilities, effective contracts, configuration, limits, verification entry points and known
gaps. Preserve still-effective constraints even if the implementation violates them.

### Compare complete scenes in both directions

Maintain a compact evidence mapping in the run: **Wiki claim → implementation path → evidence
type/reference → verdict**, plus important implementation facts absent from Wiki. For each
material scene inspect the applicable parts:

| Scene element | Questions |
| --- | --- |
| Entry | Which user/API/job entry reaches this capability? Is that route actually connected? |
| Preconditions | Which configuration, permissions, inputs and dependencies enable it? |
| Branches | Which material alternatives, supported/unsupported cases and exceptional paths matter? |
| Result | What can the caller observe, including errors, persistence and other side effects? |
| Resilience | Where claimed, what are retry, idempotency, fallback or degradation semantics? |
| Evidence | What was inspected, tested or observed, under which version and configuration? |

Check both (a) documented scenes against implementation and (b) important implemented abilities,
contracts and limitations against authoritative documentation. Do not document every helper.
A function, endpoint or button found in search proves only that fragment exists, not that an
entire scene works. Mark missing evidence as unverified.

| Difference | Candidate direction |
| --- | --- |
| Documentation is stale after an implementation change | Update the authority document from evidenced current facts |
| Implementation violates an effective business agreement | Present the defect or capability gap and fix/handoff cost; do not rewrite the agreement to bless it |
| An unrealised plan is described as available | Correct availability, preserve effective constraints and the remaining implementation gap |
| Only part of a scene or some configurations work | State supported conditions and limitations; distinguish an expected limitation from a defect |
| Important implemented behavior is undocumented | Add it at the owning authority and update the relevant discovery/MOC entry |
| Current authorities conflict | Identify the authority and evidence; obtain a decision only when a real business choice remains |

Judge **documentation consistency** separately from **business correctness**. Do not assume
changing Wiki is always the right repair, or that one undocumented code branch justifies
changing behavior. Repairs must be part of the selected candidate set.

### State what the evidence establishes

Label source inspection, test execution and runtime/deployment observation separately. Default
claims concern the checked source/configuration versions. Describe a deployed environment as
enabled or operational only with corresponding deployment and runtime evidence; ordinary
maintenance does not require production access. Record time/timezone and both repository
identities with necessary diffs. No statement implies ongoing automatic synchronisation.

Record semantic conclusions separately from `factory gate wiki`. Structural PASS confirms the
existing structural rules, not complete scene support. Retain scan limits and all unverified
or user-deferred differences in the final result, even when the selected maintenance completes.

## Candidate quality and decisions

Give each issue a stable ID, type, exact evidence, proposed action, concrete benefit, complete
cost, risks/unknowns, affected paths/callers, dependencies, acceptance and recommendation.
Cost covers investigation, implementation, verification and code/test/Wiki synchronisation.
Low/medium/high with specific work is sufficient when estimates are uncertain.

Recommend implement, investigate, retain or hand off based on evidence. Present alternatives
when they materially alter benefit/cost. A low-value style edit can reasonably be retained.
Record why candidates depend on each other and avoid a selection that promises a benefit
without its required supporting change. Preserve user decisions, not the agent's recommendation
as if approved. The runtime schema and commands are in `run-protocol.md`.

For a new capability or substantial change requiring the normal Feature process, use `handoff`.
Complete only the selected investigation and handoff in this run, record the remaining product
gap, then pause/finish the maintenance run before opening a new Initiative. Never reopen the
original Initiative or report a transfer as a fixed defect.

If the root cause is in generic workflow rules, templates, dispatch or governance, record the
proposal and evidence for another user-directed session. Current project capability, module
responsibility and contract documentation may be maintained when selected. Do not quietly
turn a project refactor into editing the factory or changing its rules.

## Independent review and Agent continuation

Use a reviewer who did not implement the selected changes. Supply selected candidates and
decisions, source identity/diffs, applicable project criteria and decisive test/Wiki evidence.
Have it inspect actual changes, scope, behavior boundaries, test protection and affected callers.
Reuse sound execution evidence; independent judgment does not require duplicate full runs.

Include a short read-only continuation exercise in that review: start at the formal project
entry, follow **all existing role-required reads**, then find the affected capability's entry,
reuse method, current authority/constraints, caller impact and verification command. Important
structural rationale should be discoverable in current material without loading all history.
Report the concrete paths and any discovery gap. Do not shrink mandatory startup reading,
write a second capability catalogue, implement a sample feature or demand a separate report
for every candidate. One review file may support both review and handoff receipts.

Before closure, recheck the affected area for newly introduced problems, ensure selected goals
and receipt evidence are satisfied, synchronise tests/current Wiki, and retain honest dispositions
for remaining issues. Stop there; speculative extra cleanup is another candidate decision.
