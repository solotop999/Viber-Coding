"""Numbered circle label tool (click to place)."""
from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QBrush, QFont, QFontMetricsF,
)

from editor.tools.base_tool import Annotation, BaseTool

_RADIUS = 14  # circle radius in pixels


class LabelTool(BaseTool):
    def __init__(self, color: QColor, stroke_width: int) -> None:
        super().__init__(color, stroke_width)
        self._counter = 1

    def release(self, pos: QPointF) -> Annotation | None:
        self._active = False
        self._current = None  # clear so preview doesn't overlap the placed label
        ann = Annotation(
            kind="label",
            start=pos,
            end=pos,
            number=self._counter,
            color=self.color,
            stroke_width=self.stroke_width,
        )
        self._counter += 1
        return ann

    def draw_preview(self, painter: QPainter) -> None:
        if self._current:
            _draw_label(painter, self._current, self._counter, self.color)

    def reset_counter(self) -> None:
        self._counter = 1


def _draw_label(painter: QPainter, center: QPointF, number: int,
                color: QColor) -> None:
    r = _RADIUS
    rect = QRectF(center.x() - r, center.y() - r, r * 2, r * 2)
    painter.setBrush(QBrush(color))
    painter.setPen(QPen(color.darker(130), 1))
    painter.drawEllipse(rect)

    painter.setPen(QPen(QColor("white")))
    font = QFont("Arial", 9, QFont.Weight.Bold)
    painter.setFont(font)
    painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(number))


def render_label(painter: QPainter, ann: Annotation) -> None:
    _draw_label(painter, ann.start, ann.number, ann.color)
