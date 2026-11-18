# METHOD-RAWQA-001 — Native-grid stellar QA

Status: Heuristic. The elliptical Gaussian is a descriptive profile model, not
a statement that the optical PSF is Gaussian.

Detect peaks in difference-of-Gaussian filtered copies at two spatial scales.
Photometry and fitting use the original FITS samples after FITS storage scaling.
Rank candidate stars by background-subtracted aperture flux. A fitted Gaussian with
a local background plane gives FWHM along the principal axes as
`2 sqrt(2 ln 2) × sigma`; the plotted scalar is their geometric mean.
Exclude low-SNR, too narrow, edge, unresolved, or suspect clipped cores. Probe for
clipping separately with a configured ADU ceiling and adjacent signal consistent
with a spatial source. Without a verified ceiling, a connected upper plateau is
only a candidate, and the confirmed count is unknown. The detection is not a
complete source catalogue and overlapping saturated sources may not be separable.

Angular conversion uses the first valid scale pair, preferring CDELT with a
celestial WCS (or its CD matrix), then SECPIX, SCALE, or binned pixel size and focal
length. Anisotropic scales are flagged and only pixel widths are published until an
anisotropic PSF transform is supported. CFA mosaics are not measured in this version.

Evidence: Gaussian width follows directly from the Gaussian half-maximum.
Validate on a seeded synthetic FITS with a known elliptical PSF and on the locally
available autofocus example (not committed). Scores in the manifest use the
project evidence rubric and are not probabilities or seeing estimates. No
statistical interval or automatic sorting/classification is inferred.
