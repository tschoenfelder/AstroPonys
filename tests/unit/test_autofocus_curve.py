from pathlib import Path

import numpy as np
import pytest
from astropy.io import fits

from astroponys.autofocus_curve import analyse_autofocus_sequence


def write_star_field(path: Path, position: int, optimum: int = 1600) -> None:
    rng = np.random.default_rng(7635 + position)
    image = rng.normal(300, 8, size=(256, 320))
    sigma = 1.2 + abs(position - optimum) / 80
    yy, xx = np.mgrid[: image.shape[0], : image.shape[1]]
    for y, x, amplitude in (
        (40, 50, 5000),
        (60, 140, 3500),
        (100, 90, 4500),
        (130, 200, 6000),
        (180, 60, 3800),
        (200, 250, 5200),
        (80, 260, 4200),
        (170, 155, 4800),
        (220, 120, 3600),
    ):
        image += amplitude * np.exp(-((yy - y) ** 2 + (xx - x) ** 2) / (2 * sigma**2))
    header = fits.Header()
    header["FOCUSPOS"] = position
    header["EXPTIME"] = 2.0
    fits.PrimaryHDU(image.astype(np.float32), header=header).writeto(path)


@pytest.mark.requirement("REQ-AUTOFOCUS-005")
def test_known_synthetic_focus_minimum_is_recovered(tmp_path: Path) -> None:
    for position in range(1500, 1701, 25):
        write_star_field(tmp_path / f"focus-{position}.fits", position)
    result = analyse_autofocus_sequence(tmp_path)
    assert result.status == "success"
    assert result.optimal_focus == pytest.approx(1600, abs=12)
    assert result.fit_r_squared is not None and result.fit_r_squared >= 0.6
    assert all(frame.usable for frame in result.frames)


@pytest.mark.requirement("REQ-AUTOFOCUS-003")
@pytest.mark.requirement("REQ-AUTOFOCUS-006")
def test_hot_pixels_are_rejected_without_inventing_optimum(tmp_path: Path) -> None:
    rng = np.random.default_rng(42)
    for index, position in enumerate(range(1500, 1550, 10)):
        image = rng.normal(300, 8, size=(128, 160)).astype(np.float32)
        image[30, 40] = 45000
        image[70, 100] = 30000
        header = fits.Header({"FOCUSPOS": position})
        fits.PrimaryHDU(image, header=header).writeto(tmp_path / f"hot-{index}.fits")
    result = analyse_autofocus_sequence(tmp_path)
    assert result.status == "insufficient-data"
    assert result.optimal_focus is None
    assert all(not frame.usable for frame in result.frames)
    assert all("PEAKS_ARE_NOT_EXTENDED_STARS" in frame.rejection_reasons for frame in result.frames)


@pytest.mark.requirement("REQ-AUTOFOCUS-004")
@pytest.mark.requirement("REQ-AUTOFOCUS-006")
def test_large_single_donut_is_measured_but_flat_curve_has_no_optimum(tmp_path: Path) -> None:
    rng = np.random.default_rng(1700)
    yy, xx = np.mgrid[:512, :640]
    for position in range(1688, 1714, 5):
        image = rng.normal(200, 6, size=(512, 640))
        radius = np.hypot(yy - 260, xx - 330)
        image += 45 * np.exp(-((radius - 105) ** 2) / (2 * 7**2))
        image[30, 40] = 45000
        header = fits.Header({"FOCUSPOS": position})
        fits.PrimaryHDU(image.astype(np.float32), header=header).writeto(
            tmp_path / f"donut-{position}.fits"
        )
    result = analyse_autofocus_sequence(tmp_path)
    assert result.optimal_focus is None
    assert result.status == "rejected-curve"
    assert all(frame.usable and frame.source_kind == "donut" for frame in result.frames)
    assert all(frame.measured_stars == 1 for frame in result.frames)
    assert all(frame.equivalent_hfd_px == pytest.approx(210, abs=20) for frame in result.frames)
