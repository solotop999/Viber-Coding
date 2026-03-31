"""
Secure redact region tool.
Preview while dragging: dark rounded overlay.
Committed redact regions are rendered as solid black by the canvas/export pipeline.
"""
from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QBrush

from editor.tools.base_tool import Annotation, BaseTool

_PREVIEW_COLOR = QColor(4, 6, 10, 210)
_RADIUS = 6.0


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
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(_PREVIEW_COLOR))
            painter.drawRoundedRect(rect, _RADIUS, _RADIUS)


def render_redact(painter: QPainter, ann: Annotation) -> None:
    """Committed redacts are painted directly from the secure redacted image layer."""
