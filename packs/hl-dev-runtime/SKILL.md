---
name: hl-dev-runtime
description: "Opt-in pack for local dev services: declares services in config, reuses a healthy equivalent listener before restarting, stops only confirmed PIDs, restarts through the configured start command, verifies health and reports PIDs and URLs. Enable with packs.enabled: [dev-runtime]; no service or port is hardcoded."
---

# Dev Runtime (pack)

## Pack status

This directory is an **optional pack**, not a core skill. Core workflow must run with
`packs.enabled: []`; no core skill may require a running service or this pack.

- Enable: install or link `<factory>/packs/dev-runtime/` into the agent skill root, then add
  the id and the service list to the work repo config:

  ```yaml
  packs:
    enabled: [dev-runtime]
    dev-runtime:
      services:
        - name: <service-id>
          cwd: <path-relative-to-work-root>
          start: [<argv>, <argv>]
          stop: [<argv>, <argv>]          # optional
          health: <loopback-http-path>
          port: <configured-port>
  ```

  Then run `factory upgrade --work <work>` and `factory doctor --work <work>`.
- Disable: remove `dev-runtime` from `packs.enabled`; the core workflow must still work.
- Services and ports are **data**. If this pack is not enabled, do not start, stop or probe
  services by hand under its rules.

## When to use

Use this pack when the user asks to start, stop, restart or reload local dev services, when a
change must be exercised against the running app, or when the question is which process is
serving a configured port. It does the shortest clean restart first and reports evidence; it is
not a debugging framework.

Do not use it for broad diagnosis, for production or shared environments, or when the config
declares no services. If a restart plus its health checks fails, stop and report — do not turn
the request into an open-ended investigation.

## Step 0 — mandatory preamble

1. Read `<work>/.factory/local.yaml` and resolve `factory_root` and `python`.
   If missing or unreadable, stop: "machine config missing — run `factory init`
   (or `$hl-factory-init`) for this work repo, then retry."
2. Read `<work>/wiki/governance/workflow-profile.md`.
   If missing, stop: "workflow profile missing — run `factory upgrade --apply --work <work>`,
   then `$hl-factory-doctor`; do not hand-write the profile."
3. Confirm `packs.enabled` contains `dev-runtime`. If not, stop with the enable snippet and
   the two commands above.
4. Read `<work>/.factory/factory.yaml` and resolve every key in `packs.dev-runtime` (the workflow
   profile only lists enabled packs, not their configuration). Missing, empty or malformed config
   stops the pack; never fall back to an assumed service name or port.
5. Run `factory doctor --work <work>`. A failing doctor stops the pack.

## Config contract

`packs.dev-runtime.services` — required, non-empty list of mappings:

| Field | Required | Meaning |
| --- | --- | --- |
| `name` | yes | stable ASCII id, unique within the list |
| `cwd` | yes | service working directory, relative to the work repo root |
| `start` | yes | argv list that launches the service in the foreground of its own process |
| `stop` | no | argv list for graceful stop; omit when terminating the PID is the stop |
| `health` | yes | loopback HTTP path used to prove the service is serving |
| `port` | yes | TCP port the service must listen on |
| `ready_seconds` | no | how long to wait for listener plus health before declaring failure |
| `stop_grace_seconds` | no | graceful window before force-terminate |

`start`/`stop` are argv lists, not shell strings: the pack must not compose a shell command
line, and must not rewrite a configured argument. `cwd` must stay inside the work repo; an
absolute path or `..` segment stops the pack (machine paths belong in `.factory/local.yaml`,
not in a service definition).

Empty-config behaviour (fail closed): if `packs.dev-runtime.services` is absent, not a list,
or empty, stop and print:

```text
dev-runtime pack cannot run: packs.dev-runtime.services is missing or empty.
Enable packs.enabled: [dev-runtime] and declare at least one service with
name, cwd, start, health and port, then run factory doctor --work <work>.
```

A service entry missing any required field stops the whole pack — a partially usable service
list is not usable. Never invent a port, a start command, or a working directory.

Resolve and print the plan before touching anything:

