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

## Platform priorities

Windows is the primary execution and development platform because the available
Windows workstation is substantially faster than the Raspberry Pi. Python 3.13 is
the current primary interpreter. Linux and Raspberry Pi/ARM64 remain supported
targets, with optimisation and native packaging following the desktop vertical slice.

The project prefers a stable supported Python/dependency combination over adopting
the newest Python release immediately. Required scientific libraries must normally
provide maintained precompiled Windows wheels for selected Python versions. A
dependency that requires local Windows compilation needs an ADR documenting why it
is unavoidable and how installation will be supported.
