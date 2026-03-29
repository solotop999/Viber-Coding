"""Rectangle border annotation tool."""
from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush

from editor.tools.base_tool import Annotation, BaseTool


class RectTool(BaseTool):
    def release(self, pos: QPointF) -> Annotation | None:
        self._active = False
        if self._start and (pos - self._start).manhattanLength() > 4:
            return Annotation(
                kind="rect",
                start=self._start,
                end=pos,
                color=self.color,
                stroke_width=self.stroke_width,
            )
        return None

    def draw_preview(self, painter: QPainter) -> None:
        if self._active and self._start and self._current:
            _draw_rect(painter, self._start, self._current,
                       self.color, self.stroke_width)


def _draw_rect(painter: QPainter, start: QPointF, end: QPointF,
               color: QColor, width: int) -> None:
    rect = QRectF(start, end).normalized()
    pen = QPen(color, width)
    painter.setPen(pen)
    painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
    painter.drawRect(rect)


def render_rect(painter: QPainter, ann: Annotation) -> None:
    _draw_rect(painter, ann.start, ann.end, ann.color, ann.stroke_width)
