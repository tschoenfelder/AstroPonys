# METHOD-AUTOFOCUS-001: Stellar HFR focus curve

- Version: 0.2
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
normal multi-star frame. Stellar apertures are measured as HFR and normalized to the
diameter metric `HFD = 2 x HFR` at the focus-curve service boundary.

A second path detects one large, low-surface-brightness defocused donut after 4× block
averaging and difference-of-Gaussians filtering. Large connected components are
measured using a sequence-stabilised centre and azimuthal radial profile. Reports expose
the ring-peak radius, radial ring-thickness FWHM and equivalent half-flux diameter
(`HFD = 2 x HFR`). The detected donut is represented to the curve service as one star
at its measured centre with this HFD value. One measurable donut is sufficient to make
a frame usable, but not to make an entire curve acceptable.

## Curve acceptance

At least five usable frames at five distinct positions are required. A quadratic is
fitted to per-frame HFD versus focus position. Multiplication by two changes the metric
scale but not the fitted vertex or R-squared value. An optimum is reported only if:

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
  defects and detection of a late large-donut subsequence; a redistributable real
  stellar sweep is not yet available.
