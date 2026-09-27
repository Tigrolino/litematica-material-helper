from __future__ import annotations

import io
import math
from typing import Dict, List, Optional, Tuple

from PIL import Image

TEXTURE_BASE = "https://raw.githubusercontent.com/misode/mcmeta/assets/assets/minecraft/textures"
MODEL_BASE = "https://raw.githubusercontent.com/misode/mcmeta/assets/assets/minecraft/models"
REQUEST_TIMEOUT = 4.0
MAX_RESOLVE_DEPTH = 12
MAX_ELEMENTS = 24

FLAT_ICON_PARENTS = {
    "item/generated",
    "builtin/generated",
    "item/handheld",
    "item/handheld_rod",
}

# fences/walls use _inventory, doors/trapdoors use the bottom half
BLOCK_MODEL_SUFFIXES = ("", "_inventory", "_bottom", "_bottom_left")

COS30 = math.cos(math.radians(30))
SIN30 = math.sin(math.radians(30))
FACE_LIGHT = {"up": 1.0, "south": 0.8, "east": 0.6}


def _strip_ns(s: str) -> str:
    return s.split(":")[-1]


class _ModelSession:
    def __init__(self, http_get):
        self._http_get = http_get
        self._model_cache: Dict[str, Optional[dict]] = {}
        self._texture_cache: Dict[str, Optional[Image.Image]] = {}

    def fetch_model(self, model_id: str) -> Optional[dict]:
        model_id = _strip_ns(model_id)
        if model_id in self._model_cache:
            return self._model_cache[model_id]
        data = self._http_get(f"{MODEL_BASE}/{model_id}.json", True)
        self._model_cache[model_id] = data
        return data

    def fetch_texture(self, tex_path: str) -> Optional[Image.Image]:
        tex_path = _strip_ns(tex_path)
        if tex_path in self._texture_cache:
            return self._texture_cache[tex_path]
        raw = self._http_get(f"{TEXTURE_BASE}/{tex_path}.png", False)
        img = None
        if raw:
            try:
                img = Image.open(io.BytesIO(raw)).convert("RGBA")
            except Exception:
                img = None
        self._texture_cache[tex_path] = img
        return img

    def resolve_chain(self, model_id: str, depth: int = 0):
        if depth > MAX_RESOLVE_DEPTH:
            return {}, None
        data = self.fetch_model(model_id)
        if data is None:
            return {}, None
        textures = dict(data.get("textures", {}))
        elements = data.get("elements")
        parent = data.get("parent")
        if parent:
            p_textures, p_elements = self.resolve_chain(_strip_ns(parent), depth + 1)
            merged = {**p_textures, **textures}
            if elements is None:
                elements = p_elements
            return merged, elements
        return textures, elements

    def flat_icon_parent(self, item_model_id: str) -> Optional[str]:
        depth = 0
        data = self.fetch_model(item_model_id)
        parent = data.get("parent") if data else None
        while parent and depth < MAX_RESOLVE_DEPTH:
            stripped = _strip_ns(parent)
            if stripped in FLAT_ICON_PARENTS:
                return stripped
            nxt = self.fetch_model(stripped)
            if nxt is None:
                return None
            parent = nxt.get("parent")
            depth += 1
        return None

    def resolve_texture_ref(self, textures: dict, ref: Optional[str], depth: int = 0) -> Optional[str]:
        if depth > MAX_RESOLVE_DEPTH or ref is None:
            return None
        if ref.startswith("#"):
            return self.resolve_texture_ref(textures, textures.get(ref[1:]), depth + 1)
        return _strip_ns(ref)


def _proj(x: float, y: float, z: float, scale: float) -> Tuple[float, float]:
    sx = (x - z) * COS30
    sy = (x + z) * SIN30 - y
    return sx * scale, sy * scale


def _solve3(matrix, rhs) -> Optional[List[float]]:
    def det3(m):
        return (
            m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
            - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
            + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0])
        )

    d = det3(matrix)
    if abs(d) < 1e-9:
        return None
    result = []
    for i in range(3):
        mi = [row[:] for row in matrix]
        for r in range(3):
            mi[r][i] = rhs[r]
        result.append(det3(mi) / d)
    return result


def _affine_dst_to_src(dst_pts, src_pts) -> Optional[tuple]:
    matrix = [[dst_pts[i][0], dst_pts[i][1], 1] for i in range(3)]
    abc = _solve3(matrix, [p[0] for p in src_pts])
    dee = _solve3(matrix, [p[1] for p in src_pts])
    if abc is None or dee is None:
        return None
    return (*abc, *dee)


def _shade(img: Image.Image, factor: float) -> Image.Image:
    if factor >= 0.999:
        return img
    r, g, b, a = img.split()
    r = r.point(lambda v, f=factor: int(v * f))
    g = g.point(lambda v, f=factor: int(v * f))
    b = b.point(lambda v, f=factor: int(v * f))
    return Image.merge("RGBA", (r, g, b, a))


