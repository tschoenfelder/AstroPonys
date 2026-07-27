"""Standalone autofocus-frame usability and optimal-focus estimation."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import numpy as np
from astropy.io import fits
from scipy import ndimage as ndi


@dataclass(frozen=True)
class AutofocusFrame:
    path: Path
    focus_position: float | None
    usable: bool
    rejection_reasons: tuple[str, ...]
    detected_peaks: int
    measured_stars: int
    median_hfr_px: float | None
    source_kind: str = "none"
    center_x_px: float | None = None
    center_y_px: float | None = None
    ring_radius_px: float | None = None
    ring_thickness_fwhm_px: float | None = None
    equivalent_hfd_px: float | None = None

    @property
    def focus_metric_hfd_px(self) -> float | None:
        """Return the diameter metric consumed by the focus-curve service."""
        if self.equivalent_hfd_px is not None:
            return self.equivalent_hfd_px
        if self.median_hfr_px is not None:
            return 2 * self.median_hfr_px
        return None


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
    donut_frames = [
        frame
        for frame in frames
        if frame.source_kind == "donut"
        and frame.center_x_px is not None
        and frame.center_y_px is not None
        and frame.ring_radius_px is not None
    ]
    if donut_frames:
        rough_x = float(np.median([frame.center_x_px for frame in donut_frames]))
        rough_y = float(np.median([frame.center_y_px for frame in donut_frames]))
        rough_radius = float(np.median([frame.ring_radius_px for frame in donut_frames]))
        common_x, common_y, common_radius = _refine_common_donut_geometry(
            [frame.path for frame in donut_frames], rough_x, rough_y, rough_radius
        )
        refined: list[AutofocusFrame] = []
        for frame in frames:
            if frame.source_kind != "donut":
                refined.append(frame)
                continue
            metrics = _measure_donut_at(frame.path, common_x, common_y, common_radius)
            refined.append(
                replace(
                    frame,
                    usable=metrics is not None,
                    rejection_reasons=() if metrics else ("DONUT_PROFILE_NOT_MEASURABLE",),
                    median_hfr_px=metrics[2] / 2 if metrics else None,
                    center_x_px=common_x,
                    center_y_px=common_y,
                    ring_radius_px=metrics[0] if metrics else None,
                    ring_thickness_fwhm_px=metrics[1] if metrics else None,
                    equivalent_hfd_px=metrics[2] if metrics else None,
                )
            )
        frames = tuple(refined)
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
    donut = _rough_donut(image)
    hfrs: list[float] = []
    for y, x in candidates:
        hfr = _stellar_hfr(image, int(y), int(x), noise)
        if hfr is not None:
            hfrs.append(hfr)
    if len(hfrs) >= minimum_stars:
        return AutofocusFrame(
            path=path,
            focus_position=position,
            usable=position is not None and not reasons,
            rejection_reasons=tuple(reasons),
            detected_peaks=len(candidates),
            measured_stars=len(hfrs),
            median_hfr_px=float(np.median(hfrs)),
            source_kind="stellar",
        )
    if donut is not None:
        center_x, center_y, approximate_radius = donut
        metrics = _measure_donut_array(image, center_x, center_y, approximate_radius)
        return AutofocusFrame(
            path=path,
            focus_position=position,
            usable=position is not None and metrics is not None,
            rejection_reasons=tuple(reasons)
            if metrics is not None
            else ("DONUT_PROFILE_NOT_MEASURABLE",),
            detected_peaks=len(candidates),
            measured_stars=1 if metrics is not None else 0,
            median_hfr_px=metrics[2] / 2 if metrics else None,
            source_kind="donut",
            center_x_px=center_x,
            center_y_px=center_y,
            ring_radius_px=metrics[0] if metrics else None,
            ring_thickness_fwhm_px=metrics[1] if metrics else None,
            equivalent_hfd_px=metrics[2] if metrics else None,
        )
    if len(candidates) == 0:
        reasons.append("NO_SIGNIFICANT_PEAKS")
    if candidates.size and len(hfrs) == 0:
        reasons.append("PEAKS_ARE_NOT_EXTENDED_STARS")
    if 0 < len(hfrs) < minimum_stars:
        reasons.append(f"TOO_FEW_MEASURABLE_STARS: {len(hfrs)} < {minimum_stars}")
    return AutofocusFrame(
        path=path,
        focus_position=position,
        usable=False,
        rejection_reasons=tuple(reasons),
        detected_peaks=len(candidates),
        measured_stars=len(hfrs),
        median_hfr_px=float(np.median(hfrs)) if hfrs else None,
        source_kind="stellar" if hfrs else "none",
    )


def fit_focus_curve(frames: tuple[AutofocusFrame, ...]) -> AutofocusResult:
    usable = [frame for frame in frames if frame.usable]
    reasons: list[str] = []
    if len(usable) < 5:
        reasons.append(f"TOO_FEW_USABLE_FRAMES: {len(usable)} < 5")
    positions = np.asarray([frame.focus_position for frame in usable], dtype=float)
    hfd = np.asarray([frame.focus_metric_hfd_px for frame in usable], dtype=float)
    if len(np.unique(positions)) < 5:
        reasons.append("TOO_FEW_DISTINCT_FOCUS_POSITIONS")
    if reasons:
        return AutofocusResult(frames, None, None, None, "insufficient-data", tuple(reasons), 0)

    coefficients = np.polyfit(positions, hfd, 2)
    predicted = np.polyval(coefficients, positions)
    residual = float(np.sum((hfd - predicted) ** 2))
    total = float(np.sum((hfd - np.mean(hfd)) ** 2))
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


def _rough_donut(image: np.ndarray) -> tuple[float, float, float] | None:
    factor = 4
    height = image.shape[0] // factor * factor
    width = image.shape[1] // factor * factor
    small = (
        image[:height, :width]
        .reshape(height // factor, factor, width // factor, factor)
        .mean(axis=(1, 3))
    )
    bandpass = ndi.gaussian_filter(small, 2) - ndi.gaussian_filter(small, 30)
    median = float(np.median(bandpass))
    noise = max(0.01, 1.4826 * float(np.median(np.abs(bandpass - median))))
    labels, _ = ndi.label(bandpass > median + 2.5 * noise)
    best: tuple[float, float, float, float] | None = None
    for label_id, slices in enumerate(ndi.find_objects(labels), start=1):
        if slices is None:
            continue
        component = labels[slices] == label_id
        area = int(np.count_nonzero(component))
        component_height, component_width = component.shape
        if area < 500 or component_height < 30 or component_width < 30:
            continue
        mask = labels == label_id
        weights = np.maximum(bandpass - median, 0) * mask
        center_y, center_x = ndi.center_of_mass(weights)
        score = float(weights.sum())
        approximate_radius = 0.43 * max(component_height, component_width) * factor
        candidate = (
            score,
            float(center_x * factor),
            float(center_y * factor),
            float(approximate_radius),
        )
        if best is None or candidate[0] > best[0]:
            best = candidate
    return (best[1], best[2], best[3]) if best else None


def _measure_donut_at(
    path: Path, center_x: float, center_y: float, expected_radius: float
) -> tuple[float, float, float] | None:
    with fits.open(path, mode="readonly", memmap=False) as hdus:
        image = np.asarray(hdus[0].data, dtype=np.float32)
    return _measure_donut_array(image, center_x, center_y, expected_radius)


def _refine_common_donut_geometry(
    paths: list[Path], rough_x: float, rough_y: float, rough_radius: float
) -> tuple[float, float, float]:
    factor = 4
    small_frames: list[np.ndarray] = []
    for path in paths:
        with fits.open(path, mode="readonly", memmap=False) as hdus:
            image = np.asarray(hdus[0].data, dtype=np.float32)
        height = image.shape[0] // factor * factor
        width = image.shape[1] // factor * factor
        small = (
            image[:height, :width]
            .reshape(height // factor, factor, width // factor, factor)
            .mean(axis=(1, 3))
        )
        small_frames.append(small - np.median(small))
    combined = np.median(np.stack(small_frames), axis=0)
    yy, xx = np.indices(combined.shape)
    expected_index = rough_radius / factor
    radius_low = max(5, round(expected_index * 0.70))
    radius_high = min(round(expected_index * 1.30) + 1, min(combined.shape) // 2)
    best: tuple[float, int, int, int] | None = None
    centre_x = round(rough_x / factor)
    centre_y = round(rough_y / factor)
    for candidate_y in range(centre_y - 8, centre_y + 9, 2):
        for candidate_x in range(centre_x - 8, centre_x + 9, 2):
            radial_index = np.rint(np.hypot(yy - candidate_y, xx - candidate_x)).astype(np.int32)
            counts = np.bincount(radial_index.ravel(), minlength=radius_high + 30)
            sums = np.bincount(
                radial_index.ravel(),
                weights=combined.ravel(),
                minlength=radius_high + 30,
            )
            profile = sums / np.maximum(counts, 1)
            residual = ndi.gaussian_filter1d(profile, 1.5) - ndi.gaussian_filter1d(profile, 12)
            radius = int(np.argmax(residual[radius_low:radius_high]) + radius_low)
            candidate = (float(residual[radius]), candidate_y, candidate_x, radius)
            if best is None or candidate[0] > best[0]:
                best = candidate
    if best is None:
        return rough_x, rough_y, rough_radius
    return float(best[2] * factor), float(best[1] * factor), float(best[3] * factor)


def _measure_donut_array(
    image: np.ndarray, center_x: float, center_y: float, expected_radius: float
) -> tuple[float, float, float] | None:
    factor = 2
    small = image[::factor, ::factor]
    yy, xx = np.indices(small.shape)
    radial_index = np.rint(np.hypot(yy - center_y / factor, xx - center_x / factor)).astype(
        np.int32
    )
    maximum_radius = min(400, int(min(small.shape) / 2))
    counts = np.bincount(radial_index.ravel(), minlength=maximum_radius + 1)
    sums = np.bincount(radial_index.ravel(), weights=small.ravel(), minlength=maximum_radius + 1)
    profile = sums[:maximum_radius] / np.maximum(counts[:maximum_radius], 1)
    residual = ndi.gaussian_filter1d(profile, 3) - ndi.gaussian_filter1d(profile, 25)
    expected_index = expected_radius / factor
    low = max(10, round(expected_index * 0.70))
    high = min(len(residual), round(expected_index * 1.30) + 1)
    if high <= low:
        return None
    peak_index = int(np.argmax(residual[low:high]) + low)
    peak = float(residual[peak_index])
    if peak < 1.0:
        return None
    left = peak_index
    right = peak_index
    while left > 1 and residual[left] >= peak / 2:
        left -= 1
    while right < len(residual) - 1 and residual[right] >= peak / 2:
        right += 1
    radial_signal = np.maximum(residual, 0) * np.arange(len(residual))
    radial_signal[:low] = 0
    radial_signal[high:] = 0
    total = float(radial_signal.sum())
    if total <= 0:
        return None
    half_flux_radius = int(np.searchsorted(np.cumsum(radial_signal), total / 2))
    ring_radius = float(factor * peak_index)
    thickness = float(factor * (right - left))
    equivalent_hfd = float(2 * factor * half_flux_radius)
    return ring_radius, thickness, equivalent_hfd


def _number(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None
