from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

_TITLE_RE = re.compile(r"Material List for placement\s+'(.*)'", re.IGNORECASE)

_ROW_RE = re.compile(
    r"^\|\s*(?P<name>.+?)\s*\|\s*(?P<total>-?[\d,]+)\s*\|\s*(?P<missing>-?[\d,]+)\s*\|\s*(?P<available>-?[\d,]+)\s*\|\s*$"
)

_HEADER_NAMES = {"item"}


@dataclass
class MaterialItem:
    name: str
    total: int
    missing: int
    available: int


@dataclass
class MaterialList:
    source_path: Path
    title: str
    items: List[MaterialItem]

    @property
    def item_count(self) -> int:
        return len(self.items)

    @property
    def total_missing(self) -> int:
        return sum(i.missing for i in self.items)


def _clean_int(raw: str) -> int:
    return int(raw.replace(",", "").strip())


def parse_material_list_text(text: str, source_path: Path) -> MaterialList:
    title: Optional[str] = None
    items: List[MaterialItem] = []
    seen = set()

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if title is None:
            m = _TITLE_RE.search(line)
            if m:
                title = m.group(1).strip() or "Unnamed"
                continue

        m = _ROW_RE.match(line)
        if not m:
            continue

        name = m.group("name").strip()
        if not name or name.lower() in _HEADER_NAMES:
            continue

        try:
            total = _clean_int(m.group("total"))
            missing = _clean_int(m.group("missing"))
            available = _clean_int(m.group("available"))
        except ValueError:
            continue

        if name.lower() == "item":
            continue

        key = name
        # paginated exports sometimes repeat a row, keep the first one
        if key in seen:
            continue
        seen.add(key)

        items.append(MaterialItem(name=name, total=total, missing=missing, available=available))

    if title is None:
        title = source_path.stem

    return MaterialList(source_path=source_path, title=title, items=items)


def parse_material_list_file(path: Path) -> MaterialList:
    text = path.read_text(encoding="utf-8", errors="replace")
    return parse_material_list_text(text, path)
