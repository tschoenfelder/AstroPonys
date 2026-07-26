# METHOD-AUTOFOCUS-001: Stellar HFR focus curve

- Version: 0.1
- Status: Experimental
- Claim types: Measurement, Classification and Statistical result
- Requirements: REQ-AUTOFOCUS-001..007

## Purpose

Classify frames in one autofocus sweep as usable or unusable and estimate an optimal
focuser position only when enough frames contain measurable stellar profiles and form
a plausible convex focus curve. The filter is not required for a single sweep.

## Frame measurement

The algorithm reads `FOCUSPOS`, estimates background and noise robustly, locates local
peaks above eight noise sigmas and measures spatial extent in a local aperture. A peak
must occupy at least four significant pixels in its central 5×5 footprint; isolated
hot/defect pixels are rejected. At least eight extended sources are required for a
usable frame. The frame metric is median stellar half-flux radius (HFR) in pixels.

## Curve acceptance

At least five usable frames at five distinct positions are required. A quadratic is
fitted to median HFR versus focus position. An optimum is reported only if:

- the quadratic is convex;
- its vertex lies inside the measured position range; and
- coefficient of determination is at least 0.60.

Otherwise the result contains explicit reasons and no optimal focus.

## Limitations

- Quadratic HFR behaviour is an approximation near focus and should not be extrapolated.
- Seeing changes, tracking, saturation, undersampling and field-dependent aberrations
  can bias HFR.
- Detected extended features are not guaranteed to be stars in every scene.
- The current fit is unweighted and has no statistically validated confidence interval.
- Real-data validation currently demonstrates rejection of frames dominated by sensor
  defects; a redistributable real stellar sweep is not yet available.
