from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QListWidget, QListWidgetItem)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from config.settings import Settings
from core.selection_manager import SelectionItem
from core.selection_mask import qimage_from_crop
from ui.glass_effect import GlassEffect


class SelectionListWidget(QWidget):
    export_merged = Signal()
    clear_all = Signal()

    def __init__(self):
        super().__init__()
        self.selections = []
        self._init_ui()
        self._apply_styles()

    def _init_ui(self):
        s = Settings
        layout = QVBoxLayout()
        layout.setSpacing(s.SPACING['normal'])
        layout.setContentsMargins(s.SPACING['normal'], s.SPACING['normal'],
                                  s.SPACING['normal'], s.SPACING['normal'])

        header_label = QLabel("已选区域")
        header_label.setStyleSheet(f"""
            QLabel {{
                font-size: {s.FONTS['size_subtitle']}pt;
                font-weight: {s.FONTS['weight_bold']};
                color: {s.TEXT['primary']};
                padding: 4px 0;
            }}
        """)
        layout.addWidget(header_label)

        self.selection_list = QListWidget()
        self.selection_list.setStyleSheet(f"""
            QListWidget {{
                background: {s.SURFACE['panel']};
                border: 1px solid {s.BORDER['subtle']};
                border-radius: {s.RADIUS['normal']}px;
                padding: 5px;
            }}
            QListWidget::item {{
                background: {s.SURFACE['list_item']};
                border: 1px solid {s.BORDER['list_item']};
                border-radius: {s.RADIUS['small']}px;
                margin: 3px;
                padding: 8px;
            }}
            QListWidget::item:hover {{
                background: {s.SURFACE['panel_hover']};
                border: 1px solid {s.BORDER['normal']};
            }}
            QListWidget::item:selected {{
                background: {s.SURFACE['list_sel']};
                border: 1px solid {s.BORDER['accent']};
            }}
            {GlassEffect._get_scrollbar_styles()}
        """)
        layout.addWidget(self.selection_list)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(s.SPACING['small'])

        self.export_btn = QPushButton("合并导出")
        self.export_btn.clicked.connect(self.export_merged.emit)
        self.export_btn.setEnabled(False)
        self.export_btn.setFixedHeight(32)
        self.export_btn.setStyleSheet(self._compact_btn_style())
        button_layout.addWidget(self.export_btn)

        self.clear_btn = QPushButton("清除全部")
        self.clear_btn.clicked.connect(self._on_clear_all)
        self.clear_btn.setEnabled(False)
        self.clear_btn.setFixedHeight(32)
        self.clear_btn.setStyleSheet(self._compact_btn_style())
        button_layout.addWidget(self.clear_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    @staticmethod
    def _compact_btn_style():
        s = Settings
        return f"""
            QPushButton {{
                background: {s.SURFACE['button']};
                border: 1px solid {s.BORDER['strong']};
                border-top: 1px solid rgba(255,255,255,0.60);
                border-radius: {s.RADIUS['normal']}px;
                color: {s.TEXT['primary']};
                padding: 6px 8px;
                font-weight: {s.FONTS['weight_semibold']};
                font-size: {s.FONTS['size_body']}pt;
            }}
            QPushButton:hover {{
                background: {s.SURFACE['button_hov']};
                border: 1px solid {s.BORDER['focus']};
            }}
            QPushButton:pressed {{
                background: {s.SURFACE['button_prs']};
                border: 1px solid {s.BORDER['accent']};
            }}
            QPushButton:disabled {{
                background: {s.SURFACE['button_dsb']};
                border: 1px solid {s.BORDER['subtle']};
                color: {s.TEXT['disabled']};
            }}
        """

    def _apply_styles(self):
        GlassEffect.apply_glass_effect(self, 'list')

    def add_selection(self, selection: SelectionItem):
        self.selections.append(selection)
        item = QListWidgetItem()
        item_widget = self._create_selection_item(selection, len(self.selections) - 1)
        item.setSizeHint(item_widget.sizeHint())
        self.selection_list.addItem(item)
        self.selection_list.setItemWidget(item, item_widget)
        self.export_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)

    def remove_selection(self, index: int):
        if 0 <= index < len(self.selections):
            self.selections.pop(index)
            self.selection_list.takeItem(index)
            self._update_item_indices()
            if len(self.selections) == 0:
                self.export_btn.setEnabled(False)
                self.clear_btn.setEnabled(False)

    def clear_selections(self):
        self.selections.clear()
        self.selection_list.clear()
        self.export_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)

    def _create_selection_item(self, selection: SelectionItem, index: int) -> QWidget:
        s = Settings
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(s.SPACING['small'])
        layout.setContentsMargins(0, 0, 0, 0)

        info_layout = QHBoxLayout()
        info_layout.setSpacing(s.SPACING['small'])

        index_label = QLabel(f"#{index + 1}")
        index_label.setStyleSheet(f"""
            QLabel {{
                background-color: {s.BORDER['accent']};
                color: {s.TEXT['selection']};
                border-radius: {s.RADIUS['micro']}px;
                padding: 2px 6px;
                font-size: {s.FONTS['size_caption']}pt;
                font-weight: {s.FONTS['weight_bold']};
            }}
        """)
        info_layout.addWidget(index_label)

        page_label = QLabel(f"第{selection.page_num + 1}页")
        page_label.setStyleSheet(f"""
            QLabel {{
                color: {s.TEXT['primary']};
                font-size: {s.FONTS['size_caption']}pt;
            }}
        """)
        info_layout.addWidget(page_label)
        if getattr(selection, 'shape_type', 'rect') == "free":
            shape_label = QLabel("自由")
            shape_label.setStyleSheet(f"""
                QLabel {{
                    background-color: rgba(0, 153, 204, 0.72);
                    color: {s.TEXT['selection']};
                    border-radius: {s.RADIUS['micro']}px;
                    padding: 2px 6px;
                    font-size: {s.FONTS['size_caption']}pt;
                    font-weight: {s.FONTS['weight_semibold']};
                }}
            """)
            info_layout.addWidget(shape_label)
        info_layout.addStretch()

        remove_btn = QPushButton("×")
        remove_btn.setFixedSize(20, 20)
        remove_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 82, 82, 0.6);
                color: {s.TEXT['selection']};
                border: none;
                border-radius: 10px;
                font-size: {s.FONTS['size_label']}pt;
                font-weight: {s.FONTS['weight_bold']};
            }}
            QPushButton:hover {{
                background-color: rgba(255, 82, 82, 0.8);
            }}
        """)
        remove_btn.clicked.connect(lambda: self._on_remove_selection(index))
        info_layout.addWidget(remove_btn)
        layout.addLayout(info_layout)

        preview_label = QLabel()
        preview_label.setFixedSize(200, 80)
        preview_label.setStyleSheet(f"""
            QLabel {{
                background-color: {s.SURFACE['input']};
                border: 1px solid {s.BORDER['normal']};
                border-radius: {s.RADIUS['micro']}px;
            }}
        """)
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        preview_image = selection.preview or self._fallback_preview(selection)
        preview_pixmap = QPixmap.fromImage(preview_image)
        scaled_pixmap = preview_pixmap.scaled(
            190, 70, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        preview_label.setPixmap(scaled_pixmap)
        layout.addWidget(preview_label)

        widget.setLayout(layout)
        return widget

    def _fallback_preview(self, selection):
        x, y, w, h = selection.rect
        img_w = selection.image.width()
        img_h = selection.image.height()
        if 0 <= x < img_w and 0 <= y < img_h:
            w = min(w, img_w - x)
            h = min(h, img_h - y)
            if w > 0 and h > 0:
                return qimage_from_crop(
                    selection.image, (x, y, w, h),
                    getattr(selection, 'mask_points', None),
                    "transparent",
                )
        return selection.image

    def _update_item_indices(self):
        for i in range(self.selection_list.count()):
            item = self.selection_list.item(i)
            widget = self.selection_list.itemWidget(item)
            self.selection_list.setItemWidget(
                item, self._create_selection_item(self.selections[i], i)
            )

    def _on_remove_selection(self, index: int):
        self.remove_selection(index)

    def _on_clear_all(self):
        self.clear_selections()
        self.clear_all.emit()

    def get_selections(self):
        return self.selections
