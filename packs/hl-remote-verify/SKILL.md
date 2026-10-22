---
name: hl-remote-verify
description: "Opt-in pack for remote/isolated verification: takes one commit through an isolated clone on a configured host and returns a machine verdict (0 pass, 10 code, 20 environment, 30 identity, 40 evidence). Environment failures must never be reported as code failures. Enable with packs.enabled: [remote-verify] and configure packs.remote-verify; nothing is hardcoded."
---

# Remote Verify (pack)

## Pack status

This directory is an **optional pack**, not a core skill. Core workflow must run with
`packs.enabled: []`; no core skill may require a remote host or this pack.

- Enable: install or link `<factory>/packs/remote-verify/` into the agent skill root, then:

  ```yaml
  packs:
    enabled: [remote-verify]
    remote-verify:
      host: <remote-host>
      user: <remote-user>
      clone_path: <absolute-remote-clone-path>
      entry: <absolute-remote-entry-path>
      evidence_root: <path-inside-work-repo>
  ```

  Then run `factory upgrade --work <work>` and `factory doctor --work <work>`.
- Disable: remove `remote-verify` from `packs.enabled`; do not run remote steps by hand under
  this contract.
- The values above are **project facts**. They live only in `.factory/factory.yaml` (or the
  work repo's generated profile) — never in this pack file.

## When to use

Use this pack when a change needs a verdict from an environment other than the author's, when
`verification.isolated_env` is `remote`, or when portability is exactly the risk (path case,
permissions, host toolchain). It consumes one commit and returns one machine verdict.

Do not use it to answer a design question, to explore an idea, or to batch-verify several
commits. A design question is answered with the design and tradeoffs; provisioning a host
starts only when the user says go. Do not use it as a substitute for checks the remote cannot
run — say those were not run.

## Step 0 — mandatory preamble

1. Read `<work>/.factory/local.yaml` and resolve `factory_root` and `python`.
   If missing or unreadable, stop: "machine config missing — run `factory init`
   (or `$hl-factory-init`) for this work repo, then retry."
2. Read `<work>/wiki/governance/workflow-profile.md`.
   If missing, stop: "workflow profile missing — run `factory upgrade --apply --work <work>`,
   then `$hl-factory-doctor`; do not hand-write the profile."
3. Confirm `packs.enabled` contains `remote-verify`. If not, stop with the enable snippet and
   the two commands above.
4. Read `<work>/.factory/factory.yaml` and resolve the `packs.remote-verify` config contract below
   (the workflow profile only lists enabled packs, not their configuration). Any required key
   missing or empty stops the pack before any remote command runs.
5. Run `factory doctor --work <work>`. A failing doctor stops the pack.

## Config contract

`packs.remote-verify`:

| Key | Required | Meaning |
| --- | --- | --- |
| `host` | yes | address the verification host is reached at |
| `user` | yes | login used for the non-interactive session |
| `clone_path` | yes | absolute path of the read-only clone **on the remote host** |
| `entry` | yes | absolute path of the remote verifier entry point, invoked non-interactively |
| `evidence_root` | yes | directory inside the work repo that receives logs and the manifest; must sit under `verification.evidence_root` when that is set |
| `transport` | no | mapping of free-form notes (see below): `notes` list, `mirror_remote`, `ssh_alias`, `bundle_dir` |

Also read from core config: `repo.default_branch`, `repo.remote`,
`verification.evidence_root`, `security.forbidden_operations`.

`transport` values are **data for a human decision**, not commands to execute blindly. The pack
must read a note, choose a fallback explicitly, and say which one it used.

Empty-config behaviour (fail closed):

```text
remote-verify pack cannot run: packs.remote-verify.<key> is missing.
Enable packs.enabled: [remote-verify], add host, user, clone_path, entry and
evidence_root under packs.remote-verify, run factory upgrade and factory doctor,
then retry.
```

Never default a host, a path or an evidence root.

## Exit-code contract (public, do not renumber)

| rc | Class | Meaning | Required action |
| --- | --- | --- | --- |
| 0 | PASS | The commit passed every stage that ran | only now may the change be called verified at that sha |
| 10 | CODE | The code at that exact sha failed a real check | read the failing stage log, fix the code, new commit, new run |
| 20 | ENVIRONMENT | Host, network, transport, toolchain, permissions or provisioning failed | do not touch code; repair the environment and rerun the same sha |
| 30 | IDENTITY | The remote state is not the identity requested: wrong repository/origin, dirty read-only clone, or the resolved sha differs from the requested one | stop; restore the configured clone identity; never reset or rewrite to hide it |
| 40 | EVIDENCE | The run happened but evidence (stage log, manifest, exit code) is missing, empty, unreadable or unsealed | fix evidence capture and rerun; never report the run as passed |

Rules:

- The exit code is the verdict channel. Do not re-read logs to guess a class, and do not
  reclassify a result after the fact.
- Every early-exit branch must print its own standalone `reason=` line; the local driver parses
  that key, so a branch without one produces an empty explanation.
- A stage that did not run is `skip`, never `pass`.
- **Environment failures must not be reported as code failures.** rc 20 never becomes 10, and a
  timeout or unreachable host is never "the code is broken".
- Only `0` authorizes "verified on the remote host at sha X". Anything else is unfinished work.

## Step-by-step flow

### 1. Local preflight

1. Resolve the commit to verify: the given sha, or the local `HEAD` of `repo.default_branch`.
2. Require a clean worktree. If the tree has uncommitted changes the sha does not contain,
   stop — the remote would verify something you cannot reproduce.
3. Confirm the object exists locally and resolve the full sha; abort on an unknown or ambiguous
   revision.
4. One commit per run. Do not batch a pipeline over several shas and report one verdict.

### 2. Reserve evidence before running

Create `<evidence_root>/<sha>/` first, so even an early failure has somewhere to write. If the
directory cannot be created or written, stop with rc 40 immediately.

### 3. Reachability

Probe the configured host and user with a non-interactive, timeout-bounded connection. One
retry on a transient failure, then classify rc 20 with a `reason=` line and captured evidence.
Do not start an interactive login and do not prompt for a password.

### 4. Make the sha available on the remote

Ask the remote clone to resolve the sha. If it cannot, treat it as a transport problem, not a
code problem, and choose one fallback explicitly:

- **Push then fetch** — normal path: the commit reaches the configured remote and the remote
  clone fetches it.
- **Bundle** — network-independent. Create a bundle at an OS-native path inside the local
  repository, copy it to the remote, fetch it there into a **throwaway ref** (never merged or
  pushed), confirm the object exists, then delete the bundle on both sides.
- **Alternate endpoint / alias** — when the default SSH route is blocked by a proxy, use the
  SSH config alias (or alternate SSH port) from `packs.remote-verify.transport.notes`. Test the
  alias, not the bare host: the bare host offers the default key and returns a misleading auth
  failure. Reachability over an alternate endpoint is an environment fact, not a code verdict.
- **Mirror** — point the remote at a mirror it can reach, fetch there, then verify the exact
  sha. Never rewrite history to match the mirror.

Re-check that the sha is resolvable after the fallback. Still missing → rc 20 with the transport
reason. Never downgrade a transport failure to rc 10.

### 5. Identity check — before executing anything

1. The remote clone's origin matches the configured `repo.remote` / repository identity.
2. The clone is clean (read-only discipline). Any dirty entry is rc 30 — surface the drift,
   never erase it.
3. The entry point that will run is the one from the commit being verified; compare content
   hashes and record both. Silent skew means you are debugging a different script.
4. The resolved remote sha equals the requested sha byte for byte.

Any mismatch → rc 30, stop, write the evidence, and report what differed.

### 6. Execute

Run `entry` on the remote non-interactively with the sha and a bounded timeout, writing each
stage's stdout/stderr to a stage log under the evidence directory. Requirements:

- An explicit `PATH` is exported for the session; non-interactive shells do not read the login
  profile.
- A command whose literal text carries a long-lived server invocation is refused by some
  hosts. Put the sequence in a script, transfer it, and invoke it by path; or run the
  long-lived part in background mode and poll readiness separately.
- Kill by PID, never by a pattern that can match the invoking session.
- Do not run GUI/browser-only checks here. Say they were not run; do not fake them.

### 7. Capture evidence

Pull stage logs and write a manifest containing: requested sha, resolved sha, entry hash, start
and end timestamps, per-stage status, exit code, and host identity. Evidence must be complete
and readable — a truncated pull, a zero-byte artefact, or a missing exit code is rc 40.

Never store credentials, tokens or account identifiers in evidence; redact before writing and
re-grep the raw value to prove redaction.

### 8. Verdict and report

Print one line and keep it stable:

```text
rc=<0|10|20|30|40> reason=<short-machine-readable-token> sha=<full-sha> evidence=<path>
```

Report, in the user's language: the verdict class, which stages actually ran, which were
skipped, the evidence path, and the single next action. Do not call a piecemeal result
"verified".

## Failure handling

| Situation | rc | Action |
| --- | --- | --- |
| Unknown/missing sha locally | 20 | stop; the input is wrong, not the code |
| Unreachable host / auth / timeout | 20 | one retry, then environment repair; keep code untouched |
| Sha not available remotely | 20 | choose and name a transport fallback; never guess |
| Wrong origin, dirty clone, sha changed | 30 | stop; restore identity; never reset or rewrite |
| Read-only discipline broken | 30 | report the exact dirty paths before anything else |
| Entry hash differs from the commit | 30 | redeploy from the commit, then rerun |
| Real check fails at the sha | 10 | read the stage log tail, fix code, new commit, new run |
| Evidence missing / partial | 40 | fix capture, rerun; do not report a pass |
| Stage skipped | — | report `skip`; it cannot contribute to a pass |
| Run interrupted | 20 | record the interruption, release the remote cleanly, rerun from scratch |

## What this pack must never do

- Never verify uncommitted work or a sha the local repo cannot reproduce.
- Never commit, push, or reset on the read-only remote clone.
- Never `reset --hard`, clean, or otherwise erase drift on the remote to make identity pass.
- Never report an environment, transport or evidence failure as a code failure.
- Never claim a pass without rc 0 and captured evidence.
- Never modify a check to turn a failing verdict green without explicit user approval that the
  check itself is wrong.
- Never put credentials or tokens in a URL, a command line, a log, or evidence.
- Never run GUI/browser-only acceptance remotely and present it as done.
