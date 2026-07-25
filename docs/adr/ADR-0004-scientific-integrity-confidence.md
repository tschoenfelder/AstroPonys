# ADR-0004: Scientific integrity and confidence model

- Status: Accepted
- Requirements: REQ-SCI-001..006

## Decision

Separate raw, calibrated-linear, integrated-scientific and presentation products.
Classify claims and distinguish statistical intervals from a 0–100 evidence confidence
index. Score confidence from method evidence (25), data quality (25), repeatability
(20), test coverage (15), model fit (10) and platform validation (5). Publish the
breakdown and rationale.

Use 100 only for deterministic/formally verified invariants. For software report
executed-check pass rate and requirement coverage instead of claiming universal
correctness. Presentation processing is derived, labelled and never overwrites its
scientific parent.

## Consequences

Reports may explicitly say an interval is not estimable. Confidence scores are
comparable only under the same rubric/version and are never probabilities of truth.
