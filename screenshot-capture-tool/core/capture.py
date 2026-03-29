"""
Full-screen selection overlay.
Displays a frozen screenshot as background, dims it,
and lets the user drag a rectangle to select a region.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt6.QtGui import (
    QColor, QPainter, QPixmap, QCursor, QKeyEvent, QPen,
)
from PyQt6.QtWidgets import QApplication, QWidget

from core.screenshot import grab_all_monitors
from PIL import Image
import io


def _pil_to_qpixmap(img: Image.Image) -> QPixmap:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    px = QPixmap()
    px.loadFromData(buf.getvalue(), "PNG")
    return px


class SelectionOverlay(QWidget):
    """
    Frameless full-screen overlay for selecting a screen region.
    Emits `region_selected(x, y, w, h)` with absolute screen coords.
    Emits `cancelled()` on Escape.
    """
    region_selected = pyqtSignal(int, int, int, int)
    cancelled = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()

        # Grab the screen before showing the overlay
        self._pil_img, (self._vx, self._vy) = grab_all_monitors()
        self._bg = _pil_to_qpixmap(self._pil_img)

        # Window setup
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))

        # Cover the entire virtual desktop
        virtual = QApplication.primaryScreen().virtualGeometry()
        for s in QApplication.screens():
            virtual = virtual.united(s.geometry())
        self.setGeometry(virtual)

        self._origin: QPoint | None = None
        self._current: QPoint | None = None
        self._selecting = False

    # ------------------------------------------------------------------ paint
    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.drawPixmap(0, 0, self._bg)

        dim = QColor(0, 0, 0, 140)
        W, H = self.width(), self.height()

        if self._selecting and self._origin and self._current:
            sel = self._selection_rect()
            # Dim the 4 sides around the selection — keep selection bright
            p.fillRect(0, 0, W, sel.top(), dim)
            p.fillRect(0, sel.bottom() + 1, W, H - sel.bottom() - 1, dim)
            p.fillRect(0, sel.top(), sel.left(), sel.height(), dim)
            p.fillRect(sel.right() + 1, sel.top(), W - sel.right() - 1, sel.height(), dim)
            # Border
            pen = QPen(QColor(255, 255, 255, 220), 1, Qt.PenStyle.SolidLine)
            p.setPen(pen)
            p.drawRect(sel)
            # Size hint
            p.setPen(QColor(255, 255, 255))
            p.drawText(sel.bottomRight() + QPoint(4, -4), f"{sel.width()} × {sel.height()}")
        else:
            p.fillRect(self.rect(), dim)

    # --------------------------------------------------------------- events
    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._origin = event.pos()
            self._current = event.pos()
            self._selecting = True

    def mouseMoveEvent(self, event) -> None:
        if self._selecting:
            self._current = event.pos()
            self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._selecting:
            self._selecting = False
            sel = self._selection_rect()
            if sel.width() > 4 and sel.height() > 4:
                # Convert widget-local coords to absolute screen coords
                geo = self.geometry()
                ax = geo.x() + sel.x() + self._vx
                ay = geo.y() + sel.y() + self._vy
                self.hide()
                self.region_selected.emit(ax, ay, sel.width(), sel.height())
            else:
                self.hide()
                self.cancelled.emit()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            self.cancelled.emit()

    # ----------------------------------------------------------------- helpers
    def _selection_rect(self) -> QRect:
        if self._origin is None or self._current is None:
            return QRect()
        return QRect(self._origin, self._current).normalized()
