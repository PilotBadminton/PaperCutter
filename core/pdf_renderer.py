"""
PDF渲染器模块
"""
import fitz
from PySide6.QtGui import QImage
from PySide6.QtCore import QObject, Signal
from collections import OrderedDict


class PDFRenderer(QObject):
    rendered = Signal(int, QImage)
    
    def __init__(self, file_path, max_cache_size=20):
        super().__init__()
        self.file_path = file_path
        self.doc = fitz.open(file_path)
        self.cache = OrderedDict()
        self.max_cache_size = max_cache_size
    
    def render_page(self, page_num, zoom=2.5):
        zoom = max(0.1, min(zoom, 10.0))
        cache_key = (page_num, zoom)
        
        if cache_key in self.cache:
            self.cache.move_to_end(cache_key)
            return self.cache[cache_key]
        
        if page_num >= len(self.doc):
            raise ValueError(f"页码超出范围：{page_num}")
        
        page = self.doc.load_page(page_num)
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix)
        
        img_data = pix.tobytes("png")
        image = QImage.fromData(img_data)
        
        self.cache[cache_key] = image
        
        if len(self.cache) > self.max_cache_size:
            self.cache.popitem(last=False)
        
        return image
    
    def get_page_size(self, page_num, zoom=2.5):
        if page_num >= len(self.doc):
            raise ValueError(f"页码超出范围：{page_num}")
        page = self.doc.load_page(page_num)
        w = int(page.rect.width * zoom)
        h = int(page.rect.height * zoom)
        return (w, h)

    def get_page_count(self):
        return len(self.doc)
    
    def clear_cache(self):
        self.cache.clear()
    
    def close(self):
        self.doc.close()
        self.cache.clear()
