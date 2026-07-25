from pathlib import Path

import pytest

from astroponys.config import load_config
from astroponys.fits_inventory import inventory
from tests.helpers import write_config, write_focus_fits


@pytest.mark.requirement("REQ-FITS-003")
def test_inventory_normalises_headers_without_changing_source(tmp_path: Path) -> None:
    source = tmp_path / "red.fits"
    write_focus_fits(source, 1, "Red", 1050)
    write_config(tmp_path)
    before = (source.stat().st_size, source.stat().st_mtime_ns, source.read_bytes())
    records = inventory(load_config(tmp_path))
    after = (source.stat().st_size, source.stat().st_mtime_ns, source.read_bytes())
    assert len(records) == 1
    assert records[0].filter_name == "Red"
    assert records[0].focus_position == 1050
    assert records[0].binning == "1x1"
    assert before == after


@pytest.mark.requirement("REQ-FITS-004")
def test_invalid_fits_remains_visible_as_warning(tmp_path: Path) -> None:
    (tmp_path / "broken.fits").write_bytes(b"not fits")
    write_config(tmp_path)
    records = inventory(load_config(tmp_path))
    assert len(records) == 1
    assert any(warning.startswith("FITS_READ_ERROR") for warning in records[0].warnings)
