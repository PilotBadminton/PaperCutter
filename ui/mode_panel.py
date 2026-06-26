from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QButtonGroup, QCheckBox, QFileDialog, QGroupBox, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton, QRadioButton,
                               QVBoxLayout, QWidget)

from config import persist
from config.settings import Settings
from core.export_naming import next_question_num
from ui.glass_effect import GlassEffect


def _btn_style():
    return GlassEffect.get_button_style()


def _accent_btn_style():
    s = Settings
    return f"""
        QPushButton {{
            background: {s.SURFACE['button_act']};
            border: 1px solid {s.BORDER['accent']};
            border-top: 1px solid {s.BORDER['highlight']};
            border-radius: {s.RADIUS['normal']}px;
            color: {s.TEXT['on_accent']};
            padding: 8px 14px;
            min-height: 28px;
            font-weight: {s.FONTS['weight_semibold']};
            font-size: {s.FONTS['size_label']}pt;
        }}
        QPushButton:hover {{
            background: {s.SURFACE['button_act_hov']};
            border: 1px solid {s.BORDER['focus']};
        }}
        QPushButton:pressed {{
            background: {s.SURFACE['button_act_prs']};
            border: 1px solid {s.BORDER['accent']};
        }}
        QPushButton:disabled {{
            background: {s.SURFACE['button_dsb']};
            border: 1px solid {s.BORDER['subtle']};
            color: {s.TEXT['disabled']};
        }}
    """


