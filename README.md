# AstroPonys

AstroPonys is a collection of small, independently usable Python tools for
evidence-oriented analysis of astronomical FITS data. Raw FITS QA runs either
standalone or from the AstroProcess web portal.

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

## Raw FITS QA quick start

Raw FITS QA is the first, read-only step after acquisition. It produces an
interactive FWHM versus peak ADU report and native-grid 1:1 previews without
copying, moving or modifying the original FITS files.

You need Git and Python 3.11 or newer with `venv` support. On Windows, the
setup script uses the `py` launcher. Run the commands from the indicated
checkout directory. Each setup creates or reuses a separate virtual environment.
If testing an unmerged pull request, switch to its branch before running setup.

### Install on Windows (PowerShell)

From a folder where you keep your tools:

```powershell
git clone https://github.com/tschoenfelder/AstroPonys.git
cd AstroPonys
.\tools\raw-fits-qa\setup.cmd
```

### Install on Linux

```sh
git clone https://github.com/tschoenfelder/AstroPonys.git
cd AstroPonys
sh tools/raw-fits-qa/setup.sh
```

### Run in the AstroProcess web portal

1. Set up [AstroProcess](https://github.com/tschoenfelder/AstroProcess) in its own checkout.
   If it is already set up, skip this step. On Windows, run `.\setup.cmd` in
   the AstroProcess checkout. On Linux, run the following there:

   ```sh
   python3 -m venv .venv
   .venv/bin/python -m pip install -r requirements.txt
   .venv/bin/python -m astroprocess init-config
   ```

2. Add your FITS directory as a dataset in `~/.astroprocess/web/config.toml`
   (`%USERPROFILE%\.astroprocess\web\config.toml` on Windows). Use an unused
   dataset ID, and use forward slashes in Windows TOML paths.

   ```toml
   [datasets.raw_night]
   name = "Raw FITS night"
   path = "/data/astro/raw-night"  # Windows example: "E:/Astro/Raw Night"
   ```

3. Register QA from the **AstroPonys** checkout:

   Windows:

   ```powershell
   .\tools\raw-fits-qa\.venv\Scripts\python.exe .\tools\raw-fits-qa\integrate_flask.py
   ```

   Linux:

   ```sh
   tools/raw-fits-qa/.venv/bin/python tools/raw-fits-qa/integrate_flask.py
   ```

   If you use a non-default portal config, pass `--config PATH` to the
   installer and use the same config when starting AstroProcess.

4. Start or restart the portal from the **AstroProcess** checkout. On Windows
   run `.\launch.cmd`. On Linux run `.venv/bin/python -m astroprocess serve`.
   Open <http://127.0.0.1:5050> (or your configured port), select your dataset,
   then open **Tools → Raw FITS QA**. Start the job and open its report when it
   finishes.

### Run standalone (no Flask)

From the AstroPonys checkout, point the worker at your raw FITS directory and
choose an output directory **outside** it.

Windows:

```powershell
.\tools\raw-fits-qa\run.cmd "E:\Astro\Raw Night" --output-root "E:\Astro\astroponys-output"
```

Linux:

```sh
tools/raw-fits-qa/.venv/bin/python -m astroponys.raw_qa_worker \
  "/data/astro/raw-night" --output-root "$HOME/astroponys-output"
```

Open the `report.html` path printed by the worker. Keep its `frames/` directory
beside it if you move the report. See the [tool guide](tools/raw-fits-qa/README.md)
for optional clipping settings and report interpretation.

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
