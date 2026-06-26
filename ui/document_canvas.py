from PySide6.QtWidgets import QWidget, QScrollArea
from PySide6.QtGui import QPainter, QColor, QPen, QImage, QCursor, QPainterPath
from PySide6.QtCore import Qt, QRect, QPoint, QPointF, Signal
from config.settings import Settings
from core.document_loader import DocumentLoader
from core.selection_mask import (
    bounding_rect_from_points,
    normalize_points_to_rect,
    qimage_from_crop,
    scale_points,
)


class DocumentCanvas(QWidget):
    selection_changed = Signal(bool)

    def __init__(self):
        super().__init__()
        self.image = None
        self.selection_rect = None
        self.is_selecting = False
        self.start_point = None
        self.selection_tool = "rect"
        self.lasso_points = []
        self.scale_factor = 1.0    # paintEvent 的乘数，只对 self.image 生效
        self.selection_mode = False
        self._file_path = None     # 原始文件路径
        self._orig_size = None     # 原始图片尺寸 (w, h)
        self._apply_styles()

    def _apply_styles(self):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(244, 254, 255, 0.72);
                border: 1px solid {Settings.BORDER['normal']};
                border-radius: {Settings.RADIUS['normal']}px;
            }}
        """)

    def load_file(self, file_path):
        """自适应加载：大图缩到阈值，存 _orig_size 备用。"""
        qimg, ow, oh = DocumentLoader.load_image_adaptive(file_path)
        self._file_path = file_path
        self._orig_size = (ow, oh)
        self.image = qimg
        self.scale_factor = 1.0
        self.selection_rect = None
        self.selection_changed.emit(False)
        self.setFixedSize(qimg.width(), qimg.height())
        self.update()

    # ── 旧接口（PDF 等不使用 _file_path 的外部路径） ─────────────
    def set_image(self, image):
        self.image = image
        self._file_path = None
        self._orig_size = None
        self.scale_factor = 1.0
        self.selection_rect = None
        self.selection_changed.emit(False)
        if image:
            self.setFixedSize(int(image.width() * self.scale_factor),
                              int(image.height() * self.scale_factor))
        else:
            self.setMinimumSize(400, 300)
        self.update()

    def set_image_without_scale(self, image):
        """PDF 渲染后使用：贴原尺寸，不额外缩放。"""
        self.image = image
        self.scale_factor = 1.0
        self.selection_rect = None
        self.selection_changed.emit(False)
        if image:
            self.setFixedSize(image.width(), image.height())
        else:
            self.setMinimumSize(400, 300)
        self.update()

    # ── 缩放 ─────────────────────────────────────────────────────
    def set_scale_factor(self, doc_scale):
        """doc_scale 是相对于原始文档尺寸的缩放倍数。
        内部换算为相对于 self.image 的 scale，再作用于 widget。"""
        if not self.image:
            return
        if self._orig_size and self.image.width() != self._orig_size[0]:
            # 当前存储的是缩略图，需要坐标系换算
            canvas_scale = doc_scale * (self._orig_size[0] / self.image.width())
        else:
            canvas_scale = doc_scale
        self.scale_factor = canvas_scale
        sw = int(self.image.width() * canvas_scale)
        sh = int(self.image.height() * canvas_scale)
        self.setFixedSize(sw, sh)
        self.update()

    def set_selection_mode(self, enabled):
        self.selection_mode = enabled
        if enabled:
            self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        else:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            self.selection_rect = None
            self.lasso_points = []
            self.selection_changed.emit(False)
            self.update()

    def set_selection_tool(self, tool):
        tool = "free" if tool == "free" else "rect"
        if self.selection_tool == tool:
            return
        self.selection_tool = tool
        self.clear_selection()

    def clear_selection(self):
        self.selection_rect = None
        self.lasso_points = []
        self.selection_changed.emit(False)
        self.update()

    def has_selection(self):
        return self.selection_rect is not None

    def get_selection_rect(self):
        """返回 self.image 坐标系中的选区 (x, y, w, h)。"""
        if not self.selection_rect:
            return None
        return self._widget_rect_to_image_rect(self.selection_rect)

    def get_selection_rect_original(self):
        """返回原始图片坐标系中的选区，用于全分辨率导出。"""
        rect = self.get_selection_rect()
        if not rect or not self._orig_size:
            return rect
        x, y, w, h = rect
        rx = self._orig_size[0] / self.image.width()
        ry = self._orig_size[1] / self.image.height()
        return (int(x * rx), int(y * ry), int(w * rx), int(h * ry))

    def get_selection_shape_type(self):
        return "free" if self.selection_tool == "free" and self.get_selection_mask_points() else "rect"

    def get_selection_mask_points(self):
        if self.selection_tool != "free" or len(self.lasso_points) < 3:
            return None
        abs_points = [self._widget_point_to_image_tuple(p) for p in self.lasso_points]
        rect = self.get_selection_rect()
        return normalize_points_to_rect(abs_points, rect)

    def get_selection_mask_points_original(self):
        points = self.get_selection_mask_points()
        rect = self.get_selection_rect()
        if not points or not rect or not self._orig_size:
            return points
        rx = self._orig_size[0] / self.image.width()
        ry = self._orig_size[1] / self.image.height()
        return scale_points(points, rx, ry)

    def get_selection_preview(self, outside_mode="transparent"):
        rect = self.get_selection_rect()
        if not rect or not self.image:
            return None
        mask_points = self.get_selection_mask_points()
        return qimage_from_crop(self.image, rect, mask_points, outside_mode)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.image:
            scaled = self.image.scaled(
                int(self.image.width() * self.scale_factor),
                int(self.image.height() * self.scale_factor),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            painter.drawImage(0, 0, scaled)
        if self.selection_rect and self.selection_tool == "rect":
            pen = QPen(QColor(255, 107, 107, 200))
            pen.setWidth(3)
            pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(pen)
            fill = QColor(255, 107, 107, 30)
            painter.fillRect(self.selection_rect, fill)
            painter.drawRect(self.selection_rect)
        elif self.selection_tool == "free" and self.lasso_points:
            pen = QPen(QColor(0, 142, 202, 230))
            pen.setWidth(3)
            pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(pen)
            path = QPainterPath(QPointF(self.lasso_points[0]))
            for point in self.lasso_points[1:]:
                path.lineTo(QPointF(point))
            if not self.is_selecting and len(self.lasso_points) >= 3:
                path.closeSubpath()
            painter.fillPath(path, QColor(0, 153, 204, 34))
            painter.drawPath(path)
            if self.selection_rect and not self.is_selecting:
                bound_pen = QPen(QColor(255, 255, 255, 210))
                bound_pen.setWidth(1)
                bound_pen.setStyle(Qt.PenStyle.DotLine)
                painter.setPen(bound_pen)
                painter.drawRect(self.selection_rect)

    def mousePressEvent(self, event):
        if self.selection_mode and event.button() == Qt.MouseButton.LeftButton:
            self.is_selecting = True
            self.start_point = self._clamp_widget_point(event.pos())
            if self.selection_tool == "free":
                self.lasso_points = [self.start_point]
                self.selection_rect = QRect(self.start_point, self.start_point)
            else:
                self.lasso_points = []
                self.selection_rect = QRect(self.start_point, self.start_point)
            self.update()

    def mouseMoveEvent(self, event):
        if self.is_selecting:
            pos = self._clamp_widget_point(event.pos())
            if self.selection_tool == "free":
                if not self.lasso_points or (pos - self.lasso_points[-1]).manhattanLength() >= 2:
                    self.lasso_points.append(pos)
                self._update_lasso_rect()
            else:
                self.selection_rect = QRect(self.start_point, pos).normalized()
            self.update()

    def mouseReleaseEvent(self, event):
        if self.is_selecting and event.button() == Qt.MouseButton.LeftButton:
            self.is_selecting = False
            if self.selection_tool == "free":
                pos = self._clamp_widget_point(event.pos())
                if not self.lasso_points or self.lasso_points[-1] != pos:
                    self.lasso_points.append(pos)
                self._update_lasso_rect()
            if self.selection_rect and self.selection_rect.width() > 5 and self.selection_rect.height() > 5:
                self.selection_changed.emit(True)
            else:
                self.selection_rect = None
                self.lasso_points = []
                self.selection_changed.emit(False)
            self.update()

    def _clamp_widget_point(self, point):
        if not self.image:
            return point
        max_x = max(0, int(self.image.width() * self.scale_factor) - 1)
        max_y = max(0, int(self.image.height() * self.scale_factor) - 1)
        return QPoint(min(max(point.x(), 0), max_x),
                      min(max(point.y(), 0), max_y))

    def _widget_point_to_image_tuple(self, point):
        x = min(max(point.x() / self.scale_factor, 0.0), self.image.width())
        y = min(max(point.y() / self.scale_factor, 0.0), self.image.height())
        return (x, y)

    def _widget_rect_to_image_rect(self, rect):
        x = int(rect.x() / self.scale_factor)
        y = int(rect.y() / self.scale_factor)
        w = int(rect.width() / self.scale_factor)
        h = int(rect.height() / self.scale_factor)
        if self.image:
            x = min(max(x, 0), self.image.width() - 1)
            y = min(max(y, 0), self.image.height() - 1)
            w = min(max(w, 1), self.image.width() - x)
            h = min(max(h, 1), self.image.height() - y)
        return (x, y, w, h)

    def _update_lasso_rect(self):
        rect = bounding_rect_from_points((p.x(), p.y()) for p in self.lasso_points)
        if rect:
            self.selection_rect = QRect(*rect)


class ScrollableCanvas(QScrollArea):
    def __init__(self):
        super().__init__()
        self.canvas = DocumentCanvas()
        self.setWidget(self.canvas)
        self.setWidgetResizable(False)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._apply_styles()

    def _apply_styles(self):
        from ui.glass_effect import GlassEffect
        self.setStyleSheet(f"""
            QScrollArea {{
                background-color: rgba(236, 252, 255, 0.34);
                border: none;
                border-radius: {Settings.RADIUS['normal']}px;
            }}
            {GlassEffect._get_scrollbar_styles()}
        """)

    def get_canvas(self):
        return self.canvas
