# Retained History Route Schema

`history-route.yaml` lives inside a retained merged Feature directory. It is provenance metadata, never canonical product authority.

```yaml
schema_version: "1.0"
status: retained-history
authority: non-authoritative
feature_id: I007-F02
canonical_targets:
  - implementation/backend/example.md
routes:
  - topic: deterministic revision identity
    question_terms:
      - why revision uses content hash
      - deterministic revision
      - content hash
    canonical_targets:
      - implementation/backend/example.md
    source_refs:
      - path: discussion/workbench.md
        headings:
          - Q-004
      - path: backend/revision-contract.md
        headings:
          - Revision identity
```

Rules:

- Keep `question_terms` semantic and human-readable; do not use only I/F IDs or filenames.
- Keep every `source_refs.path` relative to the retained Feature root and inside it.
- Route to narrow headings when possible.
- List canonical targets without inserting a reverse link into those canonical files.
- Preserve original source documents. Only after semantic merge, affected-MOC updates, and full long-term Wiki validator PASS, add `RETAINED_HISTORY.md` and this route during retained-history transformation.


A merged routing record stores the external entry point:

```yaml
id: I007-F02
phase: merged
state: completed
canonical_docs:
  - implementation/backend/example.md
merge_evidence:
  - integration-testing/evidence/example.md
retained_source:
  path: features/feat-i007-f02-example
  route: history-route.yaml

```

The record is outside canonical wiki authority. New I/F manifests must not reference the retained path.
