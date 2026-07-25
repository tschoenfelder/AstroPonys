"""Shared immutable records used by the Sprint 1 vertical slice."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class FitsRecord:
    path: Path
    size: int
    mtime_ns: int
    observed_at: datetime | None
    filter_name: str | None
    focus_position: float | None
    exposure_seconds: float | None
    camera: str | None
    gain: float | None
    offset: float | None
    binning: str | None
    sensor_temperature_c: float | None
    target: str | None
    warnings: tuple[str, ...] = ()
    header_sources: dict[str, str] = field(default_factory=dict)

    def identity(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "size": self.size,
            "mtime_ns": self.mtime_ns,
        }


@dataclass(frozen=True)
class FocusSample:
    path: Path
    filter_name: str
    observed_at: datetime
    focus_position: float
    baseline_position: float
    offset: float
    baseline_method: str
    before_reference: Path | None
    after_reference: Path | None


@dataclass(frozen=True)
class ConfidenceBreakdown:
    method_evidence: int
    data_quality: int
    repeatability: int
    test_coverage: int
    model_fit: int
    platform_validation: int

    @property
    def total(self) -> int:
        return sum(
            (
                self.method_evidence,
                self.data_quality,
                self.repeatability,
                self.test_coverage,
                self.model_fit,
                self.platform_validation,
            )
        )


@dataclass(frozen=True)
class FilterEstimate:
    filter_name: str
    sample_count: int
    offset_median: float
    mad: float
    interval_95: tuple[float, float] | None
    interval_method: str | None
    samples: tuple[FocusSample, ...]
    confidence: ConfidenceBreakdown
    warnings: tuple[str, ...] = ()
