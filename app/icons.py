from __future__ import annotations

import hashlib
import io
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable, Dict, List, Optional

from PIL import Image, ImageDraw, ImageTk

from . import model_render
from .config import ICON_CACHE_DIR

TEXTURE_BASE = "https://raw.githubusercontent.com/misode/mcmeta/assets/assets/minecraft/textures"
GALLERY_BASE = "https://raw.githubusercontent.com/Owen1212055/mc-assets/main/item-assets"
REQUEST_TIMEOUT = 4.0
MAX_CANDIDATES = 20
MANIFEST_PATH = ICON_CACHE_DIR / "manifest.json"

SHAPE_SUFFIXES = [
    "_fence_gate",
    "_hanging_sign",
    "_pressure_plate",
    "_trapdoor",
    "_stairs",
    "_fence",
    "_slab",
    "_wall",
    "_door",
    "_button",
    "_sign",
    "_carpet",
    "_pane",
]

PLACEHOLDER_PALETTE = [
    "#6b8f3c", "#8a6a3c", "#3c7a8f", "#8f3c6b", "#3c6b8f",
    "#8f6b3c", "#5c3c8f", "#3c8f5c", "#8f3c3c", "#3c8f8f",
]

RESAMPLE_BY_KIND = {
    "gallery": Image.LANCZOS,
    "model": Image.LANCZOS,
    "flat": Image.NEAREST,
    "texture": Image.NEAREST,
}

# biome tint colors for leaves/grass
_FOLIAGE_DEFAULT = (72, 181, 24)
_GRASS_DEFAULT = (145, 189, 89)
_BIRCH_LEAVES = (128, 167, 85)
_SPRUCE_LEAVES = (97, 153, 97)

TINT_MAP = {
    "oak_leaves": _FOLIAGE_DEFAULT,
    "jungle_leaves": _FOLIAGE_DEFAULT,
    "acacia_leaves": _FOLIAGE_DEFAULT,
    "dark_oak_leaves": _FOLIAGE_DEFAULT,
    "mangrove_leaves": _FOLIAGE_DEFAULT,
    "pale_oak_leaves": _FOLIAGE_DEFAULT,
    "bush": _FOLIAGE_DEFAULT,
    "vine": _FOLIAGE_DEFAULT,
    "birch_leaves": _BIRCH_LEAVES,
    "spruce_leaves": _SPRUCE_LEAVES,
    "grass_block": _GRASS_DEFAULT,
    "grass": _GRASS_DEFAULT,
    "short_grass": _GRASS_DEFAULT,
    "tall_grass": _GRASS_DEFAULT,
    "fern": _GRASS_DEFAULT,
    "large_fern": _GRASS_DEFAULT,
    "potted_fern": _GRASS_DEFAULT,
    "sugar_cane": _GRASS_DEFAULT,
}


def slugify(name: str) -> str:
    return (
        name.strip()
        .lower()
        .replace("'", "")
        .replace("-", "_")
        .replace(" ", "_")
    )


def _expand(root: str) -> List[str]:
    cands = [root]
    for suf in SHAPE_SUFFIXES:
        if root.endswith(suf) and len(root) > len(suf):
            base = root[: -len(suf)]
            cands.extend([base, base + "_planks", base + "s", base + "_bricks"])
            break
    cands.append(root + "s")
    for part in ("_top", "_side", "_front", "_end", "_bottom"):
        cands.append(root + part)
    return cands


def _candidate_slugs(slug: str) -> List[str]:
    roots = [slug]
    if slug.startswith("waxed_"):
        roots.append(slug[len("waxed_"):])
    if slug.endswith("_wood"):
        roots.append(slug[: -len("_wood")] + "_log")

    cands: List[str] = []
    for root in roots:
        cands.extend(_expand(root))

    seen = set()
    out = []
    for c in cands:
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out[:MAX_CANDIDATES]


def _initials(name: str) -> str:
    words = [w for w in name.split() if w]
    if not words:
        return "?"
    if len(words) == 1:
        return words[0][:2].upper()
    return (words[0][0] + words[1][0]).upper()


