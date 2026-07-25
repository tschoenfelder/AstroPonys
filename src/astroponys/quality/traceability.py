"""Validate requirement IDs, test markers and implementation status."""

from __future__ import annotations

import argparse
import ast
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import yaml

REQUIREMENT_PATTERN = re.compile(r"REQ-[A-Z]+-[0-9]{3}")
IMPLEMENTED_STATUSES = frozenset({"implemented", "verified"})
ALLOWED_STATUSES = frozenset({"accepted", "implemented", "verified", "retired"})


@dataclass(frozen=True)
class AuditResult:
    catalogue_count: int
    test_count: int
    covered_requirement_count: int
    implemented_requirement_count: int
    errors: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not self.errors


def audit_repository(root: Path) -> AuditResult:
    catalogue_path = root / "docs" / "requirements" / "README.md"
    status_path = root / "docs" / "requirements" / "status.yaml"
    tests_root = root / "tests"
    catalogue = extract_catalogue(catalogue_path)
    statuses, status_errors = load_statuses(status_path, catalogue)
    markers, test_count, test_errors = collect_test_markers(tests_root)

    errors = [*status_errors, *test_errors]
    unknown_markers = markers - catalogue
    errors.extend(f"Unknown test requirement marker: {item}" for item in sorted(unknown_markers))
    implemented = {
        requirement for requirement, status in statuses.items() if status in IMPLEMENTED_STATUSES
    }
    untested = implemented - markers
    errors.extend(
        f"{item} is {statuses[item]} but has no lower-level automated test"
        for item in sorted(untested)
    )
    return AuditResult(
        catalogue_count=len(catalogue),
        test_count=test_count,
        covered_requirement_count=len(markers & catalogue),
        implemented_requirement_count=len(implemented),
        errors=tuple(errors),
    )


def extract_catalogue(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    return set(REQUIREMENT_PATTERN.findall(path.read_text(encoding="utf-8")))


def load_statuses(path: Path, catalogue: set[str]) -> tuple[dict[str, str], list[str]]:
    if not path.is_file():
        return {}, [f"Missing requirement status file: {path}"]
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("schema_version") != 1:
        return {}, ["Requirement status schema_version must be 1"]
    default = str(raw.get("default_status", "")).casefold()
    if default not in ALLOWED_STATUSES:
        return {}, [f"Unknown default requirement status: {default}"]
    overrides_raw = raw.get("requirements", {})
    if not isinstance(overrides_raw, dict):
        return {}, ["requirements status overrides must be a mapping"]
    overrides = {str(key): str(value).casefold() for key, value in overrides_raw.items()}
    errors = [f"Unknown status requirement: {item}" for item in sorted(set(overrides) - catalogue)]
    errors.extend(
        f"Unknown requirement status for {key}: {value}"
        for key, value in sorted(overrides.items())
        if value not in ALLOWED_STATUSES
    )
    return {item: overrides.get(item, default) for item in catalogue}, errors


def collect_test_markers(tests_root: Path) -> tuple[set[str], int, list[str]]:
    markers: set[str] = set()
    errors: list[str] = []
    test_count = 0
    for path in sorted(tests_root.rglob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not node.name.startswith("test_"):
                continue
            test_count += 1
            found = _requirements_on(node)
            if not found:
                errors.append(f"Behaviour test lacks requirement marker: {path}:{node.lineno}")
            markers.update(found)
    return markers, test_count, errors


def _requirements_on(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    found: set[str] = set()
    for decorator in node.decorator_list:
        if not isinstance(decorator, ast.Call) or not decorator.args:
            continue
        function = decorator.func
        is_requirement = (
            isinstance(function, ast.Attribute)
            and function.attr == "requirement"
            and isinstance(function.value, ast.Attribute)
            and function.value.attr == "mark"
        )
        first = decorator.args[0]
        if is_requirement and isinstance(first, ast.Constant) and isinstance(first.value, str):
            found.add(first.value)
    return found


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path.cwd())
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    result = audit_repository(_parser().parse_args(argv).root.resolve())
    print(
        f"Traceability: {result.covered_requirement_count}/{result.catalogue_count} "
        f"requirements referenced by {result.test_count} tests; "
        f"{result.implemented_requirement_count} marked implemented/verified."
    )
    for error in result.errors:
        print(f"ERROR: {error}", file=sys.stderr)
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
