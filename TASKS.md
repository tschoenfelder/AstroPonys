# AstroPonys task list

This is the planning source of truth. States: Proposed, Planned for next release,
Ready, In progress, Blocked, In review, Done, Deferred, Cancelled. Priorities run
from P0 (required) to P3 (optional).

## Sprint 1 — focus-offset vertical slice (Planned for next release)

Sprint goal: install and run one standalone pony that inventories a focus-check
session, derives per-filter offsets from FITS header focus positions, and emits an
auditable report plus a seven-filter monochrome contact sheet without copying FITS.

The detailed execution order, automated acceptance cases and deliberately thin UAT
scenarios are maintained in `docs/sprints/sprint-1.md`.

### AP-001 Project and quality foundation — P0 — In progress

- Requirements: REQ-SAFETY-001..004, REQ-TEST-001..004, REQ-SCI-001..006
- Deliverables: packaging, CI matrix, requirement-marker validation, developer guide.
- Acceptance: the complete gate runs on Windows/Python 3.13; compatibility checks
  cover Python 3.11–3.13 on Windows/Linux as appropriate; every required scientific
  dependency has a maintained precompiled Windows wheel for the selected version;
  ARM64 compatibility and fallback constraints are documented; lint/type/unit gates
  are green.
- Tests: unit tests for traceability parser; CI smoke install and CLI invocation.

### AP-002 Session configuration contract — P0 — In progress

- Requirements: REQ-CFG-001..006
- Deliverables: versioned YAML schema, loader, clear diagnostics, example config.
- Acceptance: loads one `astroponys.yaml` by explicit path or image-directory
  adjacency; rejects unknown schema versions and unsafe output paths; no global search.
- Tests: unit matrix for defaults/errors; component test in temporary session tree.

### AP-003 FITS inventory and header normalisation — P0 — In progress

- Requirements: REQ-FITS-001..007, REQ-STORAGE-001..004
- Deliverables: read-only scanner; canonical records for path, identity, timestamp,
  filter, focuser position, exposure, camera, gain, offset, binning, temperature,
  target/session/night/panel; keyword alias configuration.
- Acceptance: corrupt/missing headers become explicit warnings; originals remain
  byte-identical; no FITS copy is created; inventory manifest is deterministic.
- Tests: parser unit tests; synthetic FITS component test; before/after hashes.

### AP-004 Focus-cycle pairing and baseline model — P0 — In progress

- Requirements: REQ-FOCUS-001..006, REQ-SCI-002..005
- Deliverables: configurable cycle detection; bracketing/interpolated Luminance
  baseline; per-filter delta records; exclusions with reasons.
- Acceptance: cycle count and filters are not hardcoded; temperature drift is
  separated from filter delta where data permits; incomplete cycles remain visible.
- Tests: synthetic series with zero/linear drift, missing frames, duplicates and
  outliers; exact expected offsets within declared tolerances.

### AP-005 Robust offset estimate and uncertainty report — P0 — In progress

- Requirements: REQ-FOCUS-007..011, REQ-SCI-003..006
- Deliverables: per-filter samples, robust centre, dispersion, justified interval
  when estimable, confidence breakdown, warnings and machine-readable JSON/CSV.
- Acceptance: Luminance is zero reference; raw samples remain inspectable; fewer or
  inconsistent samples reduce confidence; no unjustified confidence interval.
- Tests: deterministic estimator unit tests and property tests; golden report schema.

### AP-006 Monochrome contact sheet — P0 — In progress

- Requirements: REQ-CONTACT-001..006, REQ-SCI-001
- Deliverables: overview grouped by cycle/filter with common, documented stretch,
  labels, focus position, timestamp, warning badges and source-path linkage.
- Acceptance: arbitrary filter/cycle count; no colour implication; missing frames
  have placeholders; contact sheet and statistics share a run ID.
- Tests: component render against structural assertions plus small visual golden.

### AP-007 Standalone CLI and immutable run manifest — P0 — In progress

- Requirements: REQ-CLI-001..005, REQ-SAFETY-001..004
- Deliverables: `astroponys focus-offset analyse <session>`; output run directory;
  JSON manifest; documented exit codes.
- Acceptance: successful and partial-with-warning runs are distinguishable; reruns
  never overwrite; paths work on Windows/Linux; output can be deleted independently.
- Tests: integration tests for happy path, malformed FITS and existing run IDs.

### AP-008 Validate with NGC 7635 private session — P1 — In progress

- Requirements: REQ-FOCUS-010, REQ-TEST-004
- Input: user-provided private FITS via environment variable, never committed/copied.
- Acceptance: compare derived offsets with manual review; document discrepancies,
  method limits and confidence; convert only redistributable minimal cases to synthetic
  regression fixtures.
- Tests: optional local private-data acceptance test.
- Current evidence: a local read-only header compatibility check has begun; statistical
  validation remains open until sufficient repeated focus evidence is available.
  Private measurements, paths and observation metadata are never published by default.

