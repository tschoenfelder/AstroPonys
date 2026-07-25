# ADR-0003: Drift-aware focus-offset baseline

- Status: Accepted
- Requirements: REQ-FOCUS-001..011

## Context

Sequential autofocus measurements mix filter-dependent focus position with temporal
drift. A single first or last Luminance reference would bias offsets.

## Decision

Use Luminance as zero reference and derive a local reference from bracketing Luminance
measurements, interpolating over time when assumptions are met. Preserve each raw delta,
missing cycle and exclusion. Estimate per-filter centre robustly; do not hardcode five
cycles or a fixed filter set.

## Consequences

Linear drift is reduced but rapid/nonlinear focus changes remain a limitation and must
lower confidence. Exact estimator and interval choices require method documentation and
synthetic validation during AP-004/AP-005.
