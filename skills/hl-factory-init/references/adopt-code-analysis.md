# Adopt Code Analysis

Use this reference only for **adopt mode with existing code**. Its job is to turn the
adopted codebase into an evidence-based wiki baseline so the first Feature discussion does
not start from an empty wiki.

Greenfield `init` skips this phase: there is no code to analyze.

## When it runs

- after `factory adopt` has written the skeleton and `factory doctor` / `factory gate all` pass;
- before the green baseline and the initial git commit;
- it is read-only with respect to code: no source edit, no behaviour change, no dependency install.

## Output contract

Analysis subagents write findings to `.factory/analysis/<slice>.md` (gitignored). They never
edit the wiki. The main session synthesizes those findings into the long-term wiki:

| Target | Content |
| --- | --- |
| `wiki/architecture/overview.md` | system shape, modules, dependency direction, data flow, runtime boundaries |
| `wiki/domain/overview.md` | domain objects, business terms, inputs/outputs, calculations or rules found in code |
| `wiki/implementation/overview.md` (+ per-owner docs when owners are distinct) | what each implementation area does, entrypoints, key files, extension points |
| `wiki/testing/overview.md` | test layout, how to run tests, offline/network assumptions, known gaps |
| `wiki/governance/runtime-and-operations.md` | scheduling, install/deploy, config, state/lock files, logs, failure and retry behaviour |
| `wiki/02-file-authority-map.md` | add the new authority docs to the topic table |
| `wiki/code-ai/project-facts.md` | real stack, commands, repository layout, test layering |
| `wiki/governance/init-record.md` | append a short analysis summary and unknowns |

Only create the documents the code actually supports. Prefer fewer, denser documents over a
file per module. If the wiki already has a project-owned document at one of these paths
(adopt into an existing wiki), do **not** overwrite it: write a separate `*-baseline.md`
and link it, or ask the owner.

## Analysis slices

Dispatch these in parallel when the platform supports subagents. Each subagent is read-only,
has one slice, and returns the fixed handoff below. If the platform has no subagent facility,
run the slices sequentially in the main session.

| ID | Scope | Questions |
| --- | --- | --- |
| `repo-map` | repository tree, manifests, entrypoints, build/run scripts, ignored artifacts | What are the top-level areas? What runs, and how? Which files are generated and should stay out of git? Do README claims match the code? |
| `core-logic` | main modules and their responsibilities | What is the execution flow per entrypoint? Which module owns which state? Where are errors, retries and fallbacks handled? |
| `data-contracts` | inputs, outputs, file formats, APIs, persistence, external data sources | What data enters and leaves? What schemas/fields are stable? What is fetched externally, with what freshness and failure behaviour? |
| `operations` | scheduler/cron/install/deploy scripts, config, logs, state and lock files | How is the system scheduled or deployed? What state survives between runs? What are the operational failure modes and recovery steps? |
| `tests` | test files and verification scripts | Which commands run tests offline? What is covered, what is not? Which checks need network or credentials? |
| `security-privacy` | secrets, credentials, account data, private/public boundaries, irreversible actions | Where could sensitive data appear? What must never be committed or published? Which actions are irreversible or externally visible? |
| `domain-glossary` | business terms, report sections, user-facing outputs | What terms does the product use? What do the outputs mean? Which calculations or rules are domain-specific? |

## Subagent prompt template

```text
You are a read-only code analyst for the HighLand-factory adopt phase.

Scope: <paths>
Slice: <id>
Task: answer the slice questions with evidence from the code. Do not modify code, wiki or git.
Do not run installs, network calls or the product itself; static reading plus existing docs only.

Output exactly:
## Scope
<relative paths read>

## Findings
<dense, factual, one bullet per fact>

## Evidence
<relative file paths and line numbers for each non-obvious claim>

## Unknowns
<what the code does not establish>

## Risks
<fragile, surprising or security-relevant behaviour>

## Suggested wiki targets
<which target document each finding belongs to>

Rules:
- cite relative paths, never absolute machine paths;
- redact secrets, credentials, tokens, account identifiers and private data;
- mark inference explicitly; do not invent behaviour;
- write the result to <WORK_ROOT>/.factory/analysis/<slice>.md and return the same content.
```

## Synthesis rules

1. Code is authoritative over README claims; record a discrepancy instead of repeating the README.
2. Write in `project.language.docs`; keep code identifiers, paths, API names and schema fields as-is.
3. Every non-obvious factual claim cites a relative source path; unknowns stay marked as unknowns.
4. Do not copy README or comments wholesale; synthesize and de-duplicate across slices.
5. Do not write into `wiki/feature-workspace/`; this is baseline authority, not a Feature.
6. Link every new document from its domain MOC (and the root MOC when it is a primary entry),
   so the long-term wiki stays within three hops and has no orphan Markdown.
7. Update `wiki/02-file-authority-map.md` and `wiki/code-ai/project-facts.md` in the same pass.
8. Append a short summary to `wiki/governance/init-record.md`: slices run, documents written,
   unresolved unknowns and conflicts found.

## Validation gate

Before declaring init complete:

- every slice finished or is explicitly marked skipped with a reason;
- each new wiki document is reachable from the root README within three hops;
- `factory gate wiki --work <work>` passes;
- `factory doctor --work <work>` has no errors;
- no secrets, absolute machine paths or private identifiers were written;
- `git status` shows only expected wiki/config additions, no code changes;
- the handoff lists the documents to read first and the unknowns that need an owner decision.
