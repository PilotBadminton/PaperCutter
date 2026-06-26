"""
PySide6 兼容工具 — QImage ↔ PIL
"""
import io
from PIL import Image
from PySide6.QtGui import QImage
from PySide6.QtCore import QBuffer, QIODevice


def qimage_to_pil(qimg: QImage) -> Image.Image:
    """QImage → PIL Image（PySide6 用 QBuffer 替代 BytesIO）。"""
    buf = QBuffer()
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    qimg.save(buf, "PNG")
    buf.close()
    return Image.open(io.BytesIO(bytes(buf.data())))
