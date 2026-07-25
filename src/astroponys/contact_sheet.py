"""Monochrome contact-sheet rendering for focus-check frames."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import numpy as np
from astropy.io import fits
from PIL import Image, ImageDraw

from .models import FitsRecord

THUMBNAIL = (320, 240)
LABEL_HEIGHT = 44
HEADER_HEIGHT = 28


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
    usable.sort(key=_observed_at)
    cycles = _group_cycles(usable, rank)
    columns = max(1, len(order))
    rows = len(cycles)
    cell_width, cell_height = THUMBNAIL[0], THUMBNAIL[1] + LABEL_HEIGHT
    canvas = Image.new("L", (columns * cell_width, HEADER_HEIGHT + rows * cell_height), color=18)
    draw = ImageDraw.Draw(canvas)
    draw.text(
        (5, 6),
        f"Per-frame linear stretch: p{percentiles[0]:g}-p{percentiles[1]:g}",
        fill=235,
    )
    for row, cycle in enumerate(cycles):
        for column, filter_name in enumerate(order):
            x = column * cell_width
            y = HEADER_HEIGHT + row * cell_height
            record = cycle.get(filter_name.casefold())
            if record is None:
                _draw_missing(draw, x, y, row, filter_name)
                continue
            try:
                thumb = _thumbnail(record.path, percentiles)
                canvas.paste(thumb, (x, y))
            except (OSError, ValueError, TypeError):
                draw.rectangle((x, y, x + cell_width - 1, y + THUMBNAIL[1] - 1), outline=220)
                draw.text((x + 8, y + 8), "UNREADABLE", fill=255)
            stamp = _observed_at(record).isoformat(timespec="seconds")
            focus = f"{record.focus_position:g}" if record.focus_position is not None else "?"
            label = f"cycle={row + 1}  {record.filter_name}  focus={focus}\n{stamp}"
            draw.text((x + 4, y + THUMBNAIL[1] + 3), label, fill=235)
    destination.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(destination, format="PNG")


def _group_cycles(records: list[FitsRecord], rank: dict[str, int]) -> list[dict[str, FitsRecord]]:
    cycles: list[dict[str, FitsRecord]] = []
    current: dict[str, FitsRecord] = {}
    last_rank = -1
    for record in records:
        key = (record.filter_name or "").casefold()
        current_rank = rank.get(key, len(rank))
        if current and (key in current or current_rank < last_rank):
            cycles.append(current)
            current = {}
            last_rank = -1
        current[key] = record
        last_rank = current_rank
    if current:
        cycles.append(current)
    return cycles


def _draw_missing(draw: ImageDraw.ImageDraw, x: int, y: int, row: int, filter_name: str) -> None:
    draw.rectangle((x, y, x + THUMBNAIL[0] - 1, y + THUMBNAIL[1] - 1), outline=100)
    draw.text((x + 8, y + 8), "MISSING", fill=150)
    draw.text(
        (x + 4, y + THUMBNAIL[1] + 3),
        f"cycle={row + 1}  {filter_name}",
        fill=180,
    )


def _observed_at(record: FitsRecord) -> datetime:
    if record.observed_at is None:
        raise ValueError("Contact-sheet record lacks observation time")
    return record.observed_at


def _thumbnail(path: Path, percentiles: tuple[float, float]) -> Image.Image:
    # Scaled unsigned-integer FITS (BZERO/BSCALE), common for astronomy cameras,
    # cannot be read through Astropy's memory mapping. Thumbnails are processed one
    # frame at a time, so disabling memmap keeps memory bounded to a single image.
    with fits.open(path, mode="readonly", memmap=False) as hdus:
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
