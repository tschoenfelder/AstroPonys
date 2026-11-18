"""Register the independently installed QA worker in AstroProcess's TOML config."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import tomllib
from pathlib import Path

TOOL = "raw_fits_qa"


def install(config: Path, python: Path) -> bool:
    if not python.is_file():
        raise ValueError(f"Tool environment not found: {python}. Run raw-fits-qa setup first.")
    if python.is_symlink():
        raise ValueError(
            "AstroProcess resolves executable paths. Use a tool venv created with --copies."
        )
    original = config.read_text(encoding="utf-8")
    settings = tomllib.loads(original)
    command = python.absolute().as_posix()  # Do not resolve the venv executable symlink.
    entry = {
        "name": "Raw FITS QA",
        "description": "Read-only FITS analysis, FWHM/ADU plots and 1:1 sensor views.",
        "python": command,
        "module": "astroponys.raw_qa_worker",
        "inputs": {
            "recursive": {"type": "boolean", "label": "Scan subdirectories", "default": True}
        },
    }
    existing = settings.get("tools", {}).get(TOOL)
    if existing == entry:
        return False
    if existing is not None:
        raise ValueError(f"Existing tools.{TOOL} differs. Review that entry before replacing it.")
    add = f"""
[tools.{TOOL}]
name = {json.dumps(entry["name"])}
description = {json.dumps(entry["description"])}
python = {json.dumps(command, ensure_ascii=False)}
module = {json.dumps(entry["module"])}

[tools.{TOOL}.inputs.recursive]
type = "boolean"
label = "Scan subdirectories"
default = true
"""
    updated = original.rstrip() + "\n" + add
    tomllib.loads(updated)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=config.parent, delete=False
    ) as f:
        scratch = Path(f.name)
        f.write(updated)
    try:
        os.chmod(scratch, config.stat().st_mode & 0o777)
        scratch.replace(config)
    finally:
        scratch.unlink(missing_ok=True)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    default = Path.home() / ".astroprocess" / "web" / "config.toml"
    parser.add_argument(
        "--config", type=Path, default=Path(os.environ.get("ASTROPROCESS_CONFIG", default))
    )
    default_python = (
        Path(__file__).resolve().parent
        / ".venv"
        / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    )
    parser.add_argument("--tool-python", type=Path, default=default_python)
    args = parser.parse_args()
    try:
        config = args.config.expanduser().absolute()
        if not config.is_file():
            raise ValueError(f"No AstroProcess config at {config}. Run AstroProcess setup first.")
        changed = install(config, args.tool_python.expanduser())
    except (ValueError, OSError) as exc:
        parser.exit(1, str(exc) + "\n")
    print("Registered Raw FITS QA." if changed else "Raw FITS QA already registered.")
    print("Restart AstroProcess, select your dataset, then open Raw FITS QA in the Tools menu.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
