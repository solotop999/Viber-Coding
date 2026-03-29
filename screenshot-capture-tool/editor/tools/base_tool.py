"""Abstract base class for all annotation tools."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QColor, QPainter


@dataclass
class Annotation:
    """Data-only record for one annotation."""
    kind: str
    start: QPointF
    end: QPointF
    text: str = ""
    number: int = 0
    color: QColor = field(default_factory=lambda: QColor("#FF4444"))
    stroke_width: int = 3
    font_size: int = 14
    font_bold: bool = False
    # For redact: stores (left, top, right, bottom) in image pixels
    box: tuple[int, int, int, int] | None = None


class BaseTool:
    """
    All tools override press / move / release and draw_preview.
    The canvas calls these methods and manages the annotation list.
    """
    cursor_shape: ClassVar = None  # Override in subclasses if needed

    def __init__(self, color: QColor, stroke_width: int) -> None:
        self.color = color
        self.stroke_width = stroke_width
        self._start: QPointF | None = None
        self._current: QPointF | None = None
        self._active = False

    def press(self, pos: QPointF) -> None:
        self._start = pos
        self._current = pos
        self._active = True

    def move(self, pos: QPointF) -> None:
        self._current = pos

    def release(self, pos: QPointF) -> Annotation | None:
        """Return the completed Annotation or None if cancelled."""
        self._active = False
        return None

    def draw_preview(self, painter: QPainter) -> None:
        """Draw the in-progress annotation (called during mouseMoveEvent)."""

    def reset(self) -> None:
        self._start = None
        self._current = None
        self._active = False
