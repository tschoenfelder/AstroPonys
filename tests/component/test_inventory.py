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


@pytest.mark.requirement("REQ-FITS-001")
def test_recursive_discovery_is_opt_in(tmp_path: Path) -> None:
    nested = tmp_path / "nested"
    nested.mkdir()
    write_focus_fits(nested / "red.fits", 1, "Red", 1050)
    write_config(tmp_path, recursive=False)
    assert inventory(load_config(tmp_path)) == []
    write_config(tmp_path, recursive=True)
    assert [record.path.name for record in inventory(load_config(tmp_path))] == ["red.fits"]


@pytest.mark.requirement("REQ-FITS-004")
def test_conflicting_alias_values_are_reported(tmp_path: Path) -> None:
    from astropy.io import fits

    source = tmp_path / "red.fits"
    write_focus_fits(source, 1, "Red", 1050)
    with fits.open(source, mode="update") as hdus:
        hdus[0].header["FOCPOS"] = 999
    write_config(tmp_path)
    record = inventory(load_config(tmp_path))[0]
    assert record.focus_position == 1050
    assert any(warning.startswith("CONFLICTING_FOCUS_POSITION") for warning in record.warnings)


@pytest.mark.requirement("REQ-FITS-006")
def test_inventory_sorts_by_observation_time_not_filename(tmp_path: Path) -> None:
    write_focus_fits(tmp_path / "a-late.fits", 9, "Red", 1050)
    write_focus_fits(tmp_path / "z-early.fits", 1, "Red", 1050)
    write_config(tmp_path)
    assert [record.path.name for record in inventory(load_config(tmp_path))] == [
        "z-early.fits",
        "a-late.fits",
    ]
