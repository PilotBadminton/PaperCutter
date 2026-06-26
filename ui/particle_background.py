"""
Static blue main-window background.

No animation, no particles, no image assets. The background is cached on resize
so idle windows do not keep repainting.
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPixmap
from PySide6.QtWidgets import QWidget


class ParticleBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self._cache = QPixmap()
        self._cache_size = None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._rebuild_cache()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        if self._cache.isNull():
            self._rebuild_cache()
        if self._cache.isNull():
            self._draw_fallback(painter)
        else:
            painter.drawPixmap(0, 0, self._cache)

    def set_particle_count(self, count):
        return None

    def set_fps(self, fps):
        return None

    def _rebuild_cache(self):
        width = max(1, self.width())
        height = max(1, self.height())
        size_key = (width, height)
        if self._cache_size == size_key and not self._cache.isNull():
            return
        self._cache_size = size_key

        cache = QPixmap(width, height)
        cache.fill(Qt.GlobalColor.transparent)

        painter = QPainter(cache)
        self._draw_blue_background(painter, width, height)
        painter.end()
        self._cache = cache

    def _draw_blue_background(self, painter, width, height):
        base = QLinearGradient(0, 0, width, height)
        base.setColorAt(0.00, QColor(229, 251, 255))
        base.setColorAt(0.42, QColor(117, 218, 225))
        base.setColorAt(1.00, QColor(20, 140, 170))
        painter.fillRect(self.rect(), base)

        left_lift = QLinearGradient(0, 0, width * 0.28, 0)
        left_lift.setColorAt(0.00, QColor(246, 255, 255, 132))
        left_lift.setColorAt(0.72, QColor(244, 255, 255, 58))
        left_lift.setColorAt(1.00, QColor(244, 255, 255, 0))
        painter.fillRect(self.rect(), left_lift)

        top_lift = QLinearGradient(0, 0, 0, max(80, int(height * 0.14)))
        top_lift.setColorAt(0.00, QColor(255, 255, 255, 92))
        top_lift.setColorAt(0.55, QColor(255, 255, 255, 25))
        top_lift.setColorAt(1.00, QColor(255, 255, 255, 0))
        painter.fillRect(self.rect(), top_lift)

    def _draw_fallback(self, painter):
        painter.fillRect(self.rect(), QColor(112, 213, 224))