def _placeholder_image(name: str, size: int) -> Image.Image:
    digest = hashlib.md5(name.encode("utf-8")).hexdigest()
    color = PLACEHOLDER_PALETTE[int(digest[:2], 16) % len(PLACEHOLDER_PALETTE)]
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    pad = max(1, size // 16)
    radius = max(3, size // 6)
    draw.rounded_rectangle([pad, pad, size - pad, size - pad], radius=radius, fill=color)
    text = _initials(name)
    try:
        bbox = draw.textbbox((0, 0), text)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(
            (size / 2 - tw / 2 - bbox[0], size / 2 - th / 2 - bbox[1]),
            text,
            fill="#f2f2f2",
        )
    except Exception:
        pass
    return img


def _tint_image(img: Image.Image, tint: tuple) -> Image.Image:
    img = img.convert("RGBA")
    r, g, b, a = img.split()
    tr, tg, tb = tint
    r = r.point(lambda v, t=tr: v * t // 255)
    g = g.point(lambda v, t=tg: v * t // 255)
    b = b.point(lambda v, t=tb: v * t // 255)
    return Image.merge("RGBA", (r, g, b, a))


class IconManager:
    def __init__(self, root, size: int = 28, max_workers: int = 6):
        self._root = root
        self.size = size
        ICON_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._manifest_lock = threading.Lock()
        self._manifest: Dict[str, dict] = self._load_manifest()
        self._photo_cache: Dict[str, ImageTk.PhotoImage] = {}
        self._placeholder_cache: Dict[str, ImageTk.PhotoImage] = {}
        self._pending: set = set()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._session = None

    def _load_manifest(self) -> Dict[str, dict]:
        if MANIFEST_PATH.exists():
            try:
                with open(MANIFEST_PATH, "r", encoding="utf-8") as fh:
                    return json.load(fh)
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def _save_manifest(self) -> None:
        tmp = MANIFEST_PATH.with_suffix(".tmp")
        with self._manifest_lock:
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(self._manifest, fh, indent=2)
            os.replace(tmp, MANIFEST_PATH)

    def get_placeholder(self, name: str) -> ImageTk.PhotoImage:
        if name not in self._placeholder_cache:
            img = _placeholder_image(name, self.size)
            self._placeholder_cache[name] = ImageTk.PhotoImage(img)
        return self._placeholder_cache[name]

    def get_cached(self, name: str) -> Optional[ImageTk.PhotoImage]:
        return self._photo_cache.get(name)

    def request(self, name: str, on_ready: Callable[[str], None]) -> None:
        if name in self._photo_cache or name in self._pending:
            return
        slug = slugify(name)
        entry = self._manifest.get(slug, {})
        cached_file = entry.get("file")
        kind = entry.get("kind")
        if cached_file and kind == "gallery":
            path = ICON_CACHE_DIR / cached_file
            if path.exists():
                self._pending.add(name)
                self._executor.submit(self._load_from_disk, name, path, kind, on_ready)
                return
        if entry.get("status") == "miss" and kind == "gallery_miss":
            return
        self._pending.add(name)
        self._executor.submit(self._resolve_and_download, name, slug, on_ready)

    def retry_missing(self) -> None:
        with self._manifest_lock:
            self._manifest = {
                k: v for k, v in self._manifest.items() if v.get("status") != "miss"
            }
        self._save_manifest()

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)

    def _get_session(self):
        if self._session is None:
            import requests

            s = requests.Session()
            s.headers.update(
                {"User-Agent": "LitematicaMaterialHelper/1.0 (personal desktop app)"}
            )
            self._session = s
        return self._session

    def _http_get(self, url: str, json_response: bool):
        session = self._get_session()
        try:
            resp = session.get(url, timeout=REQUEST_TIMEOUT)
        except Exception:
            return None
        if resp.status_code != 200:
            return None
        if json_response:
            try:
                return resp.json()
            except Exception:
                return None
        return resp.content

    def _load_from_disk(self, name: str, path: Path, kind: str, on_ready) -> None:
        try:
            data = path.read_bytes()
        except OSError:
            data = None
        self._root.after(0, self._finish, name, data, kind, on_ready)

    def _download_gallery_icon(self, slug: str) -> Optional[bytes]:
        session = self._get_session()
        url = f"{GALLERY_BASE}/{slug.upper()}.png"
        try:
            resp = session.get(url, timeout=REQUEST_TIMEOUT)
        except Exception:
            return None
        if resp.status_code == 200 and resp.content:
            return resp.content
        return None

    def _download_legacy_texture(self, slug: str) -> Optional[bytes]:
        session = self._get_session()
        for cand in _candidate_slugs(slug):
            for folder in ("block", "item"):
                url = f"{TEXTURE_BASE}/{folder}/{cand}.png"
                try:
                    resp = session.get(url, timeout=REQUEST_TIMEOUT)
                except Exception:
                    continue
                if resp.status_code == 200 and resp.content:
                    return resp.content
        return None

    def _resolve_and_download(self, name: str, slug: str, on_ready) -> None:
        tint = TINT_MAP.get(slug)
        img: Optional[Image.Image] = None
        kind: Optional[str] = None

        gallery_raw = self._download_gallery_icon(slug)
        if gallery_raw:
            try:
                img = Image.open(io.BytesIO(gallery_raw)).convert("RGBA")
                kind = "gallery"
            except Exception:
                img = None

        if img is None:
            try:
                rendered = model_render.render_item_icon(slug, tint, self._http_get)
            except Exception:
                rendered = None
            if rendered is not None:
                img = rendered
                kind = "model"

        if img is None:
            raw = self._download_legacy_texture(slug)
            if raw:
                try:
                    img = Image.open(io.BytesIO(raw)).convert("RGBA")
                    if tint:
                        img = _tint_image(img, tint)
                    kind = "texture"
                except Exception:
                    img = None

        data: Optional[bytes] = None
        if img is not None:
            filename = f"{slug}.png"
            buf = io.BytesIO()
            try:
                img.save(buf, format="PNG")
                data = buf.getvalue()
                (ICON_CACHE_DIR / filename).write_bytes(data)
            except OSError:
                data = None
            if data is not None:
                with self._manifest_lock:
                    self._manifest[slug] = {"file": filename, "kind": kind}
                self._save_manifest()

        if data is None:
            with self._manifest_lock:
                self._manifest[slug] = {"status": "miss", "kind": "gallery_miss"}
            self._save_manifest()

        self._root.after(0, self._finish, name, data, kind or "texture", on_ready)

    def _finish(self, name: str, data: Optional[bytes], kind: str, on_ready) -> None:
        self._pending.discard(name)
        if data:
            try:
                img = Image.open(io.BytesIO(data)).convert("RGBA")
                resample = RESAMPLE_BY_KIND.get(kind, Image.NEAREST)
                img.thumbnail((self.size, self.size), resample)
                canvas = Image.new("RGBA", (self.size, self.size), (0, 0, 0, 0))
                off = ((self.size - img.width) // 2, (self.size - img.height) // 2)
                canvas.paste(img, off, img)
                self._photo_cache[name] = ImageTk.PhotoImage(canvas)
            except Exception:
                pass
        if on_ready:
            try:
                on_ready(name)
            except Exception:
                pass
