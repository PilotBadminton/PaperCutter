from PySide6.QtWidgets import (QToolBar, QWidget, QSpinBox, QLabel,
                               QHBoxLayout, QLineEdit)
from PySide6.QtGui import QAction, QIcon, QFont
from PySide6.QtCore import Qt, QSize, Signal
from config.settings import Settings
from ui.glass_effect import GlassEffect


_STYLE_LABEL = """
    QLabel {{
        color: {txt};
        font-size: {sz}pt;
        padding: 4px 8px;
        background-color: {bg};
        border: 1px solid {bd};
        border-radius: {br}px;
    }}
"""

_STYLE_SPINBOX = """
    QSpinBox {{
        background-color: {bg};
        border: 1px solid {bd};
        border-radius: {br}px;
        padding: 4px 6px;
        color: {txt};
        font-size: {sz}pt;
    }}
    QSpinBox:hover {{
        border: 1px solid {hv};
        background-color: {bgh};
    }}
    QSpinBox:focus {{
        border: 1px solid {fc};
        background-color: {bgf};
    }}
"""


class ToolBar(QToolBar):
    zoom_changed = Signal(float)
    page_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(False)
        self.setIconSize(QSize(20, 20))
        self._create_actions()
        self._create_widgets()
        GlassEffect.apply_glass_effect(self, 'toolbar')

    def _create_actions(self):
        self.open_action = QAction("打开", self)
        self.open_action.setShortcut("Ctrl+O")
        self.addAction(self.open_action)
        self.addSeparator()

        self.prev_page_action = QAction("上一页", self)
        self.prev_page_action.setShortcut("Ctrl+Left")
        self.prev_page_action.setEnabled(False)
        self.addAction(self.prev_page_action)

        self.next_page_action = QAction("下一页", self)
        self.next_page_action.setShortcut("Ctrl+Right")
        self.next_page_action.setEnabled(False)
        self.addAction(self.next_page_action)
        self.addSeparator()

        self.zoom_in_action = QAction("放大", self)
        self.zoom_in_action.setShortcut("Ctrl++")
        self.addAction(self.zoom_in_action)

        self.zoom_out_action = QAction("缩小", self)
        self.zoom_out_action.setShortcut("Ctrl+-")
        self.addAction(self.zoom_out_action)

        self.fit_width_action = QAction("适应宽度", self)
        self.addAction(self.fit_width_action)

        self.fit_page_action = QAction("适应页面", self)
        self.addAction(self.fit_page_action)

    def _mk_label(self, text, bg=None):
        lbl = QLabel(text)
        sz = Settings.FONTS['size_caption']
        lbl.setStyleSheet(_STYLE_LABEL.format(
            txt=Settings.TEXT['primary'],
            sz=sz,
            bg=bg or Settings.SURFACE['bg_base'],
            bd=Settings.BORDER['subtle'],
            br=Settings.RADIUS['micro'],
        ))
        return lbl

    def _create_widgets(self):
        self.addSeparator()

        self.page_label = self._mk_label("页码: -/-")
        self.addWidget(self.page_label)
        self.addSeparator()

        page_input_widget = QWidget()
        page_input_layout = QHBoxLayout()
        page_input_layout.setContentsMargins(0, 0, 0, 0)
        page_input_layout.setSpacing(4)

        page_input_label = self._mk_label("跳转:")
        page_input_layout.addWidget(page_input_label)

        self.page_input = QSpinBox()
        self.page_input.setMinimum(1)
        self.page_input.setMaximum(9999)
        self.page_input.setFixedWidth(60)
        self.page_input.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)
        sz = Settings.FONTS['size_caption']
        self.page_input.setStyleSheet(_STYLE_SPINBOX.format(
            bg=Settings.SURFACE['input'],
            bd=Settings.BORDER['input'],
            br=Settings.RADIUS['micro'],
            txt=Settings.TEXT['primary'],
            sz=sz,
            hv=Settings.BORDER['strong'],
            bgh=Settings.SURFACE['panel_hover'],
            fc=Settings.BORDER['focus'],
            bgf=Settings.SURFACE['input_focus'],
        ))
        self.page_input.valueChanged.connect(self._on_page_input_changed)
        self.page_input.editingFinished.connect(self._on_page_input_finished)
        page_input_layout.addWidget(self.page_input)
        page_input_widget.setLayout(page_input_layout)
        self.addWidget(page_input_widget)
        self.addSeparator()

        self.zoom_label = self._mk_label("缩放: 100%")
        self.addWidget(self.zoom_label)
        self.addSeparator()

        zoom_input_widget = QWidget()
        zoom_input_layout = QHBoxLayout()
        zoom_input_layout.setContentsMargins(0, 0, 0, 0)
        zoom_input_layout.setSpacing(4)

        zoom_input_label = self._mk_label("倍率:")
        zoom_input_layout.addWidget(zoom_input_label)

        self.zoom_input = QSpinBox()
        self.zoom_input.setMinimum(10)
        self.zoom_input.setMaximum(500)
        self.zoom_input.setSuffix("%")
        self.zoom_input.setFixedWidth(80)
        self.zoom_input.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)
        self.zoom_input.setStyleSheet(_STYLE_SPINBOX.format(
            bg=Settings.SURFACE['input'],
            bd=Settings.BORDER['input'],
            br=Settings.RADIUS['micro'],
            txt=Settings.TEXT['primary'],
            sz=sz,
            hv=Settings.BORDER['strong'],
            bgh=Settings.SURFACE['panel_hover'],
            fc=Settings.BORDER['focus'],
            bgf=Settings.SURFACE['input_focus'],
        ))
        self.zoom_input.valueChanged.connect(self._on_zoom_input_changed)
        self.zoom_input.editingFinished.connect(self._on_zoom_input_finished)
        zoom_input_layout.addWidget(self.zoom_input)
        zoom_input_widget.setLayout(zoom_input_layout)
        self.addWidget(zoom_input_widget)

    def _on_page_input_changed(self, value):
        pass

    def _on_page_input_finished(self):
        self.page_changed.emit(self.page_input.value() - 1)

    def _on_zoom_input_changed(self, value):
        pass

    def _on_zoom_input_finished(self):
        self.zoom_changed.emit(self.zoom_input.value() / 100.0)

    def set_page_info(self, current, total):
        if total > 0:
            self.page_label.setText(f"页码: {current + 1}/{total}")
            self.prev_page_action.setEnabled(current > 0)
            self.next_page_action.setEnabled(current < total - 1)
            self.page_input.blockSignals(True)
            self.page_input.setMaximum(total)
            self.page_input.setValue(current + 1)
            self.page_input.blockSignals(False)
        else:
            self.page_label.setText("页码: -/-")
            self.prev_page_action.setEnabled(False)
            self.next_page_action.setEnabled(False)
            self.page_input.setEnabled(False)

    def set_zoom_info(self, zoom):
        self.zoom_label.setText(f"缩放: {int(zoom * 100)}%")
        self.zoom_input.blockSignals(True)
        self.zoom_input.setValue(int(zoom * 100))
        self.zoom_input.blockSignals(False)

    def enable_pdf_controls(self, enabled):
        self.prev_page_action.setEnabled(enabled)
        self.next_page_action.setEnabled(enabled)
        self.page_input.setEnabled(enabled)