class ModePanel(QWidget):
    mode_changed = Signal(str)
    start_selection = Signal()
    selection_tool_changed = Signal(str)
    confirm_cut = Signal()
    add_selection = Signal()
    open_composition = Signal()

    def __init__(self, saved_path=None, export_prefix="", auto_increment_enabled=False):
        super().__init__()
        self.output_dir = Path(saved_path) if saved_path else None
        self._initial_export_prefix = export_prefix or ""
        self._initial_auto_increment = bool(auto_increment_enabled)
        self._init_ui()
        self._apply_styles()

    def _init_ui(self):
        s = Settings
        layout = QVBoxLayout()
        layout.setSpacing(s.SPACING['normal'])
        layout.setContentsMargins(s.SPACING['normal'], s.SPACING['normal'],
                                  s.SPACING['normal'], s.SPACING['normal'])

        mode_group = QGroupBox("切题模式")
        mode_layout = QVBoxLayout()
        mode_layout.setSpacing(s.SPACING['small'])

        self.question_radio = QRadioButton("切割题目")
        self.question_radio.setChecked(True)
        self.question_radio.toggled.connect(self._on_mode_changed)
        mode_layout.addWidget(self.question_radio)

        self.answer_radio = QRadioButton("切割答案")
        self.answer_radio.toggled.connect(self._on_mode_changed)
        mode_layout.addWidget(self.answer_radio)

        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        output_group = QGroupBox("输出位置")
        output_layout = QVBoxLayout()
        output_layout.setSpacing(s.SPACING['small'])

        self.output_path_label = QLabel()
        self.output_path_label.setWordWrap(True)
        self.output_path_label.setMinimumHeight(48)
        self.output_path_label.setObjectName("outputPathLabel")
        self._refresh_output_path_label()
        output_layout.addWidget(self.output_path_label)

        self.browse_btn = QPushButton("选择文件夹")
        self.browse_btn.clicked.connect(self._browse_output_dir)
        self.browse_btn.setFixedHeight(36)
        self.browse_btn.setStyleSheet(_btn_style())
        output_layout.addWidget(self.browse_btn)

        output_group.setLayout(output_layout)
        layout.addWidget(output_group)

        naming_group = QGroupBox("导出命名")
        naming_layout = QVBoxLayout()
        naming_layout.setSpacing(s.SPACING['small'])

        prefix_label = QLabel("自定义前缀")
        naming_layout.addWidget(prefix_label)

        self.prefix_input = QLineEdit()
        self.prefix_input.setPlaceholderText("留空则使用“题目/答案”")
        self.prefix_input.setText(self._initial_export_prefix)
        self.prefix_input.setFixedHeight(36)
        self.prefix_input.setToolTip("导出文件名格式：前缀_题号.png")
        naming_layout.addWidget(self.prefix_input)

        question_label = QLabel("题号")
        naming_layout.addWidget(question_label)

        self.question_num_input = QLineEdit()
        self.question_num_input.setPlaceholderText("例如 001、101、我爱你111")
        self.question_num_input.setFixedHeight(36)
        naming_layout.addWidget(self.question_num_input)

        self.auto_increment_checkbox = QCheckBox("导出成功后题号自动 +1")
        self.auto_increment_checkbox.setChecked(self._initial_auto_increment)
        self.auto_increment_checkbox.setToolTip("递增末尾数字；没有末尾数字时追加 1")
        naming_layout.addWidget(self.auto_increment_checkbox)

        self.prefix_input.textChanged.connect(self._save_settings)
        self.auto_increment_checkbox.toggled.connect(self._save_settings)

        naming_group.setLayout(naming_layout)
        layout.addWidget(naming_group)

        selection_group = QGroupBox("选区工具")
        selection_layout = QVBoxLayout()
        selection_layout.setSpacing(s.SPACING['small'])

        tool_row = QHBoxLayout()
        tool_row.setSpacing(s.SPACING['small'])
        self.rect_tool_radio = QRadioButton("矩形")
        self.rect_tool_radio.setChecked(True)
        self.free_tool_radio = QRadioButton("自由套索")
        self.selection_tool_group = QButtonGroup(self)
        self.selection_tool_group.addButton(self.rect_tool_radio)
        self.selection_tool_group.addButton(self.free_tool_radio)
        self.rect_tool_radio.toggled.connect(self._on_selection_tool_changed)
        self.free_tool_radio.toggled.connect(self._on_selection_tool_changed)
        tool_row.addWidget(self.rect_tool_radio)
        tool_row.addWidget(self.free_tool_radio)
        selection_layout.addLayout(tool_row)

        outside_label = QLabel("自由轮廓外")
        selection_layout.addWidget(outside_label)

        outside_row = QHBoxLayout()
        outside_row.setSpacing(s.SPACING['small'])
        self.outside_transparent_radio = QRadioButton("透明")
        self.outside_transparent_radio.setChecked(True)
        self.outside_white_radio = QRadioButton("白底")
        self.outside_group = QButtonGroup(self)
        self.outside_group.addButton(self.outside_transparent_radio)
        self.outside_group.addButton(self.outside_white_radio)
        outside_row.addWidget(self.outside_transparent_radio)
        outside_row.addWidget(self.outside_white_radio)
        selection_layout.addLayout(outside_row)

        selection_group.setLayout(selection_layout)
        layout.addWidget(selection_group)
        self._sync_selection_tool_options()

        self.start_selection_btn = QPushButton("开始选区")
        self.start_selection_btn.setCheckable(True)
        self.start_selection_btn.clicked.connect(self._on_start_selection)
        self.start_selection_btn.setFixedHeight(40)
        self.start_selection_btn.setStyleSheet(_btn_style())
        layout.addWidget(self.start_selection_btn)

        self.confirm_btn = QPushButton("确定切割")
        self.confirm_btn.clicked.connect(self._on_confirm_cut)
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.setFixedHeight(40)
        self.confirm_btn.setStyleSheet(_btn_style())
        layout.addWidget(self.confirm_btn)

        self.add_btn = QPushButton("添加到选区")
        self.add_btn.clicked.connect(self._on_add_selection)
        self.add_btn.setEnabled(False)
        self.add_btn.setFixedHeight(40)
        self.add_btn.setStyleSheet(_accent_btn_style())
        layout.addWidget(self.add_btn)

        self.composition_btn = QPushButton("自由编排")
        self.composition_btn.clicked.connect(self._on_open_composition)
        self.composition_btn.setEnabled(False)
        self.composition_btn.setFixedHeight(40)
        self.composition_btn.setStyleSheet(_btn_style())
        layout.addWidget(self.composition_btn)

        layout.addStretch()
        self.setLayout(layout)
        self.setFixedWidth(304)

    def _apply_styles(self):
        font = QFont(Settings.FONTS['family'])
        font.setPointSize(Settings.FONTS['size_body'])
        self.setFont(font)
        GlassEffect.apply_glass_effect(self, 'panel')

    def _refresh_output_path_label(self):
        text = str(self.output_dir) if self.output_dir else "未选择输出文件夹"
        self.output_path_label.setText(text)
        self.output_path_label.setToolTip(text)

    def _save_settings(self):
        data = {
            'export_prefix': self.get_export_prefix(),
            'auto_increment_enabled': self.is_auto_increment_enabled(),
        }
        if self.output_dir:
            data['output_dir'] = str(self.output_dir)
        persist.update(data)

    def _on_mode_changed(self):
        self.mode_changed.emit("题目" if self.question_radio.isChecked() else "答案")

    def _on_start_selection(self):
        if self.start_selection_btn.isChecked():
            self.start_selection_btn.setText("取消选区")
            self.start_selection.emit()
        else:
            self.start_selection_btn.setText("开始选区")
            self.start_selection.emit()

    def _on_confirm_cut(self):
        self.confirm_cut.emit()

    def _on_add_selection(self):
        self.add_selection.emit()

    def _on_open_composition(self):
        self.open_composition.emit()

    def _on_selection_tool_changed(self, checked=None):
        self._sync_selection_tool_options()
        self.selection_tool_changed.emit(self.get_selection_tool())

    def _sync_selection_tool_options(self):
        enabled = self.free_tool_radio.isChecked()
        self.outside_transparent_radio.setEnabled(enabled)
        self.outside_white_radio.setEnabled(enabled)

    def _browse_output_dir(self):
        start = str(self.output_dir) if self.output_dir else ""
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出文件夹", start)

        if dir_path:
            self.output_dir = Path(dir_path)
            self._refresh_output_path_label()
            self._save_settings()

    def get_mode(self):
        return "题目" if self.question_radio.isChecked() else "答案"

    def get_export_prefix(self):
        return self.prefix_input.text().strip()

    def get_selection_tool(self):
        return "free" if self.free_tool_radio.isChecked() else "rect"

    def get_selection_outside_mode(self):
        return "white" if self.outside_white_radio.isChecked() else "transparent"

    def is_auto_increment_enabled(self):
        return self.auto_increment_checkbox.isChecked()

    def get_question_num(self):
        return self.question_num_input.text().strip()

    def set_question_num(self, question_num):
        self.question_num_input.setText(str(question_num or ""))

    def increment_question_num(self):
        new_value = next_question_num(self.get_question_num())
        self.set_question_num(new_value)
        return new_value

    def get_output_dir(self):
        return self.output_dir

    def set_selection_active(self, has_selection):
        self.confirm_btn.setEnabled(has_selection)
        self.add_btn.setEnabled(has_selection)

    def cancel_selection(self):
        self.start_selection_btn.setChecked(False)
        self.start_selection_btn.setText("开始选区")
