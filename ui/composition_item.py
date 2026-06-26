"""
编排画布上的单个选区项 — full_{x,y} 为导出坐标，scene pos = full × layout_scale
"""
from io import BytesIO
import math

from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsRectItem, QGraphicsEllipseItem
from PySide6.QtGui import QPixmap, QImage, QPen, QColor, QBrush, QCursor
from PySide6.QtCore import Qt, QBuffer, QIODevice, QRectF
from PIL import Image as PILImage
from core.selection_mask import apply_mask_to_crop


class _RotationHandle(QGraphicsEllipseItem):
    def __init__(self, owner):
        super().__init__(owner)
        self._owner = owner
        self._dragging = False
        self._start_angle = 0.0
        self._start_rotation = 0.0
        self.setBrush(QBrush(QColor(255, 255, 255, 235)))
        self.setPen(QPen(QColor(0, 132, 190, 230), 2))
        self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self.setZValue(1000)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._start_rotation = self._owner.get_rotation()
            self._start_angle = self._angle_from_scene(event.scenePos())
            if self._owner._owner:
                self._owner._owner._begin_rotate(self._owner)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging:
            delta = self._angle_from_scene(event.scenePos()) - self._start_angle
            self._owner.set_rotation(self._start_rotation + delta)
            if self._owner._owner:
                self._owner._owner._rotation_changed(self._owner)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._dragging and event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            if self._owner._owner:
                self._owner._owner._end_rotate(self._owner)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def _angle_from_scene(self, scene_pos):
        center = self._owner.mapToScene(self._owner.transformOriginPoint())
        dx = scene_pos.x() - center.x()
        dy = scene_pos.y() - center.y()
        return math.degrees(math.atan2(dy, dx)) + 90.0


