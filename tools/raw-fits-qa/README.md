# Raw FITS QA

The worker scans the selected dataset in place. It measures up to five usable
unclipped stars on each mono Light and reports exposure, binning, gain mode,
camera, header provenance, clipping status and FWHM. Calibration frames are
listed but not measured. A CFA mosaic is reported as unsupported for stellar
fits, with a native-grid preview. No original FITS is modified or copied.

## Setup and standalone use

Use Python 3.11 or newer. Windows quick start from the AstroPonys checkout:

```powershell
.\tools\raw-fits-qa\setup.cmd
.\tools\raw-fits-qa\run.cmd "E:\Astro\Raw Night" --output-root "E:\Astro\astroponys-output"
```

Use an absolute launcher path from any other working directory. On Linux run
`sh tools/raw-fits-qa/setup.sh` and use
`tools/raw-fits-qa/.venv/bin/python -m astroponys.raw_qa_worker DATASET --output-root OUTPUT`.
Setup installs from the tool's own requirements file and creates or reuses its
own venv. Launch does not install dependencies. Use `--no-recursive` to scan
only the selected folder. The output root must be outside the raw dataset.

Optional user defaults belong in `~/.astroprocess/raw-fits-qa/config.toml`.
See `config.example.toml` for camera-specific clipping ceilings. The example
ceiling is for the reference autofocus frame, not a default for other cameras.
A missing ceiling yields an unknown confirmed count. Unconfirmed upper plateaus
are reported separately. An adjacent existing AstroPonys session YAML may
supply known header aliases and session identity, but does not replace the
selected dataset or output path.

## Register and run under AstroProcess

Complete AstroProcess setup first. In AstroPonys:

```powershell
.\tools\raw-fits-qa\setup.cmd
.\tools\raw-fits-qa\.venv\Scripts\python.exe .\tools\raw-fits-qa\integrate_flask.py
```

Use `--config PATH` if the host configuration is not in the default location.
The installer preserves other entries, is idempotent, and refuses to overwrite
a conflicting manual entry. Restart AstroProcess. Select the dataset, open
**Tools → Raw FITS QA**, set recursive scanning if needed, and start the job.
Use the portal's existing bounded and archive discovery actions for listing
files. The QA job runs separately in the registered tool venv, and the existing
portal concurrency limit controls parallel jobs.

Open the job's report when finished. Hover for the star's measurements or select
a dot to open its native-pixel preview. Filter by camera/readout group, filter,
exposure, session, and role. Export the filtered plot as PNG. The report uses no
CDN and works as `report.html` offline with its relative `frames/` directory.
Keep those together when moving a report. Each run is independent and immutable.
Byte-identical FITS produce one set of points per report.

The worker writes `result.json`, `manifest.json`, `report.html`, and rendered PNG
previews. The result lists `qa_inspected_files`. AstroProcess v1 does not yet ingest
that list into its discovery index, so the portal's **New** flag is not changed by
this integration. No direct writes to the portal database, sorter launch, or
automatic accept/reject changes are made.

See [the measurement method](../../docs/methods/METHOD-RAWQA-001-stellar-qa.md)
for fitting and clipping limitations.
