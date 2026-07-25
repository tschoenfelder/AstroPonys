from pathlib import Path

import numpy as np
import pytest
from astropy.io import fits
from PIL import Image

from astroponys.config import load_config
from astroponys.contact_sheet import HEADER_HEIGHT, LABEL_HEIGHT, THUMBNAIL, render_contact_sheet
from astroponys.fits_inventory import inventory
from tests.helpers import write_config, write_focus_fits


@pytest.mark.requirement("REQ-CONTACT-001")
@pytest.mark.requirement("REQ-CONTACT-004")
def test_contact_sheet_uses_cycle_filter_grid_with_missing_placeholder(tmp_path: Path) -> None:
    write_config(tmp_path)
    write_focus_fits(tmp_path / "00-l.fits", 0, "Luminance", 1000)
    write_focus_fits(tmp_path / "01-r.fits", 1, "Red", 1050)
    write_focus_fits(tmp_path / "03-l.fits", 3, "Luminance", 1001)
    write_focus_fits(tmp_path / "04-r.fits", 4, "Red", 1051)
    write_focus_fits(tmp_path / "05-g.fits", 5, "Green", 1041)
    config = load_config(tmp_path)
    destination = tmp_path / "sheet.png"
    render_contact_sheet(
        inventory(config),
        destination,
        config.filter_order,
        config.contact_sheet_percentiles,
    )
    with Image.open(destination) as image:
        assert image.mode == "L"
        assert image.size == (
            3 * THUMBNAIL[0],
            HEADER_HEIGHT + 2 * (THUMBNAIL[1] + LABEL_HEIGHT),
        )


@pytest.mark.requirement("REQ-CONTACT-001")
def test_contact_sheet_reads_scaled_unsigned_camera_fits(tmp_path: Path) -> None:
    source = tmp_path / "unsigned.fits"
    data = np.arange(32 * 48, dtype=np.uint16).reshape(32, 48)
    header = fits.Header()
    header["DATE-OBS"] = "2026-07-25T00:00:00+00:00"
    header["FILTER"] = "Luminance"
    header["FOCUSPOS"] = 12913
    fits.PrimaryHDU(data=data, header=header).writeto(source)
    write_config(tmp_path)
    config = load_config(tmp_path)
    destination = tmp_path / "unsigned-sheet.png"
    render_contact_sheet(
        inventory(config),
        destination,
        config.filter_order,
        config.contact_sheet_percentiles,
    )
    with Image.open(destination) as image:
        thumbnail_pixels = np.asarray(
            image.crop((0, HEADER_HEIGHT, THUMBNAIL[0], HEADER_HEIGHT + THUMBNAIL[1]))
        )
        assert thumbnail_pixels.max() == 255
        assert len(np.unique(thumbnail_pixels)) > 100
