from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import numpy as np
import pytest
from astropy.io import fits
from PIL import Image

from astroponys.raw_qa import ceiling_for, image_scale, measure, metadata
from astroponys.raw_qa_worker import scan


def field() -> np.ndarray:
    y, x = np.mgrid[:200, :260]
    image = np.random.default_rng(74).normal(600, 2, x.shape)
    for j, (a, b) in enumerate(
        ((38, 42), (96, 44), (164, 42), (224, 50), (40, 142), (105, 141), (175, 148))
    ):
        amplitude = 8000 if j == 0 else 2100 - j * 150
        image += amplitude * np.exp(
            -((x - a - 0.2) ** 2 / 2 / 1.4**2 + (y - b + 0.1) ** 2 / 2 / 1.15**2)
        )
    image[160, 220] = 4095  # detector defect, not a star
    return np.clip(np.round(image), 0, 4095).astype(np.uint16)


def header(kind: str = "Light Frame") -> fits.Header:
    return fits.Header(
        {
            "IMAGETYP": kind,
            "INSTRUME": "SyntheticCam",
            "XBINNING": 2,
            "YBINNING": 2,
            "GAINMODE": "HCG",
            "BINMODE": "AVG",
            "GAIN": 100,
            "EXPTIME": 240.0,
            "FILTER": "Oiii",
            "SCALE": 0.5,
            "DATE-OBS": "2026-11-18T02:43:15",
        }
    )


def clipping() -> list[dict[str, object]]:
    return [
        {
            "camera": "SyntheticCam",
            "gain_mode": "HCG",
            "bin_mode": "AVG",
            "bin_x": 2,
            "bin_y": 2,
            "ceiling_adu": 4095,
        }
    ]


@pytest.mark.requirement("REQ-RAWQA-001")
def test_header_precedes_path_and_annotates_fallback() -> None:
    items = metadata(
        {"GAINMODE": "HDR", "FRAME": "Light"}, Path("autofocus/run_hcg_bin2x2_avg.fits")
    )
    assert items["gain_mode"] == "HDR"
    assert items["sources"]["gain_mode"] == "header:GAINMODE"
    assert items["bin_x"] == items["bin_y"] == 2
    assert items["bin_mode"] == "AVG" and items["sources"]["bin_mode"] == "path:token"
    assert items["frame_role"] == "autofocus"
    assert items["pixel_scale_arcsec"] is None
    assert metadata({}, Path("HDR/HCG/file.fits"))["gain_mode"] is None


@pytest.mark.requirement("REQ-RAWQA-002")
@pytest.mark.parametrize(
    "scale,expected",
    [
        ({"XPIXSZ": 7.6, "YPIXSZ": 7.6, "XBINNING": 2, "YBINNING": 2, "FOCALLEN": 588}, 2.666),
        ({"PIXSIZE1": 3.8, "PIXSIZE2": 3.8, "XBINNING": 2, "YBINNING": 2, "FOCALLEN": 588}, 2.666),
        ({"CTYPE1": "RA---TAN", "CDELT1": -0.0001, "CDELT2": 0.0001, "SCALE": 2}, 0.36),
    ],
)
def test_angular_scale_not_binned_twice(scale: dict[str, object], expected: float) -> None:
    assert image_scale(scale)[0] == pytest.approx(expected, abs=0.001)


@pytest.mark.requirement("REQ-RAWQA-002")
def test_known_ceiling_and_native_fwhm() -> None:
    r = measure(field().astype(float), 4095, 0.5)
    assert r["clipped_stars"] == 1
    assert len(r["stars"]) == 5
    for idx, s in enumerate(r["stars"], 1):
        assert s["id"] == idx
        assert s["major_px"] == pytest.approx(2.35482 * 1.4, abs=0.06)
        assert s["minor_px"] == pytest.approx(2.35482 * 1.15, abs=0.06)
        assert s["fwhm_arcsec"] == s["fwhm_px"] * 0.5


@pytest.mark.requirement("REQ-RAWQA-002")
def test_unknown_ceiling_is_not_zero() -> None:
    image = field().astype(float)
    r = measure(image, None, None)
    assert r["clipped_stars"] is None
    assert len(r["clipping_candidates"]) == 1
    assert all(s["fwhm_arcsec"] is None for s in r["stars"])


@pytest.mark.requirement("REQ-RAWQA-002")
def test_ambiguous_ceiling_rules_refused() -> None:
    meta = metadata(header(), Path("test.fits"))
    rules = clipping()
    assert ceiling_for(meta, rules) == 4095
    assert ceiling_for({**meta, "bin_mode": "SUM"}, rules) is None
    with pytest.raises(ValueError, match="Conflicting"):
        ceiling_for(meta, [rules[0], {**rules[0], "ceiling_adu": 4096}])


