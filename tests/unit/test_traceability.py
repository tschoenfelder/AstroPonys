from pathlib import Path

import pytest

from astroponys.quality.traceability import audit_repository


def project(tmp_path: Path, *, status: str, marker: str | None) -> Path:
    requirements = tmp_path / "docs" / "requirements"
    requirements.mkdir(parents=True)
    (requirements / "README.md").write_text("- REQ-DEMO-001: Demo\n", encoding="utf-8")
    (requirements / "status.yaml").write_text(
        f"schema_version: 1\ndefault_status: accepted\nrequirements:\n  REQ-DEMO-001: {status}\n",
        encoding="utf-8",
    )
    tests = tmp_path / "tests"
    tests.mkdir()
    decorator = f'@pytest.mark.requirement("{marker}")\n' if marker else ""
    (tests / "test_demo.py").write_text(
        f"import pytest\n\n{decorator}def test_demo():\n    assert True\n", encoding="utf-8"
    )
    return tmp_path


@pytest.mark.requirement("REQ-TEST-005")
def test_verified_requirement_requires_lower_level_test(tmp_path: Path) -> None:
    result = audit_repository(project(tmp_path, status="verified", marker=None))
    assert not result.passed
    assert any("no lower-level automated test" in error for error in result.errors)


@pytest.mark.requirement("REQ-TEST-001")
def test_known_marker_satisfies_traceability_gate(tmp_path: Path) -> None:
    result = audit_repository(project(tmp_path, status="verified", marker="REQ-DEMO-001"))
    assert result.passed
    assert result.covered_requirement_count == 1


@pytest.mark.requirement("REQ-TEST-001")
def test_unknown_marker_fails_traceability_gate(tmp_path: Path) -> None:
    result = audit_repository(project(tmp_path, status="accepted", marker="REQ-NOT-999"))
    assert not result.passed
    assert any("Unknown test requirement marker" in error for error in result.errors)
