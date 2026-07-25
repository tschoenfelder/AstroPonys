"""Human- and machine-readable Sprint 1 reports."""

from __future__ import annotations

import csv
from pathlib import Path

from .models import FilterEstimate


def write_csv(path: Path, estimates: dict[str, FilterEstimate]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "filter",
                "sample_count",
                "offset_median",
                "mad",
                "interval_95_low",
                "interval_95_high",
                "confidence_index",
                "outlier_candidates",
            ]
        )
        for estimate in estimates.values():
            interval = estimate.interval_95 or ("", "")
            writer.writerow(
                [
                    estimate.filter_name,
                    estimate.sample_count,
                    estimate.offset_median,
                    estimate.mad,
                    interval[0],
                    interval[1],
                    estimate.confidence.total,
                    len(estimate.outlier_paths),
                ]
            )


def write_markdown(
    path: Path,
    run_id: str,
    reference_filter: str,
    estimates: dict[str, FilterEstimate],
    warnings: tuple[str, ...],
) -> None:
    lines = [
        "# Filter focus-offset report",
        "",
        f"- Run ID: `{run_id}`",
        f"- Reference filter: `{reference_filter}` (offset 0)",
        "- Claim type: Statistical result",
        "- Product level: Raw measurement report",
        "",
        "| Filter | Samples | Median offset | MAD | 95% interval | Evidence confidence |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for estimate in estimates.values():
        interval = (
            f"{estimate.interval_95[0]:.2f} … {estimate.interval_95[1]:.2f}"
            if estimate.interval_95
            else "not estimable"
        )
        lines.append(
            f"| {estimate.filter_name} | {estimate.sample_count} | "
            f"{estimate.offset_median:.2f} | {estimate.mad:.2f} | {interval} | "
            f"{estimate.confidence.total}/100 |"
        )
    lines.extend(
        [
            "",
            (
                "The evidence confidence index is a rubric-based evidence-strength score, "
                "not the probability that an offset is true."
            ),
            "",
            "## Confidence components and limitations",
            "",
        ]
    )
    for estimate in estimates.values():
        confidence = estimate.confidence
        lines.extend(
            [
                f"### {estimate.filter_name}",
                "",
                f"- Method evidence: {confidence.method_evidence}/25",
                f"- Data quality: {confidence.data_quality}/25",
                f"- Repeatability: {confidence.repeatability}/20",
                f"- Test coverage: {confidence.test_coverage}/15",
                f"- Model fit: {confidence.model_fit}/10",
                f"- Platform validation: {confidence.platform_validation}/5",
            ]
        )
        lines.extend(f"- Warning: {warning}" for warning in estimate.warnings)
        if estimate.outlier_paths:
            lines.append(f"- Outlier method: {estimate.outlier_method}")
            lines.extend(
                f"- Outlier candidate retained: `{item}`" for item in estimate.outlier_paths
            )
        lines.extend(
            [
                "",
                "| Time | Focus | Baseline | Offset | Baseline method | Outlier candidate |",
                "|---|---:|---:|---:|---|---|",
            ]
        )
        outliers = set(estimate.outlier_paths)
        for sample in estimate.samples:
            lines.append(
                f"| {sample.observed_at.isoformat()} | {sample.focus_position:.2f} | "
                f"{sample.baseline_position:.2f} | {sample.offset:.2f} | "
                f"{sample.baseline_method} | {'yes' if sample.path in outliers else 'no'} |"
            )
        lines.append("")
    if warnings:
        lines.extend(["## Run warnings", ""])
        lines.extend(f"- {warning}" for warning in warnings)
        lines.append("")
    lines.extend(
        [
            "## Method",
            "",
            (
                "Each non-reference autofocus position is compared with a time-interpolated "
                "baseline from bracketing reference-filter positions when available. The "
                "per-filter estimate is the median and dispersion is the median absolute "
                "deviation. With at least five samples, the displayed exploratory interval "
                "is a deterministic percentile bootstrap interval for the median."
            ),
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
