# Sprint 1 — Focus-offset vertical slice

- Sprint objective: Deliver one trustworthy standalone pony that derives filter focus
  offsets from a focus-check FITS session and produces an auditable visual and numeric
  result without changing or copying source frames.
- Target release: v0.1.0
- Status: In progress
- Primary platform: Windows, Python 3.13
- Secondary platforms: Windows/Linux, Python 3.11–3.13
- Scientific method status: Experimental until AP-008 real-session validation finishes

## Outcome

A user points the CLI at a directory containing `astroponys.yaml` and focus-check FITS
frames. AstroPonys reads the sources in place, derives drift-aware offsets relative to
Luminance, and creates one immutable run containing:

- `manifest.json` with input identity, provenance, warnings and complete measurements;
- `report.md` with samples, robust estimates, uncertainty and confidence rationale;
- `offsets.csv` for reuse;
- `contact-sheet.png` as a monochrome filter/cycle overview.

The sprint does not calibrate, register, stack, reject science frames, diagnose
collimation or write filter offsets into Ekos.

## Delivery sequence

### S1.1 — Quality and traceability gate

- Tasks: AP-001, AP-009
- Requirements: REQ-TEST-001..008, REQ-PLATFORM-001..004
- Work:
  - validate all pytest behaviour tests have known requirement markers;
  - maintain explicit requirement implementation status;
  - reject `Implemented`/`Verified` status without a lower-level test;
  - execute Windows/Python 3.13 binary-wheel gate plus compatibility matrix;
  - generate release evidence with checks, coverage, failures and confidence.
- Done when: the gate is automated locally and in CI, and Sprint 1 has no untested
  requirement labelled Implemented or Verified.

### S1.2 — Session configuration

- Task: AP-002
- Requirements: REQ-CFG-001..006
- Work:
  - load only explicit or adjacent `astroponys.yaml` schema version 1;
  - validate all supported keys, values, path boundaries, aliases and filter order;
  - supply Windows-oriented example and actionable diagnostics.
- Done when: positive and negative configuration matrices pass at unit/component level.

### S1.3 — Read-only FITS inventory

- Task: AP-003
- Requirements: REQ-FITS-001..007, REQ-STORAGE-001..004
- Work:
  - deterministic configured discovery including `.fit`, `.fits` and `.fits.fz`;
  - canonical header records with original keyword provenance;
  - explicit missing/conflicting/corrupt-header warnings;
  - before/after identity checks proving no source mutation or copy.
- Done when: synthetic component cases pass and source bytes remain identical.

### S1.4 — Focus baseline and cycles

- Task: AP-004
- Requirements: REQ-FOCUS-001..006
- Work:
  - infer arbitrary filter cycles without a fixed count;
  - associate samples with preceding/following Luminance references;
  - interpolate slow reference drift and retain nearest-only edge samples with warnings;
  - make incomplete cycles and exclusions visible.
- Done when: known zero/linear drift, arbitrary cycles, missing brackets and malformed
  sample cases reproduce expected results within declared tolerances.

### S1.5 — Estimate, uncertainty and confidence

- Task: AP-005
- Requirements: REQ-FOCUS-007..011, REQ-SCI-002..006
- Work:
  - preserve individual offsets;
  - compute robust centre and dispersion;
  - identify influential outliers without silent rejection;
  - emit a statistical interval only under documented assumptions;
  - publish confidence components and method/version.
- Done when: estimators, outlier policy, insufficient-data handling and report schemas
  pass unit/property/golden tests.

### S1.6 — Contact sheet

- Task: AP-006
- Requirements: REQ-CONTACT-001..006, REQ-SCI-001
- Work:
  - organise monochrome frames by cycle and configured filter order;
  - use one documented stretch policy;
  - label cycle/filter/time/focus and visibly represent missing/unreadable frames;
  - link visual and statistics by run ID.
- Done when: structural image assertions and a small reviewed visual golden pass.

### S1.7 — CLI, manifests and failure behaviour

- Task: AP-007
- Requirements: REQ-CLI-001..005, REQ-SAFETY-001..004
- Work:
  - complete the standalone CLI and documented exit codes 0/1/2;
  - generate immutable, atomic outputs beneath the configured output root;
  - support machine-readable console output;
  - preserve partial diagnostics without presenting a failed run as successful.
- Done when: Windows/Linux integration cases pass for success, warning, failure and rerun.

### S1.8 — Private NGC 7635 validation

- Task: AP-008
- Requirements: REQ-FOCUS-010, REQ-TEST-004
- Work:
  - reference the external focus-check directory without copying FITS;
  - compare program estimates and contact sheet against manual measurements;
  - investigate discrepancies and turn only generic cases into synthetic fixtures;
  - revise method status/confidence and document real-data limitations.
