from __future__ import annotations

import tkinter as tk
from pathlib import Path

import customtkinter as ctk
from tkinter import ttk

from .. import theme
from ..config import config
from ..global_hotkey import GlobalHotkeyManager
from ..icons import IconManager
from ..paths import resource_path
from .home_view import HomeView
from .list_view import ListView
from .settings_view import SettingsView

APP_TITLE = "Litematica Material Helper"


class AppWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title(APP_TITLE)
        self.geometry(config.get("window_geometry", "1200x760"))
        self.minsize(920, 600)
        self.configure(fg_color=theme.BG)
        self._set_window_icon()

        style = ttk.Style(self)
        theme.apply_treeview_style(style)

        self.icon_manager = IconManager(self, size=28)

        self.hotkey_manager = GlobalHotkeyManager(self, self._on_global_hotkey)
        if config.global_hotkey_enabled:
            self.hotkey_manager.set_hotkey(config.global_hotkey)

        self.content = ctk.CTkFrame(self, fg_color=theme.BG, corner_radius=0)
        self.content.pack(side="top", fill="both", expand=True)

        self.home_view = HomeView(self.content, self)
        self.settings_view = SettingsView(self.content, self)
        self.current_view = None

        self.show_home()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _set_window_icon(self) -> None:
        try:
            # windows needs the .ico for the taskbar
            self.iconbitmap(str(resource_path("app/assets/icon.ico")))
        except Exception:
            pass
        try:
            self._icon_photo = tk.PhotoImage(file=str(resource_path("app/assets/icon.png")))
            self.iconphoto(True, self._icon_photo)
        except Exception:
            pass

    def _show_view(self, view) -> None:
        if self.current_view is not None and self.current_view is not view:
            self.current_view.pack_forget()
        view.pack(side="top", fill="both", expand=True)
        self.current_view = view

    def show_home(self) -> None:
        self.home_view.refresh()
        self._show_view(self.home_view)

    def show_settings(self) -> None:
        self._show_view(self.settings_view)

    def open_list(self, path: Path) -> None:
        view = ListView(self.content, self, path)
        if self.current_view is not None:
            self.current_view.pack_forget()
        view.pack(side="top", fill="both", expand=True)
        if self.current_view not in (self.home_view, self.settings_view):
            if self.current_view is not None:
                self.current_view.destroy()
        self.current_view = view

    def _on_global_hotkey(self) -> None:
        view = self.current_view
        if isinstance(view, ListView) and view.winfo_exists():
            view.trigger_from_global_hotkey()

    def _on_close(self) -> None:
        try:
            config.set("window_geometry", self.geometry())
        except Exception:
            pass
        self.hotkey_manager.unregister()
        self.icon_manager.shutdown()
        self.destroy()
