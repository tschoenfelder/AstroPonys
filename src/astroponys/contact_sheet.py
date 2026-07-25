"""Monochrome contact-sheet rendering for focus-check frames."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from astropy.io import fits
from PIL import Image, ImageDraw

from .models import FitsRecord

THUMBNAIL = (320, 240)
LABEL_HEIGHT = 44


def render_contact_sheet(
    records: list[FitsRecord],
    destination: Path,
    filter_order: tuple[str, ...],
    percentiles: tuple[float, float],
) -> None:
    usable = [record for record in records if record.filter_name and record.observed_at]
    if not usable:
        raise ValueError("No timestamped filter frames available for contact sheet")
    order = list(filter_order) or sorted(
        {record.filter_name for record in usable if record.filter_name}, key=str.casefold
    )
    rank = {name.casefold(): index for index, name in enumerate(order)}
    usable.sort(
        key=lambda record: (
            record.observed_at,
            rank.get((record.filter_name or "").casefold(), len(rank)),
        )
    )
    columns = max(1, len(order))
    rows = (len(usable) + columns - 1) // columns
    cell_width, cell_height = THUMBNAIL[0], THUMBNAIL[1] + LABEL_HEIGHT
    canvas = Image.new("L", (columns * cell_width, rows * cell_height), color=18)
    draw = ImageDraw.Draw(canvas)
    for index, record in enumerate(usable):
        x = (index % columns) * cell_width
        y = (index // columns) * cell_height
        try:
            thumb = _thumbnail(record.path, percentiles)
            canvas.paste(thumb, (x, y))
        except (OSError, ValueError, TypeError):
            draw.rectangle((x, y, x + cell_width - 1, y + THUMBNAIL[1] - 1), outline=220)
            draw.text((x + 8, y + 8), "UNREADABLE", fill=255)
        stamp = record.observed_at.isoformat(timespec="seconds") if record.observed_at else "?"
        label = (
            f"{record.filter_name}  focus={record.focus_position:g}\n{stamp}"
            if record.focus_position is not None
            else f"{record.filter_name}  focus=?\n{stamp}"
        )
        draw.text((x + 4, y + THUMBNAIL[1] + 3), label, fill=235)
    destination.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(destination, format="PNG")


def _thumbnail(path: Path, percentiles: tuple[float, float]) -> Image.Image:
    with fits.open(path, mode="readonly", memmap=True) as hdus:
        data = np.asarray(hdus[0].data, dtype=np.float32)
    data = np.squeeze(data)
    if data.ndim != 2:
        raise ValueError("Expected a two-dimensional image")
    finite = data[np.isfinite(data)]
    if finite.size == 0:
        raise ValueError("Image has no finite pixels")
    low, high = np.percentile(finite, percentiles)
    if high <= low:
        high = low + 1.0
    scaled = np.clip((data - low) / (high - low), 0.0, 1.0)
    image = Image.fromarray(np.asarray(scaled * 255, dtype=np.uint8), mode="L")
    image.thumbnail(THUMBNAIL, Image.Resampling.LANCZOS)
    result = Image.new("L", THUMBNAIL, color=0)
    result.paste(image, ((THUMBNAIL[0] - image.width) // 2, (THUMBNAIL[1] - image.height) // 2))
    return result
