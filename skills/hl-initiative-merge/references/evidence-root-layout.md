# Integration Evidence And Result Binding

Load factory context first: use `.factory/local.yaml` and `wiki/governance/workflow-profile.md`
for paths, commands, required criteria and safety boundaries.

## Minimum Record

Keep one integration run record under the configured Initiative evidence root. It identifies:

- the source revision and relevant diff/new files, plus runtime or external identity needed by the criteria;
- each required criterion, its expected result, actual status and the evidence that decides it;
- commands actually run and their exits, applicable reused results and original provenance;
- unresolved limitations, failure facts, cleanup and the overall verdict.

Use the existing handoff/report and a small result file if a machine gate needs one. A separate
index, directory per Feature, frozen/ subtree, hash manifest and log-checksum collection are not
defaults. Add structure only when it makes the actual evidence easier to use. Do not introduce
configuration, approval steps or a new evidence framework.

## Criteria And Changes

State criteria before running their checks. Do not rewrite failures into passes or silently relax
the criterion after observing results. Preserve the original outcome when a criterion is revised;
apply the ordinary scope/authorization boundary to material changes without duplicate approvals.
Non-semantic corrections may be noted without rerunning tests or replacing valid results.

After a fix, changed conditions or a missing record, identify affected rows and execute what remains
unproven. Reuse unaffected results only when relevant sources, fixtures, runtime and criterion
conditions remain applicable. Record where those results came from instead of calling them fresh
executions. Same-artifact, same-session or clean-state comparisons must still meet their stated
requirements; a partial replay cannot prove a required first-run sequence.

## Evidence Location

Make each required row's decisive evidence discoverable from the normal record. One mapping is
enough; do not keep multiple manually synchronized indexes or independently re-hash every file.
Git identity and relevant diff are sufficient for ordinary source tracking. Use byte hashes for
an actual artifact identity/integrity need, not to certify every piece of evidence recursively.

Keep raw logs outside directories test tools may clear. Preserve command exits and failure output
as they occur; if a record is missing or ambiguous, say which criterion remains unverified and
repair that gap without automatically discarding every other result. Never fabricate a pass.

Keep sensitive configuration, credentials, real data and raw logs out of repositories according
to the project policy. Retain only safe results and references. Check redaction on the affected
surface before sharing; keep original sensitive values in their authorized location.

## Final Decision

The coordinator checks criterion coverage and decisive evidence, sampling or rerunning by actual
risk rather than duplicating every delegated check. A total is a convenience, not proof of coverage.
Required failed, blocked or unverified rows still block PASS. Execute the official registration and
readiness gates, respect commit/merge/push authorization, and stop once the delivery boundary is met.
