"""
自由编排窗口 — Frutiger Aero 工作台 v1
"""
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QGraphicsView, QGraphicsScene, QSplitter,
    QMessageBox, QApplication, QComboBox, QSpinBox, QColorDialog, QFrame
)
from PySide6.QtCore import Qt, QRectF, QMimeData, QPointF, QPoint, QTimer, QEvent, QSize, Signal
from PySide6.QtGui import (
    QPainter, QColor, QPen, QKeyEvent, QDrag, QWheelEvent,
    QDragEnterEvent, QDropEvent, QLinearGradient, QBrush, QCursor,
    QPixmap, QImage, QShortcut, QKeySequence
)

from core.composition_merger import CompositionMerger
from ui.composition_item import CompositionItem
from config.settings import Settings


def _button_style(accent=False):
    s = Settings
    if accent:
        bg = "qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 rgba(0,164,224,0.78), stop:1 rgba(0,128,190,0.68))"
        hov = "qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 rgba(0,188,245,0.86), stop:1 rgba(0,146,210,0.74))"
        color = s.TEXT['on_accent']
        border = "rgba(0, 102, 160, 0.72)"
    else:
        bg = "qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 rgba(255,255,255,0.90), stop:1 rgba(219,248,250,0.78))"
        hov = "qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 rgba(255,255,255,0.98), stop:1 rgba(196,240,247,0.88))"
        color = s.TEXT['primary']
        border = "rgba(68, 156, 184, 0.48)"
    return f"""
        QPushButton {{
            background: {bg};
            border: 1px solid {border};
            border-top: 1px solid rgba(255,255,255,0.68);
            border-radius: {s.RADIUS['normal']}px;
            color: {color};
            padding: 6px 8px;
            min-width: 46px;
            min-height: 28px;
            font-weight: {s.FONTS['weight_semibold']};
            font-size: {s.FONTS['size_body']}pt;
        }}
        QPushButton:hover {{
            background: {hov};
            border: 1px solid rgba(0, 142, 190, 0.68);
        }}
        QPushButton:pressed, QPushButton:checked {{
            background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 rgba(133,224,241,0.86), stop:1 rgba(52,180,213,0.72));
            border: 1px solid {s.BORDER['focus']};
        }}
        QPushButton:disabled {{
            background: rgba(226, 243, 246, 0.50);
            border: 1px solid rgba(130, 163, 176, 0.30);
            color: #6F8292;
        }}
    """


def _field_style():
    s = Settings
    return f"""
        QComboBox, QSpinBox {{
            background: rgba(255,255,255,0.88);
            border: 1px solid rgba(68,156,184,0.42);
            border-radius: {s.RADIUS['small']}px;
            color: {s.TEXT['primary']};
            padding: 5px 8px;
            font-size: {s.FONTS['size_body']}pt;
            min-height: 28px;
        }}
        QComboBox:hover, QSpinBox:hover {{
            background: rgba(255,255,255,0.96);
            border: 1px solid rgba(0,142,190,0.66);
        }}
        QComboBox:focus, QSpinBox:focus {{
            border: 1px solid {s.BORDER['focus']};
        }}
    """


class _DragList(QListWidget):
    def __init__(self, win, parent=None):
        super().__init__(parent)
        self._win = win
        self._press_pos = None

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self._press_pos = event.pos() if event.button() == Qt.MouseButton.LeftButton else None

    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.MouseButton.LeftButton
                and self._press_pos is not None
                and (event.pos() - self._press_pos).manhattanLength()
                    >= QApplication.startDragDistance()):
            item = self.itemAt(self._press_pos)
            if item:
                idx = item.data(Qt.ItemDataRole.UserRole)
                drag = QDrag(self)
                mime = QMimeData()
                mime.setText(str(idx))
                drag.setMimeData(mime)
                drag.exec(Qt.DropAction.CopyAction)
            self._press_pos = None
            return
        super().mouseMoveEvent(event)


class _ZoomView(QGraphicsView):
    def __init__(self, scene, win, parent=None):
        super().__init__(scene, parent)
        self._win = win
        self._panning = False
        self._pan_start = QPoint()
        self._pan_h = 0
        self._pan_v = 0
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAcceptDrops(True)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)

    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
            self._win._zoom_at(factor, event.position())
            event.accept()
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event):
        if self._win._eyedropper_active and event.button() == Qt.MouseButton.LeftButton:
            self._win._sample_background_at(self.mapToScene(event.pos()))
            event.accept()
            return
        if self._win._space_down and event.button() == Qt.MouseButton.LeftButton:
            self._panning = True
            self._pan_start = event.pos()
            self._pan_h = self.horizontalScrollBar().value()
            self._pan_v = self.verticalScrollBar().value()
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning:
            delta = event.pos() - self._pan_start
            self.horizontalScrollBar().setValue(self._pan_h - delta.x())
            self.verticalScrollBar().setValue(self._pan_v - delta.y())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._panning and event.button() == Qt.MouseButton.LeftButton:
            self._panning = False
            self._win._sync_view_cursor()
            event.accept()
            return
        super().mouseReleaseEvent(event)


