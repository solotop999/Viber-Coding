"""Arrow annotation tool."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QColor, QPainter, QPen, QPolygonF, QBrush

from editor.tools.base_tool import Annotation, BaseTool


_ARROW_HEAD_LEN = 14  # pixels
_ARROW_HEAD_ANGLE = math.radians(25)


def _draw_arrow(painter: QPainter, start: QPointF, end: QPointF,
                color: QColor, width: int) -> None:
    pen = QPen(color, width)
    pen.setCapStyle(painter.pen().capStyle())
    painter.setPen(pen)
    painter.drawLine(start, end)

    # Arrowhead
    dx = end.x() - start.x()
    dy = end.y() - start.y()
    angle = math.atan2(dy, dx)

    p1 = QPointF(
        end.x() - _ARROW_HEAD_LEN * math.cos(angle - _ARROW_HEAD_ANGLE),
        end.y() - _ARROW_HEAD_LEN * math.sin(angle - _ARROW_HEAD_ANGLE),
    )
    p2 = QPointF(
        end.x() - _ARROW_HEAD_LEN * math.cos(angle + _ARROW_HEAD_ANGLE),
        end.y() - _ARROW_HEAD_LEN * math.sin(angle + _ARROW_HEAD_ANGLE),
    )
    poly = QPolygonF([end, p1, p2])
    painter.setBrush(QBrush(color))
    painter.setPen(QPen(color, 1))
    painter.drawPolygon(poly)


class ArrowTool(BaseTool):
    def release(self, pos: QPointF) -> Annotation | None:
        self._active = False
        if self._start and (pos - self._start).manhattanLength() > 4:
            return Annotation(
                kind="arrow",
                start=self._start,
                end=pos,
                color=self.color,
                stroke_width=self.stroke_width,
            )
        return None

    def draw_preview(self, painter: QPainter) -> None:
        if self._active and self._start and self._current:
            _draw_arrow(painter, self._start, self._current,
                        self.color, self.stroke_width)


def render_arrow(painter: QPainter, ann: Annotation) -> None:
    _draw_arrow(painter, ann.start, ann.end, ann.color, ann.stroke_width)
