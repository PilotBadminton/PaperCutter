"""
玻璃效果样式工具 - Frutiger Aero 风格
所有色值引用自 config.settings 语义令牌，消除硬编码。
"""
from PySide6.QtWidgets import QWidget
from config.settings import Settings


class GlassEffect:

    # ── 共享滚动条样式（消除 4 处重复） ─────────────────────────────
    @staticmethod
    def _get_scrollbar_styles():
        s = Settings
        scroll_track = 'rgba(188, 225, 236, 0.34)'
        scroll_track_mid = 'rgba(255, 255, 255, 0.62)'
        return f"""
            QScrollBar:vertical {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {scroll_track},
                    stop:0.5 {scroll_track_mid},
                    stop:1 {scroll_track});
                border: 1px solid rgba(60, 142, 172, 0.42);
                border-radius: {s.RADIUS['small']}px;
                width: 14px;
            }}
            QScrollBar::handle:vertical {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(255, 255, 255, 0.86),
                    stop:0.25 rgba(143, 220, 238, 0.82),
                    stop:0.72 rgba(57, 158, 196, 0.78),
                    stop:1 rgba(15, 115, 166, 0.72));
                border: 1px solid rgba(13, 107, 154, 0.62);
                border-radius: 7px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(100, 180, 255, 0.9),
                    stop:0.3 rgba(135, 206, 250, 1.0),
                    stop:0.7 rgba(100, 180, 255, 1.0),
                    stop:1 rgba(70, 150, 230, 0.9));
                border: 1px solid rgba(30, 144, 255, 0.9);
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {scroll_track},
                    stop:0.5 {scroll_track_mid},
                    stop:1 {scroll_track});
                border: 1px solid rgba(60, 142, 172, 0.42);
                border-radius: {s.RADIUS['small']}px;
                height: 14px;
            }}
            QScrollBar::handle:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.86),
                    stop:0.25 rgba(143, 220, 238, 0.82),
                    stop:0.72 rgba(57, 158, 196, 0.78),
                    stop:1 rgba(15, 115, 166, 0.72));
                border: 1px solid rgba(13, 107, 154, 0.62);
                border-radius: 7px;
                min-width: 30px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(100, 180, 255, 0.9),
                    stop:0.3 rgba(135, 206, 250, 1.0),
                    stop:0.7 rgba(100, 180, 255, 1.0),
                    stop:1 rgba(70, 150, 230, 0.9));
                border: 1px solid rgba(30, 144, 255, 0.9);
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
        """

    # ── 面板 ─────────────────────────────────────────────────────────
    @staticmethod
    def get_panel_style():
        s = Settings
        return f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255,255,255,0.88),
                    stop:0.42 {s.SURFACE['panel']},
                    stop:1 rgba(205,239,246,0.78));
                border: 1px solid {s.BORDER['normal']};
                border-top: 1px solid {s.BORDER['highlight']};
                border-radius: {s.RADIUS['large']}px;
                color: {s.TEXT['primary']};
            }}
            QLabel {{
                background: transparent;
                border: none;
                color: {s.TEXT['primary']};
                font-weight: {s.FONTS['weight_medium']};
                font-size: {s.FONTS['size_body']}pt;
            }}
            QGroupBox {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255,255,255,0.88),
                    stop:0.55 {s.SURFACE['bg_base']},
                    stop:1 rgba(208,242,248,0.70));
                border: 1px solid {s.BORDER['normal']};
                border-top: 1px solid {s.BORDER['highlight']};
                border-radius: {s.RADIUS['medium']}px;
                margin-top: 12px;
                padding: 14px 10px 10px 10px;
                color: {s.TEXT['primary']};
                font-weight: {s.FONTS['weight_semibold']};
                font-size: {s.FONTS['size_label']}pt;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: {s.TEXT['primary']};
                font-size: {s.FONTS['size_label']}pt;
            }}
            QRadioButton {{
                background: transparent;
                border: none;
                color: {s.TEXT['primary']};
                font-size: {s.FONTS['size_body']}pt;
                padding: 4px;
            }}
            QRadioButton::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {s.TEXT['secondary']};
                border-radius: 9px;
                background: {s.SURFACE['input']};
            }}
            QRadioButton::indicator:checked {{
                background: {s.BORDER['focus']};
                border-color: {s.AERO_SKY};
            }}
            QRadioButton::indicator:hover {{
                border-color: {s.BORDER['accent']};
            }}
            QLineEdit {{
                background: {s.SURFACE['input']};
                border: 1px solid {s.BORDER['input']};
                border-radius: {s.RADIUS['small']}px;
                color: {s.TEXT['primary']};
                padding: 6px 10px;
                selection-background-color: {s.SURFACE['list_sel']};
                font-size: {s.FONTS['size_body']}pt;
            }}
            QLineEdit:hover {{
                background: {s.SURFACE['panel_hover']};
                border: 1px solid {s.BORDER['strong']};
            }}
            QLineEdit:focus {{
                background: {s.SURFACE['input_focus']};
                border: 1px solid {s.BORDER['focus']};
            }}
            QCheckBox {{
                background: transparent;
                border: none;
                color: {s.TEXT['primary']};
                font-size: {s.FONTS['size_body']}pt;
                padding: 5px 2px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: {s.RADIUS['micro']}px;
                border: 1px solid {s.BORDER['input']};
                background: {s.SURFACE['input']};
            }}
            QCheckBox::indicator:hover {{
                border: 1px solid {s.BORDER['focus']};
                background: {s.SURFACE['input_focus']};
            }}
            QCheckBox::indicator:checked {{
                background: {s.SURFACE['button_act']};
                border: 1px solid {s.BORDER['focus']};
            }}
            QLabel#outputPathLabel {{
                background: {s.SURFACE['input']};
                border: 1px solid {s.BORDER['input']};
                border-radius: {s.RADIUS['small']}px;
                padding: 8px 10px;
                color: {s.TEXT['secondary']};
                font-size: {s.FONTS['size_caption']}pt;
                font-weight: {s.FONTS['weight_regular']};
            }}
        """

    # ── 按钮 ─────────────────────────────────────────────────────────
    @staticmethod
    def get_button_style():
        s = Settings
        return f"""
            QPushButton {{
                background: {s.SURFACE['button']};
                border: 1px solid {s.BORDER['strong']};
                border-top: 1px solid {s.BORDER['highlight']};
                border-radius: {s.RADIUS['normal']}px;
                color: {s.TEXT['primary']};
                padding: 8px 14px;
                min-height: 28px;
                font-weight: {s.FONTS['weight_semibold']};
                font-size: {s.FONTS['size_label']}pt;
            }}
            QPushButton:hover {{
                background: {s.SURFACE['button_hov']};
                border: 1px solid {s.BORDER['focus']};
                border-top: 1px solid {s.BORDER['highlight']};
            }}
            QPushButton:pressed {{
                background: {s.SURFACE['button_prs']};
                border: 1px solid {s.BORDER['accent']};
                border-top: 1px solid {s.BORDER['strong']};
            }}
            QPushButton:checked {{
                background: {s.SURFACE['button_act']};
                border: 1px solid {s.BORDER['accent']};
                border-top: 1px solid {s.BORDER['focus']};
                color: {s.TEXT['on_accent']};
            }}
            QPushButton:disabled {{
                background: {s.SURFACE['button_dsb']};
                border: 1px solid {s.BORDER['subtle']};
                color: {s.TEXT['disabled']};
            }}
        """

    # ── 输入框 ─────────────────────────────────────────────────────────
    @staticmethod
    def get_input_style():
        s = Settings
        return f"""
            QLineEdit, QSpinBox, QComboBox {{
                background: {s.SURFACE['input']};
                border: 1px solid {s.BORDER['input']};
                border-radius: {s.RADIUS['small']}px;
                color: {s.TEXT['primary']};
                padding: 6px 10px;
                selection-background-color: {s.SURFACE['list_sel']};
                font-size: {s.FONTS['size_body']}pt;
            }}
            QLineEdit:hover, QSpinBox:hover, QComboBox:hover {{
                background: {s.SURFACE['panel_hover']};
                border: 1px solid {s.BORDER['strong']};
            }}
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
                background: {s.SURFACE['input_focus']};
                border: 1px solid {s.BORDER['focus']};
            }}
            QComboBox::drop-down {{
                border: none;
                background: transparent;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {s.TEXT['secondary']};
                margin-right: 5px;
            }}
            QComboBox QAbstractItemView {{
                background: {s.SURFACE['dropdown']};
                border: 1px solid {s.BORDER['normal']};
                border-radius: {s.RADIUS['small']}px;
                color: {s.TEXT['primary']};
                selection-background-color: {s.SURFACE['list_sel']};
                font-size: {s.FONTS['size_body']}pt;
            }}
        """

    # ── 工具栏 ─────────────────────────────────────────────────────────
    @staticmethod
    def get_toolbar_style():
        s = Settings
        return f"""
            QToolBar {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,0.92),
                    stop:0.20 {s.SURFACE['toolbar']},
                    stop:1 rgba(183,232,242,0.78));
                border: none;
                border-bottom: 1px solid {s.BORDER['divider']};
                spacing: 5px;
                padding: 7px;
            }}
            QToolBar::separator {{
                background: {s.BORDER['divider']};
                width: 1px;
                margin: 5px 10px;
            }}
            QToolButton {{
                background: {s.SURFACE['button']};
                border: 1px solid {s.BORDER['subtle']};
                border-top: 1px solid {s.BORDER['highlight']};
                border-radius: {s.RADIUS['small']}px;
                color: {s.TEXT['primary']};
                padding: 6px 10px;
                font-size: {s.FONTS['size_body']}pt;
            }}
            QToolButton:hover {{
                background: {s.SURFACE['button_hov']};
                border: 1px solid {s.BORDER['focus']};
            }}
            QToolButton:pressed {{
                background: {s.SURFACE['button_prs']};
                border: 1px solid {s.BORDER['accent']};
            }}
            QToolButton:disabled {{
                color: {s.TEXT['disabled']};
            }}
            QLabel {{
                background: transparent;
                border: none;
                color: {s.TEXT['primary']};
                font-size: {s.FONTS['size_caption']}pt;
            }}
            QLineEdit {{
                background: {s.SURFACE['input']};
                border: 1px solid {s.BORDER['input']};
                border-radius: {s.RADIUS['micro']}px;
                color: {s.TEXT['primary']};
                padding: 3px 8px;
                font-size: {s.FONTS['size_caption']}pt;
            }}
        """

    # ── 状态栏 ─────────────────────────────────────────────────────────
    @staticmethod
    def get_statusbar_style():
        s = Settings
        return f"""
            QStatusBar {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,0.88),
                    stop:1 {s.SURFACE['statusbar']});
                border: none;
                border-top: 1px solid {s.BORDER['divider']};
                color: {s.TEXT['primary']};
            }}
            QStatusBar::item {{
                border: none;
            }}
            QStatusBar QLabel {{
                background: {s.SURFACE['bg_base']};
                border: 1px solid {s.BORDER['subtle']};
                border-radius: {s.RADIUS['micro']}px;
                color: {s.TEXT['primary']};
                padding: 3px 10px;
                font-size: {s.FONTS['size_caption']}pt;
            }}
        """

    # ── 列表 ─────────────────────────────────────────────────────────
    @staticmethod
    def get_list_style():
        s = Settings
        return f"""
            QListWidget {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255,255,255,0.86),
                    stop:1 {s.SURFACE['panel']});
                border: 1px solid {s.BORDER['normal']};
                border-top: 1px solid {s.BORDER['highlight']};
                border-radius: {s.RADIUS['normal']}px;
                color: {s.TEXT['primary']};
                padding: 5px;
                font-size: {s.FONTS['size_body']}pt;
            }}
            QListWidget::item {{
                background: {s.SURFACE['list_item']};
                border: 1px solid {s.BORDER['list_item']};
                border-radius: {s.RADIUS['small']}px;
                margin: 3px;
                padding: 8px;
                font-size: {s.FONTS['size_body']}pt;
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
        """

    # ── 画布 ─────────────────────────────────────────────────────────
    @staticmethod
    def get_canvas_style():
        s = Settings
        return f"""
            QWidget {{
                background: rgba(235, 252, 255, 0.56);
                border: 1px solid {s.BORDER['normal']};
                border-radius: {s.RADIUS['normal']}px;
            }}
            QScrollArea {{
                background: rgba(235, 252, 255, 0.34);
                border: none;
                border-radius: {s.RADIUS['normal']}px;
            }}
            {GlassEffect._get_scrollbar_styles()}
        """

    # ── 分发 ─────────────────────────────────────────────────────────
    @staticmethod
    def apply_glass_effect(widget, style_type='panel'):
        styles = {
            'panel':     GlassEffect.get_panel_style,
            'button':    GlassEffect.get_button_style,
            'input':     GlassEffect.get_input_style,
            'toolbar':   GlassEffect.get_toolbar_style,
            'statusbar': GlassEffect.get_statusbar_style,
            'list':      GlassEffect.get_list_style,
            'canvas':    GlassEffect.get_canvas_style,
        }
        fn = styles.get(style_type)
        if fn:
            widget.setStyleSheet(fn())
