# AstroPonys

AstroPonys is a collection of small, independently usable Python tools for
evidence-oriented analysis of astronomical FITS data. A later UI may orchestrate
the tools; the command-line tools and analysis modules remain usable on their own.

The project prioritises reproducibility, traceability and preservation of recorded
data over presentation-oriented image processing.

## Planned MVP

The first vertical slice measures filter focus offsets from FITS headers, produces
an auditable report and creates a monochrome contact sheet. The broader MVP adds
FITS inventory, image-quality trends, motion analysis and reversible frame
selection. Automated calibration, stacking and mosaics follow later.

## Status

Planning and Sprint 1 foundation. See [TASKS.md](TASKS.md),
[requirements](docs/requirements/README.md), and [traceability](docs/traceability.md).

## Principles

- Source FITS files are read-only and analysed in place.
- One `astroponys.yaml` lives beside the session images.
- Generated artefacts live below `astroponys-output/<pony>/<run-id>/`.
- Measurements, inferences and presentation products are kept distinct.
- Statistical intervals are reported only when their assumptions are satisfied.
- A 0–100 confidence index communicates evidence strength, not probability of truth.

## Licence

MIT. See [LICENSE](LICENSE).
