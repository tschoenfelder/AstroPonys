# AGENTS.md — AstroPonys project constitution

These rules apply to humans and coding agents throughout this repository.

## Mission and scope

Build independently runnable Python "one-trick ponies" for reproducible,
evidence-oriented FITS analysis. Preserve scientific meaning and raw data. A UI
may orchestrate tools later but must not contain the scientific core algorithms.

## Mandatory workflow

1. Identify or create requirement IDs before changing behaviour.
2. Record material design decisions in `docs/adr/`.
3. Add or update a task in `TASKS.md` and link requirements and planned tests.
4. Implement the smallest independently testable scientific or infrastructure unit.
5. Run the relevant local test pyramid levels, lint and type checks.
6. Update `docs/traceability.md`, user documentation and `CHANGELOG.md` when applicable.
7. Report checks actually run; never imply unexecuted checks passed.

Traceability is `requirement -> ADR (when needed) -> task -> code -> test -> release`.
Unknown requirement IDs and implemented requirements without tests are release blockers.

## Data safety and storage

- Treat all source FITS files and their containing raw directories as read-only.
- Never modify, rename, move or delete source files.
- Analyse sources at their original paths. Do not duplicate FITS files by default.
- Prefer path references and manifests, then symlinks/reflinks where supported.
- Do not use hard links. Physical copies require explicit user approval and a size estimate.
- Write only below the configured `astroponys-output` directory.
- Derived caches must be reproducible, versioned, bounded by a quota and removable.
- Destructive cleanup must resolve and validate the exact output path first.

## Configuration and outputs

- Use one session-level `astroponys.yaml` beside the image directory.
- Do not search the complete system for configuration.
- Each pony writes to `astroponys-output/<pony>/<run-id>/`.
- Every run produces a manifest containing inputs by path and identity, configuration,
  software version, parameters, timestamps, warnings and generated artefacts.
- Outputs are immutable per run. A rerun gets a new run ID.

## Scientific integrity

- Keep these product levels explicit: raw, calibrated-linear,
  integrated-scientific and presentation.
- Never overwrite a parent product. Record provenance between product levels.
- Presentation-only operations (including aesthetic saturation or mapped narrowband
  colour) must be labelled and must not be represented as measured colour.
- Do not use generative reconstruction, inpainting, star reduction or unvalidated
  AI denoising in scientific products.
- Noise reduction is disabled in the scientific branch until validated against
  known synthetic truth for flux bias, PSF change, false structure, background
  bias, signal recovery and residual/noise behaviour.
- Register analysis methods in `docs/methods/` with mathematics, assumptions,
  limits, primary evidence, validation and one status: Established,
  Project-validated, Experimental, Heuristic, Presentation-only or Rejected.
- Separate measurements from classifications, selection policy and presentation.
- Never present correlation as causation. Mount movement, focus, seeing, clouds,
  tilt and collimation indicators are competing explanations unless isolated.

## Uncertainty and confidence

Classify material conclusions as Measurement, Statistical result, Correlation,
Inference, Hypothesis or Recommendation.

- Report a statistical confidence/credible interval only when a defined statistical
  model and its assumptions justify one; otherwise state "not estimable".
- Report a 0–100 evidence confidence index with the method and reasons. It is an
  evidence-strength score, not the probability that a statement is true.
- Use the project rubric: method evidence 0–25, data quality 0–25, repeatability
  0–20, test coverage 0–15, model fit 0–10, platform validation 0–5.
- Reserve 100 for deterministic or formally checked invariants. Do not claim that
  non-trivial software is universally "100% correct".
- For software, separately report planned checks passed, requirement coverage,
  supported-platform test results, known failures and the evidence confidence index.

## Architecture

- Windows is the primary runtime and development platform; Python 3.13 is the
  current primary interpreter.
- Support Python 3.11+ on Windows, Linux and Raspberry Pi/ARM64, but do not chase
  the newest Python release at the expense of reliable binary dependencies.
- Prefer dependencies that publish maintained precompiled Windows wheels for the
  supported Python versions. Avoid requiring users to compile scientific libraries
  locally on Windows.
- Treat wheel availability, platform maintenance and installation reliability as
  dependency-selection criteria alongside scientific and technical suitability.
- Scientific algorithms are pure, deterministic modules where practical.
- CLI and future UI layers only validate inputs and orchestrate domain services.
- Adapters isolate FITS I/O, filesystem behaviour and future Ekos/KStars integration.
- Do not hardcode five focus cycles, filter names, FITS keyword variants or thresholds.
- Preserve forward-compatible session/night/target/panel identifiers for mosaics.

## Testing

Maintain a test pyramid, never an ice-cream cone:

- 65–75% unit tests for mathematics, policies and parsing.
- 15–25% component tests using deterministic synthetic FITS.
- 5–10% integration tests across filesystem/CLI boundaries.
- At most 5% acceptance/UI tests.

Use deterministic random seeds and documented numeric tolerances. Synthetic FITS
fixtures must encode known ground truth. Small redistributable golden fixtures may
be committed under `tests/fixtures/public-golden`; private observations belong in
gitignored `tests/private-data` and are optional via an environment variable.

Every behaviour test carries a valid requirement marker, for example
`@pytest.mark.requirement("REQ-FOCUS-003")`. Test focus, motion, PSF/collimation
indicators and selection policy independently before integration. The UI receives
only minimal orchestration and acceptance tests.

Before completion run, as relevant:

```text
pytest
ruff check .
ruff format --check .
mypy src
```

Run the complete release-relevant suite on Windows with Python 3.13. Additional
Python/platform jobs may qualify compatibility but do not replace this primary gate.

## Definition of Ready

A task is Ready only when its outcome, requirement IDs, acceptance criteria,
dependencies, data implications and test levels are specified.

## Definition of Done

A task is Done only when code and documentation are complete, local relevant tests
pass, traceability is updated, scientific limitations are reported, source-data
safety is preserved and no known critical defect remains.

## Changes prohibited without an ADR

- Breaking configuration or CLI changes.
- New physical data-copy behaviour.
- New scientific method, rejection metric or confidence formula.
- New database/catalogue technology.
- Moving scientific logic into a UI or external service.
- Changing product-level or provenance semantics.