def _tint(img: Image.Image, tint_rgb: Tuple[int, int, int]) -> Image.Image:
    r, g, b, a = img.split()
    tr, tg, tb = tint_rgb
    r = r.point(lambda v, t=tr: v * t // 255)
    g = g.point(lambda v, t=tg: v * t // 255)
    b = b.point(lambda v, t=tb: v * t // 255)
    return Image.merge("RGBA", (r, g, b, a))


def _face_geometry(face_name: str, x1, y1, z1, x2, y2, z2):
    if face_name == "up":
        return [(x1, y2, z1), (x2, y2, z1), (x2, y2, z2), (x1, y2, z2)]
    if face_name == "south":
        return [(x1, y2, z2), (x2, y2, z2), (x2, y1, z2), (x1, y1, z2)]
    if face_name == "east":
        return [(x2, y2, z1), (x2, y2, z2), (x2, y1, z2), (x2, y1, z1)]
    return None


def _render_elements(
    session: _ModelSession, textures: dict, elements: list, tint_rgb: Optional[Tuple[int, int, int]]
) -> Optional[Image.Image]:
    scale = 6
    canvas_w = int(16 * COS30 * scale * 2) + 12
    canvas_h = int(16 * scale) * 2 + 12
    cx, cy = canvas_w / 2, canvas_h / 2

    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    drew_anything = False

    for elem in elements[:MAX_ELEMENTS]:
        fr = elem.get("from", [0, 0, 0])
        to = elem.get("to", [16, 16, 16])
        faces = elem.get("faces", {})
        x1, y1, z1 = fr
        x2, y2, z2 = to

        for face_name in ("east", "south", "up"):
            face = faces.get(face_name)
            if not face:
                continue
            tex_path = session.resolve_texture_ref(textures, face.get("texture"))
            if not tex_path:
                continue
            tex_img = session.fetch_texture(tex_path)
            if tex_img is None:
                continue

            tw, th = tex_img.size
            su, sv = tw / 16.0, th / 16.0
            u1, v1, u2, v2 = face.get("uv", [0, 0, 16, 16])
            px1, py1, px2, py2 = u1 * su, v1 * sv, u2 * su, v2 * sv
            crop_l, crop_t = min(px1, px2), min(py1, py2)
            crop_r = max(max(px1, px2), crop_l + 1)
            crop_b = max(max(py1, py2), crop_t + 1)
            try:
                crop = tex_img.crop((int(crop_l), int(crop_t), math.ceil(crop_r), math.ceil(crop_b)))
            except Exception:
                continue
            if tint_rgb:
                crop = _tint(crop, tint_rgb)

            local_src = [
                (px1 - crop_l, py1 - crop_t),
                (px2 - crop_l, py1 - crop_t),
                (px2 - crop_l, py2 - crop_t),
                (px1 - crop_l, py2 - crop_t),
            ]
            corners3d = _face_geometry(face_name, x1, y1, z1, x2, y2, z2)
            dst_pts = [(cx + p[0], cy + p[1]) for p in (_proj(*c, scale) for c in corners3d)]

            coeffs = _affine_dst_to_src(dst_pts[:3], local_src[:3])
            if coeffs is None:
                continue
            try:
                warped = crop.transform((canvas_w, canvas_h), Image.AFFINE, coeffs, resample=Image.BICUBIC)
            except Exception:
                continue
            warped = _shade(warped, FACE_LIGHT[face_name])
            canvas = Image.alpha_composite(canvas, warped)
            drew_anything = True

    if not drew_anything:
        return None
    bbox = canvas.getbbox()
    return canvas.crop(bbox) if bbox else canvas


def render_item_icon(slug: str, tint_rgb: Optional[Tuple[int, int, int]], http_get) -> Optional[Image.Image]:
    session = _ModelSession(http_get)

    item_model_id = f"item/{slug}"
    item_model = session.fetch_model(item_model_id)

    if item_model is not None:
        flat_parent = session.flat_icon_parent(item_model_id)
        if flat_parent:
            textures, _ = session.resolve_chain(item_model_id)
            tex_path = session.resolve_texture_ref(textures, textures.get("layer0"))
            if tex_path:
                img = session.fetch_texture(tex_path)
                if img is not None:
                    if tint_rgb:
                        img = _tint(img, tint_rgb)
                    return img
        textures, elements = session.resolve_chain(item_model_id)
        if elements:
            img = _render_elements(session, textures, elements, tint_rgb)
            if img is not None:
                return img

    for suffix in BLOCK_MODEL_SUFFIXES:
        candidate = f"block/{slug}{suffix}"
        textures, elements = session.resolve_chain(candidate)
        if elements:
            img = _render_elements(session, textures, elements, tint_rgb)
            if img is not None:
                return img

    return None
