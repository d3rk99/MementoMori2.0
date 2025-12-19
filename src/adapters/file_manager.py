from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List

logger = logging.getLogger(__name__)


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=str(path.parent)) as tmp:
        tmp.write(content)
        temp_name = tmp.name
    os.replace(temp_name, path)
    logger.debug("Atomic write complete", extra={"path": str(path)})


def write_lines(path: Path, lines: Iterable[str]) -> None:
    atomic_write(path, "\n".join(lines) + "\n")


def read_lines(path: Path) -> List[str]:
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


def read_json(path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        logger.warning("Failed to decode JSON, using default", extra={"path": str(path)})
        return default


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    atomic_write(path, json.dumps(payload, indent=2))