### AP-009 Sprint 1 release evidence — P0 — Planned for next release

- Requirements: all Sprint 1 requirements
- Deliverables: traceability audit, platform test report, known-limitations report,
  example output, changelog and `v0.1.0` release checklist.
- Acceptance: 100% planned Sprint 1 checks passed, 100% implemented Sprint 1
  requirements linked to tests, zero known critical failures; confidence index reported.

### AP-010 Standalone autofocus-curve audit — P1 — In progress

- Requirements: REQ-AUTOFOCUS-001..007
- Deliverables: filter-independent per-frame usability classification, robust stellar
  HFR measurements, guarded optimal-focus fit and explicit no-result reasons.
- Acceptance: isolated defect pixels are rejected; synthetic stellar sweeps recover a
  known optimum; non-convex, weak and insufficient curves never produce an optimum.
- Tests: synthetic unit/component cases plus local-only real-sequence compatibility.
- Current evidence: core domain algorithm and hot-pixel/known-focus tests are complete;
  CLI/report integration and broader real stellar validation remain open.

## MVP follow-up — detailed epics, scheduling open

### AP-100 Frame quality metrics and trends — P0 — Proposed

Implement standalone PSF/star/background/transparency measurements, per-filter and
per-camera-mode baselines, rolling median/MAD trends and change-point candidates.
Show time degradation, clouds, focus drift and discontinuities after events without
claiming causation. Requirements: REQ-PSF-*, REQ-QUALITY-*.

### AP-110 Reversible frame-quality selection — P0 — Proposed

Separate metrics from policy. Support thresholds, best-N, best percentile and target
integration time per filter/night/panel. Persist accepted/review/rejected status,
reasons and manual overrides in manifests; never move or delete source frames.
Requirements: REQ-QUALITY-*, REQ-SAFETY-*.

### AP-120 Frame motion audit — P0 — Proposed

Measure translation and rotation relative to both previous frame and fixed reference;
report drift and dither/mount-correction candidates. Correlate motion with sharpness
but keep causality unresolved without guiding/mount logs. Requirements: REQ-MOTION-*.

### AP-130 PSF field map and optical-train indicators — P1 — Proposed

Compare centre/corners and field directionality to expose signatures compatible with
tilt, collimation error, coma, defocus, seeing and guiding. Results are indicators,
not definitive diagnoses. Standalone synthetic validation required. Requirements:
REQ-PSF-*, REQ-SCI-*.

### AP-140 Master-frame compatibility audit — P1 — Proposed

Inventory masters and match only scientifically compatible camera, temperature,
gain, offset, binning, exposure and filter metadata. Report missing/ambiguous masters;
do not calibrate in MVP. Requirements: REQ-MASTER-*.

### AP-150 Sensor-floor audit — P1 — Proposed

Measure clipping, pedestal/offset evidence and distribution summaries without treating
`min == 0` alone as proof of an incorrect acquisition offset. Requirements:
REQ-SENSOR-*, REQ-SCI-*.

### AP-160 Trail candidate review — P2 — Proposed

Flag satellite/aircraft/meteor/cosmic-ray candidates for review. Keep the method
experimental until synthetic and real validation quantifies false positives; never
auto-reject solely from this signal. Requirements: REQ-TRAIL-*.

### AP-170 Unified session report — P1 — Proposed

Combine contact sheets, time-series statistics, quality/motion events, provenance and
confidence-labelled conclusions under one run-linked overview. Requirements:
REQ-REPORT-*.

## Post-MVP roadmap — intentionally coarse

- AP-200 Ekos sequence builder and validated filter-offset export — P1 — Proposed.
- AP-210 Optional Ekos/KStars/guiding-log ingestion and event correlation — P1 — Proposed.
- AP-220 Siril calibration/registration/stack runner with master matching — P1 — Deferred.
- AP-230 Multi-night catalogue and rolling quality selection — P1 — Proposed.
- AP-240 Mosaic-ready panel planning, WCS validation and overlap reporting — P1 — Proposed.
- AP-250 Scientific mosaic registration, normalisation and integration — P2 — Deferred.
- AP-260 Presentation branch with explicitly labelled mapped colour/saturation — P2 — Deferred.
- AP-270 Local UI that only orchestrates stable pony APIs — P2 — Deferred.
- AP-280 Raspberry Pi packaging, resource profiling and bounded cache controls — P1 — Proposed.
- AP-290 Plugin architecture for additional metrics/exporters — P3 — Proposed.

## Release horizon

- v0.1.0: Sprint 1 focus-offset vertical slice.
- v0.2.x: MVP quality metrics, trends, motion and reversible selection.
- v0.3.x: optical-train/master/sensor/trail audits and unified reporting.
- v0.4.x: Ekos/log integration and multi-night catalogue.
- v0.5+: calibrated processing, mosaics and optional UI/presentation branch.
