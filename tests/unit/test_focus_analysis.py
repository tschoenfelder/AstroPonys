from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from astroponys.focus_analysis import analyse_focus_offsets
from astroponys.models import FitsRecord


def record(minute: int, filter_name: str, focus: float) -> FitsRecord:
    return FitsRecord(
        path=Path(f"{minute:03}-{filter_name}.fits"),
        size=1,
        mtime_ns=1,
        observed_at=datetime(2026, 7, 25, tzinfo=UTC) + timedelta(minutes=minute),
        filter_name=filter_name,
        focus_position=focus,
        exposure_seconds=30,
        camera="ATR585M",
        gain=100,
        offset=260,
        binning="1x1",
        sensor_temperature_c=-10,
        target="NGC 7635",
    )


@pytest.mark.requirement("REQ-FOCUS-005")
def test_linear_drift_is_removed_from_offsets() -> None:
    records: list[FitsRecord] = []
    for cycle in range(5):
        start = cycle * 10
        records.extend(
            [
                record(start, "Luminance", 1000 + start),
                record(start + 3, "Red", 1050 + start + 3),
                record(start + 6, "Green", 1040 + start + 6),
                record(start + 10, "Luminance", 1000 + start + 10),
            ]
        )
    estimates, warnings = analyse_focus_offsets(records, "Luminance")
    assert estimates["Red"].offset_median == pytest.approx(50)
    assert estimates["Green"].offset_median == pytest.approx(40)
    assert estimates["Red"].interval_95 == pytest.approx((50, 50))
    assert warnings == ()


@pytest.mark.requirement("REQ-FOCUS-003")
def test_cycle_count_is_not_hardcoded() -> None:
    records = [record(0, "Luminance", 1000), record(1, "Blue", 997), record(2, "Luminance", 1000)]
    estimates, _ = analyse_focus_offsets(records, "Luminance")
    assert estimates["Blue"].sample_count == 1
    assert estimates["Blue"].offset_median == -3
    assert estimates["Blue"].interval_95 is None


@pytest.mark.requirement("REQ-FOCUS-006")
def test_edge_sample_is_retained_and_warned() -> None:
    records = [record(0, "Red", 1050), record(1, "Luminance", 1000), record(2, "Luminance", 1001)]
    estimates, warnings = analyse_focus_offsets(records, "Luminance")
    assert estimates["Red"].samples[0].baseline_method == "nearest"
    assert any("limited" in warning for warning in warnings)


@pytest.mark.requirement("REQ-FOCUS-008")
def test_influential_outlier_is_flagged_but_retained() -> None:
    records: list[FitsRecord] = []
    offsets = [50, 50, 50, 50, 110]
    for index, offset in enumerate(offsets):
        minute = index * 3
        records.extend(
            [
                record(minute, "Luminance", 1000),
                record(minute + 1, "Red", 1000 + offset),
                record(minute + 2, "Luminance", 1000),
            ]
        )
    estimates, _ = analyse_focus_offsets(records, "Luminance")
    red = estimates["Red"]
    assert red.sample_count == 5
    assert red.offset_median == 50
    assert len(red.outlier_paths) == 1
    assert red.outlier_paths[0].name == "013-Red.fits"
    assert {sample.offset for sample in red.samples} == {50, 110}
