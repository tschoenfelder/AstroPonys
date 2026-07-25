from __future__ import annotations

import re
from pathlib import Path

import pytest

REQUIREMENT_PATTERN = re.compile(r"REQ-[A-Z]+-[0-9]{3}")


def _known_requirements() -> set[str]:
    catalogue = Path(__file__).parents[1] / "docs" / "requirements" / "README.md"
    return set(REQUIREMENT_PATTERN.findall(catalogue.read_text(encoding="utf-8")))


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    known = _known_requirements()
    for item in items:
        markers = list(item.iter_markers("requirement"))
        if not markers:
            raise pytest.UsageError(f"Behaviour test lacks requirement marker: {item.nodeid}")
        for marker in markers:
            requirement = marker.args[0] if marker.args else None
            if requirement not in known:
                raise pytest.UsageError(
                    f"Unknown requirement marker {requirement!r}: {item.nodeid}"
                )
