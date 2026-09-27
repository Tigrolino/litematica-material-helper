from __future__ import annotations

from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from .. import theme
from ..config import DEFAULT_GLOBAL_HOTKEY, config
from ..global_hotkey import capture_hotkey


class SettingsView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=theme.BG)
        self.app = app
        self._recording = False
        self._build_ui()

    def _build_ui(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(side="top", fill="x", padx=24, pady=(22, 10))

        ctk.CTkLabel(
            header, text="Settings", font=(theme.FONT_FAMILY, 20, "bold"),
            text_color=theme.FG,
        ).pack(side="left")

        ctk.CTkButton(
            header, text="← Back", width=90, fg_color="transparent",
            hover_color=theme.BG_HOVER, text_color=theme.FG_MUTED,
            border_width=1, border_color=theme.BORDER,
            command=lambda: self.app.show_home(),
        ).pack(side="right")

        body = ctk.CTkFrame(self, fg_color=theme.BG_CARD, corner_radius=10)
        body.pack(side="top", fill="both", expand=True, padx=24, pady=(4, 24))
        body.grid_columnconfigure(0, weight=1)

        section = self._section(body, "Material list folder", row=0)
        ctk.CTkLabel(
            section,
            text="The folder Litematica writes materials_list_*.txt files into.",
            font=(theme.FONT_FAMILY, 11), text_color=theme.FG_MUTED, anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="w")

        self.folder_var = ctk.StringVar(value=config.material_list_folder)
        entry = ctk.CTkEntry(section, textvariable=self.folder_var, width=460)
        entry.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        section.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(
            section, text="Browse…", width=90, command=self._browse_folder,
            fg_color=theme.BG_PANEL, hover_color=theme.BG_HOVER, text_color=theme.FG,
        ).grid(row=1, column=1, sticky="e", padx=(10, 0), pady=(8, 0))

        self.folder_status = ctk.CTkLabel(
            section, text="", font=(theme.FONT_FAMILY, 11), anchor="w",
        )
        self.folder_status.grid(row=2, column=0, columnspan=2, sticky="w", pady=(6, 0))
        self.folder_var.trace_add("write", lambda *a: self._on_folder_changed())
        self._update_folder_status()

        section2 = self._section(body, "Table columns", row=1)
        ctk.CTkLabel(
            section2,
            text="\"Missing\" is always shown. These are off by default.",
            font=(theme.FONT_FAMILY, 11), text_color=theme.FG_MUTED, anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="w")

        self.total_var = ctk.BooleanVar(value=config.show_total_column)
        ctk.CTkSwitch(
            section2, text="Show Total column", variable=self.total_var,
            command=lambda: config.set("show_total_column", self.total_var.get()),
            progress_color=theme.ACCENT, font=(theme.FONT_FAMILY, 12),
        ).grid(row=1, column=0, sticky="w", pady=(10, 0))

        self.available_var = ctk.BooleanVar(value=config.show_available_column)
        ctk.CTkSwitch(
            section2, text="Show Available column", variable=self.available_var,
            command=lambda: config.set("show_available_column", self.available_var.get()),
            progress_color=theme.ACCENT, font=(theme.FONT_FAMILY, 12),
        ).grid(row=2, column=0, sticky="w", pady=(8, 0))

        section_hk = self._section(body, "Global shortcut", row=2)
        ctk.CTkLabel(
            section_hk,
            text=(
                "Works even when the app isn't focused, so you can "
                "press it in Minecraft to check off the selected "
                "item(s) and jump to the next one."
            ),
            font=(theme.FONT_FAMILY, 11), text_color=theme.FG_MUTED, anchor="w",
            wraplength=520, justify="left",
        ).grid(row=0, column=0, columnspan=3, sticky="w")

        self.hotkey_enabled_var = ctk.BooleanVar(value=config.global_hotkey_enabled)
        ctk.CTkSwitch(
            section_hk, text="Enable global shortcut", variable=self.hotkey_enabled_var,
            command=self._on_hotkey_enabled_changed,
            progress_color=theme.ACCENT, font=(theme.FONT_FAMILY, 12),
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(10, 0))

        self.hotkey_var = ctk.StringVar(value=config.global_hotkey)
        self.hotkey_entry = ctk.CTkEntry(section_hk, textvariable=self.hotkey_var, width=200)
        self.hotkey_entry.grid(row=2, column=0, sticky="w", pady=(10, 0))

        self.hotkey_record_btn = ctk.CTkButton(
            section_hk, text="Record shortcut…", width=150,
            fg_color=theme.BG_PANEL, hover_color=theme.BG_HOVER, text_color=theme.FG,
            command=self._start_recording_hotkey,
        )
        self.hotkey_record_btn.grid(row=2, column=1, sticky="w", padx=(10, 0), pady=(10, 0))

        ctk.CTkButton(
            section_hk, text="Reset", width=70, fg_color="transparent",
            hover_color=theme.BG_HOVER, text_color=theme.FG_MUTED,
            border_width=1, border_color=theme.BORDER,
            command=self._reset_hotkey,
        ).grid(row=2, column=2, sticky="w", padx=(8, 0), pady=(10, 0))

        self.hotkey_status = ctk.CTkLabel(
            section_hk, text="", font=(theme.FONT_FAMILY, 11), anchor="w",
            wraplength=520, justify="left",
        )
        self.hotkey_status.grid(row=3, column=0, columnspan=3, sticky="w", pady=(8, 0))
        self._update_hotkey_status()
        self.hotkey_entry.bind("<Return>", lambda e: self._apply_typed_hotkey())
        self.hotkey_entry.bind("<FocusOut>", lambda e: self._apply_typed_hotkey())
        self._set_hotkey_controls_enabled(self.hotkey_enabled_var.get())

        section3 = self._section(body, "Item icons", row=3)
        ctk.CTkLabel(
            section3,
            text=(
                "Icons get downloaded the first time you open a list "
                "and cached after that. Hit retry if some are missing."
            ),
            font=(theme.FONT_FAMILY, 11), text_color=theme.FG_MUTED, anchor="w",
            wraplength=520, justify="left",
        ).grid(row=0, column=0, sticky="w")

        self.retry_status = ctk.CTkLabel(
            section3, text="", font=(theme.FONT_FAMILY, 11), text_color=theme.ACCENT,
        )
        ctk.CTkButton(
            section3, text="Retry missing icons", width=160,
            fg_color=theme.BG_PANEL, hover_color=theme.BG_HOVER, text_color=theme.FG,
            command=self._retry_icons,
        ).grid(row=1, column=0, sticky="w", pady=(10, 0))
        self.retry_status.grid(row=1, column=1, sticky="w", padx=(10, 0))

    def _section(self, parent, title, row):
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.grid(row=row, column=0, sticky="ew", padx=22, pady=(20, 6))
        ctk.CTkLabel(
            wrap, text=title, font=(theme.FONT_FAMILY, 13, "bold"), text_color=theme.FG,
            anchor="w",
        ).pack(side="top", anchor="w", pady=(0, 8))
        inner = ctk.CTkFrame(wrap, fg_color="transparent")
        inner.pack(side="top", fill="x")
        return inner

    def _browse_folder(self) -> None:
        initial = config.material_list_folder.strip()
        if not initial or not Path(initial).exists():
            initial = str(Path.home())
        chosen = filedialog.askdirectory(initialdir=initial, title="Choose material list folder")
        if chosen:
            self.folder_var.set(chosen)

    def _on_folder_changed(self) -> None:
        config.set("material_list_folder", self.folder_var.get())
        self._update_folder_status()

    def _update_folder_status(self) -> None:
        raw = self.folder_var.get().strip()
        if not raw:
            self.folder_status.configure(text="No folder chosen yet.", text_color=theme.FG_MUTED)
            return
        path = Path(raw)
        if path.exists() and path.is_dir():
            self.folder_status.configure(text="Folder found.", text_color=theme.ACCENT)
        else:
            self.folder_status.configure(
                text="This folder doesn't exist, check the path.",
                text_color=theme.WARNING,
            )

    def _retry_icons(self) -> None:
        self.app.icon_manager.retry_missing()
        self.retry_status.configure(text="Missing icons will be retried when you open a list.")

    def _set_hotkey_controls_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        self.hotkey_entry.configure(state=state)
        self.hotkey_record_btn.configure(state=state)

    def _on_hotkey_enabled_changed(self) -> None:
        enabled = self.hotkey_enabled_var.get()
        config.global_hotkey_enabled = enabled
        self._set_hotkey_controls_enabled(enabled)
        if enabled:
            self.app.hotkey_manager.set_hotkey(self.hotkey_var.get())
        else:
            self.app.hotkey_manager.unregister()
        self._update_hotkey_status()

    def _apply_typed_hotkey(self) -> None:
        if self._recording:
            return
        combo = self.hotkey_var.get().strip()
        if not combo or combo == config.global_hotkey:
            return
        config.global_hotkey = combo
        if self.hotkey_enabled_var.get():
            self.app.hotkey_manager.set_hotkey(combo)
        self._update_hotkey_status()

    def _reset_hotkey(self) -> None:
        self.hotkey_var.set(DEFAULT_GLOBAL_HOTKEY)
        self._apply_typed_hotkey()

    def _start_recording_hotkey(self) -> None:
        if self._recording:
            return
        self._recording = True
        self.hotkey_record_btn.configure(state="disabled", text="Press your keys…")
        self.hotkey_entry.configure(state="disabled")
        self.hotkey_status.configure(
            text="Press the key combo you want…",
            text_color=theme.FG_MUTED,
        )
        capture_hotkey(self._on_hotkey_captured)

    def _on_hotkey_captured(self, combo: str | None, error: str | None) -> None:
        self.after(0, self._finish_recording_hotkey, combo, error)

    def _finish_recording_hotkey(self, combo: str | None, error: str | None) -> None:
        self._recording = False
        self.hotkey_record_btn.configure(state="normal", text="Record shortcut…")
        self.hotkey_entry.configure(state="normal")
        if not self.winfo_exists():
            return
        if error:
            self.hotkey_status.configure(
                text=f"Couldn't record a shortcut: {error}", text_color=theme.DANGER,
            )
            return
        if not combo:
            self._update_hotkey_status()
            return
        self.hotkey_var.set(combo)
        config.global_hotkey = combo
        if self.hotkey_enabled_var.get():
            self.app.hotkey_manager.set_hotkey(combo)
        self._update_hotkey_status()

    def _update_hotkey_status(self) -> None:
        mgr = self.app.hotkey_manager
        if not self.hotkey_enabled_var.get():
            self.hotkey_status.configure(text="Global shortcut is off.", text_color=theme.FG_MUTED)
            return
        if not mgr.available:
            self.hotkey_status.configure(
                text=(
                    "The \"keyboard\" package isn't installed, so the global shortcut "
                    "can't be registered. Run: pip install keyboard"
                ),
                text_color=theme.WARNING,
            )
            return
        if mgr.active_combo:
            self.hotkey_status.configure(
                text=f"Listening for \"{mgr.active_combo}\" everywhere on your PC.",
                text_color=theme.ACCENT,
            )
        else:
            reason = mgr.last_error or "unknown error"
            self.hotkey_status.configure(
                text=(
                    f"Couldn't register the shortcut ({reason}). If it's a permissions "
                    "issue, try running the app as administrator."
                ),
                text_color=theme.WARNING,
            )
