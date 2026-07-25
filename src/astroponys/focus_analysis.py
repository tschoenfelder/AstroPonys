"""Drift-aware filter focus-offset measurement."""

from __future__ import annotations

import random
import statistics
from collections import defaultdict
from datetime import datetime

from .models import ConfidenceBreakdown, FilterEstimate, FitsRecord, FocusSample


class FocusAnalysisError(ValueError):
    """Raised when the focus session cannot support an offset analysis."""


def analyse_focus_offsets(
    records: list[FitsRecord], reference_filter: str
) -> tuple[dict[str, FilterEstimate], tuple[str, ...]]:
    usable = [
        record
        for record in records
        if record.observed_at is not None
        and record.filter_name is not None
        and record.focus_position is not None
    ]
    references = [r for r in usable if _same_filter(r.filter_name, reference_filter)]
    if not references:
        raise FocusAnalysisError(f"No usable reference frames for filter {reference_filter!r}")
    references.sort(key=lambda record: _timestamp(record.observed_at))

    grouped: dict[str, list[FocusSample]] = defaultdict(list)
    warnings: list[str] = []
    for record in usable:
        if _same_filter(record.filter_name, reference_filter):
            continue
        filter_name = record.filter_name
        if filter_name is None:
            continue
        baseline, method, before, after = _baseline(record, references)
        if method != "interpolated":
            warnings.append(f"{record.path.name}: baseline {method}; drift correction is limited")
        grouped[filter_name].append(
            FocusSample(
                path=record.path,
                filter_name=filter_name,
                observed_at=_required_datetime(record.observed_at),
                focus_position=_required_float(record.focus_position),
                baseline_position=baseline,
                offset=_required_float(record.focus_position) - baseline,
                baseline_method=method,
                before_reference=before.path if before else None,
                after_reference=after.path if after else None,
            )
        )

    estimates = {
        name: _estimate(name, tuple(samples))
        for name, samples in sorted(grouped.items(), key=lambda item: item[0].casefold())
    }
    if not estimates:
        raise FocusAnalysisError("No non-reference focus samples were found")
    return estimates, tuple(dict.fromkeys(warnings))


def _baseline(
    sample: FitsRecord, references: list[FitsRecord]
) -> tuple[float, str, FitsRecord | None, FitsRecord | None]:
    sample_time = _timestamp(sample.observed_at)
    before = next(
        (r for r in reversed(references) if _timestamp(r.observed_at) <= sample_time), None
    )
    after = next((r for r in references if _timestamp(r.observed_at) >= sample_time), None)
    if before is not None and after is not None and before is not after:
        before_time = _timestamp(before.observed_at)
        after_time = _timestamp(after.observed_at)
        fraction = (sample_time - before_time) / (after_time - before_time)
        before_focus = _required_float(before.focus_position)
        after_focus = _required_float(after.focus_position)
        return (
            before_focus + fraction * (after_focus - before_focus),
            "interpolated",
            before,
            after,
        )
    nearest = before or after
    if nearest is None:
        raise FocusAnalysisError("Internal error: reference list unexpectedly empty")
    return _required_float(nearest.focus_position), "nearest", before, after


def _estimate(filter_name: str, samples: tuple[FocusSample, ...]) -> FilterEstimate:
    values = [sample.offset for sample in samples]
    centre = float(statistics.median(values))
    mad = float(statistics.median(abs(value - centre) for value in values))
    interval = _bootstrap_median_interval(values) if len(values) >= 5 else None
    outlier_indices = _outlier_indices(values, centre, mad)
    outlier_paths = tuple(samples[index].path for index in outlier_indices)
    warnings: list[str] = []
    if len(values) < 5:
        warnings.append("Fewer than five samples: 95% bootstrap interval not estimated")
    if mad > 10:
        warnings.append("High offset dispersion; inspect autofocus repeatability and drift")
    if outlier_paths:
        warnings.append(
            f"{len(outlier_paths)} influential outlier candidate(s) flagged but retained"
        )
    confidence = _confidence(samples, mad, interval is not None)
    return FilterEstimate(
        filter_name=filter_name,
        sample_count=len(samples),
        offset_median=centre,
        mad=mad,
        interval_95=interval,
        interval_method="deterministic percentile bootstrap of median, 10000 resamples"
        if interval
        else None,
        samples=samples,
        outlier_paths=outlier_paths,
        outlier_method=(
            "absolute deviation > 3.5 x scaled MAD; non-median values when MAD is zero"
            if len(values) >= 5
            else None
        ),
        confidence=confidence,
        warnings=tuple(warnings),
    )


def _outlier_indices(values: list[float], centre: float, mad: float) -> tuple[int, ...]:
    if len(values) < 5:
        return ()
    if mad == 0:
        return tuple(index for index, value in enumerate(values) if value != centre)
    threshold = 3.5 * 1.4826 * mad
    return tuple(index for index, value in enumerate(values) if abs(value - centre) > threshold)


def _bootstrap_median_interval(values: list[float]) -> tuple[float, float]:
    rng = random.Random(7307635)
    medians = sorted(statistics.median(rng.choices(values, k=len(values))) for _ in range(10_000))
    return float(medians[249]), float(medians[9749])


def _confidence(
    samples: tuple[FocusSample, ...], mad: float, has_interval: bool
) -> ConfidenceBreakdown:
    count = len(samples)
    interpolated = sum(sample.baseline_method == "interpolated" for sample in samples)
    method_evidence = 20 if interpolated == count else 15
    data_quality = min(25, 5 + count * 4)
    repeatability = max(0, 20 - min(20, round(mad)))
    test_coverage = 12
    model_fit = round(10 * interpolated / count) if count else 0
    platform_validation = 3
    if not has_interval:
        data_quality = min(data_quality, 20)
    return ConfidenceBreakdown(
        method_evidence=method_evidence,
        data_quality=data_quality,
        repeatability=repeatability,
        test_coverage=test_coverage,
        model_fit=model_fit,
        platform_validation=platform_validation,
    )


def _same_filter(left: str | None, right: str) -> bool:
    return left is not None and left.casefold() == right.casefold()


def _timestamp(value: datetime | None) -> float:
    return _required_datetime(value).timestamp()


def _required_datetime(value: datetime | None) -> datetime:
    if value is None:
        raise FocusAnalysisError("Internal error: missing observation time")
    return value


def _required_float(value: float | None) -> float:
    if value is None:
        raise FocusAnalysisError("Internal error: missing focus position")
    return value
