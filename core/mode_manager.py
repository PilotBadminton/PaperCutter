"""
模式管理器模块
"""
from enum import Enum


class CutMode(Enum):
    QUESTION = "题目"
    ANSWER = "答案"


class ModeManager:
    def __init__(self):
        self.current_mode = CutMode.QUESTION
    
    def set_mode(self, mode):
        if isinstance(mode, str):
            self.current_mode = CutMode(mode)
        else:
            self.current_mode = mode
    
    def get_mode(self):
        return self.current_mode
    
    def get_mode_name(self):
        return self.current_mode.value
