import json
from pathlib import Path

import pytest

from astroponys.cli import EXIT_FAILURE, EXIT_SUCCESS, EXIT_WARNING, main
from tests.helpers import write_config, write_focus_fits


@pytest.mark.requirement("REQ-CLI-001")
def test_focus_offset_cli_creates_complete_immutable_run(tmp_path: Path) -> None:
    write_config(tmp_path)
    for cycle in range(5):
        minute = cycle * 4
        write_focus_fits(tmp_path / f"{minute:03}-l.fits", minute, "Luminance", 1000 + minute)
        write_focus_fits(tmp_path / f"{minute + 1:03}-r.fits", minute + 1, "Red", 1051 + minute)
        write_focus_fits(tmp_path / f"{minute + 2:03}-g.fits", minute + 2, "Green", 1042 + minute)
        write_focus_fits(
            tmp_path / f"{minute + 3:03}-l.fits", minute + 3, "Luminance", 1003 + minute
        )

    assert main(["focus-offset", "analyse", str(tmp_path)]) == EXIT_SUCCESS
    runs = list((tmp_path / "astroponys-output" / "focus-offset").iterdir())
    assert len(runs) == 1
    run = runs[0]
    assert {path.name for path in run.iterdir()} == {
        "manifest.json",
        "report.md",
        "offsets.csv",
        "contact-sheet.png",
    }
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "success"
    assert manifest["estimates"]["Red"]["offset_median"] == pytest.approx(50)
    assert len(manifest["inputs"]) == 20


@pytest.mark.requirement("REQ-SAFETY-002")
def test_rerun_creates_a_second_run(tmp_path: Path) -> None:
    write_config(tmp_path)
    write_focus_fits(tmp_path / "l1.fits", 0, "Luminance", 1000)
    write_focus_fits(tmp_path / "r.fits", 1, "Red", 1050)
    write_focus_fits(tmp_path / "l2.fits", 2, "Luminance", 1000)
    assert main(["focus-offset", "analyse", str(tmp_path)]) == EXIT_SUCCESS
    assert main(["focus-offset", "analyse", str(tmp_path)]) == EXIT_SUCCESS
    runs = list((tmp_path / "astroponys-output" / "focus-offset").iterdir())
    assert len(runs) == 2


@pytest.mark.requirement("REQ-CLI-002")
def test_cli_returns_warning_for_unbracketed_focus_sample(tmp_path: Path) -> None:
    write_config(tmp_path)
    write_focus_fits(tmp_path / "r.fits", 0, "Red", 1050)
    write_focus_fits(tmp_path / "l1.fits", 1, "Luminance", 1000)
    write_focus_fits(tmp_path / "l2.fits", 2, "Luminance", 1001)
    assert main(["focus-offset", "analyse", str(tmp_path)]) == EXIT_WARNING


@pytest.mark.requirement("REQ-CLI-002")
def test_cli_returns_failure_without_config(tmp_path: Path) -> None:
    assert main(["focus-offset", "analyse", str(tmp_path)]) == EXIT_FAILURE
    assert not (tmp_path / "astroponys-output").exists()
