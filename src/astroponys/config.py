"""Versioned, adjacent-only YAML configuration loading."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    """Raised when a session configuration is missing or unsafe."""


DEFAULT_HEADER_ALIASES: dict[str, tuple[str, ...]] = {
    "observed_at": ("DATE-OBS", "DATEOBS"),
    "filter_name": ("FILTER", "FILTERID"),
    "focus_position": ("FOCUSPOS", "FOCPOS", "FOCUS"),
    "exposure_seconds": ("EXPTIME", "EXPOSURE"),
    "camera": ("INSTRUME", "CAMERA"),
    "gain": ("GAIN", "EGAIN"),
    "offset": ("OFFSET", "BLKLEVEL"),
    "bin_x": ("XBINNING", "XBIN"),
    "bin_y": ("YBINNING", "YBIN"),
    "sensor_temperature_c": ("CCD-TEMP", "SENSORT"),
    "target": ("OBJECT", "TARGET"),
}


@dataclass(frozen=True)
class SessionConfig:
    config_path: Path
    image_directory: Path
    output_directory: Path
    reference_filter: str = "Luminance"
    recursive: bool = False
    header_aliases: dict[str, tuple[str, ...]] = field(
        default_factory=lambda: dict(DEFAULT_HEADER_ALIASES)
    )
    filter_order: tuple[str, ...] = ()
    contact_sheet_percentiles: tuple[float, float] = (1.0, 99.5)
    session_id: str | None = None
    night_id: str | None = None
    target_id: str | None = None
    panel_id: str | None = None


def locate_config(session: Path) -> Path:
    candidate = session if session.is_file() else session / "astroponys.yaml"
    if candidate.name != "astroponys.yaml" or not candidate.is_file():
        raise ConfigError(f"No astroponys.yaml at explicit/adjacent path: {candidate}")
    return candidate.resolve()


def _mapping(value: Any, name: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ConfigError(f"{name} must be a mapping")
    return {str(key): item for key, item in value.items()}


def load_config(session: Path) -> SessionConfig:
    config_path = locate_config(session)
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    root = _mapping(raw, "configuration")
    if root.get("schema_version") != 1:
        raise ConfigError("schema_version must be 1")

    allowed = {"schema_version", "images", "output", "focus", "fits", "contact_sheet", "identity"}
    unknown = set(root) - allowed
    if unknown:
        raise ConfigError(f"Unknown top-level keys: {', '.join(sorted(unknown))}")

    base = config_path.parent
    images = _mapping(root.get("images"), "images")
    image_directory = (base / str(images.get("directory", "."))).resolve()
    if not image_directory.is_dir():
        raise ConfigError(f"Image directory does not exist: {image_directory}")

    output = _mapping(root.get("output"), "output")
    output_directory = (base / str(output.get("directory", "astroponys-output"))).resolve()
    if output_directory == image_directory or image_directory not in output_directory.parents:
        raise ConfigError("Output directory must be a child of the image directory")

    focus = _mapping(root.get("focus"), "focus")
    fits = _mapping(root.get("fits"), "fits")
    custom_aliases = _mapping(fits.get("header_aliases"), "fits.header_aliases")
    aliases = dict(DEFAULT_HEADER_ALIASES)
    for field_name, values in custom_aliases.items():
        if field_name not in aliases or not isinstance(values, list) or not values:
            raise ConfigError(f"Invalid FITS alias entry: {field_name}")
        aliases[field_name] = tuple(str(value).upper() for value in values)

    order_raw = focus.get("filter_order", [])
    if not isinstance(order_raw, list):
        raise ConfigError("focus.filter_order must be a list")

    sheet = _mapping(root.get("contact_sheet"), "contact_sheet")
    percentiles = sheet.get("percentiles", [1.0, 99.5])
    if (
        not isinstance(percentiles, list)
        or len(percentiles) != 2
        or not 0 <= float(percentiles[0]) < float(percentiles[1]) <= 100
    ):
        raise ConfigError("contact_sheet.percentiles must be two increasing values in 0..100")

    identity = _mapping(root.get("identity"), "identity")
    return SessionConfig(
        config_path=config_path,
        image_directory=image_directory,
        output_directory=output_directory,
        reference_filter=str(focus.get("reference_filter", "Luminance")),
        recursive=bool(images.get("recursive", False)),
        header_aliases=aliases,
        filter_order=tuple(str(value) for value in order_raw),
        contact_sheet_percentiles=(float(percentiles[0]), float(percentiles[1])),
        session_id=_optional_string(identity.get("session_id")),
        night_id=_optional_string(identity.get("night_id")),
        target_id=_optional_string(identity.get("target_id")),
        panel_id=_optional_string(identity.get("panel_id")),
    )


def _optional_string(value: Any) -> str | None:
    return None if value is None else str(value)
