"""Portable raw QA reports and native-resolution display previews."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

from .raw_qa import ImageArray, Record


def write_preview(image: ImageArray, path: Path) -> None:
    lo, hi = np.percentile(image[::4, ::4], [0.5, 99.8])
    if hi <= lo:
        hi = lo + 1
    preview = np.arcsinh(8 * np.clip((image - lo) / (hi - lo), 0, 1)) / np.arcsinh(8)
    Image.fromarray(np.rint(255 * preview).astype(np.uint8)).save(path)


def write_report(frames: list[Record], path: Path) -> None:
    template = Path(__file__).with_name("raw_qa_report.html").read_text(encoding="utf-8")
    data = json.dumps(frames, allow_nan=False, separators=(",", ":")).replace("<", "\\u003c")
    path.write_text(template.replace("__RAW_QA_DATA__", data), encoding="utf-8")
