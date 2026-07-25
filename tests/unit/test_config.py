from pathlib import Path

import pytest

from astroponys.config import ConfigError, load_config
from tests.helpers import write_config


@pytest.mark.requirement("REQ-CFG-001")
def test_loads_only_adjacent_named_config(tmp_path: Path) -> None:
    write_config(tmp_path)
    loaded = load_config(tmp_path)
    assert loaded.config_path == (tmp_path / "astroponys.yaml").resolve()
    assert loaded.output_directory == (tmp_path / "astroponys-output").resolve()


@pytest.mark.requirement("REQ-CFG-003")
def test_rejects_unknown_schema(tmp_path: Path) -> None:
    (tmp_path / "astroponys.yaml").write_text("schema_version: 99\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="schema_version"):
        load_config(tmp_path)


@pytest.mark.requirement("REQ-CFG-006")
def test_rejects_output_outside_image_directory(tmp_path: Path) -> None:
    (tmp_path / "astroponys.yaml").write_text(
        "schema_version: 1\noutput:\n  directory: ../outside\n", encoding="utf-8"
    )
    with pytest.raises(ConfigError, match="child"):
        load_config(tmp_path)


@pytest.mark.requirement("REQ-CFG-003")
def test_rejects_unknown_nested_key(tmp_path: Path) -> None:
    (tmp_path / "astroponys.yaml").write_text(
        "schema_version: 1\nimages:\n  directory: .\n  surprise: true\n", encoding="utf-8"
    )
    with pytest.raises(ConfigError, match="Unknown images keys"):
        load_config(tmp_path)


@pytest.mark.requirement("REQ-CFG-004")
def test_loads_configurable_header_alias(tmp_path: Path) -> None:
    (tmp_path / "astroponys.yaml").write_text(
        "schema_version: 1\nfits:\n  header_aliases:\n    focus_position: [MYFOCUS]\n",
        encoding="utf-8",
    )
    assert load_config(tmp_path).header_aliases["focus_position"] == ("MYFOCUS",)