class CompositionItem(QGraphicsPixmapItem):
    def __init__(self, pixmap, export_data, full_w, full_h, parent=None):
        super().__init__(pixmap, parent)
        self.setFlags(
            QGraphicsPixmapItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsPixmapItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsPixmapItem.GraphicsItemFlag.ItemIsFocusable |
            QGraphicsPixmapItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setCacheMode(QGraphicsPixmapItem.CacheMode.NoCache)
        self.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
        self._export = export_data
        self._full_x = 0.0
        self._full_y = 0.0
        self._full_w = full_w
        self._full_h = full_h
        self._layout_scale = 1.0
        self._render_scale = 1.0
        self._render_ready = False
        self._pixmap_offset_x = 0.0
        self._pixmap_offset_y = 0.0
        self._block_item_change = False
        self._border = None
        self._handle = None
        self._handle_line = None
        self._rotation_deg = 0.0
        self._owner = None
        self._move_start = None
        self._rebuild_border()

    def set_owner(self, owner):
        self._owner = owner

    def set_layout_scale(self, scale):
        """按固定布局比例重建代理图；视图缩放不调用这里。"""
        same_scale = abs(scale - self._layout_scale) < 0.0001 and self._render_ready
        self._block_item_change = True
        self._layout_scale = max(0.001, float(scale))
        if not same_scale:
            self._render_scale = min(self._render_scale, self._max_render_scale())
            self._rebuild_pixmap()
        self.setPos(self._full_x * self._layout_scale,
                    self._full_y * self._layout_scale)
        self._block_item_change = False
        if not same_scale:
            self._rebuild_border()

    def set_display_scale(self, scale):
        """兼容旧调用：这里的 scale 现在表示固定布局比例，不表示视图缩放。"""
        self.set_layout_scale(scale)

    def set_view_zoom(self, zoom):
        target = max(1.0, min(float(zoom), self._max_render_scale()))
        if abs(target - self._render_scale) / max(self._render_scale, 0.001) < 0.12:
            return
        self._render_scale = target
        self._block_item_change = True
        self._rebuild_pixmap()
        self._block_item_change = False
        self._rebuild_border()

    def _max_render_scale(self):
        return max(1.0, 1.0 / max(self._layout_scale, 0.001))

    def _rebuild_pixmap(self):
        orig = self._export.get('_full_pil') if self._export else None
        if not orig:
            return
        draw_w = max(int(self._full_w * self._layout_scale * self._render_scale), 4)
        draw_h = max(int(self._full_h * self._layout_scale * self._render_scale), 4)
        thumb = orig.resize((draw_w, draw_h), PILImage.LANCZOS)
        buf = BytesIO()
        thumb.save(buf, 'PNG')
        buf.seek(0)
        self.setPixmap(QPixmap.fromImage(QImage.fromData(buf.getvalue())))
        self._render_ready = True
        self._update_geometry_transform()

    def set_full_pos(self, x, y):
        self._block_item_change = True
        self._full_x = float(x)
        self._full_y = float(y)
        self.setPos(self._full_x * self._layout_scale,
                    self._full_y * self._layout_scale)
        self._block_item_change = False

    def get_full_pos(self):
        return (float(self._full_x), float(self._full_y))

    def get_full_rect(self):
        rect = self.mapToScene(self._content_rect()).boundingRect()
        return (
            float(rect.x() / self._layout_scale),
            float(rect.y() / self._layout_scale),
            float(rect.width() / self._layout_scale),
            float(rect.height() / self._layout_scale),
        )

    def get_unrotated_full_rect(self):
        return (float(self._full_x), float(self._full_y),
                float(self._full_w), float(self._full_h))

    def get_rotation(self):
        return float(self._rotation_deg)

    def set_rotation(self, angle):
        angle = ((float(angle) + 180.0) % 360.0) - 180.0
        if abs(angle) < 0.01:
            angle = 0.0
        self._rotation_deg = angle
        self.setRotation(angle)

    def set_edit_handles_visible(self, visible):
        for child in (self._border, self._handle_line, self._handle):
            if child:
                child.setVisible(bool(visible))

    def _content_rect(self):
        return QRectF(
            self._pixmap_offset_x,
            self._pixmap_offset_y,
            self.pixmap().width(),
            self.pixmap().height(),
        )

    def _update_geometry_transform(self):
        pm = self.pixmap()
        if not pm.isNull():
            visual_w = self._full_w * self._layout_scale
            visual_h = self._full_h * self._layout_scale
            origin_x = visual_w / 2.0
            origin_y = visual_h / 2.0
            scale = 1.0 / max(self._render_scale, 0.001)
            # Qt applies item scale around the same origin used for rotation.
            # Offset the high-resolution pixmap so the scaled visual top-left
            # still maps to item pos/full_pos instead of drifting with zoom.
            self._pixmap_offset_x = -((1.0 - scale) * origin_x / scale)
            self._pixmap_offset_y = -((1.0 - scale) * origin_y / scale)
            self.setOffset(self._pixmap_offset_x, self._pixmap_offset_y)
            self.setTransformOriginPoint(origin_x, origin_y)
            self.setScale(scale)

    def _rebuild_border(self):
        for child in (self._border, self._handle_line, self._handle):
            if child:
                child.setParentItem(None)
                if child.scene():
                    child.scene().removeItem(child)
        self._border = None
        self._handle_line = None
        self._handle = None
        content = self._content_rect()
        scale = max(1.0 / max(self._render_scale, 0.001), 0.001)
        handle_unit = 1.0 / scale
        r = QGraphicsRectItem(
            content.x() - handle_unit,
            content.y() - handle_unit,
            content.width() + handle_unit * 2,
            content.height() + handle_unit * 2,
            self,
        )
        pen = QPen(QColor(0, 153, 204, 210), 2, Qt.PenStyle.DashLine)
        pen.setCosmetic(True)
        r.setPen(pen)
        r.setBrush(QColor(0, 0, 0, 0))
        self._border = r
        center_x = self.transformOriginPoint().x()
        line_top = content.y() - 30 * handle_unit
        line = QGraphicsRectItem(
            center_x - 0.5 * handle_unit,
            line_top,
            handle_unit,
            30 * handle_unit,
            self,
        )
        line_pen = QPen(QColor(0, 132, 190, 190), 1)
        line_pen.setCosmetic(True)
        line.setPen(line_pen)
        line.setBrush(QColor(0, 132, 190, 90))
        self._handle_line = line
        handle = _RotationHandle(self)
        handle.setRect(
            center_x - 7 * handle_unit,
            content.y() - 44 * handle_unit,
            14 * handle_unit,
            14 * handle_unit,
        )
        self._handle = handle
        self._update_geometry_transform()
        self.set_edit_handles_visible(self.isSelected())

    def itemChange(self, change, value):
        if (change == QGraphicsPixmapItem.GraphicsItemChange.ItemPositionHasChanged
                and not self._block_item_change
                and self._layout_scale > 0):
            self._full_x = value.x() / self._layout_scale
            self._full_y = value.y() / self._layout_scale
            if self._owner:
                self._owner._item_moved_live(self)
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        self._move_start = self.get_full_pos()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self._owner and self._move_start:
            before = self._move_start
            after = self.get_full_pos()
            self._owner._record_move(self, before, after)
        self._move_start = None

    def export_data(self):
        d = dict(self._export) if self._export else {}
        d['comp_x'] = self._full_x
        d['comp_y'] = self._full_y
        d['comp_rotation'] = self._rotation_deg
        return d

    def sample_color_at_scene(self, scene_pos):
        local = self.mapFromScene(scene_pos)
        content = self._content_rect()
        if not content.contains(local):
            return None
        pix_x = local.x() - self._pixmap_offset_x
        pix_y = local.y() - self._pixmap_offset_y

        pil = self._export.get('_full_pil') if self._export else None
        if pil:
            full_scale = self._layout_scale * self._render_scale
            x = max(0, min(self._full_w - 1, int(pix_x / full_scale)))
            y = max(0, min(self._full_h - 1, int(pix_y / full_scale)))
            color = pil.convert('RGBA').getpixel((x, y))
            return color[:3]

        image = self.pixmap().toImage()
        x = max(0, min(image.width() - 1, int(pix_x)))
        y = max(0, min(image.height() - 1, int(pix_y)))
        color = image.pixelColor(x, y)
        return (color.red(), color.green(), color.blue())

    @staticmethod
    def from_file_crop(file_path, rect_orig, shape_type="rect", mask_points=None):
        pil = PILImage.open(file_path).crop((
            rect_orig[0], rect_orig[1],
            rect_orig[0] + rect_orig[2],
            rect_orig[1] + rect_orig[3]
        ))
        if shape_type == "free" and mask_points:
            pil = apply_mask_to_crop(pil, mask_points, "transparent")
        fw, fh = pil.size
        pix = _pil_to_pixmap(pil)
        data = {
            'file_path': file_path,
            'rect_orig': rect_orig,
            'shape_type': shape_type,
            'mask_points': mask_points,
            '_full_pil': pil,
        }
        return CompositionItem(pix, data, fw, fh)

    @staticmethod
    def from_qimage_crop(qimage, rect, shape_type="rect", mask_points=None):
        x, y, w, h = rect
        crop = qimage.copy(x, y, w, h)
        buf = QBuffer()
        buf.open(QIODevice.OpenModeFlag.WriteOnly)
        crop.save(buf, 'PNG')
        buf.close()
        pil = PILImage.open(BytesIO(bytes(buf.data())))
        if shape_type == "free" and mask_points:
            pil = apply_mask_to_crop(pil, mask_points, "transparent")
        fw, fh = pil.size
        pix = _pil_to_pixmap(pil)
        data = {
            'file_path': None,
            'rect_orig': rect,
            'display_image': qimage,
            'shape_type': shape_type,
            'mask_points': mask_points,
            '_full_pil': pil,
        }
        return CompositionItem(pix, data, fw, fh)


def _pil_to_pixmap(pil_img, max_w=240, max_h=180):
    w, h = pil_img.size
    ratio = min(max_w / w, max_h / h, 1.0)
    if ratio < 1.0:
        pil_img = pil_img.resize((int(w * ratio), int(h * ratio)), PILImage.LANCZOS)
    buf = BytesIO()
    pil_img.save(buf, 'PNG')
    buf.seek(0)
    return QPixmap.fromImage(QImage.fromData(buf.getvalue()))
