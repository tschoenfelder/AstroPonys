# ADR-0002: Zero-copy source safety

- Status: Accepted
- Requirements: REQ-FITS-002, REQ-STORAGE-001..004, REQ-SAFETY-001..004

## Decision

Analyse original FITS paths read-only and store references in manifests. Do not copy,
move, rename, delete or overwrite source data. Prefer manifests, then supported symbolic
or copy-on-write references. Forbid hard links. Require explicit approval and a size
estimate for physical copies.

## Consequences

Large observations are not multiplied. Runs depend on original paths remaining
available; manifests therefore record identity evidence and report missing/changed files.
