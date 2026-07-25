# Architecture

AstroPonys uses a ports-and-adapters shape without requiring a framework:

```text
CLI / future UI
      |
application use cases
      |
domain models + pure scientific methods
      |
FITS, filesystem, report and future Ekos adapters
```

Each pony owns a narrow application use case and CLI entry point while sharing stable
domain records, configuration, provenance and reporting utilities. Scientific modules
accept arrays/records and return typed results; they do not access global configuration,
the network or UI state.

Initial package shape:

```text
src/astroponys/
  config/        schema and loading
  fits/          read-only adapters and canonical metadata
  focus/         cycle, baseline, estimator and confidence logic
  contact_sheet/ rendering
  provenance/    run manifests and immutable output management
  cli/           standalone pony entry points
```

The session model reserves `session_id`, `night_id`, `target_id` and `panel_id` so
multi-night and mosaic work can be added without redefining input identity.
