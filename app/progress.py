from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Dict

from .config import PROGRESS_DIR

_SAFE_RE = re.compile(r"[^A-Za-z0-9_.-]+")


def _progress_path(list_filename: str) -> Path:
    safe = _SAFE_RE.sub("_", list_filename)
    return PROGRESS_DIR / f"{safe}.json"


def load_progress(list_filename: str) -> Dict[str, Dict[str, bool]]:
    path = _progress_path(list_filename)
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def save_progress(list_filename: str, data: Dict[str, Dict[str, bool]]) -> None:
    PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
    path = _progress_path(list_filename)
    tmp_path = path.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    os.replace(tmp_path, path)
