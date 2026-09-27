from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk

import customtkinter as ctk

from .. import theme
from ..config import config
from ..formatting import format_int, format_quantity
from ..parser import parse_material_list_file
from ..progress import load_progress, save_progress
from .scrollbar import ThinScrollbar

COLUMNS = ("missing", "total", "available", "done")
HEADING_TEXT = {
    "name": "Item",
    "missing": "Missing",
    "total": "Total",
    "available": "Available",
    "checked": "Done",
}
COLUMN_ID_FOR_KEY = {"missing": "missing", "total": "total", "available": "available", "checked": "done"}


class ListView(ctk.CTkFrame):
    def __init__(self, parent, app, file_path: Path):
        super().__init__(parent, fg_color=theme.BG)
        self.app = app
        self.file_path = Path(file_path)
        self.progress_key = self.file_path.name

        self.material_list = parse_material_list_file(self.file_path)
        saved_progress = load_progress(self.progress_key)

        self.rows = []
        for item in self.material_list.items:
            p = saved_progress.get(item.name, {})
            self.rows.append(
                {
                    "name": item.name,
                    "total": item.total,
                    "missing": item.missing,
                    "available": item.available,
                    "checked": bool(p.get("checked", False)),
                    "removed": bool(p.get("removed", False)),
                }
            )
        self.row_by_name = {r["name"]: r for r in self.rows}
        self._current_order: list[str] = []

        self.sort_key = "missing"
        self.sort_reverse = True
        self.show_removed = False

        self.search_var = tk.StringVar()
        self._search_after_id = None

        self._drag_toggle_active = False
        self._drag_touched_rows: set[str] = set()

        self._select_drag_active = False
        self._select_drag_anchor: str | None = None
        self._select_drag_moved = False
        self._select_drag_touched: set[str] = set()

        self._build_ui()
        self._update_heading_labels()
        self._refresh_table()
        self._prefetch_icons()

    def _build_ui(self) -> None:
        toolbar = ctk.CTkFrame(self, fg_color=theme.BG_PANEL, corner_radius=0, height=58)
        toolbar.pack(side="top", fill="x")
        toolbar.pack_propagate(False)

        ctk.CTkButton(
            toolbar, text="← Back", width=80, fg_color="transparent",
            hover_color=theme.BG_HOVER, text_color=theme.FG_MUTED,
            command=lambda: self.app.show_home(),
        ).pack(side="left", padx=(14, 14), pady=10)

        title = self.material_list.title
        if not title or title.lower() == "unnamed":
            title = self.file_path.stem
        if len(title) > 34:
            title = title[:31] + "…"
        ctk.CTkLabel(
            toolbar, text=title, font=(theme.FONT_FAMILY, 15, "bold"), text_color=theme.FG,
        ).pack(side="left", padx=(0, 16))

        self.show_removed_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            toolbar, text="Show removed", variable=self.show_removed_var,
            command=self._on_toggle_removed, font=(theme.FONT_FAMILY, 11),
            checkbox_width=18, checkbox_height=18,
            fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
            border_color=theme.BORDER, text_color=theme.FG_MUTED,
        ).pack(side="right", padx=(0, 16))

        search_entry = ctk.CTkEntry(
            toolbar, textvariable=self.search_var, placeholder_text="Search items or amounts…",
            width=240,
        )
        search_entry.pack(side="right", padx=10, pady=10)
        self.search_var.trace_add("write", lambda *a: self._on_search_changed())

        table_wrap = ctk.CTkFrame(self, fg_color=theme.BG_CARD, corner_radius=10)
        table_wrap.pack(side="top", fill="both", expand=True, padx=16, pady=(12, 8))
        table_wrap.grid_rowconfigure(0, weight=1)
        table_wrap.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            table_wrap, columns=COLUMNS, show="tree headings",
            style="Dark.Treeview", selectmode="extended",
        )
        self.tree.grid(row=0, column=0, sticky="nswe", padx=(2, 0), pady=2)

        vsb = ThinScrollbar(table_wrap, command=self.tree.yview, width=12, bg=theme.BG_CARD)
        vsb.grid(row=0, column=1, sticky="ns", pady=2, padx=(2, 4))
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.heading("#0", text=HEADING_TEXT["name"], command=lambda: self._on_sort("name"))
        self.tree.column("#0", width=360, minwidth=200, anchor="w", stretch=True)

        self.tree.heading("missing", text=HEADING_TEXT["missing"], command=lambda: self._on_sort("missing"))
        self.tree.column("missing", width=190, minwidth=120, anchor="w", stretch=False)

        self.tree.heading("total", text=HEADING_TEXT["total"], command=lambda: self._on_sort("total"))
        self.tree.column("total", width=90, minwidth=70, anchor="center", stretch=False)

        self.tree.heading("available", text=HEADING_TEXT["available"], command=lambda: self._on_sort("available"))
        self.tree.column("available", width=100, minwidth=80, anchor="center", stretch=False)

        self.tree.heading("done", text=HEADING_TEXT["checked"], command=lambda: self._on_sort("checked"))
        self.tree.column("done", width=64, minwidth=64, anchor="center", stretch=False)

        self._apply_column_visibility()

        self.tree.tag_configure("checked_row", foreground=theme.FG_FAINT)
        self.tree.tag_configure("removed_row", foreground=theme.FG_FAINT)

        self.tree.bind("<ButtonPress-1>", self._on_tree_press, add="+")
        self.tree.bind("<B1-Motion>", self._on_tree_drag_motion, add="+")
        self.tree.bind("<ButtonRelease-1>", self._on_tree_release, add="+")
        self.tree.bind("<Return>", self._on_enter)
        self.tree.bind("<KP_Enter>", self._on_enter)
        self.tree.bind("<Delete>", self._on_delete)

        status = ctk.CTkFrame(self, fg_color=theme.BG_PANEL, corner_radius=0, height=56)
        status.pack(side="bottom", fill="x")
        status.pack_propagate(False)

        self.progress_bar = ctk.CTkProgressBar(
            status, width=170, height=8, progress_color=theme.ACCENT, fg_color=theme.BORDER,
        )
        self.progress_bar.pack(side="left", padx=(18, 12), pady=10)

        self.status_label = ctk.CTkLabel(
            status, text="", font=(theme.FONT_FAMILY, 12, "bold"), text_color=theme.FG,
        )
        self.status_label.pack(side="left", pady=10)

        self.needed_label = ctk.CTkLabel(
            status, text="", font=(theme.FONT_FAMILY, 12), text_color=theme.FG_MUTED,
        )
        self.needed_label.pack(side="right", padx=18, pady=10)

        ctk.CTkLabel(
            status,
            text="Enter: check off + advance     Delete: remove from list",
            font=(theme.FONT_FAMILY, 10), text_color=theme.FG_FAINT,
        ).pack(side="right", padx=18, pady=10)

    def _apply_column_visibility(self) -> None:
        cols = ["missing"]
        if config.show_total_column:
            cols.append("total")
        if config.show_available_column:
            cols.append("available")
        cols.append("done")
        self.tree["displaycolumns"] = cols

    def _visible_rows(self):
        rows = [r for r in self.rows if (self.show_removed or not r["removed"])]
        query = self.search_var.get().strip().lower()
        if not query:
            return rows
        if query.isdigit():
            qnum = int(query)
            rows = [
                r for r in rows
                if qnum in (r["total"], r["missing"], r["available"]) or query in r["name"].lower()
            ]
        else:
            rows = [
                r for r in rows
                if query in r["name"].lower() or query in format_quantity(r["missing"], r["name"]).lower()
            ]
        return rows

    def _sorted_rows(self, rows):
        key_fns = {
            "name": lambda r: r["name"].lower(),
            "missing": lambda r: r["missing"],
            "total": lambda r: r["total"],
            "available": lambda r: r["available"],
            "checked": lambda r: r["checked"],
        }
        fn = key_fns.get(self.sort_key, key_fns["missing"])
        return sorted(rows, key=fn, reverse=self.sort_reverse)

    def _refresh_table(self, keep_selection: bool = True) -> None:
        previously_selected = set(self.tree.selection()) if keep_selection else set()

        self.tree.delete(*self.tree.get_children())
        rows = self._sorted_rows(self._visible_rows())
        self._current_order = [r["name"] for r in rows]

        for r in rows:
            tags = []
            if r["removed"]:
                tags.append("removed_row")
            elif r["checked"]:
                tags.append("checked_row")

            icon = self.app.icon_manager.get_cached(r["name"]) or self.app.icon_manager.get_placeholder(r["name"])
            done_glyph = "☑" if r["checked"] else "☐"
            label = r["name"] + ("  (removed)" if r["removed"] else "")
            values = (
                format_quantity(r["missing"], r["name"]),
                format_int(r["total"]),
                format_int(r["available"]),
                done_glyph,
            )
            self.tree.insert(
                "", "end", iid=r["name"], text=" " + label, image=icon,
                values=values, tags=tuple(tags),
            )

        for name in previously_selected:
            if self.tree.exists(name):
                self.tree.selection_add(name)

        self._update_status_bar()

    def _update_status_bar(self) -> None:
        active = [r for r in self.rows if not r["removed"]]
        total_count = len(active)
        checked_count = len([r for r in active if r["checked"]])
        pct = (checked_count / total_count * 100) if total_count else 100.0

        total_missing_sum = sum(r["missing"] for r in active)
        remaining_missing_sum = sum(r["missing"] for r in active if not r["checked"])

        self.status_label.configure(text=f"{checked_count} / {total_count} checked  ({pct:.0f}%)")
        self.needed_label.configure(
            text=f"Remaining: {format_int(remaining_missing_sum)}    Total needed: {format_int(total_missing_sum)}"
        )
        self.progress_bar.set((pct / 100.0) if total_count else 1.0)

    def _update_heading_labels(self) -> None:
        for key, col_id in (("name", "#0"), *[(k, COLUMN_ID_FOR_KEY[k]) for k in ("missing", "total", "available", "checked")]):
            base = HEADING_TEXT[key]
            suffix = ""
            if key == self.sort_key:
                suffix = "  ▲" if not self.sort_reverse else "  ▼"
            self.tree.heading(col_id, text=base + suffix)

    def _prefetch_icons(self) -> None:
        for r in self.rows:
            self.app.icon_manager.request(r["name"], self._on_icon_ready)

    def _on_icon_ready(self, name: str) -> None:
        if not self.winfo_exists():
            return
        if self.tree.exists(name):
            icon = self.app.icon_manager.get_cached(name)
            if icon:
                self.tree.item(name, image=icon)

    def _save_progress(self) -> None:
        data = {
            r["name"]: {"checked": r["checked"], "removed": r["removed"]}
            for r in self.rows
            if r["checked"] or r["removed"]
        }
        save_progress(self.progress_key, data)

    def _on_search_changed(self) -> None:
        if self._search_after_id:
            self.after_cancel(self._search_after_id)
        self._search_after_id = self.after(150, lambda: self._refresh_table())

    def _on_toggle_removed(self) -> None:
        self.show_removed = self.show_removed_var.get()
        self._refresh_table()

    def _on_sort(self, key: str) -> None:
        if self.sort_key == key:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_key = key
            self.sort_reverse = key in ("missing", "total", "available")
        self._update_heading_labels()
        self._refresh_table()

    def _colname_at(self, x: int) -> str | None:
        displaycols = self.tree["displaycolumns"]
        if displaycols == "#all":
            displaycols = self.tree["columns"]
        col = self.tree.identify_column(x)
        try:
            idx = int(str(col).replace("#", "")) - 1
            return displaycols[idx]
        except (ValueError, IndexError):
            return None

    def _set_row_checked_visual(self, iid: str, checked: bool) -> None:
        values = list(self.tree.item(iid, "values"))
        values[COLUMNS.index("done")] = "☑" if checked else "☐"
        r = self.row_by_name.get(iid)
        tags = []
        if r and r["removed"]:
            tags.append("removed_row")
        elif checked:
            tags.append("checked_row")
        self.tree.item(iid, values=values, tags=tuple(tags))

    def _drag_toggle_row(self, iid: str) -> None:
        if iid in self._drag_touched_rows:
            return
        self._drag_touched_rows.add(iid)
        r = self.row_by_name.get(iid)
        if not r:
            return
        r["checked"] = not r["checked"]
        self._set_row_checked_visual(iid, r["checked"])
        self._update_status_bar()

    def _select_toggle_row(self, iid: str) -> None:
        if iid in self._select_drag_touched:
            return
        self._select_drag_touched.add(iid)
        self.tree.selection_toggle(iid)

    def _on_tree_press(self, event) -> None:
        region = self.tree.identify_region(event.x, event.y)
        if region not in ("cell", "tree"):
            return
        row_iid = self.tree.identify_row(event.y)
        if not row_iid:
            return
        # we return "break" below which skips tk's default binding, so grab focus manually
        self.tree.focus_set()

        if region == "cell" and self._colname_at(event.x) == "done":
            self._drag_toggle_active = True
            self._drag_touched_rows = set()
            self._drag_toggle_row(row_iid)
            return

        # shift/ctrl held, let tk handle it
        if event.state & 0x0005:
            return
        self._select_drag_active = True
        self._select_drag_anchor = row_iid
        self._select_drag_moved = False
        self._select_drag_touched = set()
        return "break"

    def _on_tree_drag_motion(self, event) -> None:
        if self._drag_toggle_active:
            row_iid = self.tree.identify_row(event.y)
            if row_iid:
                self._drag_toggle_row(row_iid)
            return
        if self._select_drag_active:
            row_iid = self.tree.identify_row(event.y)
            if not row_iid:
                return "break"
            if not self._select_drag_moved:
                if row_iid == self._select_drag_anchor:
                    return "break"
                self._select_drag_moved = True
                self._select_toggle_row(self._select_drag_anchor)
            self._select_toggle_row(row_iid)
            return "break"

    def _on_tree_release(self, event) -> None:
        if self._drag_toggle_active:
            self._drag_toggle_active = False
            self._drag_touched_rows = set()
            self._save_progress()
            self._refresh_table()
            return
        if self._select_drag_active:
            if not self._select_drag_moved and self._select_drag_anchor:
                self.tree.selection_set(self._select_drag_anchor)
                self.tree.focus(self._select_drag_anchor)
            self._select_drag_active = False
            self._select_drag_anchor = None
            self._select_drag_moved = False
            self._select_drag_touched = set()
            return "break"

    def _next_after_selection(self, selected) -> str | None:
        selected_set = set(selected)
        indices = [self._current_order.index(n) for n in selected_set if n in self._current_order]
        if not indices:
            return None
        max_idx = max(indices)
        for j in range(max_idx + 1, len(self._current_order)):
            if self._current_order[j] not in selected_set:
                return self._current_order[j]
        return None

    def _select_only(self, name: str | None) -> None:
        self.tree.selection_set()
        if name and self.tree.exists(name):
            self.tree.selection_set(name)
            self.tree.focus(name)
            self.tree.see(name)

    def _check_off(self, selected: list[str]) -> None:
        if not selected:
            return
        next_name = self._next_after_selection(selected)
        for n in selected:
            r = self.row_by_name.get(n)
            if r:
                r["checked"] = True
        self._save_progress()
        self._refresh_table(keep_selection=False)
        self._select_only(next_name)

    def _on_enter(self, event) -> str:
        self._check_off(list(self.tree.selection()))
        return "break"

    def trigger_from_global_hotkey(self) -> None:
        selected = list(self.tree.selection())
        if not selected and self._current_order:
            selected = [self._current_order[0]]
        self._check_off(selected)

    def _on_delete(self, event) -> str:
        selected = list(self.tree.selection())
        if not selected:
            return "break"
        next_name = self._next_after_selection(selected)
        for n in selected:
            r = self.row_by_name.get(n)
            if r:
                r["removed"] = not r["removed"]
        self._save_progress()
        self._refresh_table(keep_selection=False)
        self._select_only(next_name)
        return "break"
