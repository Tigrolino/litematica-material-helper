from __future__ import annotations

import sys
from pathlib import Path


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def app_root() -> Path:
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def resource_path(relative: str) -> Path:
    if is_frozen():
        base = Path(getattr(sys, "_MEIPASS", app_root()))
    else:
        base = Path(__file__).resolve().parent.parent
    return base / relative
