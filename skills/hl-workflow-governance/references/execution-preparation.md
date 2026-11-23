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

## Cross-Session Continuity

Decide debug recording once, at intake for each independent workflow (including Quick
Change). Default to off, silently, even in the same chat, workspace or Initiative as a
recorded task. Only an explicit request from the user at that workflow's start authorizes
`factory debug flow start`. Choose a fresh flow ID. When the opening request omits debug,
use the ordinary workflow commands throughout; create no recording, emit no marker and
do not enable recording mid-flow. Prior chat instructions, old handoffs and open ledgers
are not preferences to inherit.

For opted-in work on a registered Initiative or Leaf, pass `--scope <full-ID>` at start,
using the canonical work root and registry. Bind to the requested Leaf when the request
covers that Leaf alone. An Initiative enrollment covers its registered children. If formal
registration comes after intake, declare `--pending-scope initiative` or `feature` at
start and use `factory debug flow bind` with the same recording coordinates as soon as
the authorized ID is registered. Ordinary unscoped tasks use the original start command.

On a fresh continuation resolve the target using the validated registry. Read
`factory debug flow lookup --work <WORK_ROOT> --registry <registry> --scope <full-ID>`
and reuse its flow ID and records root on a match. A lookup recovers the opening
authorization for that scope. Only link a parent event when a specific handoff
supplies it, since parallel branches can share a recording. If the result is null, continue
with the ordinary commands unless a current handoff explicitly continues an unscoped
recording. On conflict or ambiguous identity, resolve the actual task before writing
debug events. A recovered parent recording stays open across individual Leaf completions.

When continuing the same opted-in work (including a child dispatch or its current
`factory-flow <id> <phase>` handoff), use the existing flow ID and write evidence through
`factory debug flow` from the agreed work root. Read `<FACTORY_ROOT>/docs/flow-eval.md`
for syntax. Every participating client or role uses the same flow ID and records root.
Use `begin/end` at meaningful phase or task boundaries, `run` around actual tests,
builds and gates, and `note` for consequential decisions, blockers, retries, deliveries
and handoffs. Attach the actual deliverable with `--artifact` at first delivery and on
revision. Include the upstream event via `--parent` when one is provided. Record observed
results as they occur. Flag a missed recording in the usual handoff.

Prepend `factory-flow <same-id> <next-phase>` **inside** each copyable or authorized
dispatched prompt continuing the work, including child tasks and parallel roles. Carry
the common WORK_ROOT, any explicit `--records` location, and the dispatch or handoff
event number. Tell the receiver to continue recording with `factory debug flow` using
its own role label. Scope propagation to the selected workflow; the audit is read-only.

At final completion or cancellation of the enrolled workflow, the coordinating agent
finishes its outstanding evidence and runs `factory debug flow seal` for that ID. Use
`--incomplete` if the workflow truly ended with unfinished steps. A phase end, pause
or same-workflow handoff is not final closure. Drop the recording coordinates at the
workflow boundary; a handoff suggesting a separate next task carries no debug marker.

Make the existing handoff sufficient without the prior chat. Carry the current task/next action,
formal authority paths and the few critical conditions that must survive the handoff, including
linked same-object, artifact, session or sequence requirements where applicable. State those
conditions directly with their source sections; a long must-read list alone does not preserve
them. Separate confirmed constraints from proposals, deferred questions and unresolved gaps.

For evidence the next step will rely on or continue, cite the actual record and what it proves,
its relevant source/run/object/version identity, reuse conditions and continuation entry point.
Use the existing evidence record and allowed local-configuration references to locate the required
state, artifact or client. Do not rely solely on a transient path or prior chat. Keep private
connection details outside versioned documents. State missing/unavailable entries as gaps rather
than assuming the environment or original scenario survives. Omit predecessor evidence when none
is needed; never invent a passing result to fill the handoff.

List required checks not yet executed, not proven or blocked, and what remains to establish them.
The receiver reconciles the critical conditions and claimed evidence with current manifests,
contracts and sources as part of its normal work. Successful file reads are not semantic acceptance;
the coordinator retains the cross-step conditions even when a reader surveys their source files.
This needs no separate acknowledgement turn, checklist document or repeated user confirmation.

## Evidence Source Changes

If the selected evidence/state becomes unavailable, or work switches to a recreated scenario,
reset baseline, different artifact or session, preserve the old observations and record the change
where that work is already tracked:

- Identify the reason and old/new source, with only the identities needed to judge applicability.
- Explain which continuity conditions remain proven or were lost, and the affected criteria/rows.
  Same labels, manually reused IDs or the same code do not by themselves establish state lineage.
- Update the relevant assumption/decision and revision in the existing plan when its selected
  source changes, and synchronize the acceptance/result mapping. Keep unaffected valid results.
  Do not rewrite the original run or carry its PASS onto an unproven changed claim.
- Judge the new evidence against the original criterion. A fresh scenario may prove capability;
  it proves continuation only with the required lineage and linked conditions. A different physical
  instance can qualify when that lineage is demonstrated and the criterion permits it. Keep a
  missing required connection unverified/blocked and execute only the affected missing path.

The coordinator and independent verifier assess that impact; neither a replacement source nor
the implementer's summary grants acceptance. Source changes within existing authorized scope do
not require another user approval. If the goal, acceptance condition or permission must change,
use the existing decision/authorization boundary, retaining any authorization that already covers
it. Continue independent work and preserve the existing lifecycle owner and gates; add no status,
source registry, hash requirement or extra report.

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
