# Recording an assigned workflow

Recording is opt-in. Each experimental group gets one private directory for its ledger, outside the execution repos. Use a common operator-owned switch directory across groups. The trusted hook host needs write access to its ledger and switch read access. Grant evaluators read access to their own group. Use host filesystem isolation so execution sessions cannot read the ledger, other groups, grader materials, future Git objects or another thread's transcripts. Separate Git clones alone grant no filesystem isolation. Verify those boundaries with synthetic canaries on the selected agent surface before enrolling an experiment.

## Operator setup

Run `factory` from the pinned checkout, using the project's configured Python. Choose a different exact first line per stage in the same work directory. Both groups may use identical opening lines in separate workspaces.

```text
factory debug arm --work WORK --group-dir GROUP --stage STAGE --marker "OPENING LINE"
factory debug hook-config --group-dir GROUP --switch SWITCH
factory debug on --switch SWITCH
```

Install the emitted JSON in the trusted runtime hook configuration for the enrolled workspace. Review the generated hook commands through the runtime's normal hook-trust flow. Preserve existing hooks when installing in an existing profile. Select the corresponding stage by placing its exact opening line at the beginning of a fresh session's first prompt. A stage binds once. Agents that have not enrolled continue normally. The switch defaults off and a new switch epoch never resumes a prior enrollment.

Use synthetic or approved inputs whose visible messages and tool results are permitted in the private ledger. The process records tool arguments and output verbatim. Keep credentials and production data outside the enrolled workload. A trusted host writes the SQLite ledger even where the model's tool sandbox cannot read it. Model-visible tool events and hook tool payloads are separately identified. Opaque binary/media outputs and unavailable fields should be assessed only to the extent actually observed.

## Handoff and grading

Preserve each stage's first delivery, Git revisions and any uncommitted changes at handoff, before repair; record assistance and product decisions independently. A failed handoff can be evaluated with no downstream session. After the session ends and the runtime has flushed its transcript, seal the named stage and disable the switch when all intended stages are complete.

```text
factory debug seal --group-dir GROUP --switch SWITCH --stage STAGE
factory debug off --switch SWITCH
factory debug report --group-dir GROUP --stage STAGE --events
factory debug content --group-dir GROUP --sha256 DIGEST
```

Sealing reads any remaining timestamped rows from the already identified transcript, including late usage. Sealed stages ignore future hooks. Exact content references resolve inside the same group. The recorder accepts visible assistant messages, tool calls and returned results, and runtime token counts. It skips private reasoning and system/developer messages. Recorded event span is an observation window. Report known usage and actors without counts; a missing runtime field is unknown, and a truncated tool return supplies only the visible part. Capturing a path or tool call alone does not establish that an agent saw a specific rule. The grader independently runs the real entry point and captures stdout, stderr and exit status separately when the recording contains a combined stream.
