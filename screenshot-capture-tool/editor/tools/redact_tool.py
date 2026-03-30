"""
Redact / blur region tool.
Preview while dragging: semi-transparent gray rectangle.
Committed redact regions are blurred by the canvas/export pipeline.
"""
from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush

from editor.tools.base_tool import Annotation, BaseTool

_PREVIEW_COLOR = QColor(30, 30, 30, 170)
_OUTER_BORDER = QColor(20, 20, 20, 150)
_INNER_BORDER = QColor(255, 255, 255, 90)
_PREVIEW_FILL = QColor(20, 20, 20, 35)
_RADIUS = 6.0


def _draw_redact_frame(painter: QPainter, rect: QRectF, preview: bool = False) -> None:
    border_rect = rect.adjusted(0.5, 0.5, -0.5, -0.5)

    if preview:
        painter.setBrush(QBrush(_PREVIEW_FILL))
    else:
        painter.setBrush(Qt.BrushStyle.NoBrush)

    outer_pen = QPen(_OUTER_BORDER, 1)
    painter.setPen(outer_pen)
    painter.drawRoundedRect(border_rect, _RADIUS, _RADIUS)

    inner_pen = QPen(_INNER_BORDER, 1)
    painter.setPen(inner_pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(border_rect.adjusted(1.5, 1.5, -1.5, -1.5), _RADIUS - 1.5, _RADIUS - 1.5)


class RedactTool(BaseTool):
    def release(self, pos: QPointF) -> Annotation | None:
        self._active = False
        if self._start and (pos - self._start).manhattanLength() > 4:
            rect = QRectF(self._start, pos).normalized()
            box = (
                int(rect.left()), int(rect.top()),
                int(rect.right()), int(rect.bottom()),
            )
            return Annotation(
                kind="redact",
                start=self._start,
                end=pos,
                color=self.color,
                stroke_width=self.stroke_width,
                box=box,
            )
        return None

    def draw_preview(self, painter: QPainter) -> None:
        if self._active and self._start and self._current:
            rect = QRectF(self._start, self._current).normalized()
            painter.fillRect(rect, _PREVIEW_COLOR)
            _draw_redact_frame(painter, rect, preview=True)


def render_redact(painter: QPainter, ann: Annotation) -> None:
    """Committed redacts are painted from a blurred image layer in the canvas."""
    rect = QRectF(ann.start, ann.end).normalized()
    _draw_redact_frame(painter, rect)
