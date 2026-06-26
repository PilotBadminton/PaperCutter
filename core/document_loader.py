"""
文档加载器模块
"""
from PySide6.QtGui import QImage, QImageReader
from PySide6.QtCore import QSize
from pathlib import Path
from PIL import Image as PILImage
import fitz

# 显示阈值：超过此尺寸的图片 QImageReader 缩略加载
_MAX_DISPLAY_W = 1920
_MAX_DISPLAY_H = 1440


class DocumentLoader:
    @staticmethod
    def load_image(file_path):
        image = QImage(str(file_path))
        if image.isNull():
            raise ValueError(f"无法加载图片：{file_path}")
        return image

    @staticmethod
    def load_image_adaptive(file_path, max_w=_MAX_DISPLAY_W, max_h=_MAX_DISPLAY_H):
        """返回 (display_qimage, orig_w, orig_h)，大图自动缩到 max 范围。"""
        reader = QImageReader(str(file_path))
        reader.setAutoTransform(True)
        orig = reader.size()
        ow, oh = orig.width(), orig.height()
        if ow <= max_w and oh <= max_h:
            return reader.read(), ow, oh
        ratio = min(max_w / ow, max_h / oh)
        reader.setScaledSize(QSize(int(ow * ratio), int(oh * ratio)))
        qimg = reader.read()
        if qimg.isNull():
            raise ValueError(f"无法加载图片：{file_path}")
        return qimg, ow, oh

    @staticmethod
    def reread_at_size(file_path, target_w, target_h):
        """从原文件解码指定尺寸（不超过原始像素）。"""
        reader = QImageReader(str(file_path))
        reader.setAutoTransform(True)
        orig = reader.size()
        tw = min(target_w, orig.width())
        th = min(target_h, orig.height())
        reader.setScaledSize(QSize(tw, th))
        return reader.read()

    @staticmethod
    def pil_open_crop(file_path, rect_orig):
        """用 PIL 从原始文件裁剪原始坐标系中的区域，返回 PIL Image。"""
        src = PILImage.open(str(file_path))
        x, y, w, h = rect_orig
        return src.crop((x, y, x + w, y + h))
    
    @staticmethod
    def load_pdf(file_path, page_num=0, zoom=2.5):
        doc = fitz.open(str(file_path))
        if page_num >= len(doc):
            doc.close()
            raise ValueError(f"页码超出范围：{page_num}")
        
        page = doc.load_page(page_num)
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix)
        
        img_data = pix.tobytes("png")
        image = QImage.fromData(img_data)
        
        doc.close()
        return image
    
    @staticmethod
    def get_pdf_page_count(file_path):
        doc = fitz.open(str(file_path))
        count = len(doc)
        doc.close()
        return count
    
    @staticmethod
    def get_document_name(file_path):
        return Path(file_path).stem
