# Development

## Windows setup (primary)

Use a normal 64-bit CPython 3.13 installation:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install --only-binary=:all: ".[dev]"
```

`--only-binary=:all:` makes missing Windows wheels fail visibly instead of silently
starting a compiler toolchain. `pyproject.toml` is the dependency source of truth;
manually maintained duplicate `requirements.txt` files are intentionally absent.

## Local quality gate

```powershell
python -m pytest --cov=astroponys --cov-report=term-missing
python -m ruff check .
python -m ruff format --check .
python -m mypy src
```

Tests using private observations are opt-in and must reference their external location
through `ASTROPONYS_PRIVATE_DATA`. Never copy private FITS into this repository.

## Requirement markers

Every behavioural pytest test needs at least one known marker:

```text
@pytest.mark.requirement("REQ-FOCUS-005")
def test_linear_drift_is_removed() -> None:
    ...
```

The collection hook rejects absent and unknown markers. Before release, the traceability
audit also rejects implemented requirements without a linked test.