- Done when: a private validation report records comparison, deviations, explanations,
  warnings and evidence confidence without committing private observations.

## Automated acceptance cases below UAT

These cases establish implementation status. They are assigned to the lowest suitable
automated test level and are not repeated in UAT.

| ID | Level | Given / When / Then | Requirements |
|---|---|---|---|
| AT-S1-001 | Unit | Given schema v1, when loaded, then canonical paths/defaults are returned. | REQ-CFG-001..005 |
| AT-S1-002 | Unit | Given unsafe/unknown config, when loaded, then analysis stops with a precise error. | REQ-CFG-003, REQ-CFG-006 |
| AT-S1-003 | Component | Given deterministic FITS aliases, when inventoried, then canonical values and source keywords match. | REQ-FITS-001..006 |
| AT-S1-004 | Component | Given source FITS, when inventoried/analyzed, then byte hash, size and mtime remain unchanged and no FITS copy exists. | REQ-FITS-002, REQ-STORAGE-001, REQ-SAFETY-004 |
| AT-S1-005 | Unit | Given five cycles with known linear drift and offsets, when analyzed, then drift is removed and offsets match truth. | REQ-FOCUS-003..005 |
| AT-S1-006 | Unit | Given incomplete/edge cycles, when analyzed, then samples remain visible with method and warnings. | REQ-FOCUS-006..009 |
| AT-S1-007 | Unit | Given stable, noisy and outlier samples, when estimated, then median/MAD/outlier flags and interval rules match specification. | REQ-FOCUS-007..009, REQ-SCI-004 |
| AT-S1-008 | Component | Given arbitrary filters/cycles and a missing frame, when rendered, then the monochrome grid retains configured positions and labels. | REQ-CONTACT-001..005 |
| AT-S1-009 | Integration | Given a valid session, when CLI runs, then one complete immutable run and exit 0 are produced. | REQ-CLI-001..005, REQ-SAFETY-001..003 |
| AT-S1-010 | Integration | Given usable data with limitations, when CLI runs, then outputs remain inspectable and exit 2 signals warnings. | REQ-CLI-002, REQ-FITS-004 |
| AT-S1-011 | Integration | Given a fatal/unsafe session, when CLI runs, then exit 1 is returned and no successful manifest is emitted. | REQ-CLI-002, REQ-SAFETY-001 |
| AT-S1-012 | Meta-test | Given project traceability, when audited, then unknown markers and implemented requirements without lower-level tests fail. | REQ-TEST-001, REQ-TEST-005..008 |

## UAT scenarios

UAT is intentionally small and does not re-check formulas, header permutations,
filesystem edge cases or source immutability already covered below.

### UAT-S1-001 — First successful focus-check report

- Given: a representative complete focus-check session and adjacent reviewed YAML.
- When: the user runs the documented command on Windows/Python 3.13.
- Then: the command is understandable; the user can locate the four outputs; the
  contact sheet gives a useful all-filter overview; the report clearly communicates
  suggested offsets, uncertainty, confidence and limitations.
- Pass evidence: signed checklist, run ID and user comment; no duplicated numeric tests.

### UAT-S1-002 — Limited session is not misleading

- Given: a representative session with incomplete cycles or non-bracketed frames.
- When: the user runs the same command.
- Then: the user notices warning status, can identify affected samples, and is not led
  to interpret confidence as probability or a limited estimate as definitive.
- Pass evidence: signed checklist and run ID; technical warning branches remain covered
  by automated tests below UAT.

## Sprint exit criteria

- AP-001..AP-009 are Done under `AGENTS.md`; AP-008 may not be waived for v0.1.0.
- Every Implemented/Verified Sprint 1 requirement has a passing lower-level test.
- All AT-S1 cases pass; both UAT cases are accepted by the user.
- Windows/Python 3.13 installs required dependencies from wheels and passes the full gate.
- Supported compatibility jobs pass; known exceptions are documented.
- Source FITS are neither changed nor copied.
- Release evidence reports check pass rate, requirement coverage, known failures,
  method status and confidence index without claiming universal correctness.

## Current implementation snapshot

- Present: executable configuration, inventory, baseline estimator, report, cycle-aware
  contact sheet, immutable manifest, CLI, traceability gate, outlier-candidate policy,
  warning/failure paths, 23 lower-level tests and platform CI.
- Private validation: a local read-only compatibility check has started, but the
  repeated autofocus evidence required to complete AP-008 is not yet available. Private
  measurements and paths are not published in this repository.
- Next: remaining configuration/FITS edge cases, explicit cycle records and exclusions,
  visual golden review, release evidence and sufficient repeated private focus evidence.
