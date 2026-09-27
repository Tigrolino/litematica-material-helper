from __future__ import annotations

from tkinter import ttk

BG = "#1a1b1e"
BG_PANEL = "#212226"
BG_CARD = "#26282c"
BG_CARD_ALT = "#2b2d32"
BG_HOVER = "#313339"
BG_SELECTED = "#45484d"

FG = "#eceef0"
FG_MUTED = "#9aa0a6"
FG_FAINT = "#6b7076"

ACCENT = "#a9adb4"
ACCENT_HOVER = "#8f949b"
ACCENT_DIM = "#71757a"

DANGER = "#e0655b"
WARNING = "#e0a63b"

BORDER = "#34363b"

FONT_FAMILY = "Segoe UI"
FONT_FAMILY_MONO = "Consolas"


def apply_treeview_style(style: ttk.Style, row_height: int = 34) -> None:
    style.theme_use("clam")

    style.configure(
        "Dark.Treeview",
        background=BG_CARD,
        fieldbackground=BG_CARD,
        foreground=FG,
        borderwidth=0,
        rowheight=row_height,
        font=(FONT_FAMILY, 11),
    )
    style.map(
        "Dark.Treeview",
        background=[("selected", BG_SELECTED)],
        foreground=[("selected", FG)],
    )

    style.configure(
        "Dark.Treeview.Heading",
        background=BG_PANEL,
        foreground=FG_MUTED,
        borderwidth=0,
        relief="flat",
        font=(FONT_FAMILY, 10, "bold"),
        padding=(10, 8),
    )
    style.map(
        "Dark.Treeview.Heading",
        background=[("active", BG_HOVER)],
        foreground=[("active", FG)],
    )

    style.layout(
        "Dark.Treeview",
        [("Dark.Treeview.treearea", {"sticky": "nswe"})],
    )

    style.configure(
        "Dark.Vertical.TScrollbar",
        background=BG_PANEL,
        troughcolor=BG,
        bordercolor=BG,
        arrowcolor=FG_MUTED,
        relief="flat",
    )
    style.map("Dark.Vertical.TScrollbar", background=[("active", BG_HOVER)])
