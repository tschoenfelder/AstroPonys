from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
from astropy.io import fits


def write_focus_fits(
    path: Path,
    minute: int,
    filter_name: str,
    focus: float,
    *,
    date_start: datetime = datetime(2026, 7, 25, tzinfo=UTC),
) -> None:
    rng = np.random.default_rng(minute + 7635)
    data = rng.normal(1000, 20, size=(32, 48)).astype(np.float32)
    header = fits.Header()
    header["DATE-OBS"] = (date_start + timedelta(minutes=minute)).isoformat()
    header["FILTER"] = filter_name
    header["FOCUSPOS"] = focus
    header["EXPTIME"] = 30.0
    header["INSTRUME"] = "ATR585M"
    header["GAIN"] = 100
    header["OFFSET"] = 260
    header["XBINNING"] = 1
    header["YBINNING"] = 1
    header["CCD-TEMP"] = -10.0
    header["OBJECT"] = "NGC 7635"
    fits.PrimaryHDU(data=data, header=header).writeto(path)


def write_config(directory: Path, recursive: bool = False) -> Path:
    config = directory / "astroponys.yaml"
    config.write_text(
        "\n".join(
            [
                "schema_version: 1",
                "images:",
                "  directory: .",
                f"  recursive: {str(recursive).lower()}",
                "output:",
                "  directory: astroponys-output",
                "focus:",
                "  reference_filter: Luminance",
                "  filter_order: [Luminance, Red, Green]",
                "contact_sheet:",
                "  percentiles: [1.0, 99.5]",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return config
