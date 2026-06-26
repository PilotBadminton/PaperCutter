from PySide6.QtWidgets import QStatusBar, QLabel
from config.settings import Settings
from ui.glass_effect import GlassEffect


_SEP_STYLE = """
    QLabel {{
        color: {c};
        font-size: {sz}pt;
        padding: 0 4px;
    }}
"""


def _lbl(text, color=None, fw=None):
    lbl = QLabel(text)
    c = color or Settings.TEXT['primary']
    css = f"""
        QLabel {{
            color: {c};
            font-size: {Settings.FONTS['size_caption']}pt;
            padding: 4px 8px;
            background-color: {Settings.SURFACE['bg_base']};
            border: 1px solid {Settings.BORDER['subtle']};
            border-radius: {Settings.RADIUS['micro']}px;
        }}
    """
    if fw:
        css = css.rstrip('}') + f" font-weight: {fw};" + "}"
    lbl.setStyleSheet(css)
    return lbl


class StatusBar(QStatusBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        GlassEffect.apply_glass_effect(self, 'statusbar')
        self._init_ui()

    def _init_ui(self):
        self.file_label = _lbl("未打开文件")
        self.addWidget(self.file_label)

        sep_css = _SEP_STYLE.format(
            c='rgba(0, 0, 0, 0.3)',
            sz=Settings.FONTS['size_caption'],
        )
        sep1 = QLabel("|")
        sep1.setStyleSheet(sep_css)
        self.addPermanentWidget(sep1)

        self.page_label = _lbl("页码: -/-")
        self.addPermanentWidget(self.page_label)

        sep2 = QLabel("|")
        sep2.setStyleSheet(sep_css)
        self.addPermanentWidget(sep2)

        self.mode_label = _lbl("模式: 题目", color=Settings.TEXT['primary'], fw=Settings.FONTS['weight_bold'])
        self.addPermanentWidget(self.mode_label)

        sep3 = QLabel("|")
        sep3.setStyleSheet(sep_css)
        self.addPermanentWidget(sep3)

        self.zoom_label = _lbl("缩放: 100%")
        self.addPermanentWidget(self.zoom_label)

    def set_file_info(self, file_name):
        self.file_label.setText(f"文件: {file_name}")

    def set_page_info(self, current, total):
        if total > 0:
            self.page_label.setText(f"页码: {current + 1}/{total}")
        else:
            self.page_label.setText("页码: -/-")

    def set_mode_info(self, mode):
        self.mode_label.setText(f"模式: {mode}")

    def set_zoom_info(self, zoom):
        self.zoom_label.setText(f"缩放: {int(zoom * 100)}%")

    def set_selection_info(self, rect, shape_type="rect"):
        if rect:
            x, y, w, h = rect
            label = "自由选区" if shape_type == "free" else "选区"
            self.showMessage(f"{label}: ({x}, {y}) {w}x{h}", 3000)
        else:
            self.clearMessage()
