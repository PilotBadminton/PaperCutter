"""
页面导航器模块
"""
from PySide6.QtCore import QObject, Signal


class PageNavigator(QObject):
    page_changed = Signal(int)
    
    def __init__(self, total_pages):
        super().__init__()
        self.current_page = 0
        self.total_pages = total_pages
    
    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.page_changed.emit(self.current_page)
    
    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.page_changed.emit(self.current_page)
    
    def goto_page(self, page_num):
        if 0 <= page_num < self.total_pages:
            self.current_page = page_num
            self.page_changed.emit(self.current_page)
    
    def get_current_page(self):
        return self.current_page
    
    def get_total_pages(self):
        return self.total_pages
