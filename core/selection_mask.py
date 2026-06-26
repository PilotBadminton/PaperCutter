"""
自由形状选区 mask 工具。

约定：mask_points 始终是相对裁剪外接框左上角的坐标。
"""
from io import BytesIO

from PIL import Image as PILImage, ImageDraw, ImageChops
from PySide6.QtCore import QBuffer, QIODevice
from PySide6.QtGui import QImage

from core.compat import qimage_to_pil


def bounding_rect_from_points(points):
    pts = _clean_points(points)
    if not pts:
        return None
    min_x = min(x for x, _ in pts)
    min_y = min(y for _, y in pts)
    max_x = max(x for x, _ in pts)
    max_y = max(y for _, y in pts)
    return (
        int(min_x),
        int(min_y),
        max(1, int(max_x - min_x)),
        max(1, int(max_y - min_y)),
    )


def normalize_points_to_rect(points, rect):
    pts = _clean_points(points)
    if not pts or not rect:
        return None
    x, y, w, h = rect
    if w <= 0 or h <= 0:
        return None
    normalized = []
    for px, py in pts:
        nx = min(max(px - x, 0.0), float(w))
        ny = min(max(py - y, 0.0), float(h))
        normalized.append((float(nx), float(ny)))
    return normalized if len(normalized) >= 3 else None


def scale_points(points, sx, sy):
    pts = _clean_points(points)
    if not pts:
        return None
    return [(float(x) * float(sx), float(y) * float(sy)) for x, y in pts]


def apply_mask_to_crop(crop, mask_points=None, outside_mode="transparent"):
    if not mask_points:
        return crop.copy()

    base = crop.convert("RGBA")
    mask = build_alpha_mask(base.size, mask_points)
    if mask is None:
        return base

    alpha = ImageChops.multiply(base.getchannel("A"), mask)
    if outside_mode == "white":
        out = PILImage.new("RGBA", base.size, (255, 255, 255, 255))
        out.paste(base, (0, 0), alpha)
        return out

    out = base.copy()
    out.putalpha(alpha)
    return out


def crop_qimage_with_mask(qimage, rect, mask_points=None, outside_mode="transparent"):
    x, y, w, h = rect
    crop = qimage_to_pil(qimage).crop((x, y, x + w, y + h))
    return apply_mask_to_crop(crop, mask_points, outside_mode)


def qimage_from_pil(pil_img):
    buf = BytesIO()
    pil_img.save(buf, "PNG")
    return QImage.fromData(buf.getvalue())


def qimage_from_crop(qimage, rect, mask_points=None, outside_mode="transparent"):
    return qimage_from_pil(crop_qimage_with_mask(qimage, rect, mask_points, outside_mode))


def qimage_to_png_bytes(qimage):
    buf = QBuffer()
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    qimage.save(buf, "PNG")
    buf.close()
    return bytes(buf.data())


def build_alpha_mask(size, mask_points):
    w, h = int(size[0]), int(size[1])
    pts = _clean_points(mask_points)
    if w <= 0 or h <= 0 or len(pts) < 3:
        return None

    scale = _antialias_scale(w, h)
    hi_size = (w * scale, h * scale)
    hi_pts = [
        (
            min(max(float(x), 0.0), float(w)) * scale,
            min(max(float(y), 0.0), float(h)) * scale,
        )
        for x, y in pts
    ]
    mask = PILImage.new("L", hi_size, 0)
    draw = ImageDraw.Draw(mask)
    draw.polygon(hi_pts, fill=255)
    if scale > 1:
        mask = mask.resize((w, h), PILImage.Resampling.LANCZOS)
    return mask


def _antialias_scale(w, h):
    pixels = max(1, int(w) * int(h))
    if pixels <= 4_000_000:
        return 4
    if pixels <= 10_000_000:
        return 2
    return 1


def _clean_points(points):
    if not points:
        return []
    cleaned = []
    for point in points:
        try:
            x, y = point
            cleaned.append((float(x), float(y)))
        except (TypeError, ValueError):
            continue
    return cleaned
