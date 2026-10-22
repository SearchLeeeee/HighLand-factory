# Adopt example: an existing two-repo project

> **Adopt is optional.** HighLand-factory is a reference implementation of the workflow; you do
> not need to modify any existing repository to use it. Adopt is only for when you deliberately
> want to attach the workflow to a repo you own. The v0.1 verification for this example was run
> against a **temporary copy** of a project, never a real repository.

This directory shows the answers file used to attach HighLand-factory to an existing
project that already has a code repository and a documentation repository, using
`repo.mode: split`.

Command (the docs repo becomes the work repo):

```bash
factory adopt \
  --work  <docs-repo> \
  --code  <code-repo> \
  --wiki  <existing-wiki-folder> \
  --answers examples/adopt-existing-project/answers.yaml
```

Notes:

- Freeze the pre-adopt state first: `git -C <docs-repo> tag pre-adopt-<date>`.
- Pass `--wiki` explicitly when the wiki root is not `wiki/` or `docs/`; adopt only
  auto-detects those two names.
- Existing authoritative documents are never rewritten; adopt adds `.factory/`, the
  workflow digest, missing skeleton files and owner profiles, and reports skipped paths.
- After adopt, run `factory doctor --work <docs-repo>` and fix failures before any
  implementation. The wiki gate may fail on pre-existing links; fix them in a separate
  commit so the adopt commit stays mechanical.

The answers file next to this README is a generic starting point. Replace paths,
commands, owners and security boundaries with your project's real values.
