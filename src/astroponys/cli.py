"""Command-line entry point for independently runnable ponies."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from .config import ConfigError, load_config
from .contact_sheet import render_contact_sheet
from .fits_inventory import inventory
from .focus_analysis import FocusAnalysisError, analyse_focus_offsets
from .provenance import base_manifest, create_run_directory, write_json
from .reporting import write_csv, write_markdown

EXIT_SUCCESS = 0
EXIT_WARNING = 2
EXIT_FAILURE = 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="astroponys")
    commands = parser.add_subparsers(dest="command", required=True)
    focus = commands.add_parser("focus-offset", help="Filter focus-offset tools")
    focus_commands = focus.add_subparsers(dest="focus_command", required=True)
    analyse = focus_commands.add_parser("analyse", help="Analyse a focus-check session")
    analyse.add_argument("session", type=Path, help="Image folder or astroponys.yaml")
    analyse.add_argument("--json", action="store_true", help="Print result summary as JSON")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "focus-offset" and args.focus_command == "analyse":
        return run_focus_offset(args.session, json_console=args.json)
    return EXIT_FAILURE


def run_focus_offset(session: Path, json_console: bool = False) -> int:
    try:
        config = load_config(session)
        records = inventory(config)
        if not records:
            raise FocusAnalysisError("No FITS inputs found")
        estimates, analysis_warnings = analyse_focus_offsets(records, config.reference_filter)
        run_id, run_directory = create_run_directory(config, "focus-offset")
        sheet_path = run_directory / "contact-sheet.png"
        render_contact_sheet(
            records, sheet_path, config.filter_order, config.contact_sheet_percentiles
        )
        write_csv(run_directory / "offsets.csv", estimates)
        write_markdown(
            run_directory / "report.md",
            run_id,
            config.reference_filter,
            estimates,
            analysis_warnings,
        )
        input_warnings = [
            f"{record.path.name}: {warning}" for record in records for warning in record.warnings
        ]
        manifest = base_manifest(config, run_id, "focus-offset")
        manifest.update(
            {
                "status": "warning" if input_warnings or analysis_warnings else "success",
                "reference_filter": config.reference_filter,
                "inputs": [record.identity() for record in records],
                "inventory": records,
                "estimates": estimates,
                "warnings": [*input_warnings, *analysis_warnings],
                "artifacts": ["manifest.json", "report.md", "offsets.csv", "contact-sheet.png"],
            }
        )
        manifest_path = run_directory / "manifest.json"
        write_json(manifest_path, manifest)
        if json_console:
            print(manifest_path.read_text(encoding="utf-8"), end="")
        else:
            print(f"AstroPonys run: {run_id}")
            print(f"Report: {run_directory / 'report.md'}")
            print(f"Contact sheet: {sheet_path}")
        return EXIT_WARNING if manifest["status"] == "warning" else EXIT_SUCCESS
    except (ConfigError, FocusAnalysisError, OSError, ValueError) as exc:
        print(f"astroponys: error: {exc}", file=sys.stderr)
        return EXIT_FAILURE


if __name__ == "__main__":
    raise SystemExit(main())
