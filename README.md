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

Sprint 1 implementation in progress. The first executable vertical slice and its
synthetic test pyramid are present; real-session validation and requirement completion
remain open. See [TASKS.md](TASKS.md),
[requirements](docs/requirements/README.md), and [traceability](docs/traceability.md).

## Development installation

On the primary Windows/Python 3.13 platform:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --only-binary=:all: ".[dev]"
```

Dependencies are defined only in `pyproject.toml`. The binary-only installation is an
intentional check that every required library has a precompiled Windows wheel.

## Focus-offset pony

Place an `astroponys.yaml` beside the FITS files (see `examples/astroponys.yaml`) and run:

```powershell
astroponys focus-offset analyse E:\path\to\focuscheck
```

Outputs are created below
`astroponys-output/focus-offset/<run-id>/`: `manifest.json`, `report.md`, `offsets.csv`
and a monochrome `contact-sheet.png`. Exit code 0 means success, 2 means a completed
run with warnings, and 1 means failure.

## Principles

- Source FITS files are read-only and analysed in place.
- One `astroponys.yaml` lives beside the session images.
- Generated artefacts live below `astroponys-output/<pony>/<run-id>/`.
- Measurements, inferences and presentation products are kept distinct.
- Statistical intervals are reported only when their assumptions are satisfied.
- A 0–100 confidence index communicates evidence strength, not probability of truth.

## Licence

MIT. See [LICENSE](LICENSE).
