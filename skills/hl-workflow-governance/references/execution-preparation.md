# Execution Preparation And Handoff

This is the shared operating procedure for preparing and reusing execution prerequisites.
It adds no lifecycle state, configuration switch, approval, environment service or standalone
report. Apply only the parts needed by the current plan and acceptance contract; documentation-only
work does not need an application runtime. Project facts come from the workflow profile, local
configuration, dependency/build inputs and formal task sources, never from this reference.
Existing project and enabled-pack service lifecycle rules still own start/stop operations; this
procedure does not introduce another runtime manager or widen their authorization.

## Prepare Once For The Required Path

The coordinator assigns one role to prepare the required environment and identify who will clean
up each resource. Others consume that handoff rather than independently installing dependencies,
starting equivalent services or initializing the same store.

Before an expensive install, build or acceptance run:

1. Identify the required surface and isolation from the actual criteria. Select the project's
   supported executable, version and command from its existing configuration, lock files and
   maintained instructions; do not default to the first global executable on PATH.
2. Inspect the applicable existing toolchain, cache, build or runtime. Use the smallest checks that
   decide suitability: version/identity, required input changes, configuration, health, resource
   ownership and the client's actual tool discovery or permitted read-only operation. If a
   temporary/output directory is needed and access is uncertain, probe creation/readback/removal
   of a disposable file in the task-owned directory before a long run. Do not probe real data.
3. Repair only a missing or disproven prerequisite through the supported project setup path and
   existing authorization. Do not update locks, change acceptance surfaces, relax permissions or
   disable checks to obtain a successful preflight. Preparation cannot grant missing permission.
4. Put the useful outcome in the existing plan or handoff: configuration/command references,
   applicable source/build identity, prepared resources and owner, observed check result, remaining
   prerequisites and reuse limits. Include only facts the next role needs; omit inapplicable parts.
   No extra inventory, receipt, hash layer or mandatory preparation file is required.

Tool discovery or health proves readiness to attempt a path, not successful business acceptance.
Keep machine-private paths, endpoints, credentials and raw sensitive logs in the project's ignored
local configuration or permitted private handoff. Persist only allowed references and synthetic
evidence in versioned task documents.

## Reuse At The Appropriate Level

Reusing a toolchain or download cache does not imply reusing a build, running process or dataset.
The receiving role independently checks only the conditions relevant to the next operation:
use current observations from the handoff where applicable, rather than replaying every probe
merely to acknowledge receipt.

- Existing tools/caches remain usable while their configured versions and access remain suitable.
- A build remains usable when its source, dependencies and build inputs meet the criterion; a tag
  or unrelated HEAD change alone neither proves nor disproves that. Use existing revision/diff and
  build evidence rather than another build merely because the role changed.
- A running environment also needs the required configuration, health, known ownership and state.
  Preserve a required clean baseline, session identity or continuous sequence. Shared mutable
  state requires sequenced consumers or separate state/process resources as the contract demands.

The designated owner manages shared configuration, start/stop and baseline resets. Consumers
perform the test or business calls already authorized by the plan, respecting its state/isolation
conditions; normal consumption needs no extra owner handoff. A new role or session is not an
automatic teardown trigger. Transfer management ownership explicitly when it changes; check which resources
survived an interruption before continuing. Stop only confirmed task-owned resources when their
last required consumer has finished, respecting the existing retention and cleanup policy.

Invalidate the affected preparation or result when its actual inputs or conditions change. A
small change is not a reason to discard an unrelated working toolchain or every previous result.

## Overlap Preparation, Preserve Judgement Order

Source survey and safe prerequisite preparation may overlap when they do not change the same
files, resources or required state. A reviewer may read the contract and prepare checks early;
formal review judges the identified, stable implementation. A separate verifier may prepare
tools, permitted synthetic resources and a coverage plan while implementation/review proceeds,
but final acceptance starts only after required review passes. Preparation is never reported as
acceptance, and stale preparation is repaired before use. If even preparation would alter a
required baseline or interfere with another role, sequence or isolate it instead.
Warm only stable dependencies/caches or reuse an already suitable build. Do not produce the final
reviewed/accepted artifact from source inputs still being edited; wait for the relevant inputs to
stabilize, then build only what changed.

Use one canonical implementation plan. Reuse current source surveys and owner proposals for the
same scope; request only missing or changed input. Do not create an extra planning or confirmation
turn merely to change a role label. Every implementer still checks the approved plan and assigned
write scope before editing; missing authority, changed contracts and scope conflicts stop the
affected work. Independent review and separated verification remain independent roles.

## Hand Off The Delta And Remaining Work

Use the existing role-specific handoff, with references rather than a second report or copied
transcript. Supply the identified source/plan and relevant changes; the actual commands, exits,
evidence and conditions of reusable results; available resources and cleanup responsibility; and
the remaining required checks or blockers. Reuse current reading notes and formal sources, then
inspect the changed, uncertain or decision-relevant parts. A summary alone is not evidence.

Dispatch the next permitted role as soon as its required inputs are ready. Do not hold it for
cosmetic restatement, duplicate source inventory or a new narrative of unchanged history. Material
documentation sync, required gates and source stability still govern that boundary. Re-review and
re-verify affected findings and their dependent paths after repairs, preserving valid results.

## Diagnose Waiting Instead Of Repeating Work

Prefer completion notifications or a bounded wait that wakes on a result. When those are absent,
poll the existing task at a reasonable interval using its last known phase/output; do not launch
a second install, build or service just because the first is slow. Keep user updates meaningful.

At a stall or failure, identify the running process/phase, last output and concrete cause before
retrying: incompatible tool, access/approval, lock, download, unavailable service, test fixture or
product defect. A retry needs a changed prerequisite or an explicit bounded diagnostic purpose;
an unchanged failed command is not a repair. Preserve failure facts, distinguish environment
failures from code failures and continue independent work. Use applicable project/tool timeouts;
do not repeatedly extend a hung task without evidence of progress. Never count a wait's requested
duration as measured idle time or treat a timeout as a passing check.
