from __future__ import annotations

import tkinter as tk

from .. import theme


def _round_rect(canvas: tk.Canvas, x1: float, y1: float, x2: float, y2: float, radius: float, **kwargs):
    radius = max(0.0, min(radius, (x2 - x1) / 2, (y2 - y1) / 2))
    points = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


class ThinScrollbar(tk.Canvas):
    MIN_THUMB = 28
    PAD = 3

    def __init__(self, parent, command=None, width: int = 12, **kwargs):
        bg = kwargs.pop("bg", theme.BG_CARD)
        super().__init__(parent, width=width, highlightthickness=0, bd=0, bg=bg, **kwargs)
        self.command = command
        self._first = 0.0
        self._last = 1.0
        self._dragging = False
        self._drag_grab_offset = 0.0
        self._hover = False

        self.bind("<Configure>", lambda e: self._redraw())
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_motion)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))

    def set(self, first, last) -> None:
        self._first = max(0.0, float(first))
        self._last = min(1.0, float(last))
        self._redraw()

    def _thumb_bounds(self):
        h = self.winfo_height()
        if h <= 1:
            return 0.0, 0.0, h
        y1 = self._first * h
        y2 = self._last * h
        if y2 - y1 < self.MIN_THUMB:
            mid = (y1 + y2) / 2
            y1, y2 = mid - self.MIN_THUMB / 2, mid + self.MIN_THUMB / 2
            if y1 < 0:
                y1, y2 = 0, self.MIN_THUMB
            elif y2 > h:
                y1, y2 = h - self.MIN_THUMB, h
        return y1, y2, h

    def _redraw(self) -> None:
        self.delete("all")
        w = self.winfo_width()
        y1, y2, h = self._thumb_bounds()
        if h <= 1 or w <= 1:
            return
        if self._last - self._first >= 0.999:
            return
        color = theme.ACCENT_DIM if (self._dragging or self._hover) else theme.BG_HOVER
        x1, x2 = self.PAD, w - self.PAD
        radius = max(1.0, (x2 - x1) / 2)
        _round_rect(self, x1, y1 + self.PAD, x2, y2 - self.PAD, radius, fill=color, outline="")

    def _on_press(self, event) -> None:
        y1, y2, _ = self._thumb_bounds()
        if y1 <= event.y <= y2:
            self._drag_grab_offset = event.y - y1
        else:
            self._drag_grab_offset = (y2 - y1) / 2
        self._dragging = True
        self._jump_to(event.y)
        self._redraw()

    def _on_motion(self, event) -> None:
        if self._dragging:
            self._jump_to(event.y)

    def _on_release(self, event) -> None:
        self._dragging = False
        self._redraw()

    def _jump_to(self, y: float) -> None:
        _, _, h = self._thumb_bounds()
        if h <= 1 or not self.command:
            return
        thumb_h = max((self._last - self._first) * h, self.MIN_THUMB)
        new_y1 = min(max(0.0, y - self._drag_grab_offset), h - thumb_h)
        frac = (new_y1 / h) if h > thumb_h else 0.0
        self.command("moveto", frac)

    def _set_hover(self, val: bool) -> None:
        self._hover = val
        self._redraw()
