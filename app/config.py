from __future__ import annotations

import json
import os
from typing import Any, Dict

from .paths import app_root


ROOT_DIR = app_root()
DATA_DIR = ROOT_DIR / "data"
PROGRESS_DIR = DATA_DIR / "progress"
ICON_CACHE_DIR = DATA_DIR / "icon_cache"
CONFIG_PATH = DATA_DIR / "config.json"

DEFAULT_MATERIAL_LIST_FOLDER = ""

DEFAULT_GLOBAL_HOTKEY = "ctrl+enter"

DEFAULTS: Dict[str, Any] = {
    "material_list_folder": DEFAULT_MATERIAL_LIST_FOLDER,
    "show_total_column": False,
    "show_available_column": False,
    "window_geometry": "1200x760",
    "global_hotkey_enabled": True,
    "global_hotkey": DEFAULT_GLOBAL_HOTKEY,
}


def _ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
    ICON_CACHE_DIR.mkdir(parents=True, exist_ok=True)


class Config:
    def __init__(self) -> None:
        _ensure_dirs()
        self._data: Dict[str, Any] = dict(DEFAULTS)
        self.load()

    def load(self) -> None:
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
                    saved = json.load(fh)
                if isinstance(saved, dict):
                    self._data.update(saved)
            except (json.JSONDecodeError, OSError):
                pass
        else:
            self.save()

    def save(self) -> None:
        _ensure_dirs()
        tmp_path = CONFIG_PATH.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as fh:
            json.dump(self._data, fh, indent=2)
        os.replace(tmp_path, CONFIG_PATH)

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
        self.save()

    @property
    def material_list_folder(self) -> str:
        return self._data.get("material_list_folder", DEFAULT_MATERIAL_LIST_FOLDER)

    @material_list_folder.setter
    def material_list_folder(self, value: str) -> None:
        self.set("material_list_folder", value)

    @property
    def show_total_column(self) -> bool:
        return bool(self._data.get("show_total_column", False))

    @show_total_column.setter
    def show_total_column(self, value: bool) -> None:
        self.set("show_total_column", bool(value))

    @property
    def show_available_column(self) -> bool:
        return bool(self._data.get("show_available_column", False))

    @show_available_column.setter
    def show_available_column(self, value: bool) -> None:
        self.set("show_available_column", bool(value))

    @property
    def global_hotkey_enabled(self) -> bool:
        return bool(self._data.get("global_hotkey_enabled", True))

    @global_hotkey_enabled.setter
    def global_hotkey_enabled(self, value: bool) -> None:
        self.set("global_hotkey_enabled", bool(value))

    @property
    def global_hotkey(self) -> str:
        return self._data.get("global_hotkey", DEFAULT_GLOBAL_HOTKEY) or DEFAULT_GLOBAL_HOTKEY

    @global_hotkey.setter
    def global_hotkey(self, value: str) -> None:
        self.set("global_hotkey", value)


config = Config()
