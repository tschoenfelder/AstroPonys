# Requirements catalogue

Status values are Proposed, Accepted, Implemented, Verified and Retired. Sprint 1
requirements below are Accepted; later wildcard families in `TASKS.md` are placeholders
and must be expanded before their tasks become Ready.

## Configuration

- REQ-CFG-001: Use one versioned `astroponys.yaml` per session.
- REQ-CFG-002: Load it only by explicit path or adjacency to the selected image folder.
- REQ-CFG-003: Validate types, ranges and schema version before analysis.
- REQ-CFG-004: Support configurable FITS keyword aliases and filter names.
- REQ-CFG-005: Resolve paths cross-platform without storing platform-only separators.
- REQ-CFG-006: Reject output paths that could write into or above the source tree root.

## FITS inventory and storage

- REQ-FITS-001: Discover FITS/FIT/FITS.FZ inputs recursively only when configured.
- REQ-FITS-002: Open sources read-only and preserve bytes and metadata.
- REQ-FITS-003: Record canonical observation metadata with original header provenance.
- REQ-FITS-004: Represent missing, conflicting and malformed fields explicitly.
- REQ-FITS-005: Use stable file identity based on path, size, mtime and optional hash.
- REQ-FITS-006: Sort deterministically by observation time then stable path.
- REQ-FITS-007: Preserve session, night, target and optional mosaic panel identity.
- REQ-STORAGE-001: Do not copy source FITS by default.
- REQ-STORAGE-002: Reference inputs by original path in catalogues/manifests.
- REQ-STORAGE-003: Bound and version reproducible derived caches.
- REQ-STORAGE-004: Estimate size and require explicit approval before physical copies.

## Focus offset

- REQ-FOCUS-001: Read focuser position, filter and time from configurable FITS headers.
- REQ-FOCUS-002: Use Luminance as the zero-offset reference by default.
- REQ-FOCUS-003: Support any configured filter set and positive cycle count.
- REQ-FOCUS-004: Associate each filter sample with a bracketing or interpolated reference.
- REQ-FOCUS-005: Model temporal reference drift separately from filter deltas.
- REQ-FOCUS-006: Preserve incomplete cycles and exclusion reasons.
- REQ-FOCUS-007: Report every individual delta and robust per-filter centre/dispersion.
- REQ-FOCUS-008: Detect influential outliers without silently removing them.
- REQ-FOCUS-009: Report sample count and method/version with each estimate.
- REQ-FOCUS-010: Compare estimates with manual/private-session validation when available.
- REQ-FOCUS-011: Export machine-readable and human-readable results.

## Contact sheet and CLI

- REQ-CONTACT-001: Produce a monochrome overview organised by cycle and filter.
- REQ-CONTACT-002: Use a common documented stretch or clearly label per-panel stretching.
- REQ-CONTACT-003: Label filter, cycle, time and focuser position.
- REQ-CONTACT-004: Represent missing/unreadable frames visibly.
- REQ-CONTACT-005: Support arbitrary filter and cycle counts.
- REQ-CONTACT-006: Link the sheet and statistics through the same run ID.
- REQ-CLI-001: Expose focus analysis through an independently runnable CLI.
- REQ-CLI-002: Return documented success, warning and failure exit codes.
- REQ-CLI-003: Offer machine-readable output without parsing console prose.
- REQ-CLI-004: Operate without a UI or network connection.
- REQ-CLI-005: Behave consistently on supported Windows/Linux paths.

## Safety, testing and scientific integrity

- REQ-SAFETY-001: Write generated artefacts only below the configured output directory.
- REQ-SAFETY-002: Never overwrite an existing immutable run.
- REQ-SAFETY-003: Record input/configuration/software provenance in a run manifest.
- REQ-SAFETY-004: Make all source-data operations non-destructive.
- REQ-TEST-001: Link every behaviour test to a valid requirement ID.
- REQ-TEST-002: Enforce the test pyramid and deterministic fixture policy.
- REQ-TEST-003: Validate supported desktop platforms in CI.
- REQ-TEST-004: Allow opt-in private FITS tests without committing observations.
- REQ-PLATFORM-001: Use Windows with Python 3.13 as the primary execution and release gate.
- REQ-PLATFORM-002: Prefer stable supported Python versions over immediate adoption of
  a newer interpreter when scientific dependency support lags.
- REQ-PLATFORM-003: Required dependencies shall provide maintained precompiled Windows
  wheels for selected Python versions unless an ADR approves and supports an exception.
- REQ-PLATFORM-004: Keep Linux and Raspberry Pi/ARM64 as supported secondary targets.
- REQ-SCI-001: Label every output product level and preserve its parent provenance.
- REQ-SCI-002: Keep measurement separate from inference and recommendation.
- REQ-SCI-003: State method, assumptions, limits and evidence status.
- REQ-SCI-004: Report statistical intervals only when justified by a defined model.
- REQ-SCI-005: Report an evidence confidence index and component breakdown.
- REQ-SCI-006: Never describe the confidence index as probability of truth.
