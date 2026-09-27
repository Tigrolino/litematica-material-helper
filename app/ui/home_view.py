from __future__ import annotations

import datetime as _dt
from pathlib import Path

import customtkinter as ctk

from .. import theme
from ..config import config
from ..formatting import format_int
from ..parser import parse_material_list_file


def _make_clickable(widget, handler) -> None:
    widget.bind("<Button-1>", lambda e: handler())
    widget.configure(cursor="hand2")
    for child in widget.winfo_children():
        _make_clickable(child, handler)


class HomeView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=theme.BG)
        self.app = app
        self._build_static_ui()
        self.refresh()

    def _build_static_ui(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(side="top", fill="x", padx=24, pady=(22, 10))

        title = ctk.CTkLabel(
            header, text="Material Lists", font=(theme.FONT_FAMILY, 20, "bold"),
            text_color=theme.FG,
        )
        title.pack(side="left")

        refresh_btn = ctk.CTkButton(
            header, text="Refresh", width=90, fg_color=theme.BG_CARD,
            hover_color=theme.BG_HOVER, text_color=theme.FG,
            command=self.refresh,
        )
        refresh_btn.pack(side="right")

        settings_btn = ctk.CTkButton(
            header, text="Settings", width=90, fg_color="transparent",
            hover_color=theme.BG_HOVER, text_color=theme.FG_MUTED,
            border_width=1, border_color=theme.BORDER,
            command=lambda: self.app.show_settings(),
        )
        settings_btn.pack(side="right", padx=(0, 8))

        self.folder_label = ctk.CTkLabel(
            self, text="", font=(theme.FONT_FAMILY, 11), text_color=theme.FG_MUTED,
            anchor="w", justify="left",
        )
        self.folder_label.pack(side="top", fill="x", padx=24, pady=(0, 14))

        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=theme.BG_HOVER,
            scrollbar_button_hover_color=theme.ACCENT_DIM,
        )
        self.scroll.pack(side="top", fill="both", expand=True, padx=20, pady=(0, 16))
        self.scroll.grid_columnconfigure(0, weight=1)

        self.empty_state = ctk.CTkFrame(self, fg_color="transparent")

    def refresh(self) -> None:
        for child in self.scroll.winfo_children():
            child.destroy()

        raw_folder = config.material_list_folder.strip()
        if not raw_folder:
            self.folder_label.configure(text="Folder:  not set")
            self._show_message(
                "No folder set.",
                "Set your Litematica folder in Settings.",
            )
            return

        folder = Path(raw_folder)
        self.folder_label.configure(text=f"Folder:  {folder}")

        if not folder.exists() or not folder.is_dir():
            self._show_message(
                "This folder doesn't exist.",
                "Set your Litematica folder in Settings.",
            )
            return

        files = sorted(
            [p for p in folder.glob("*.txt") if p.is_file()],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        if not files:
            self._show_message(
                "No material lists here yet.",
                "Export one in Litematica (Materials > Export to file) and it'll show up here.",
            )
            return

        for row, path in enumerate(files):
            self._build_card(row, path)

    def _show_message(self, title: str, subtitle: str) -> None:
        wrap = ctk.CTkFrame(self.scroll, fg_color="transparent")
        wrap.grid(row=0, column=0, sticky="ew", pady=40)
        ctk.CTkLabel(
            wrap, text=title, font=(theme.FONT_FAMILY, 14, "bold"), text_color=theme.FG,
        ).pack()
        ctk.CTkLabel(
            wrap, text=subtitle, font=(theme.FONT_FAMILY, 11), text_color=theme.FG_MUTED,
            wraplength=520, justify="center",
        ).pack(pady=(6, 0))

    def _build_card(self, row: int, path: Path) -> None:
        try:
            ml = parse_material_list_file(path)
            title = ml.title if ml.title and ml.title.lower() != "unnamed" else path.stem
            item_count = ml.item_count
            missing_sum = ml.total_missing
            parse_ok = True
        except Exception:
            title = path.stem
            item_count = 0
            missing_sum = 0
            parse_ok = False

        mtime = _dt.datetime.fromtimestamp(path.stat().st_mtime)
        when = mtime.strftime("%b %d, %Y  •  %H:%M")

        card = ctk.CTkFrame(self.scroll, fg_color=theme.BG_CARD, corner_radius=10)
        card.grid(row=row, column=0, sticky="ew", pady=6)
        card.grid_columnconfigure(0, weight=1)

        def on_enter(_e=None):
            card.configure(fg_color=theme.BG_HOVER)

        def on_leave(_e=None):
            card.configure(fg_color=theme.BG_CARD)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.grid(row=0, column=0, sticky="ew", padx=16, pady=12)
        inner.grid_columnconfigure(0, weight=1)

        name_lbl = ctk.CTkLabel(
            inner, text=title, font=(theme.FONT_FAMILY, 14, "bold"),
            text_color=theme.FG, anchor="w",
        )
        name_lbl.grid(row=0, column=0, sticky="w")

        if parse_ok:
            sub_text = f"{item_count} item types   •   {format_int(missing_sum)} items still needed   •   {when}"
        else:
            sub_text = f"Couldn't read this file   •   {when}"
        sub_lbl = ctk.CTkLabel(
            inner, text=sub_text, font=(theme.FONT_FAMILY, 11), text_color=theme.FG_MUTED,
            anchor="w",
        )
        sub_lbl.grid(row=1, column=0, sticky="w", pady=(2, 0))

        open_lbl = ctk.CTkLabel(
            inner, text="Open  ›", font=(theme.FONT_FAMILY, 11, "bold"),
            text_color=theme.ACCENT,
        )
        open_lbl.grid(row=0, column=1, rowspan=2, sticky="e", padx=(10, 0))

        handler = (lambda p=path: self.app.open_list(p)) if parse_ok else None
        for w in (card, inner, name_lbl, sub_lbl, open_lbl):
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            if handler:
                w.bind("<Button-1>", lambda e, h=handler: h())
                w.configure(cursor="hand2")
