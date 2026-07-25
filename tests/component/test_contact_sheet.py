from pathlib import Path

import pytest
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
