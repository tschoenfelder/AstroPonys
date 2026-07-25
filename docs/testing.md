# Testing strategy

## Pyramid

Target distribution by meaningful behaviour tests: 65–75% unit, 15–25% component,
5–10% integration and no more than 5% acceptance/UI. Counts are reported, not gamed;
one parameterised test represents one behaviour family for ratio review.

## Implementation and UAT boundary

A behaviour is considered implemented only after it has a passing automated test at
the lowest appropriate level below UAT. Depending on scope, this is a unit, component
or integration test. UAT is not part of this minimum and cannot replace missing
lower-level verification.

UAT answers whether representative user workflows and acceptance criteria work for
their intended use. It is deliberately thin and must not re-test mathematical cases,
parser variants, failure modes, adapter contracts or integration branches already
verified below it. When UAT exposes a defect, first add a reproducing test at the
lowest appropriate automated level, then implement and re-run the narrow test before
repeating the affected UAT scenario.

## Fixtures

- Synthetic FITS are generated deterministically with known header/image truth.
- Public golden files are small, redistributable and documented.
- Private observations are referenced by `ASTROPONYS_PRIVATE_DATA`; they are never
  copied into build/output directories or committed.
- Numeric tests declare physical units, seed, tolerance and why the tolerance is valid.

## Scientific algorithm suites

- Focus: known offsets, zero/linear/nonlinear drift, missing cycles, duplicates,
  outliers, header aliases, insufficient samples and temperature correlation.
- PSF/collimation indicators: symmetric stars, defocus, directional elongation,
  spatial coma/tilt patterns and guiding-like common direction; no diagnosis assertion.
- Motion: known translations, rotations, steady drift, dither-like steps and failures.
- Quality selection: per-filter baselines, clouds, post-event changes, multi-night
  replacement, manual override and manifest-only rejection.
- Denoising (post-MVP only): known truth for flux, PSF, background, invented structure,
  signal recovery and residual/noise spectrum.

## Local and CI gates

Fast unit/component tests run on every change. Integration tests run before merge.
Private-data acceptance is opt-in. CI covers Windows and Linux Python 3.11–3.13;
ARM64 dependency compatibility is checked in Sprint 1 and native Raspberry Pi execution
is added when a runner is available.

Windows with Python 3.13 is the primary release gate. Compatibility jobs for other
supported Python versions and Linux supplement this gate. Dependency validation must
confirm that required packages install from precompiled Windows wheels; source builds
must not occur silently. Raspberry Pi/ARM64 is a secondary compatibility and resource
target and gains a native execution gate when a suitable runner is available.

Release evidence distinguishes check pass rate, requirement/test coverage, known
failures and confidence. Coverage percentage alone is never evidence of correctness.
