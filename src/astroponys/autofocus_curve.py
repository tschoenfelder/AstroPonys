"""Standalone autofocus-frame usability and optimal-focus estimation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from astropy.io import fits


@dataclass(frozen=True)
class AutofocusFrame:
    path: Path
    focus_position: float | None
    usable: bool
    rejection_reasons: tuple[str, ...]
    detected_peaks: int
    measured_stars: int
    median_hfr_px: float | None


@dataclass(frozen=True)
class AutofocusResult:
    frames: tuple[AutofocusFrame, ...]
    optimal_focus: float | None
    fit_coefficients: tuple[float, float, float] | None
    fit_r_squared: float | None
    status: str
    reasons: tuple[str, ...]
    confidence_index: int


def analyse_autofocus_sequence(directory: Path) -> AutofocusResult:
    paths = sorted(path for path in directory.glob("*.fits") if path.is_file())
    frames = tuple(measure_autofocus_frame(path) for path in paths)
    return fit_focus_curve(frames)


def measure_autofocus_frame(path: Path, minimum_stars: int = 8) -> AutofocusFrame:
    reasons: list[str] = []
    try:
        with fits.open(path, mode="readonly", memmap=False) as hdus:
            header = hdus[0].header
            image = np.asarray(hdus[0].data, dtype=np.float32)
    except (OSError, ValueError, TypeError) as exc:
        return AutofocusFrame(path, None, False, (f"FITS_READ_ERROR: {exc}",), 0, 0, None)
    position = _number(header.get("FOCUSPOS"))
    if position is None:
        reasons.append("MISSING_FOCUS_POSITION")
    if image.ndim != 2:
        reasons.append("IMAGE_NOT_2D")
        return AutofocusFrame(path, position, False, tuple(reasons), 0, 0, None)

    background, noise = _background_noise(image)
    candidates = _peak_candidates(image, background + 8 * noise, limit=200, border=14)
    hfrs: list[float] = []
    for y, x in candidates:
        hfr = _stellar_hfr(image, int(y), int(x), noise)
        if hfr is not None:
            hfrs.append(hfr)
    if len(candidates) == 0:
        reasons.append("NO_SIGNIFICANT_PEAKS")
    if candidates.size and len(hfrs) == 0:
        reasons.append("PEAKS_ARE_NOT_EXTENDED_STARS")
    if 0 < len(hfrs) < minimum_stars:
        reasons.append(f"TOO_FEW_MEASURABLE_STARS: {len(hfrs)} < {minimum_stars}")
    usable = position is not None and len(hfrs) >= minimum_stars and not reasons
    return AutofocusFrame(
        path=path,
        focus_position=position,
        usable=usable,
        rejection_reasons=tuple(reasons),
        detected_peaks=len(candidates),
        measured_stars=len(hfrs),
        median_hfr_px=float(np.median(hfrs)) if hfrs else None,
    )


def fit_focus_curve(frames: tuple[AutofocusFrame, ...]) -> AutofocusResult:
    usable = [frame for frame in frames if frame.usable]
    reasons: list[str] = []
    if len(usable) < 5:
        reasons.append(f"TOO_FEW_USABLE_FRAMES: {len(usable)} < 5")
    positions = np.asarray([frame.focus_position for frame in usable], dtype=float)
    hfr = np.asarray([frame.median_hfr_px for frame in usable], dtype=float)
    if len(np.unique(positions)) < 5:
        reasons.append("TOO_FEW_DISTINCT_FOCUS_POSITIONS")
    if reasons:
        return AutofocusResult(frames, None, None, None, "insufficient-data", tuple(reasons), 0)

    coefficients = np.polyfit(positions, hfr, 2)
    predicted = np.polyval(coefficients, positions)
    residual = float(np.sum((hfr - predicted) ** 2))
    total = float(np.sum((hfr - np.mean(hfr)) ** 2))
    r_squared = 1.0 - residual / total if total > 0 else 0.0
    a, b, c = (float(value) for value in coefficients)
    optimum = -b / (2 * a) if a > 0 else None
    if a <= 0:
        reasons.append("CURVE_NOT_CONVEX")
    if optimum is None or not float(np.min(positions)) <= optimum <= float(np.max(positions)):
        reasons.append("CURVE_MINIMUM_OUTSIDE_MEASURED_RANGE")
    if r_squared < 0.6:
        reasons.append(f"CURVE_FIT_TOO_WEAK: R2={r_squared:.3f} < 0.600")
    if reasons:
        return AutofocusResult(
            frames, None, (a, b, c), r_squared, "rejected-curve", tuple(reasons), 30
        )
    confidence = min(95, round(55 + 25 * r_squared + min(15, len(usable))))
    return AutofocusResult(frames, optimum, (a, b, c), r_squared, "success", (), confidence)


def _background_noise(image: np.ndarray) -> tuple[float, float]:
    sample = image[::4, ::4]
    background = float(np.median(sample))
    noise = float(1.4826 * np.median(np.abs(sample - background)))
    return background, max(noise, 1.0)


def _peak_candidates(image: np.ndarray, threshold: float, limit: int, border: int) -> np.ndarray:
    center = image[1:-1, 1:-1]
    peaks = center > threshold
    for dy in range(3):
        for dx in range(3):
            if dy == 1 and dx == 1:
                continue
            peaks &= center > image[dy : image.shape[0] - 2 + dy, dx : image.shape[1] - 2 + dx]
    coordinates = np.argwhere(peaks) + 1
    if len(coordinates):
        keep = (
            (coordinates[:, 0] >= border)
            & (coordinates[:, 0] < image.shape[0] - border)
            & (coordinates[:, 1] >= border)
            & (coordinates[:, 1] < image.shape[1] - border)
        )
        coordinates = coordinates[keep]
    if len(coordinates) > limit:
        values = image[coordinates[:, 0], coordinates[:, 1]]
        coordinates = coordinates[np.argsort(values)[-limit:]]
    return coordinates


def _stellar_hfr(image: np.ndarray, y: int, x: int, frame_noise: float) -> float | None:
    radius = 12
    patch = image[y - radius : y + radius + 1, x - radius : x + radius + 1].astype(float)
    border = np.concatenate(
        (patch[:2].ravel(), patch[-2:].ravel(), patch[:, :2].ravel(), patch[:, -2:].ravel())
    )
    background = float(np.median(border))
    local_noise = max(1.0, 1.4826 * float(np.median(np.abs(border - background))), frame_noise)
    significant = patch > background + 4 * local_noise
    cy, cx = radius, radius
    footprint = significant[cy - 2 : cy + 3, cx - 2 : cx + 3]
    if int(np.count_nonzero(footprint)) < 4:
        return None
    yy, xx = np.mgrid[-radius : radius + 1, -radius : radius + 1]
    aperture = np.hypot(yy, xx) <= radius
    weights = np.maximum(patch - background - local_noise, 0) * aperture
    if float(weights.sum()) <= 0:
        return None
    centroid_y = float((weights * yy).sum() / weights.sum())
    centroid_x = float((weights * xx).sum() / weights.sum())
    distances = np.hypot(yy - centroid_y, xx - centroid_x).ravel()
    flattened = weights.ravel()
    order = np.argsort(distances)
    cumulative = np.cumsum(flattened[order])
    index = int(np.searchsorted(cumulative, cumulative[-1] / 2))
    hfr = float(distances[order][min(index, len(order) - 1)])
    return hfr if 0.6 <= hfr <= radius * 0.9 else None


def _number(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None