```text
service=<name> cwd=<relative-path> port=<port> url=<loopback-url>
```

## Step-by-step flow

### 1. Inspect before acting

For each declared service:

1. List TCP listeners for the declared `port` only, using the OS listener query
   (`Get-NetTCPConnection` on Windows; `ss`/`lsof` on POSIX). If process querying is denied,
   fall back to the plain listener/connection table, then to netstat output.
2. If a listener exists, resolve its owning PID and inspect that PID's command line and
   working directory.
3. Classify the listener: **same service** (command line and cwd match the declared `start`)
   versus **foreign** (anything else). Command line is the deciding evidence; a bind address
   or executable path alone is not.

### 2. Reuse before restart

Probe the declared health path on the loopback address for the declared port, bypassing any
configured HTTP proxy (a proxy error page is not a dead service; connection refused is).

- Listener is the same service and health passes → **reuse it**. Report its PID and URL and
  skip stop/start. A healthy equivalent instance is success, not a conflict.
- Listener is foreign → do not touch it. Report the conflicting PID, command line and URL, and
  ask the user how to proceed (another port or a stop authorization).
- Listener is the same service but unhealthy, stale, or started before the change being
  loaded → continue to restart.

### 3. Stop only confirmed PIDs

1. Run the configured `stop` argv if present, in the service `cwd`.
2. Terminate the confirmed PID tree — graceful first, force after `stop_grace_seconds`.
   Kill by PID, never by broad name or process group, and never a pattern that can match the
   invoking shell itself.
3. Re-check the port. A killed process does not imply a released port; an orphan child can
   hold it. Only the listener check proves release.

### 4. Start

1. Launch the configured `start` argv in `cwd`, detached from this session's terminal and
   hidden from the interactive desktop where the OS supports it. Record the launched PID.
2. Do not add output redirection to a Windows hidden launch (it can fail on this host); read
   output from the process/log channel the service already provides, or capture it in a
   wrapper script placed in the work repo.
3. If the launch returns but no listener appears within `ready_seconds`, do not retry the same
   launch in a loop. If the host sandbox reaped the background process, request escalation for
   that exact launch once; otherwise report the failure with the captured exit state.
4. Never use an auto-reload/dev-watch mode to prove freshly changed code. The restart itself
   must load the new code.

### 5. Verify

1. Wait for the declared port to be listened on, polling until `ready_seconds` expires.
2. Probe the declared health path over loopback with the proxy bypassed. Record status code
   and a short body fingerprint.
3. If the service exposes an API base URL to a client, verify that client configuration points
   at the same host and port; report a mismatch before testing through it.
4. Only listener plus health together count as "running". Started is not healthy.

### 6. Report

Per service: `name`, action (`reused` / `restarted` / `started`), PID, port, URL, health
result. Add: listeners observed and deliberately left alone, any port that ended up different
from the declared one, and any follow-up the user must authorize. Match the user's language.

## Failure handling

| Situation | Action |
| --- | --- |
| Config empty or a required field missing | fail closed with the message above; start nothing |
| Listener owned by a foreign process | do not kill; report PID + command line; ask for a port/authorization decision |
| Process query denied | fall back to listener table, then netstat; report the reduced evidence |
| Launch returns but no listener | capture exit state, escalate once if sandboxed, else report failure |
| Health fails or times out | report unhealthy with the probe result; at most one further restart backed by new evidence |
| Health returns a proxy-generated error | bypass the proxy and re-probe; do not conclude the service is down |
| Another agent session holds an equivalent healthy instance | coexist, report it, do not reclaim the port |
| Port in use after stop | inspect for orphan children, stop by PID, re-verify |

## What this pack must never do

- Never hardcode a service, a port, a health path, or a start command.
- Never kill unrelated processes, broad process groups, or a process matched only by name.
- Never stop a healthy equivalent instance just to run its own copy.
- Never report success from a launched PID alone; require listener plus health.
- Never edit source or configuration while doing a restart unless the user asks for a fix.
- Never leave the runtime in a state the config does not describe (extra services, changed
  ports) without reporting it.
- Never retry a failing launch repeatedly without new evidence.
