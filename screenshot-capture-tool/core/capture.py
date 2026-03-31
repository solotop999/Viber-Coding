"""
Full-screen selection overlay.
Displays a frozen screenshot as background, dims it,
and lets the user drag a rectangle to select a region.
"""
from __future__ import annotations

from PIL import Image
from PyQt6.QtCore import QPoint, QRect, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QCursor, QImage, QKeyEvent, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QApplication, QWidget

from core.screenshot import grab_all_monitors


def _pil_to_qpixmap(img: Image.Image) -> QPixmap:
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    raw = img.tobytes("raw", "RGBA")
    qimg = QImage(raw, img.width, img.height, img.width * 4,
                  QImage.Format.Format_RGBA8888).copy()
    return QPixmap.fromImage(qimg)


class SelectionOverlay(QWidget):
    """
    Frameless full-screen overlay for selecting a screen region.
    Emits `region_selected(x, y, w, h)` with absolute screen coordinates.
    Emits `cancelled()` on Escape.
    """

    region_selected = pyqtSignal(int, int, int, int)
    cancelled = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()

        self._pil_img, (self._vx, self._vy) = grab_all_monitors()
        self._bg = _pil_to_qpixmap(self._pil_img)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))

        virtual = QApplication.primaryScreen().virtualGeometry()
        for screen in QApplication.screens():
            virtual = virtual.united(screen.geometry())
        self.setGeometry(virtual)

        self._origin: QPoint | None = None
        self._current: QPoint | None = None
        self._selecting = False

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self._bg)

        dim = QColor(0, 0, 0, 140)
        width, height = self.width(), self.height()

        if self._selecting and self._origin and self._current:
            selection = self._selection_rect()

            painter.fillRect(0, 0, width, selection.top(), dim)
            painter.fillRect(0, selection.bottom() + 1, width, height - selection.bottom() - 1, dim)
            painter.fillRect(0, selection.top(), selection.left(), selection.height(), dim)
            painter.fillRect(
                selection.right() + 1,
                selection.top(),
                width - selection.right() - 1,
                selection.height(),
                dim,
            )

            painter.setPen(QPen(QColor(255, 255, 255, 220), 1, Qt.PenStyle.SolidLine))
            painter.drawRect(selection)

            painter.setPen(QColor(255, 255, 255))
            painter.drawText(selection.bottomRight() + QPoint(4, -4), f"{selection.width()} x {selection.height()}")
        else:
            painter.fillRect(self.rect(), dim)

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
        if event.button() != Qt.MouseButton.LeftButton or not self._selecting:
            return

        self._selecting = False
        selection = self._selection_rect()
        geometry = self.geometry()
        x = geometry.x() + selection.x() + self._vx
        y = geometry.y() + selection.y() + self._vy
        width = selection.width()
        height = selection.height()
        if width > 4 and height > 4:
            self.hide()
            self.region_selected.emit(x, y, width, height)
        else:
            self.hide()
            self.cancelled.emit()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            self.cancelled.emit()

    def _selection_rect(self) -> QRect:
        if self._origin is None or self._current is None:
            return QRect()
        return QRect(self._origin, self._current).normalized()
