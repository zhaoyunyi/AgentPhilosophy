from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .errors import SyncError
from .fileio import write_bytes_atomic


def read_yaml(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise SyncError(f"YAML file not found: {path}") from exc
    try:
        value = yaml.safe_load(raw) or {}
    except yaml.YAMLError as exc:
        raise SyncError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SyncError(f"YAML root must be a mapping: {path}")
    return value


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    write_bytes_atomic(
        path,
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False).encode("utf-8"),
    )
