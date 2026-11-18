"""Native-grid raw stellar measurements. No filesystem or presentation side effects."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from pathlib import PurePath
from typing import Any

import numpy as np
from numpy.typing import NDArray
from scipy.ndimage import gaussian_filter, label, maximum_filter
from scipy.optimize import least_squares

from .config import DEFAULT_HEADER_ALIASES

ImageArray = NDArray[np.float64]
Record = dict[str, Any]
METHOD = "METHOD-RAWQA-001"
ALIASES = {
    **DEFAULT_HEADER_ALIASES,
    "frame_type": ("IMAGETYP", "FRAME"),
    "gain_mode": ("GAINMODE",),
    "bin_mode": ("BINMODE",),
    "readout_mode": ("READMODE", "RESMODE"),
    "session": ("SESSIONID", "SESSION"),
    "frame_role": ("FRAMEROLE", "OBSTYPE"),
}
NUMERIC = {
    "bin_x",
    "bin_y",
    "gain",
    "offset",
    "exposure_seconds",
    "focus_position",
    "sensor_temperature_c",
}
FACT = math.sqrt(8 * math.log(2))


def finite(value: Any) -> float | None:
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def image_scale(h: Mapping[str, Any]) -> tuple[float | None, str]:
    def pair(a: Any, b: Any, to_arcsec: float, key: str) -> tuple[float, str] | None:
        x, y = finite(a), finite(b)
        if x is None or y is None or x == 0 or y == 0:
            return None
        if not math.isclose(abs(x), abs(y), rel_tol=0.01):
            return (0.0, "anisotropic:" + key)
        return ((abs(x) + abs(y)) * 0.5 * to_arcsec, key)

    tests: list[tuple[Any, Any, float, str]] = []
    if str(h.get("CTYPE1", "")).startswith("RA"):
        units = (
            str(h.get("CUNIT1", "deg")).strip().lower(),
            str(h.get("CUNIT2", "deg")).strip().lower(),
        )
        if units == ("deg", "deg"):
            cd = [finite(h.get(k)) for k in ("CD1_1", "CD1_2", "CD2_1", "CD2_2")]
            if all(c is not None for c in cd):
                c = [float(x) for x in cd if x is not None]
                tests.append((math.hypot(c[0], c[2]), math.hypot(c[1], c[3]), 3600, "WCS:CD"))
            elif not any(k.startswith("PC") and "_" in k for k in h):
                tests.append((h.get("CDELT1"), h.get("CDELT2"), 3600, "WCS:CDELT"))
    tests += [
        (h.get("SECPIX1"), h.get("SECPIX2"), 1, "header:SECPIX"),
        (h.get("SCALE"), h.get("SCALE"), 1, "header:SCALE"),
    ]
    for x, y, unitscale, name in tests:
        val = pair(x, y, unitscale, name)
        if val:
            return val[0] or None, val[1]
    x, y, fl = (finite(h.get(k)) for k in ("XPIXSZ", "YPIXSZ", "FOCALLEN"))
    if x is None:
        pix, binning = finite(h.get("PIXSIZE1")), finite(h.get("XBINNING"))
        x = pix * binning if pix and binning else None
    if y is None:
        pix, binning = finite(h.get("PIXSIZE2")), finite(h.get("YBINNING"))
        y = pix * binning if pix and binning else None
    val = pair(x, y, 206.264806 / fl, "header:pixel_size/focal_length") if fl and fl > 0 else None
    return (val[0] or None, val[1]) if val else (None, "unknown")


def metadata(
    h: Mapping[str, Any], path: PurePath, aliases: Mapping[str, tuple[str, ...]] | None = None
) -> Record:
    result: Record = {}
    sources: dict[str, str] = {}
    for field, keys in {**ALIASES, **(aliases or {})}.items():
        result[field] = None
        for key in keys:
            raw = h.get(key)
            value = (
                finite(raw) if field in NUMERIC else (str(raw).strip() if raw is not None else None)
            )
            if value is None or value == "":
                continue
            if field in {"bin_x", "bin_y"} and (
                not isinstance(value, float) or value < 1 or not value.is_integer()
            ):
                continue
            result[field] = value
            sources[field] = "header:" + key
            break
    parts = re.split(r"[^a-z0-9]+", "/".join(path.parts).lower())
    for field, options in (
        ("gain_mode", {"hcg", "lcg", "hdr"}),
        ("bin_mode", {"sum", "avg"}),
        ("frame_type", {"light", "bias", "dark", "flat"}),
    ):
        matched = options.intersection(parts)
        if result[field] is None and len(matched) == 1:
            result[field] = matched.pop().upper()
            sources[field] = "path:token"
    bins = re.search(r"(?i)(?:^|[^a-z0-9])bin[_-]?(\d+)x(\d+)(?!\d)", "/".join(path.parts))
    if bins:
        for i, field in enumerate(("bin_x", "bin_y"), 1):
            if result[field] is None and int(bins[i]) > 0:
                result[field] = int(bins[i])
                sources[field] = "path:binNxM"
    for k in ("gain_mode", "bin_mode"):
        if result[k] is not None:
            result[k] = result[k].upper()
    frame = str(result["frame_type"] or "").lower()
    result["frame_type"] = frame.removesuffix(" frame") or None
    role = str(result["frame_role"] or "").lower()
    if role in {"focus", "autofocus"} or result["frame_type"] == "focus":
        result["frame_role"] = "autofocus"
        if result["frame_type"] in {None, "focus"}:
            result["frame_type"] = "light"
            sources["frame_type"] = sources.get("frame_type", sources.get("frame_role", "header"))
    elif role in {"science", "object"}:
        result["frame_role"] = "science"
    elif any(x in {"autofocus", "focus"} or re.fullmatch(r"autofocus\d+", x) for x in parts):
        result["frame_role"] = "autofocus"
        sources["frame_role"] = "path:focus"
        if result["frame_type"] is None:
            result["frame_type"] = "light"
            sources["frame_type"] = "path:focus"
    else:
        result["frame_role"] = "unknown"
    result["pixel_scale_arcsec"], sources["pixel_scale_arcsec"] = image_scale(h)
    result["sources"] = sources
    return result


def ceiling_for(meta: Record, rules: list[Record]) -> float | None:
    matches: list[tuple[int, float]] = []
    keys = ("camera", "gain_mode", "bin_mode", "bin_x", "bin_y", "readout_mode", "gain", "offset")
    for rule in rules:
        if not rule.get("camera") or set(rule) - {*keys, "ceiling_adu"}:
            raise ValueError("Clipping rules require a camera and supported selector keys")
        cap = finite(rule.get("ceiling_adu"))
        if cap is None or cap <= 0:
            raise ValueError("ceiling_adu must be positive and finite")
        selectors = [(k, v) for k, v in rule.items() if k in keys]

        def equal(k: str, v: Any) -> bool:
            found = meta.get(k)
            if found is None:
                return False
            if k in NUMERIC:
                return finite(found) == finite(v)
            return str(found).casefold() == str(v).casefold()

        if all(equal(k, v) for k, v in selectors):
            matches.append((len(selectors), cap))
    if not matches:
        return None
    specificity = max(s for s, _ in matches)
    limits = {c for s, c in matches if s == specificity}
    if len(limits) != 1:
        raise ValueError("Conflicting equally specific clipping rules")
    return limits.pop()


def noise(values: ImageArray) -> float:
    return max(1e-6, float(1.4826 * np.median(np.abs(values - np.median(values)))))


def profile(
    patch: ImageArray, radius: float, sigma: float, background: float, rms: float
) -> tuple[float, ...] | None:
    r = patch.shape[0] // 2
    y, x = np.mgrid[-r : r + 1, -r : r + 1]
    mask = np.hypot(x, y) <= radius
    amplitude = float(np.max(patch[mask]) - background)
    if amplitude < 8 * rms:
        return None

    def residual(p: ImageArray) -> ImageArray:
        b, gx, gy, a, cx, cy, sx, sy, t = p
        u, v = x - cx, y - cy
        c, s = np.cos(t), np.sin(t)
        model = (
            b
            + gx * x
            + gy * y
            + a * np.exp(-0.5 * (((u * c + v * s) / sx) ** 2 + ((-u * s + v * c) / sy) ** 2))
        )
        return np.asarray((model - patch)[mask], dtype=np.float64)

    q = least_squares(
        residual,
        [background, 0, 0, amplitude, 0, 0, 1.4 * sigma, 1.4 * sigma, 0],
        bounds=(
            [-np.inf, -np.inf, -np.inf, 0, -3, -3, 0.35, 0.35, -5],
            [np.inf, np.inf, np.inf, np.inf, 3, 3, radius, radius, 5],
        ),
        max_nfev=90,
    )
    _, _, _, amp, cx, cy, sx, sy, _ = q.x
    if (
        not q.success
        or amp < 8 * rms
        or min(sx, sy) <= 0.43
        or min(sx, sy) / max(sx, sy) < 0.35
        or max(abs(cx), abs(cy)) >= 2.8
        or max(sx, sy) > radius * 0.72
    ):
        return None
    major, minor = sorted((FACT * sx, FACT * sy), reverse=True)
    if float(np.sqrt(np.mean(q.fun**2))) > max(4 * rms, 0.15 * amp):
        return None
    return float(cx), float(cy), float(major), float(minor)


def measure(im: ImageArray, cap: float | None, scale: float | None) -> Record:
    if im.ndim != 2 or min(im.shape) < 19 or not np.isfinite(im).all():
        raise ValueError("Expected a finite two-dimensional image of at least 19×19 pixels")
    rough = gaussian_filter(im, 0.85) - gaussian_filter(im, 6)
    broad = gaussian_filter(im, 3) - gaussian_filter(im, 12)
    sample = im[:: max(1, im.shape[0] // 400), :: max(1, im.shape[1] // 400)]
    bg_global = float(np.median(sample))
    rms_global = noise(sample)
    high = float(np.max(im))
    candidate_level = bg_global + 0.97 * (high - bg_global)
    xy = np.argwhere(
        ((rough == maximum_filter(rough, 9)) & (rough > 4 * noise(rough[::5, ::5])))
        | ((broad == maximum_filter(broad, 19)) & (broad > 4 * noise(broad[::5, ::5])))
    )
    ranked = sorted(xy.tolist(), key=lambda p: -float(max(rough[*p], broad[*p])))
    truncated = len(ranked) > 4000
    used: list[tuple[int, int]] = []
    stars: list[Record] = []
    saturated: list[Record] = []
    candidates: list[Record] = []
    pending: list[tuple[float, int, int, int, float, float, ImageArray, float, float]] = []
    for y, x in ranked[:4000]:
        if min(y, x, im.shape[0] - 1 - y, im.shape[1] - 1 - x) < 9:
            continue
        yy, xx = np.mgrid[-9:10, -9:10]
        patch = im[y - 9 : y + 10, x - 9 : x + 10]
        local = patch[(np.hypot(xx, yy) >= 7)]
        bg = float(np.median(local))
        rms = max(noise(local), rms_global * 0.25)
        core = patch[7:12, 7:12]
        peak = float(np.max(core))
        if np.count_nonzero(core - bg > 5 * rms) < 4:
            continue
        if any((y - uy) ** 2 + (x - ux) ** 2 <= 25 for uy, ux in used):
            continue
        used.append((y, x))
        core_peak = (core == peak).astype(np.uint8)
        labels, n = label(core_peak)
        connected = np.bincount(labels.ravel())[1:].max() if n else 0
        loc = {"x": x, "y": y, "peak_adu": peak}
        if cap is not None and peak >= cap:
            saturated.append(loc)
            continue
        if cap is None and peak >= candidate_level and connected >= 3 and peak - bg > 20 * rms:
            candidates.append(loc)
            continue
        sigma = 3.0 if broad[y, x] > 0.44 * rough[y, x] else 1.0
        r = min(26 if sigma > 1 else 9, y, x, im.shape[0] - 1 - y, im.shape[1] - 1 - x)
        stamp = im[y - r : y + r + 1, x - r : x + r + 1]
        y0, x0 = np.mgrid[-r : r + 1, -r : r + 1]
        d = np.hypot(x0, y0)
        inner = 5 if sigma == 1 else min(18, r - 4)
        outer = stamp[d >= max(inner + 2, r * 0.75)]
        sky = float(np.median(outer))
        flux = float(np.sum(stamp[d <= inner] - sky))
        pending.append(
            (flux, y, x, r, sigma, peak, stamp, sky, max(noise(outer), rms_global * 0.25))
        )
    pending.sort(key=lambda p: (-p[0], p[1], p[2]))
    for flux, y, x, r, sigma, peak, stamp, sky, rms in pending:
        fit = profile(stamp, min(r - 1, 5.5 if sigma == 1 else 23), sigma, sky, rms)
        if fit is None:
            continue
        cx, cy, ma, mi = fit
        scalar = math.sqrt(ma * mi)
        stars.append(
            {
                "id": len(stars) + 1,
                "x": x + cx,
                "y": y + cy,
                "flux_adu": flux,
                "peak_adu": peak,
                "major_px": ma,
                "minor_px": mi,
                "fwhm_px": scalar,
                "major_arcsec": ma * scale if scale else None,
                "minor_arcsec": mi * scale if scale else None,
                "fwhm_arcsec": scalar * scale if scale else None,
            }
        )
        if len(stars) == 5:
            break
    return {
        "stars": stars,
        "clipped_stars": len(saturated) if cap is not None and not truncated else None,
        "clipped_cores": saturated,
        "clipping_candidates": candidates,
        "ceiling_adu": cap,
        "candidate_limit_reached": truncated,
        "max_adu": high,
    }
