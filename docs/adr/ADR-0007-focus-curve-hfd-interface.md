# ADR-0007: HFD interface for focus-curve measurements

- Status: Accepted
- Date: 2026-07-26
- Requirements: REQ-AUTOFOCUS-004, REQ-AUTOFOCUS-005, REQ-AUTOFOCUS-008
- Task: AP-010

## Context

Normal stellar profiles were passed to the curve fit as median HFR, while a large
defocused donut also exposed an equivalent HFD. A curve service should consume one
unambiguous size convention regardless of source morphology.

## Decision

Each accepted frame exposes `focus_metric_hfd_px`. For a normal stellar field this is
twice the median measured HFR. For a detected single donut it is the equivalent HFD
derived from the positive radial signal around the sequence-stabilised measured centre.
The curve fit consumes only this diameter metric. Detection coordinates are measured,
not configured as camera constants.

## Consequences

The ordinate and polynomial coefficients are scaled by two relative to an HFR fit.
The vertex and R-squared are invariant under this positive scaling. Donut HFD remains
an experimental equivalent-size measurement and is not a Gaussian FWHM.
