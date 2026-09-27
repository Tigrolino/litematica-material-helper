#!/usr/bin/env python3
from __future__ import annotations

import sys
import traceback


def _show_fatal_error(exc: BaseException) -> None:
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Litematica Material Helper",
            "Couldn't start:\n\n"
            f"{exc}\n\n"
            "Check the terminal for details.",
        )
        root.destroy()
    except Exception:
        pass
    traceback.print_exc()


def main() -> int:
    try:
        from app.ui.app_window import AppWindow
    except ImportError as exc:
        print(
            "Missing dependencies. Install them first with:\n"
            "    pip install -r requirements.txt\n",
            file=sys.stderr,
        )
        _show_fatal_error(exc)
        return 1

    try:
        app = AppWindow()
        app.mainloop()
    except Exception as exc:
        _show_fatal_error(exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
