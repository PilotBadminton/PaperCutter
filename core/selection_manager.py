"""
选区管理模块
"""
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QImage
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class SelectionItem:
    page_num: int
    rect: tuple           # 原始坐标系 (x, y, w, h)
    image: QImage         # 显示用图（低分辨率版）
    preview: Optional[QImage] = None
    file_path: Optional[str] = None  # 原始文件路径，用于全分辨率导出
    shape_type: str = "rect"
    mask_points: Optional[list] = None


class SelectionManager(QObject):
    selection_added = Signal(object)
    selection_removed = Signal(int)
    selection_cleared = Signal()
    
    def __init__(self):
        super().__init__()
        self.selections: List[SelectionItem] = []
        self.current_mode: str = "题目"
        self.current_question_num: str = ""
    
    def add_selection(self, page_num: int, rect: tuple, image: QImage,
                      file_path: str = None, shape_type: str = "rect",
                      mask_points=None, preview: Optional[QImage] = None):
        selection = SelectionItem(
            page_num=page_num,
            rect=rect,
            image=image,
            preview=preview,
            file_path=file_path,
            shape_type=shape_type or "rect",
            mask_points=mask_points
        )
        self.selections.append(selection)
        self.selection_added.emit(selection)
    
    def remove_selection(self, index: int):
        if 0 <= index < len(self.selections):
            del self.selections[index]
            self.selection_removed.emit(index)
    
    def clear_selections(self):
        self.selections.clear()
        self.selection_cleared.emit()
    
    def get_selections(self) -> List[SelectionItem]:
        return self.selections
    
    def get_selection_count(self) -> int:
        return len(self.selections)
    
    def set_mode(self, mode: str):
        self.current_mode = mode
    
    def set_question_num(self, question_num: str):
        self.current_question_num = question_num
    
    def get_mode(self) -> str:
        return self.current_mode
    
    def get_question_num(self) -> str:
        return self.current_question_num
