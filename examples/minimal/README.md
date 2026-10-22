# Minimal example

A greenfield project takes one command after the factory is installed:

```bash
mkdir my-project && cd my-project
factory init --work .
factory doctor --work .
```

With no answers file, init derives the project name from the directory, uses a single
`core` owner, empty commands and conservative defaults. The result is a valid skeleton,
but `factory doctor` will warn about the empty test/verify commands and the pending
baseline until you fill them in.

For a guided setup, give your agent `prompts/quickstart.md` from the factory checkout and
let it walk you through install and init one decision at a time; once the factory skills
are installed, `$hl-factory-init` runs the same conversation from inside the work repo.
