from __future__ import annotations

import threading
from typing import Callable, Optional

try:
    import keyboard  # type: ignore
except Exception:
    keyboard = None


class GlobalHotkeyManager:
    def __init__(self, root, on_trigger: Callable[[], None]):
        self._root = root
        self._on_trigger = on_trigger
        self._active_combo: Optional[str] = None
        self.last_error: Optional[str] = None

    @property
    def available(self) -> bool:
        return keyboard is not None

    @property
    def active_combo(self) -> Optional[str]:
        return self._active_combo

    def set_hotkey(self, combo: str) -> bool:
        self.unregister()
        combo = (combo or "").strip()
        if not combo:
            return True
        if keyboard is None:
            self.last_error = "The \"keyboard\" package isn't installed."
            return False
        try:
            keyboard.add_hotkey(combo, self._fire, suppress=False)
        except Exception as exc:
            self.last_error = str(exc) or type(exc).__name__
            self._active_combo = None
            return False
        self._active_combo = combo
        self.last_error = None
        return True

    def unregister(self) -> None:
        if self._active_combo and keyboard is not None:
            try:
                keyboard.remove_hotkey(self._active_combo)
            except (KeyError, ValueError):
                pass
            except Exception:
                pass
        self._active_combo = None

    def _fire(self) -> None:
        try:
            self._root.after(0, self._on_trigger)
        except Exception:
            pass


def capture_hotkey(callback: Callable[[Optional[str], Optional[str]], None]) -> None:
    if keyboard is None:
        callback(None, "The \"keyboard\" package isn't installed.")
        return

    def worker() -> None:
        try:
            combo = keyboard.read_hotkey(suppress=False)
        except Exception as exc:
            callback(None, str(exc) or type(exc).__name__)
            return
        callback(combo, None)

    threading.Thread(target=worker, daemon=True).start()
