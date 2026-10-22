# Quick Change Record Template

Load factory context first: confirm the quick-workspace root from
`wiki/governance/workflow-profile.md` before creating a record, and keep the record inside that
root. This template is process material, never a lifecycle manifest.

Persist prose in `project.language.docs` when the profile sets it, otherwise in the user's language.
Keep IDs, keys, paths, `status` values, `scope_verdict` values and verdict labels ASCII.

```yaml
id: quick-YYYYMMDD-###
title: ""
kind: bugfix | adjustment
status: draft
created_at: "YYYY-MM-DDTHH:MM:SS+00:00"
updated_at: "YYYY-MM-DDTHH:MM:SS+00:00"
scope_verdict: pending | lightweight | escalate
escalation_reason: null
next_skill: null
wiki_targets: []
wiki_merge_readiness: ready | needs-target | blocked
```

## Request

- Original request:
- User intent: fix/adjust | analysis-only
- Reproduction or current behavior:
- Desired behavior:

## Feasibility Grill

Record one question and answer at a time. Capture the value, available code and data, compatibility,
security, privacy and project-specific risk categories, testing, rollback and failure handling, and
the lightweight eligibility conclusion.

## Scope Gate

- Hard gates checked:
- Complexity or supporting evidence:
- Verdict:
- Reason:

## Confirmed Change Points

- In scope:
- Explicit non-goals:
- Files/modules and ownership boundaries:
- Failure and compatibility behavior:

## Context Compaction

- Goal:
- Non-goals:
- Final change points:
- Acceptance criteria:
- Verification commands:
- Risks and escalation triggers:
- Open items:
- Compaction performed at (ISO-8601, required):
- Compaction method: native | fixed-block

## Implementation Notes

Append implementation decisions, changed paths, and deviations from the compact handoff.

## Verification Evidence

- Command or reproducible manual path:
- Expected result:
- Observed result:
- Evidence path or reference:
- Residual risk:

## Wiki Merge Handoff

- `wiki_targets`:
- Facts to merge:
- Candidate authority document:
- `wiki_merge_readiness`:
- Merge authorization and evidence:

## Escalation Handoff

- Escalation reason:
- Hard gate or newly discovered scope:
- Suggested Initiative/Feature decomposition:
- Existing evidence and constraints:
- `next_skill`:

## Open Questions / Residual Risk

Append unresolved items. Do not hide them in TODO comments or silently defer them.

## Addenda

After `completed` or `escalated`, append corrections and new evidence here without rewriting prior
sections, including one explicit `Final State` addendum that supersedes earlier `status`,
`scope_verdict` and `wiki_merge_readiness` values.

## Grill Confirmation Checklist

For each item, record an explicit user confirmation or `not applicable` with a reason:

- observed behavior and reproduction conditions;
- desired behavior;
- in-scope change points and non-goals;
- affected files/modules and ownership boundary;
- failure, compatibility and rollback behavior;
- acceptance criteria and repeatable verification;
- wiki target and residual risk.

Silence or an agent recommendation is not confirmation.
