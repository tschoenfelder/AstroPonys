# Changelog

All notable changes will be documented here. The project follows Keep a Changelog
and intends to use semantic versioning after the first release.

## [Unreleased]

### Added

- Normalized stellar and donut focus-curve inputs to HFD (`2 x HFR`) while retaining
  the detected centre and source classification for every frame.

### Fixed

- Reject unmeasurable large-donut candidates instead of including incomplete geometry
  in sequence stabilization.
- Prefer a valid multi-star measurement over a large donut/nebulosity candidate in the
  same frame.
- Initial project constitution, requirements, ADRs, test strategy and roadmap.
- Detailed Sprint 1 plan for the focus-offset vertical slice.
- Windows/Python 3.13 primary-platform and precompiled-wheel dependency policy.
- Initial executable focus-offset vertical slice: YAML configuration, read-only FITS
  inventory, drift-aware analysis, reports, contact sheet, immutable manifest and CLI.
- Synthetic unit/component/integration tests and Windows/Python 3.13 CI gate.
- Definition of Done and UAT guardrails requiring lower-level automated tests for all
  implemented behaviour and prohibiting duplicated pyramid verification in UAT.
- Detailed Sprint 1 delivery plan with lower-level acceptance cases and deliberately
  thin UAT scenarios.
- Automated requirement-status traceability gate integrated into local and CI checks.
- Cycle/filter contact-sheet grid with explicit missing-frame placeholders and labelled
  per-frame stretch policy.
- Robust retained outlier-candidate reporting, strict nested configuration validation,
  FITS alias-conflict warnings and expanded CLI/inventory acceptance tests.
- Local-only private-data validation workflow with explicit prohibition on publishing
  private measurements or observation metadata by default.
- Corrected repeatability confidence so a single sample scores 0/20 instead of treating
  its necessarily zero dispersion as perfect repeatability.
- Fixed contact-sheet rendering for scaled unsigned-integer camera FITS using
  `BZERO`/`BSCALE`, covered by a realistic component regression test.
- Experimental standalone autofocus-curve domain algorithm with per-frame usability,
  hot-pixel rejection, stellar HFR and guarded quadratic optimum estimation.
- Large single-donut detection with sequence-stabilised centre, ring radius, radial
  ring-thickness FWHM and equivalent half-flux diameter.
