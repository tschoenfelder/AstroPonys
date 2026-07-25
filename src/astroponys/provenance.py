"""Immutable run directories and JSON-safe provenance output."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from . import __version__
from .config import SessionConfig


def create_run_directory(config: SessionConfig, pony: str) -> tuple[str, Path]:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
    run_id = f"{timestamp}-{uuid4().hex[:8]}"
    pony_root = config.output_directory / pony
    pony_root.mkdir(parents=True, exist_ok=True)
    run_directory = pony_root / run_id
    run_directory.mkdir(exist_ok=False)
    return run_id, run_directory


def write_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(_jsonable(value), indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def base_manifest(config: SessionConfig, run_id: str, pony: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "run_id": run_id,
        "pony": pony,
        "software": {"name": "astroponys", "version": __version__},
        "created_at": datetime.now(UTC).isoformat(),
        "product_level": "raw-measurement-report",
        "config_path": str(config.config_path),
        "image_directory": str(config.image_directory),
        "identity": {
            "session_id": config.session_id,
            "night_id": config.night_id,
            "target_id": config.target_id,
            "panel_id": config.panel_id,
        },
    }


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _jsonable(asdict(cast(Any, value)))
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, (Path, datetime)):
        return value.isoformat() if isinstance(value, datetime) else str(value)
    return value
