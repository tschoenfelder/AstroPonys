"""Raw FITS QA CLI and AstroProcess v1 worker adapter."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tomllib
from collections.abc import Callable
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any
from uuid import uuid4

import numpy as np
from astropy.io import fits

from .config import load_config
from .raw_qa import METHOD, Record, ceiling_for, measure, metadata
from .raw_qa_report import write_preview, write_report

SUFFIXES = (".fits", ".fit", ".fts", ".fits.fz", ".fit.fz", ".fts.fz")


def utc() -> str:
    return datetime.now(UTC).isoformat()


def config_path() -> Path:
    return Path.home() / ".astroprocess" / "raw-fits-qa" / "config.toml"


def inputs(root: Path, recursive: bool) -> list[Path]:
    out: list[Path] = []
    for base, dirs, names in os.walk(root, followlinks=False):
        here = Path(base)
        dirs[:] = sorted(
            d
            for d in dirs
            if recursive
            and not (here / d).is_symlink()
            and (here / d).resolve().is_relative_to(root)
        )
        out.extend(
            here / n
            for n in sorted(names)
            if n.lower().endswith(SUFFIXES)
            and not (here / n).is_symlink()
            and (here / n).is_file()
            and (here / n).resolve().is_relative_to(root)
        )
    return out


def load_fits(path: Path) -> tuple[Record, Any]:
    with fits.open(
        path, mode="readonly", memmap=False, ignore_missing_end=False, lazy_load_hdus=False
    ) as hdus:
        for hdu in hdus:
            if hdu.header.get("NAXIS") == 2:
                header = dict(hdus[0].header)
                header.update(dict(hdu.header))
                raw = hdu.data
                if raw is None or np.shape(raw) != (header["NAXIS2"], header["NAXIS1"]):
                    raise ValueError("FITS image length does not match its header")
                return header, np.asarray(raw, dtype=np.float64)
        return dict(hdus[0].header), None


def write_json(path: Path, value: Record) -> None:
    with path.open("x", encoding="utf-8") as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write("\n")


def scan(
    root: Path,
    output: Path,
    settings: Record,
    recursive: bool,
    progress: Callable[[float], None],
    dataset_id: str | None = None,
) -> Record:
    root, output = root.resolve(), output.resolve()
    if not root.is_dir() or output.is_relative_to(root):
        raise ValueError("Dataset must exist and output must be outside the raw dataset")
    reserved = ("frames", "manifest.json", "result.json", "report.html")
    if any((output / name).exists() or (output / name).is_symlink() for name in reserved):
        raise ValueError("QA run output already exists")
    files = inputs(root, recursive)
    if not files:
        raise ValueError("No FITS files found in the selected scope")
    aliases = None
    session = None
    # Use adjacent session metadata only; the host's dataset remains the scan root.
    if (root / "astroponys.yaml").is_file():
        session = load_config(root)
        aliases = session.header_aliases
    rules = settings.get("clipping", [])
    if not isinstance(rules, list) or not all(isinstance(r, dict) for r in rules):
        raise ValueError("Clipping configuration must contain [[clipping]] tables")
    ceiling_for({}, rules)
    output.mkdir(parents=True, exist_ok=True)
    (output / "frames").mkdir()
    started = utc()
    records: list[Record] = []
    duplicates: list[Record] = []
    seen: dict[str, str] = {}
    for index, path in enumerate(files, 1):
        rel = path.relative_to(root).as_posix()
        row: Record = {
            "relative_path": rel,
            "metadata": metadata({}, path.relative_to(root), aliases),
            "stars": [],
            "clipped_stars": None,
            "ceiling_adu": None,
            "preview": None,
            "status": "error",
            "warnings": [],
        }
        try:
            with path.open("rb") as f:
                sha = hashlib.file_digest(f, "sha256").hexdigest()
            if sha in seen:
                duplicates.append({"relative_path": rel, "duplicate_of": seen[sha], "sha256": sha})
                progress(index / len(files) * 99)
                continue
            seen[sha] = rel
            row["sha256"] = sha
            stat = path.stat()
            row.update(size_bytes=stat.st_size, mtime_ns=stat.st_mtime_ns)
            header, img = load_fits(path)
            m = metadata(header, path.relative_to(root), aliases)
            if not m.get("session"):
                if session and (session.session_id or session.night_id):
                    m["session"] = session.session_id or session.night_id
                    m["sources"]["session"] = "session:astroponys.yaml"
                elif m.get("observed_at"):
                    m["session"] = str(m["observed_at"])[:10]
                    m["sources"]["session"] = "derived:observation_date"
            row["metadata"] = m
            if m["frame_type"] != "light":
                row["status"] = "not_light" if m["frame_type"] is not None else "unknown_frame_type"
            elif img is None:
                row["status"] = "unsupported_image"
                row["warnings"].append("No two-dimensional image plane")
            else:
                cap = ceiling_for(m, rules)
                row.update(width=img.shape[1], height=img.shape[0])
                if header.get("BAYERPAT"):
                    row["status"] = "unsupported_cfa"
                    row["warnings"].append("CFA image shown but not fitted")
                else:
                    row.update(measure(img, cap, m["pixel_scale_arcsec"]))
                    row["status"] = "measured" if row["stars"] else "no_usable_stars"
                    if len(row["stars"]) < 5:
                        row["warnings"].append(f"Only {len(row['stars'])} usable stellar fits")
                    if cap is None:
                        row["warnings"].append(
                            "No verified clipping ceiling; clipped-star count unknown"
                        )
                    if row["candidate_limit_reached"]:
                        row["warnings"].append(
                            "Source candidate limit reached; clipped-star count unknown"
                        )
                    if row["clipping_candidates"]:
                        row["warnings"].append(
                            f"{len(row['clipping_candidates'])} unconfirmed upper plateaus"
                        )
                row["preview"] = "frames/" + sha + ".png"
                write_preview(img, output / row["preview"])
        except (OSError, ValueError, TypeError, KeyError, IndexError) as exc:
            row["status"] = "error"
            row["preview"] = None
            row["warnings"].append(f"{type(exc).__name__}: {exc}")
            print(f"QA warning {rel}: {exc}", file=sys.stderr, flush=True)
        records.append(row)
        progress(index / len(files) * 99)
    successfully_inspected = [
        r["relative_path"] for r in records if r["status"] in {"measured", "no_usable_stars"}
    ]
    if not successfully_inspected and any(r["status"] == "error" for r in records):
        raise ValueError("No Light successfully inspected; see worker log")
    try:
        software = version("astroponys")
    except PackageNotFoundError:
        software = "source-tree"
    result = {
        "contract_version": 1,
        "status": "ok",
        "dataset_id": dataset_id,
        "fits_count": len(records),
        "duplicate_count": len(duplicates),
        "measured_count": sum(bool(r["stars"]) for r in records),
        "qa_inspected_files": successfully_inspected,
        "report": "report.html",
        "next_step": {
            "tool_id": "raw_fits_qa_review",
            "label": "Review the initial QA report",
            "launch_automatically": False,
        },
    }
    write_report(records, output / "report.html")
    write_json(
        output / "manifest.json",
        {
            **result,
            "method": METHOD,
            "method_status": "Heuristic",
            "parent_level": "raw",
            "output_levels": {"measurements": "raw", "report_and_previews": "presentation"},
            "started_at": started,
            "ended_at": utc(),
            "dataset_root": str(root),
            "recursive": recursive,
            "astroponys_version": software,
            "clipping_rules": rules,
            "session_config": str(session.config_path) if session else None,
            "warnings": [w for row in records for w in row["warnings"]],
            "evidence_confidence": {
                "index": 52,
                "method_evidence": 16,
                "data_quality": 14,
                "repeatability": 10,
                "test_coverage": 8,
                "model_fit": 4,
                "platform_validation": 0,
                "reason": "Heuristic Gaussian measurements. Synthetic lower-level verification; "
                "no independent night-by-night PSF or primary-platform evidence in this run.",
            },
            "frames": records,
            "duplicates": duplicates,
            "artifacts": [
                "manifest.json",
                "result.json",
                "report.html",
                *(r["preview"] for r in records if r["preview"]),
            ],
        },
    )
    write_json(output / "result.json", result)
    progress(100)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path, nargs="?")
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--recursive", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--config", type=Path, default=config_path())
    parser.add_argument("--job-spec", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--events", type=Path)
    a = parser.parse_args()
    try:
        settings = tomllib.loads(a.config.read_text(encoding="utf-8")) if a.config.exists() else {}
        if a.job_spec:
            if not a.output_dir or not a.events or a.dataset or a.output_root:
                raise ValueError("Worker requires --job-spec, --output-dir and --events only")
            job = json.loads(a.job_spec.read_text(encoding="utf-8"))
            if job.get("contract_version") != 1:
                raise ValueError("Unsupported AstroProcess worker contract")
            output = a.output_dir.resolve()
            if not a.events.resolve().is_relative_to(output):
                raise ValueError("Event file must be inside job output")
            root = Path(job["dataset_path"]).resolve()
            recursive = job.get("inputs", {}).get("recursive", settings.get("recursive", True))
            if not isinstance(recursive, bool):
                raise ValueError("recursive must be boolean")

            def event(v: float) -> None:
                with a.events.open("a", encoding="utf-8") as f:
                    f.write(json.dumps({"type": "progress", "value": v, "at": utc()}) + "\n")

            result = scan(root, output, settings, recursive, event, job["dataset_id"])
        else:
            dataset = a.dataset or settings.get("dataset")
            output_root = a.output_root or settings.get("output_root")
            if not dataset or not output_root or a.output_dir or a.events:
                raise ValueError("Standalone usage requires dataset and --output-root")
            output = Path(output_root).expanduser() / "raw-fits-qa" / uuid4().hex
            recursive = a.recursive if a.recursive is not None else settings.get("recursive", True)
            if not isinstance(recursive, bool):
                raise ValueError("recursive must be boolean")
            result = scan(Path(dataset).expanduser(), output, settings, recursive, lambda _: None)
        print(f"QA: {result['measured_count']} measured of {result['fits_count']} unique FITS")
        print(output / "report.html")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Raw FITS QA failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