@pytest.mark.requirement("REQ-RAWQA-002")
def test_no_stars_is_not_a_fake_width() -> None:
    r = measure(np.full((40, 40), 200, dtype=float), None, None)
    assert r["stars"] == []
    assert r["clipped_stars"] is None


@pytest.mark.requirement("REQ-RAWQA-001")
@pytest.mark.requirement("REQ-RAWQA-003")
def test_component_report_dedup_pixels_and_read_only(tmp_path: Path) -> None:
    root = tmp_path / "raw"
    root.mkdir()
    light = root / "star_autofocus03.fits"
    dark = root / "dark.fits"
    fits.writeto(light, field(), header())
    fits.writeto(dark, field(), header("Dark Frame"))
    shutil.copyfile(light, root / "z duplicate.fits")
    before = {p.name: p.read_bytes() for p in root.iterdir()}
    out = tmp_path / "my report"
    events: list[float] = []
    result = scan(root, out, {"clipping": clipping()}, True, events.append, "night")
    manifest = json.loads((out / "manifest.json").read_text())
    measured = next(r for r in manifest["frames"] if r["status"] == "measured")
    assert (result["fits_count"], result["duplicate_count"]) == (2, 1)
    assert result["qa_inspected_files"] == [light.name] and events[-1] == 100
    assert measured["metadata"]["frame_role"] == "autofocus"
    assert measured["clipped_stars"] == 1 and len(measured["stars"]) == 5
    assert {p.name: p.read_bytes() for p in root.iterdir()} == before
    assert not list(out.rglob("*.fits"))
    with Image.open(out / measured["preview"]) as frame:
        assert frame.size == (260, 200)
    report = (out / "report.html").read_text(encoding="utf-8")
    assert "FWHM versus peak ADU" in report and measured["preview"] in report
    assert "https://" not in report and "__RAW_QA_DATA__" not in report
    with pytest.raises(ValueError, match="already exists"):
        scan(root, out, {}, True, lambda _: None)


@pytest.mark.requirement("REQ-RAWQA-001")
def test_output_cannot_be_under_raw(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="outside"):
        scan(tmp_path, tmp_path / "inside", {}, True, lambda _: None)
    assert not (tmp_path / "inside").exists()


@pytest.mark.requirement("REQ-RAWQA-004")
def test_worker_subprocess_contract(tmp_path: Path) -> None:
    raw = tmp_path / "source"
    raw.mkdir()
    fits.writeto(raw / "science.fits", field(), header())
    output = tmp_path / "job"
    output.mkdir()
    spec = output / "job-spec.json"
    spec.write_text(
        json.dumps(
            {
                "contract_version": 1,
                "job_id": "test",
                "tool_id": "raw_fits_qa",
                "dataset_id": "night",
                "dataset_path": str(raw),
                "inputs": {},
            }
        )
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        [str(Path(__file__).resolve().parents[1] / "src"), env.get("PYTHONPATH", "")]
    )
    events = output / "events.jsonl"
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "astroponys.raw_qa_worker",
            "--config",
            str(tmp_path / "none.toml"),
            "--job-spec",
            str(spec),
            "--output-dir",
            str(output),
            "--events",
            str(events),
        ],
        env=env,
        cwd=output,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    assert json.loads(events.read_text().splitlines()[-1])["value"] == 100
    assert json.loads((output / "result.json").read_text())["dataset_id"] == "night"


@pytest.mark.requirement("REQ-RAWQA-004")
@pytest.mark.parametrize("encoding", ["utf-8", "cp1252"])
def test_registration_cli_preserves_host_config(tmp_path: Path, encoding: str) -> None:
    registration = Path(__file__).resolve().parents[1] / "tools/raw-fits-qa/integrate_flask.py"
    config = tmp_path / "config.toml"
    original = '[datasets.night]\npath = "C:/Astro Data"\n[jobs]\nconcurrency = 2\n'
    config.write_text(original)
    python = tmp_path / "venv with spaces" / "python"
    python.parent.mkdir()
    python.touch()
    args = [
        sys.executable,
        str(registration),
        "--config",
        str(config),
        "--tool-python",
        str(python),
    ]
    env = {**os.environ, "PYTHONIOENCODING": encoding}
    proc = subprocess.run(
        args, check=False, cwd=tmp_path, capture_output=True, encoding=encoding, env=env
    )
    assert proc.returncode == 0, proc.stderr
    assert "Registered Raw FITS QA." in proc.stdout
    once = config.read_text()
    assert once.startswith(original)
    entry = tomllib.loads(once)["tools"]["raw_fits_qa"]
    assert entry["module"] == "astroponys.raw_qa_worker"
    assert entry["python"] == python.as_posix()
    proc = subprocess.run(
        args, check=False, cwd=tmp_path, capture_output=True, encoding=encoding, env=env
    )
    assert proc.returncode == 0, proc.stderr
    assert "Raw FITS QA already registered." in proc.stdout
    assert config.read_text() == once
