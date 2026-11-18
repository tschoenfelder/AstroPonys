# ADR-0008 — Raw QA stays outside the Flask process

Status: Accepted (AP-011, REQ-RAWQA-001..004).

AstroProcess already has a bounded discovery API and separate archive discovery and
tool-job execution. Register one Raw FITS QA worker in its own venv. That worker owns
CPU-heavy FITS decoding, measurements and rendering, and emits a single immutable
portable report. Do not introduce a second scheduler or import scientific code into
Flask. The generic registered tool page is the launch UI; the QA-specific report is
the measurement and 1:1 inspection UI.

The standalone pony writes into a new `raw-fits-qa/<run-id>` below an explicitly supplied
output root outside the raw tree. Under the portal, the existing job output directory
is the explicitly assigned run root. The same rule prevents output inside the raw tree.
No source FITS is copied. Preview PNGs are derived presentation products, not FITS copies.

Session YAML is optionally used for the existing header aliases and identity. User
defaults live in `~/.astroprocess/raw-fits-qa/config.toml`. Registration edits only the
named tool table in the existing portal config and preserves other settings.

The AstroProcess v1 host currently does not consume per-file QA completion from
worker results. The worker publishes successfully inspected relative paths; it
does not access the host's SQLite database or change discovery status. A supported
host ingestion hook is a separate follow-up.
