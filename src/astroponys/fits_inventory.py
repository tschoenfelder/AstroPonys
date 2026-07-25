"""Read-only FITS discovery and canonical header inventory."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from astropy.io import fits

from .config import SessionConfig
from .models import FitsRecord

FITS_SUFFIXES = (".fit", ".fits", ".fits.fz")


def discover_fits(config: SessionConfig) -> list[Path]:
    iterator = (
        config.image_directory.rglob("*") if config.recursive else config.image_directory.glob("*")
    )
    output = config.output_directory
    paths = [
        path.resolve()
        for path in iterator
        if path.is_file()
        and path.name.lower().endswith(FITS_SUFFIXES)
        and output not in path.resolve().parents
    ]
    return sorted(paths, key=lambda path: str(path).casefold())


def inventory(config: SessionConfig) -> list[FitsRecord]:
    records = [_read_record(path, config.header_aliases) for path in discover_fits(config)]
    return sorted(records, key=_sort_key)


def _sort_key(record: FitsRecord) -> tuple[datetime, str]:
    latest = datetime.max.replace(tzinfo=UTC)
    return (record.observed_at or latest, str(record.path).casefold())


def _first(
    header: fits.Header, aliases: tuple[str, ...], field_name: str, warnings: list[str]
) -> tuple[Any | None, str | None]:
    present = [(key, header[key]) for key in aliases if key in header]
    if present:
        chosen_key, chosen_value = present[0]
        conflicting = [key for key, value in present[1:] if str(value) != str(chosen_value)]
        if conflicting:
            warnings.append(
                f"CONFLICTING_{field_name.upper()}: chose {chosen_key}; also {', '.join(conflicting)}"
            )
        return chosen_value, chosen_key
    return None, None


def _read_record(path: Path, aliases: dict[str, tuple[str, ...]]) -> FitsRecord:
    stat_before = path.stat()
    warnings: list[str] = []
    sources: dict[str, str] = {}
    try:
        with fits.open(path, mode="readonly", memmap=True, do_not_scale_image_data=True) as hdus:
            header = hdus[0].header
            values: dict[str, Any] = {}
            for field_name, keys in aliases.items():
                value, source = _first(header, keys, field_name, warnings)
                values[field_name] = value
                if source:
                    sources[field_name] = source
            observed_at = _parse_datetime(values["observed_at"], warnings)
            filter_name = _text(values["filter_name"])
            focus_position = _number(values["focus_position"], "focus_position", warnings)
            exposure = _number(values["exposure_seconds"], "exposure_seconds", warnings)
            gain = _number(values["gain"], "gain", warnings)
            offset = _number(values["offset"], "offset", warnings)
            temperature = _number(values["sensor_temperature_c"], "sensor_temperature_c", warnings)
            xbin = _number(values["bin_x"], "bin_x", warnings)
            ybin = _number(values["bin_y"], "bin_y", warnings)
    except (OSError, ValueError, TypeError) as exc:
        warnings.append(f"FITS_READ_ERROR: {type(exc).__name__}: {exc}")
        observed_at = None
        filter_name = None
        focus_position = exposure = gain = offset = temperature = xbin = ybin = None
        values = {}

    stat_after = path.stat()
    if (stat_before.st_size, stat_before.st_mtime_ns) != (
        stat_after.st_size,
        stat_after.st_mtime_ns,
    ):
        warnings.append("SOURCE_CHANGED_DURING_READ")
    for required in ("observed_at", "filter_name", "focus_position"):
        if locals().get(required) is None:
            warnings.append(f"MISSING_{required.upper()}")
    binning = None if xbin is None and ybin is None else f"{_fmt(xbin)}x{_fmt(ybin)}"
    return FitsRecord(
        path=path,
        size=stat_after.st_size,
        mtime_ns=stat_after.st_mtime_ns,
        observed_at=observed_at,
        filter_name=filter_name,
        focus_position=focus_position,
        exposure_seconds=exposure,
        camera=_text(values.get("camera")),
        gain=gain,
        offset=offset,
        binning=binning,
        sensor_temperature_c=temperature,
        target=_text(values.get("target")),
        warnings=tuple(warnings),
        header_sources=sources,
    )


def _parse_datetime(value: Any, warnings: list[str]) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).strip())
        return parsed.replace(tzinfo=parsed.tzinfo or UTC).astimezone(UTC)
    except ValueError:
        warnings.append(f"INVALID_OBSERVED_AT: {value}")
        return None


def _number(value: Any, name: str, warnings: list[str]) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        warnings.append(f"INVALID_{name.upper()}: {value}")
        return None


def _text(value: Any) -> str | None:
    if value is None or not str(value).strip():
        return None
    return str(value).strip()


def _fmt(value: float | None) -> str:
    if value is None:
        return "?"
    return str(int(value)) if value.is_integer() else str(value)
