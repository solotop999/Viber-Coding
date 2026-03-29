"""
Redact / blur region tool.
Preview: semi-transparent gray rectangle.
On export: the region is blurred with Pillow (non-destructive until flatten).
"""
from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush

from editor.tools.base_tool import Annotation, BaseTool

_PREVIEW_COLOR = QColor(30, 30, 30, 170)


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
            painter.setBrush(QBrush(_PREVIEW_COLOR))
            painter.setPen(QPen(QColor(80, 80, 80), 1))
            painter.drawRect(rect)


def render_redact(painter: QPainter, ann: Annotation) -> None:
    """Draw the redact placeholder in the editor (actual blur applied at export)."""
    rect = QRectF(ann.start, ann.end).normalized()
    painter.setBrush(QBrush(_PREVIEW_COLOR))
    painter.setPen(QPen(QColor(80, 80, 80), 1))
    painter.drawRect(rect)