class _GridScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(QRectF(-6000, -6000, 24000, 24000))

    def drawBackground(self, painter: QPainter, rect):
        grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
        grad.setColorAt(0, QColor(226, 255, 255))
        grad.setColorAt(0.48, QColor(174, 232, 236))
        grad.setColorAt(1, QColor(112, 204, 203))
        painter.fillRect(rect, QBrush(grad))

        gs = 40
        left = int(rect.left() / gs) * gs
        top = int(rect.top() / gs) * gs
        painter.setPen(QPen(QColor(255, 255, 255, 70), 1))
        for x in range(left, int(rect.right()) + gs, gs):
            painter.drawLine(x, int(rect.top()), x, int(rect.bottom()))
        for y in range(top, int(rect.bottom()) + gs, gs):
            painter.drawLine(int(rect.left()), y, int(rect.right()), y)

        win = self.parent()
        export_rect = win._export_rect_scene() if win else None
        if export_rect:
            bg = win._preview_background_color()
            if bg is None:
                self._draw_checker(painter, export_rect)
            else:
                painter.fillRect(export_rect, bg)

    def drawForeground(self, painter: QPainter, rect):
        win = self.parent()
        if not win:
            return
        export_rect = win._export_rect_scene()
        if export_rect:
            painter.setPen(QPen(QColor(255, 255, 255, 220), 4))
            painter.drawRoundedRect(export_rect, 8, 8)
            painter.setPen(QPen(QColor(0, 153, 204, 230), 2, Qt.PenStyle.DashLine))
            painter.drawRoundedRect(export_rect, 8, 8)

        drop_rect = win._drop_preview_rect
        if drop_rect:
            painter.setPen(QPen(QColor(0, 132, 190, 230), 2, Qt.PenStyle.DashLine))
            painter.drawRoundedRect(drop_rect, 6, 6)

        if win._guide_lines:
            painter.save()
            painter.setPen(QPen(QColor(0, 120, 200, 220), 1.5, Qt.PenStyle.DashLine))
            for orientation, scene_value in win._guide_lines:
                if orientation == "v":
                    painter.drawLine(QPointF(scene_value, rect.top()),
                                     QPointF(scene_value, rect.bottom()))
                else:
                    painter.drawLine(QPointF(rect.left(), scene_value),
                                     QPointF(rect.right(), scene_value))
            painter.restore()

    def _draw_checker(self, painter, target):
        tile = 18
        light = QColor(255, 255, 255, 210)
        dark = QColor(203, 228, 232, 210)
        left = int(target.left() / tile) * tile
        top = int(target.top() / tile) * tile
        painter.save()
        painter.setClipRect(target)
        for x in range(left, int(target.right()) + tile, tile):
            for y in range(top, int(target.bottom()) + tile, tile):
                painter.fillRect(x, y, tile, tile,
                                 light if ((x // tile) + (y // tile)) % 2 == 0 else dark)
        painter.restore()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            try:
                idx = int(event.mimeData().text())
            except (ValueError, TypeError):
                event.ignore()
                return
            self.parent()._set_drop_preview(idx, event.scenePos())
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self.parent()._clear_drop_preview()
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        try:
            idx = int(event.mimeData().text())
        except (ValueError, TypeError):
            event.ignore()
            return
        pos = event.scenePos()
        self.parent()._clear_drop_preview()
        if self.parent()._drop_selection(idx, pos.x(), pos.y()):
            event.accept()
        else:
            event.ignore()


class CompositionWindow(QDialog):
    export_succeeded = Signal(str)

    _MAX_INIT_W = 320
    _MIN_ZOOM = 0.10
    _MAX_ZOOM = 8.0

    def __init__(self, selections, doc_name, mode, question_num,
                 output_dir, parent=None, custom_prefix=""):
        super().__init__(parent)
        self._selections = selections
        self._doc_name = doc_name
        self._mode = mode
        self._question_num = question_num
        self._custom_prefix = custom_prefix or ""
        self._output_dir = Path(output_dir) if output_dir else Path.cwd()
        self._layout_scale = self._initial_layout_scale()
        self._view_zoom = 1.0
        self._fullscreen_restore_maximized = False
        self._background_mode = "transparent"
        self._background_color = QColor("#F8FEFF")
        self._padding = 16
        self._drop_preview_rect = None
        self._guide_lines = []
        self._snap_adjusting = False
        self._rotate_start = None
        self._eyedropper_active = False
        self._space_down = False
        self._history_block = False
        self._undo_stack = []
        self._redo_stack = []

        self.setWindowTitle("自由编排 — " + doc_name)
        self.resize(1280, 780)
        self.setMinimumSize(920, 560)

        self._scene = _GridScene(self)
        self._scene.selectionChanged.connect(self._on_sel_changed)
        self._view = _ZoomView(self._scene, self, self)
        self._view.setStyleSheet("""
            QGraphicsView {
                background: #C6F1F3;
                border: 1px solid rgba(56,143,171,0.42);
                border-radius: 10px;
            }
        """)

        left = self._build_left_panel()
        right = self._build_workbench()

        spl = QSplitter(Qt.Orientation.Horizontal, self)
        spl.addWidget(left)
        spl.addWidget(right)
        spl.setSizes([280, 1000])

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(spl)
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #E0FFFF, stop:0.48 #82DDE2, stop:1 #20B2AA);
                color: {Settings.TEXT['primary']};
                font-family: {Settings.FONTS['family']};
            }}
            QLabel {{
                color: {Settings.TEXT['primary']};
                background: transparent;
            }}
        """)

        self._undo_shortcut = QShortcut(QKeySequence(QKeySequence.StandardKey.Undo), self)
        self._redo_shortcut = QShortcut(QKeySequence(QKeySequence.StandardKey.Redo), self)
        self._undo_shortcut.activated.connect(self._undo)
        self._redo_shortcut.activated.connect(self._redo)
        self._fullscreen_shortcut = QShortcut(QKeySequence("F11"), self)
        self._escape_shortcut = QShortcut(QKeySequence("Esc"), self)
        self._fullscreen_shortcut.activated.connect(self._toggle_fullscreen)
        self._escape_shortcut.activated.connect(self._exit_fullscreen)
        self._apply_view_zoom()
        self._refresh_after_items_changed()
        self._notify("拖入选区开始编排；Ctrl+滚轮缩放，Space+拖拽平移，Alt拖动禁用吸附。")

    def _build_left_panel(self):
        s = Settings
        panel = QWidget()
        panel.setFixedWidth(280)
        panel.setStyleSheet(f"""
            QWidget {{
                background: rgba(238, 253, 255, 0.72);
                border-right: 1px solid rgba(52, 139, 170, 0.30);
            }}
            QLabel {{
                color: {s.TEXT['primary']};
                font-size: {s.FONTS['size_body']}pt;
                font-weight: {s.FONTS['weight_semibold']};
            }}
        """)
        lyt = QVBoxLayout(panel)
        lyt.setSpacing(10)
        lyt.setContentsMargins(12, 12, 12, 34)
        title = QLabel("可用选区")
        title.setStyleSheet(f"font-size: {s.FONTS['size_subtitle']}pt; font-weight: {s.FONTS['weight_bold']};")
        lyt.addWidget(title)
        hint = QLabel("拖到画布，或用按钮添加到当前视图中心")
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {s.TEXT['secondary']}; font-size: {s.FONTS['size_caption']}pt;")
        lyt.addWidget(hint)

        self._list = _DragList(self)
        self._list.setDragEnabled(True)
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list.setTextElideMode(Qt.TextElideMode.ElideRight)
        self._list.setStyleSheet(f"""
            QListWidget {{
                background: rgba(255,255,255,0.58);
                border: 1px solid rgba(64,150,178,0.36);
                border-radius: {s.RADIUS['normal']}px;
                padding: 6px;
                font-size: {s.FONTS['size_body']}pt;
            }}
            QListWidget::item {{
                background: rgba(234,250,253,0.86);
                border: 1px solid rgba(84,164,190,0.22);
                border-radius: {s.RADIUS['small']}px;
                padding: 8px;
                margin: 3px;
                color: {s.TEXT['primary']};
            }}
            QListWidget::item:hover {{
                background: rgba(255,255,255,0.96);
                border: 1px solid rgba(0,142,190,0.56);
            }}
            QListWidget::item:selected {{
                background: rgba(0,164,224,0.76);
                border: 1px solid rgba(0,102,160,0.75);
                color: #FFFFFF;
            }}
        """)
        lyt.addWidget(self._list, stretch=1)

        self._btn_add = QPushButton("添加到画布中心")
        self._btn_add.setStyleSheet(_button_style())
        self._btn_add.clicked.connect(self._add_center)
        lyt.addWidget(self._btn_add)

        row = QHBoxLayout()
        self._btn_del = QPushButton("删除")
        self._btn_del.setStyleSheet(_button_style())
        self._btn_del.clicked.connect(self._delete)
        self._btn_clear = QPushButton("清空")
        self._btn_clear.setStyleSheet(_button_style())
        self._btn_clear.clicked.connect(self._clear)
        row.addWidget(self._btn_del)
        row.addWidget(self._btn_clear)
        lyt.addLayout(row)

        self._btn_export = QPushButton("导出组合图")
        self._btn_export.setStyleSheet(_button_style(accent=True))
        self._btn_export.clicked.connect(self._export)
        lyt.addWidget(self._btn_export)
        lyt.addSpacing(4)
        self._populate()
        return panel

    def _build_workbench(self):
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        layout.addWidget(self._build_top_toolbar())
        layout.addWidget(self._view, stretch=1)

        self._status = QLabel("")
        self._status.setFixedHeight(32)
        self._status.setStyleSheet("""
            QLabel {
                background: rgba(245,253,255,0.78);
                border: 1px solid rgba(68,156,184,0.34);
                border-radius: 8px;
                padding: 6px 10px;
                color: #1A1A2E;
            }
        """)
        layout.addWidget(self._status)
        self._toast_timer = QTimer(self)
        self._toast_timer.setSingleShot(True)
        self._toast_timer.timeout.connect(lambda: self._status.setText(""))
        return box

    def _build_top_toolbar(self):
        s = Settings
        toolbar = QFrame()
        toolbar.setStyleSheet(f"""
            QFrame {{
                background: rgba(241,253,255,0.76);
                border: 1px solid rgba(70,156,184,0.34);
                border-radius: {s.RADIUS['large']}px;
            }}
        """)
        lyt = QHBoxLayout(toolbar)
        lyt.setContentsMargins(10, 8, 10, 8)
        lyt.setSpacing(8)

        self._btn_undo = QPushButton("撤销")
        self._btn_redo = QPushButton("恢复")
        self._btn_zoom_out = QPushButton("缩小")
        self._btn_zoom_reset = QPushButton("100%")
        self._btn_zoom_in = QPushButton("放大")
        self._btn_fit = QPushButton("适应")
        self._btn_maximize = QPushButton("最大")
        self._btn_fullscreen = QPushButton("全屏")
        self._btn_layer_up = QPushButton("上移")
        self._btn_layer_down = QPushButton("下移")
        self._btn_layer_top = QPushButton("置顶")
        self._btn_layer_bottom = QPushButton("置底")
        for btn in (self._btn_undo, self._btn_redo, self._btn_zoom_out,
                    self._btn_zoom_reset, self._btn_zoom_in, self._btn_fit,
                    self._btn_maximize, self._btn_fullscreen):
            btn.setStyleSheet(_button_style())
            btn.setMinimumWidth(54)
            lyt.addWidget(btn)
        for btn in (self._btn_layer_up, self._btn_layer_down,
                    self._btn_layer_top, self._btn_layer_bottom):
            btn.setStyleSheet(_button_style())
            btn.setMinimumWidth(48)
            lyt.addWidget(btn)
        self._btn_fit.setToolTip("适应全部内容")
        self._btn_maximize.setToolTip("最大化/还原窗口")
        self._btn_fullscreen.setToolTip("全屏/退出全屏（F11）")
        self._btn_layer_up.setToolTip("选中对象上移一层")
        self._btn_layer_down.setToolTip("选中对象下移一层")
        self._btn_layer_top.setToolTip("选中对象置顶")
        self._btn_layer_bottom.setToolTip("选中对象置底")

        self._btn_undo.clicked.connect(self._undo)
        self._btn_redo.clicked.connect(self._redo)
        self._btn_zoom_out.clicked.connect(lambda: self._zoom_at(1 / 1.15, QPointF(self._view.viewport().width() / 2, self._view.viewport().height() / 2)))
        self._btn_zoom_reset.clicked.connect(lambda: self._set_view_zoom(1.0, center=True))
        self._btn_zoom_in.clicked.connect(lambda: self._zoom_at(1.15, QPointF(self._view.viewport().width() / 2, self._view.viewport().height() / 2)))
        self._btn_fit.clicked.connect(self._fit_content)
        self._btn_maximize.clicked.connect(self._toggle_maximized)
        self._btn_fullscreen.clicked.connect(self._toggle_fullscreen)
        self._btn_layer_up.clicked.connect(lambda: self._change_layer("up"))
        self._btn_layer_down.clicked.connect(lambda: self._change_layer("down"))
        self._btn_layer_top.clicked.connect(lambda: self._change_layer("top"))
        self._btn_layer_bottom.clicked.connect(lambda: self._change_layer("bottom"))

        self._zoom_label = QLabel("100%")
        self._zoom_label.setMinimumWidth(48)
        self._zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lyt.addWidget(self._zoom_label)
        lyt.addSpacing(8)

        lyt.addWidget(QLabel("背景"))
        self._bg_combo = QComboBox()
        self._bg_combo.addItem("透明", "transparent")
        self._bg_combo.addItem("白色", "white")
        self._bg_combo.addItem("自定义色", "color")
        self._bg_combo.setStyleSheet(_field_style())
        self._bg_combo.setFixedWidth(82)
        self._bg_combo.currentIndexChanged.connect(self._on_background_combo)
        lyt.addWidget(self._bg_combo)

        self._btn_color = QPushButton("颜色")
        self._btn_color.setStyleSheet(_button_style())
        self._btn_color.setFixedWidth(64)
        self._btn_color.clicked.connect(self._pick_color_dialog)
        lyt.addWidget(self._btn_color)

        self._btn_eyedropper = QPushButton("吸管")
        self._btn_eyedropper.setCheckable(True)
        self._btn_eyedropper.setStyleSheet(_button_style())
        self._btn_eyedropper.setFixedWidth(64)
        self._btn_eyedropper.clicked.connect(self._toggle_eyedropper)
        lyt.addWidget(self._btn_eyedropper)

        lyt.addWidget(QLabel("边距"))
        self._padding_spin = QSpinBox()
        self._padding_spin.setRange(0, 200)
        self._padding_spin.setValue(self._padding)
        self._padding_spin.setSuffix(" px")
        self._padding_spin.setStyleSheet(_field_style())
        self._padding_spin.setFixedWidth(82)
        self._padding_spin.valueChanged.connect(self._set_padding)
        lyt.addWidget(self._padding_spin)
        lyt.addStretch()
        return toolbar

    def _populate(self):
        for i, sel in enumerate(self._selections):
            text = f"选区 #{i + 1} · P{sel.page_num + 1} · {sel.rect[2]}x{sel.rect[3]}"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, i)
            item.setToolTip(text)
            item.setSizeHint(QSize(0, 38))
            self._list.addItem(item)
        if self._list.count() > 0:
            self._list.setCurrentRow(0)

    def _drag_pixmap_for_index(self, idx):
        try:
            comp = self._make_item(self._selections[idx])
        except Exception:
            return None
        pix = comp.pixmap().scaled(
            180, 120, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        img = QImage(pix.size(), QImage.Format.Format_ARGB32_Premultiplied)
        img.fill(QColor(255, 255, 255, 0))
        painter = QPainter(img)
        painter.setOpacity(0.82)
        painter.drawPixmap(0, 0, pix)
        painter.end()
        return QPixmap.fromImage(img)

    def _make_item(self, sel):
        shape_type = getattr(sel, 'shape_type', 'rect')
        mask_points = getattr(sel, 'mask_points', None)
        if sel.file_path:
            return CompositionItem.from_file_crop(sel.file_path, sel.rect, shape_type, mask_points)
        return CompositionItem.from_qimage_crop(sel.image, sel.rect, shape_type, mask_points)

    def _initial_layout_scale(self):
        widths = []
        for sel in self._selections:
            try:
                widths.append(float(sel.rect[2]))
            except (AttributeError, IndexError, TypeError, ValueError):
                pass
        max_w = max(widths, default=1.0)
        return min(self._MAX_INIT_W / max(max_w, 1.0), 1.0)

    def _full_to_scene(self, x, y):
        return QPointF(float(x) * self._layout_scale, float(y) * self._layout_scale)

    def _scene_to_full(self, x, y):
        return QPointF(float(x) / self._layout_scale, float(y) / self._layout_scale)

    def _full_rect_to_scene(self, rect):
        return QRectF(
            rect.x() * self._layout_scale,
            rect.y() * self._layout_scale,
            rect.width() * self._layout_scale,
            rect.height() * self._layout_scale,
        )

    def _scene_rect_to_full(self, rect):
        return QRectF(
            rect.x() / self._layout_scale,
            rect.y() / self._layout_scale,
            rect.width() / self._layout_scale,
            rect.height() / self._layout_scale,
        )

    def _ensure_scene_contains(self, rect=None):
        if rect is None:
            rect = self._export_rect_scene()
        if not rect:
            return
        padded = QRectF(rect).adjusted(-2000, -2000, 2000, 2000)
        current = self._scene.sceneRect()
        if not current.contains(padded):
            self._scene.setSceneRect(current.united(padded))

    def _all_items(self):
        return [it for it in self._scene.items() if isinstance(it, CompositionItem)]

    def _sorted_items(self):
        return sorted(self._all_items(), key=lambda x: x.zValue())

    def _attach_item(self, item):
        item.set_owner(self)
        item.set_layout_scale(self._layout_scale)
        item.set_view_zoom(self._view_zoom)
        if item.scene() is not self._scene:
            self._scene.addItem(item)

    def _remove_item(self, item):
        if item.scene() is self._scene:
            self._scene.removeItem(item)

    def _next_z(self):
        items = self._all_items()
        return max((it.zValue() for it in items), default=0) + 1

    def _add_item(self, comp, full_x, full_y, push=True):
        comp.set_owner(self)
        comp.set_layout_scale(self._layout_scale)
        comp.set_view_zoom(self._view_zoom)
        comp.set_full_pos(full_x, full_y)
        comp.setZValue(self._next_z())
        self._scene.addItem(comp)
        comp.setSelected(True)

        if push:
            self._push_command(
                "添加选区",
                undo=lambda c=comp: self._remove_item(c),
                redo=lambda c=comp: self._attach_item(c),
            )
        self._refresh_after_items_changed()
        self._notify("已添加选区到画布")

    def _drop_selection(self, idx, scene_x, scene_y):
        if idx < 0 or idx >= len(self._selections):
            return False
        try:
            comp = self._make_item(self._selections[idx])
            full = self._scene_to_full(scene_x, scene_y)
            self._add_item(comp, full.x(), full.y())
            return True
        except Exception as e:
            self._notify(f"无法加载选区：{e}", "error")
            return False

    def _add_center(self):
        cur = self._list.currentItem()
        if not cur:
            self._notify("请先选择一个可用选区", "warning")
            return
        idx = cur.data(Qt.ItemDataRole.UserRole)
        try:
            comp = self._make_item(self._selections[idx])
            center = self._view.mapToScene(self._view.viewport().rect().center())
            full_center = self._scene_to_full(center.x(), center.y())
            n = len(self._all_items())
            full_x = full_center.x() - comp._full_w / 2 + n * 24
            full_y = full_center.y() - comp._full_h / 2 + n * 24
            self._add_item(comp, full_x, full_y)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法加载选区：{e}")

    def _delete(self):
        items = [it for it in self._scene.selectedItems() if isinstance(it, CompositionItem)]
        if not items:
            self._notify("没有选中的画布对象", "warning")
            return
        states = [(it, it.get_full_pos(), it.get_rotation(), it.zValue()) for it in items]
        for it in items:
            self._remove_item(it)

        def undo():
            for it, pos, angle, z in states:
                it.setZValue(z)
                it.set_full_pos(*pos)
                it.set_rotation(angle)
                self._attach_item(it)

        def redo():
            for it, _, _, _ in states:
                self._remove_item(it)

        self._push_command("删除选区", undo=undo, redo=redo)
        self._refresh_after_items_changed()
        self._notify(f"已删除 {len(items)} 个选区")

    def _clear(self):
        items = [(it, it.get_full_pos(), it.get_rotation(), it.zValue()) for it in self._all_items()]
        if not items:
            self._notify("画布已经是空的", "warning")
            return
        for it, _, _, _ in items:
            self._remove_item(it)

        def undo():
            for it, pos, angle, z in items:
                it.setZValue(z)
                it.set_full_pos(*pos)
                it.set_rotation(angle)
                self._attach_item(it)

        def redo():
            for it, _, _, _ in items:
                self._remove_item(it)

        self._push_command("清空画布", undo=undo, redo=redo)
        self._refresh_after_items_changed()
        self._notify("已清空画布")

    def _record_move(self, item, before, after):
        if self._history_block:
            return
        self._guide_lines = []
        if abs(before[0] - after[0]) < 0.5 and abs(before[1] - after[1]) < 0.5:
            self._scene.update()
            return
        self._push_command(
            "移动选区",
            undo=lambda i=item, p=before: i.set_full_pos(*p),
            redo=lambda i=item, p=after: i.set_full_pos(*p),
        )
        self._ensure_scene_contains(item.sceneBoundingRect())
        self._scene.update()

    def _item_moved_live(self, item):
        if self._history_block or self._snap_adjusting:
            return
        if item not in self._scene.selectedItems() or len(self._scene.selectedItems()) != 1:
            self._guide_lines = []
            self._scene.update()
            return
        if QApplication.keyboardModifiers() & Qt.KeyboardModifier.AltModifier:
            self._guide_lines = []
            self._scene.update()
            return

        dx, dy, guides = self._snap_delta_for_item(item)
        self._guide_lines = guides
        if abs(dx) > 0.001 or abs(dy) > 0.001:
            x, y = item.get_full_pos()
            self._snap_adjusting = True
            try:
                item.set_full_pos(x + dx, y + dy)
            finally:
                self._snap_adjusting = False
        self._scene.update()

    def _snap_delta_for_item(self, item):
        threshold = 6.0 / max(self._layout_scale, 0.001)
        ix, iy, iw, ih = item.get_full_rect()
        item_x = [ix, ix + iw / 2, ix + iw]
        item_y = [iy, iy + ih / 2, iy + ih]
        target_x, target_y = self._snap_targets(item)

        best_dx = None
        guide_x = None
        for value in item_x:
            for target in target_x:
                delta = target - value
                if abs(delta) <= threshold and (best_dx is None or abs(delta) < abs(best_dx)):
                    best_dx = delta
                    guide_x = target

        best_dy = None
        guide_y = None
        for value in item_y:
            for target in target_y:
                delta = target - value
                if abs(delta) <= threshold and (best_dy is None or abs(delta) < abs(best_dy)):
                    best_dy = delta
                    guide_y = target

        guides = []
        if guide_x is not None:
            guides.append(("v", guide_x * self._layout_scale))
        if guide_y is not None:
            guides.append(("h", guide_y * self._layout_scale))
        return (best_dx or 0.0, best_dy or 0.0, guides)

    def _snap_targets(self, moving_item):
        xs = []
        ys = []
        for it in self._all_items():
            if it is moving_item:
                continue
            x, y, w, h = it.get_full_rect()
            xs.extend([x, x + w / 2, x + w])
            ys.extend([y, y + h / 2, y + h])

        export_rect = self._export_rect_full()
        if export_rect:
            xs.append(export_rect.center().x())
            ys.append(export_rect.center().y())
        return xs, ys

    def _begin_rotate(self, item):
        self._rotate_start = (item, item.get_rotation())

    def _rotation_changed(self, item):
        self._notify(f"旋转：{item.get_rotation():.1f}°")
        self._scene.update()

    def _end_rotate(self, item):
        if not self._rotate_start or self._rotate_start[0] is not item:
            self._rotate_start = None
            return
        before = self._rotate_start[1]
        after = item.get_rotation()
        self._rotate_start = None
        if abs(before - after) < 0.1:
            return
        self._push_command(
            "旋转选区",
            undo=lambda i=item, a=before: i.set_rotation(a),
            redo=lambda i=item, a=after: i.set_rotation(a),
        )
        self._refresh_after_items_changed()

    def _selected_composition_items(self):
        return [it for it in self._scene.selectedItems() if isinstance(it, CompositionItem)]

    def _change_layer(self, mode):
        selected = self._selected_composition_items()
        if not selected:
            self._notify("没有选中的画布对象", "warning")
            return
        before = [(it, it.zValue()) for it in self._all_items()]
        items = self._sorted_items()
        selected_ids = {id(it) for it in selected}
        if mode == "top":
            base = max((it.zValue() for it in items), default=0) + 1
            for offset, it in enumerate(sorted(selected, key=lambda x: x.zValue())):
                it.setZValue(base + offset)
        elif mode == "bottom":
            base = min((it.zValue() for it in items), default=0) - len(selected)
            for offset, it in enumerate(sorted(selected, key=lambda x: x.zValue())):
                it.setZValue(base + offset)
        else:
            ordered = items[:]
            if mode == "up":
                rng = range(len(ordered) - 2, -1, -1)
                for i in rng:
                    if id(ordered[i]) in selected_ids and id(ordered[i + 1]) not in selected_ids:
                        ordered[i], ordered[i + 1] = ordered[i + 1], ordered[i]
            elif mode == "down":
                for i in range(1, len(ordered)):
                    if id(ordered[i]) in selected_ids and id(ordered[i - 1]) not in selected_ids:
                        ordered[i], ordered[i - 1] = ordered[i - 1], ordered[i]
            for z, it in enumerate(ordered):
                it.setZValue(z + 1)

        after = [(it, it.zValue()) for it in self._all_items()]
        if [(id(i), z) for i, z in before] == [(id(i), z) for i, z in after]:
            self._notify("层级没有变化", "warning")
            return

        def apply_state(state):
            for it, z in state:
                it.setZValue(z)

        self._push_command(
            "调整层级",
            undo=lambda s=before: apply_state(s),
            redo=lambda s=after: apply_state(s),
        )
        self._refresh_after_items_changed()
        self._notify("已调整层级")

    def _nudge_selected(self, dx, dy):
        items = self._selected_composition_items()
        if not items:
            return False
        before = [(it, it.get_full_pos()) for it in items]
        for it in items:
            x, y = it.get_full_pos()
            it.set_full_pos(x + dx, y + dy)
        after = [(it, it.get_full_pos()) for it in items]

        def apply_positions(state):
            for it, pos in state:
                it.set_full_pos(*pos)

        self._push_command(
            "微调位置",
            undo=lambda s=before: apply_positions(s),
            redo=lambda s=after: apply_positions(s),
        )
        self._refresh_after_items_changed()
        return True

    def _push_command(self, label, undo, redo):
        if self._history_block:
            return
        self._undo_stack.append({"label": label, "undo": undo, "redo": redo})
        self._redo_stack.clear()
        self._update_controls()

    def _undo(self):
        if not self._undo_stack:
            self._notify("没有可撤销的操作", "warning")
            return
        cmd = self._undo_stack.pop()
        self._history_block = True
        try:
            cmd["undo"]()
        finally:
            self._history_block = False
        self._redo_stack.append(cmd)
        self._refresh_after_items_changed()
        self._notify(f"已撤销：{cmd['label']}")

    def _redo(self):
        if not self._redo_stack:
            self._notify("没有可恢复的操作", "warning")
            return
        cmd = self._redo_stack.pop()
        self._history_block = True
        try:
            cmd["redo"]()
        finally:
            self._history_block = False
        self._undo_stack.append(cmd)
        self._refresh_after_items_changed()
        self._notify(f"已恢复：{cmd['label']}")

    def _background_state(self):
        c = self._background_color
        return (self._background_mode, (c.red(), c.green(), c.blue()))

    def _apply_background_state(self, state):
        mode, color = state
        self._background_mode = mode
        self._background_color = QColor(*color)
        self._sync_background_controls()
        self._scene.update()

    def _set_background_mode(self, mode, color=None, push=True):
        before = self._background_state()
        if color is not None:
            self._background_color = QColor(color)
        self._background_mode = mode
        after = self._background_state()
        if before == after:
            return
        self._sync_background_controls()
        self._scene.update()
        if push:
            self._push_command(
                "背景设置",
                undo=lambda s=before: self._apply_background_state(s),
                redo=lambda s=after: self._apply_background_state(s),
            )
        self._notify("已更新导出背景")

    def _on_background_combo(self):
        mode = self._bg_combo.currentData()
        if mode == "white":
            self._set_background_mode("white", QColor("#FFFFFF"))
        elif mode == "transparent":
            self._set_background_mode("transparent")
        else:
            self._set_background_mode("color", self._background_color)

    def _pick_color_dialog(self):
        color = QColorDialog.getColor(self._background_color, self, "选择导出背景色")
        if color.isValid():
            self._set_background_mode("color", color)

    def _toggle_eyedropper(self):
        self._eyedropper_active = self._btn_eyedropper.isChecked()
        self._sync_view_cursor()
        if self._eyedropper_active:
            self._notify("吸管已开启：点击画布上的选区取背景色")
        else:
            self._notify("吸管已关闭")

    def _sample_background_at(self, scene_pos):
        for item in self._scene.items(scene_pos):
            if isinstance(item, CompositionItem):
                rgb = item.sample_color_at_scene(scene_pos)
                if rgb:
                    self._set_background_mode("color", QColor(*rgb))
                    self._btn_eyedropper.setChecked(False)
                    self._eyedropper_active = False
                    self._sync_view_cursor()
                    self._notify(f"已取色：#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}")
                    return
        self._notify("这里没有可取色的选区", "warning")

    def _set_padding(self, value):
        value = int(value)
        before = self._padding
        if before == value:
            return
        self._padding = value
        self._scene.update()
        self._push_command(
            "导出边距",
            undo=lambda v=before: self._apply_padding(v),
            redo=lambda v=value: self._apply_padding(v),
        )
        self._notify(f"导出边距：{value}px")

    def _apply_padding(self, value):
        self._padding = int(value)
        self._padding_spin.blockSignals(True)
        self._padding_spin.setValue(self._padding)
        self._padding_spin.blockSignals(False)
        self._scene.update()

    def _sync_background_controls(self):
        self._bg_combo.blockSignals(True)
        idx = self._bg_combo.findData(self._background_mode)
        if idx >= 0:
            self._bg_combo.setCurrentIndex(idx)
        self._bg_combo.blockSignals(False)
        c = self._background_color
        self._btn_color.setStyleSheet(_button_style() + f"""
            QPushButton {{
                border-left: 12px solid {c.name()};
            }}
        """)

    def _preview_background_color(self):
        if self._background_mode == "transparent":
            return None
        if self._background_mode == "white":
            return QColor("#FFFFFF")
        return QColor(self._background_color)

    def _export_background(self):
        if self._background_mode == "transparent":
            return None
        color = QColor("#FFFFFF") if self._background_mode == "white" else self._background_color
        return (color.red(), color.green(), color.blue(), 255)

    def _items_bounds_full(self):
        items = self._all_items()
        if not items:
            return None
        rects = [it.get_full_rect() for it in items]
        min_x = min(r[0] for r in rects)
        min_y = min(r[1] for r in rects)
        max_x = max(r[0] + r[2] for r in rects)
        max_y = max(r[1] + r[3] for r in rects)
        return QRectF(min_x, min_y, max_x - min_x, max_y - min_y)

    def _export_rect_full(self):
        bounds = self._items_bounds_full()
        if not bounds:
            return None
        pad = self._padding
        return QRectF(bounds.x() - pad, bounds.y() - pad,
                      bounds.width() + pad * 2, bounds.height() + pad * 2)

    def _export_rect_scene(self):
        full = self._export_rect_full()
        if not full:
            return None
        return self._full_rect_to_scene(full)

    def _set_drop_preview(self, idx, scene_pos):
        if idx < 0 or idx >= len(self._selections):
            self._drop_preview_rect = None
            return
        sel = self._selections[idx]
        self._drop_preview_rect = QRectF(
            scene_pos.x(), scene_pos.y(),
            max(4, sel.rect[2] * self._layout_scale),
            max(4, sel.rect[3] * self._layout_scale),
        )
        self._scene.update()

    def _clear_drop_preview(self):
        self._drop_preview_rect = None
        self._scene.update()

    def _set_view_zoom(self, zoom, center=False):
        ns = max(self._MIN_ZOOM, min(self._MAX_ZOOM, float(zoom)))
        if abs(ns - self._view_zoom) < 0.001:
            return
        center_sp = None
        if center:
            center_sp = self._view.mapToScene(self._view.viewport().rect().center())
        self._view_zoom = ns
        self._apply_view_zoom()
        if center_sp is not None:
            self._view.centerOn(center_sp)
        self._scene.update()
        self._update_controls()

    def _apply_view_zoom(self):
        self._view.resetTransform()
        self._view.scale(self._view_zoom, self._view_zoom)
        for item in self._all_items():
            item.set_view_zoom(self._view_zoom)

    def _zoom_at(self, factor, vp_pos: QPointF):
        vp = QPoint(int(vp_pos.x()), int(vp_pos.y()))
        old_sp = self._view.mapToScene(vp)
        ns = max(self._MIN_ZOOM, min(self._MAX_ZOOM, self._view_zoom * factor))
        if abs(ns - self._view_zoom) < 0.001:
            return
        self._view_zoom = ns
        self._apply_view_zoom()
        new_vp = self._view.mapFromScene(old_sp)
        dx = vp.x() - new_vp.x()
        dy = vp.y() - new_vp.y()
        self._view.horizontalScrollBar().setValue(round(self._view.horizontalScrollBar().value() - dx))
        self._view.verticalScrollBar().setValue(round(self._view.verticalScrollBar().value() - dy))
        self._scene.update()
        self._update_controls()

    def _fit_content(self):
        full = self._export_rect_full()
        if not full:
            self._notify("画布上还没有内容", "warning")
            return
        vw = max(1, self._view.viewport().width())
        vh = max(1, self._view.viewport().height())
        rect = self._export_rect_scene()
        if rect:
            zoom = min(vw / max(1, rect.width()), vh / max(1, rect.height())) * 0.84
            self._view_zoom = max(self._MIN_ZOOM, min(self._MAX_ZOOM, zoom))
            self._apply_view_zoom()
            self._view.centerOn(rect.center())
        self._scene.update()
        self._update_controls()
        self._notify("已适应全部内容")

    def _update_title(self):
        n = len(self._all_items())
        self.setWindowTitle(f"自由编排 — {self._doc_name}  ({n} 个选区)")

    def _on_sel_changed(self):
        selected = self._selected_composition_items()
        show_handle = len(selected) == 1
        for item in self._all_items():
            item.set_edit_handles_visible(show_handle and item in selected)
        self._update_controls()

    def _refresh_after_items_changed(self):
        self._update_title()
        self._ensure_scene_contains()
        self._scene.update()
        self._update_controls()

    def _update_controls(self):
        count = len(self._all_items())
        self._btn_del.setEnabled(bool(self._scene.selectedItems()))
        self._btn_clear.setEnabled(count > 0)
        self._btn_export.setEnabled(count > 0)
        self._btn_undo.setEnabled(bool(self._undo_stack))
        self._btn_redo.setEnabled(bool(self._redo_stack))
        has_selected = bool(self._selected_composition_items())
        for btn in (self._btn_layer_up, self._btn_layer_down,
                    self._btn_layer_top, self._btn_layer_bottom):
            btn.setEnabled(has_selected)
        self._zoom_label.setText(f"{int(self._view_zoom * 100)}%")
        if hasattr(self, "_btn_maximize"):
            self._btn_maximize.setText("还原" if self.isMaximized() and not self.isFullScreen() else "最大")
        if hasattr(self, "_btn_fullscreen"):
            self._btn_fullscreen.setText("退出" if self.isFullScreen() else "全屏")
        self._sync_background_controls()

    def _sync_view_cursor(self):
        if self._eyedropper_active:
            self._view.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        elif self._space_down:
            self._view.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        else:
            self._view.unsetCursor()

    def _view_center_scene(self):
        return self._view.mapToScene(self._view.viewport().rect().center())

    def _restore_view_center_later(self, center):
        keep = QPointF(center.x(), center.y())

        def restore():
            self._view.centerOn(keep)
            self._update_controls()

        QTimer.singleShot(0, restore)

    def _toggle_maximized(self):
        center = self._view_center_scene()
        if self.isFullScreen() or not self.isMaximized():
            self.showMaximized()
        else:
            self.showNormal()
        self._restore_view_center_later(center)

    def _toggle_fullscreen(self):
        center = self._view_center_scene()
        if self.isFullScreen():
            if self._fullscreen_restore_maximized:
                self.showMaximized()
            else:
                self.showNormal()
        else:
            self._fullscreen_restore_maximized = self.isMaximized()
            self.showFullScreen()
        self._restore_view_center_later(center)

    def _exit_fullscreen(self):
        if not self.isFullScreen():
            return
        center = self._view_center_scene()
        if self._fullscreen_restore_maximized:
            self.showMaximized()
        else:
            self.showNormal()
        self._restore_view_center_later(center)

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange:
            self._update_controls()

    def _notify(self, text, kind="info"):
        colors = {
            "info": ("rgba(245,253,255,0.82)", "#102A43"),
            "warning": ("rgba(255,237,153,0.88)", "#3D2E00"),
            "error": ("rgba(255,211,211,0.88)", "#5C1A1A"),
        }
        bg, fg = colors.get(kind, colors["info"])
        self._status.setStyleSheet(f"""
            QLabel {{
                background: {bg};
                border: 1px solid rgba(68,156,184,0.36);
                border-radius: 8px;
                padding: 6px 10px;
                color: {fg};
            }}
        """)
        self._status.setText(text)
        self._toast_timer.start(4200)

    def set_question_num(self, question_num):
        self._question_num = str(question_num or "")

    def _export(self):
        items = self._sorted_items()
        if not items:
            self._notify("画布上没有选区", "warning")
            return
        try:
            data = [it.export_data() for it in items]
            path = CompositionMerger.export(
                data, self._output_dir, self._doc_name,
                self._mode, self._question_num,
                background=self._export_background(),
                padding=self._padding,
                custom_prefix=self._custom_prefix,
            )
            self._notify(f"已导出：{path}")
            self.export_succeeded.emit(path)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败：{e}")

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_F11:
            self._toggle_fullscreen()
            event.accept()
            return
        if event.key() == Qt.Key.Key_Escape and self.isFullScreen():
            self._exit_fullscreen()
            event.accept()
            return
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self._delete()
            return
        nudges = {
            Qt.Key.Key_Left: (-1, 0),
            Qt.Key.Key_Right: (1, 0),
            Qt.Key.Key_Up: (0, -1),
            Qt.Key.Key_Down: (0, 1),
        }
        if event.key() in nudges:
            step = 10 if event.modifiers() & Qt.KeyboardModifier.ShiftModifier else 1
            dx, dy = nudges[event.key()]
            if self._nudge_selected(dx * step, dy * step):
                event.accept()
                return
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            self._space_down = True
            self._sync_view_cursor()
            event.accept()
            return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            self._space_down = False
            self._sync_view_cursor()
            event.accept()
            return
        super().keyReleaseEvent(event)
