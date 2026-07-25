# METHOD-FOCUS-001: Drift-aware filter-offset estimate

- Version: 0.1
- Status: Experimental
- Claim type: Statistical result
- Requirements: REQ-FOCUS-004..010, REQ-SCI-002..006

## Purpose

Estimate the focuser-position difference between each filter and a configured reference
filter while reducing bias from slow temporal focus drift.

## Definition

For a sample at time `t` bracketed by reference measurements `(t0, f0)` and `(t1, f1)`,
the reference baseline is linear interpolation:

`b(t) = f0 + (t - t0) / (t1 - t0) * (f1 - f0)`

The sample offset is `filter_focus(t) - b(t)`. The per-filter estimate is the median;
dispersion is the median absolute deviation (MAD). For at least five samples, an
exploratory 95% percentile bootstrap interval of the median is produced using 10,000
resamples and a fixed seed. Otherwise the interval is reported as not estimable.

With at least five samples, influential outlier candidates are flagged using an
absolute deviation greater than 3.5 times the scaled MAD (`1.4826 × MAD`). If MAD is
zero, non-median samples are flagged. Candidates remain in the sample list and in the
bootstrap population; the pony never silently rejects them.

## Assumptions and limits

- Reference drift is approximately linear between bracketing measurements.
- Autofocus positions measure the same optical state apart from filter and temporal drift.
- Samples are sufficiently representative; close temporal dependence limits bootstrap
  interpretation.
- A nearest-only edge baseline does not correct drift and reduces confidence.
- The outlier rule is a review aid, not proof that a measurement is invalid. Its
  behaviour for zero MAD is intentionally sensitive and must be interpreted with the
  focuser step size and autofocus repeatability.
- Temperature, backlash, direction of approach, seeing and optical movement can remain
  confounders. The result is not by itself proof of a physical filter property.

## Validation status

Synthetic tests cover constant and linear drift, arbitrary cycle counts, missing
brackets and insufficient samples. Validation on private real observations is planned
under AP-008. Until then the method remains Experimental.
