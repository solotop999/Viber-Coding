"""
QPainter-based annotation canvas.

Maintains a list of Annotation objects. Draws base image → committed
annotations → in-progress preview. All annotations are non-destructive
until flatten_to_pil() is called.
"""
from __future__ import annotations

import copy
import io
from typing import TYPE_CHECKING

from PyQt6.QtCore import QPointF, Qt, QRect
from PyQt6.QtGui import QColor, QPainter, QPixmap, QImage
from PyQt6.QtWidgets import QWidget, QGraphicsDropShadowEffect

from editor.tools.base_tool import Annotation, BaseTool
from editor.tools.arrow_tool  import ArrowTool,  render_arrow
from editor.tools.label_tool  import LabelTool,  render_label
from editor.tools.rect_tool   import RectTool,   render_rect
from editor.tools.text_tool   import TextTool,   render_text
from editor.tools.redact_tool import RedactTool, render_redact
from PIL import Image

_RENDER_MAP = {
    "arrow":  render_arrow,
    "label":  render_label,
    "rect":   render_rect,
    "text":   render_text,
    "redact": render_redact,
}

TOOL_ARROW  = "arrow"
TOOL_LABEL  = "label"
TOOL_RECT   = "rect"
TOOL_TEXT   = "text"
TOOL_REDACT = "redact"

_MAX_UNDO = 50


def _pil_to_qpixmap(img: Image.Image) -> QPixmap:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    px = QPixmap()
    px.loadFromData(buf.getvalue(), "PNG")
    return px


class AnnotationCanvas(QWidget):
    """Widget that displays the captured image and annotation tools."""

    def __init__(self, pil_image: Image.Image, parent=None) -> None:
        super().__init__(parent)
        self._original_pil = pil_image.copy()  # never modified — used by effects
        self._pil_image = pil_image
        self._pixmap = _pil_to_qpixmap(pil_image)
        self.setFixedSize(self._pixmap.size())

        self._annotations: list[Annotation] = []
        self._undo_stack: list[list[Annotation]] = []

        self._color = QColor("#FF4444")
        self._stroke_width = 3
        self._text_font_size = 14
        self._text_font_bold = False

        self._active_tool_name = TOOL_RECT
        self._tool: BaseTool = self._make_tool(TOOL_RECT)

        # Drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 3)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)

    # --------------------------------------------------------- public API
    def set_tool(self, name: str) -> None:
        if hasattr(self._tool, "cancel"):
            self._tool.cancel()  # type: ignore[attr-defined]
        self._active_tool_name = name
        self._tool = self._make_tool(name)
        self.update()

    def set_color(self, color: QColor) -> None:
        self._color = color
        self._tool = self._make_tool(self._active_tool_name)

    def set_stroke_width(self, w: int) -> None:
        self._stroke_width = w
        self._tool = self._make_tool(self._active_tool_name)

    def set_text_format(self, font_size: int, bold: bool) -> None:
        self._text_font_size = font_size
        self._text_font_bold = bold
        self._tool = self._make_tool(self._active_tool_name)

    def add_annotation(self, ann: Annotation) -> None:
        """Called by TextTool after user finishes typing."""
        self._push_undo()
        self._annotations.append(ann)
        self.update()

    def undo(self) -> None:
        if self._undo_stack:
            self._annotations = self._undo_stack.pop()
            # Reset label counter to match annotation count
            label_count = sum(1 for a in self._annotations if a.kind == "label")
            if isinstance(self._tool, LabelTool):
                self._tool._counter = label_count + 1
            self.update()

    def clear(self) -> None:
        self._push_undo()
        self._annotations.clear()
        if isinstance(self._tool, LabelTool):
            self._tool.reset_counter()
        self.update()

    def flatten_to_pil(self) -> Image.Image:
        """
        Bake all annotations onto a copy of the base PIL image.
        Redact annotations apply Gaussian blur to the image region.
        """
        from processing.blur import blur_region
        from processing.corners import apply_rounded_corners

        img = self._pil_image.copy().convert("RGBA")

        # Apply redacts with Pillow (actual blur)
        for ann in self._annotations:
            if ann.kind == "redact" and ann.box:
                # Clamp box to image bounds
                iw, ih = img.size
                l, t, r, b = ann.box
                l, t = max(0, l), max(0, t)
                r, b = min(iw, r), min(ih, b)
                if r > l and b > t:
                    img = img.convert("RGB")
                    from processing.blur import blur_region
                    img = blur_region(img, (l, t, r, b), radius=20)
                    img = img.convert("RGBA")

        # Render vector annotations via QPainter onto a QImage then paste
        if any(a.kind != "redact" for a in self._annotations):
            qimg = QImage(img.width, img.height, QImage.Format.Format_ARGB32)
            qimg.fill(Qt.GlobalColor.transparent)
            p = QPainter(qimg)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            for ann in self._annotations:
                if ann.kind == "redact":
                    continue
                renderer = _RENDER_MAP.get(ann.kind)
                if renderer:
                    renderer(p, ann)
            p.end()

            # Convert QImage to PIL and composite over img
            buf = io.BytesIO()
            buf.write(qimg.bits().asarray(qimg.sizeInBytes()))
            # Use QImage save to avoid raw bytes issues
            ba = bytearray()
            q_buf = io.BytesIO()
            qimg.save_to_file = None
            # simpler: save qimg to bytes via QBuffer
            from PyQt6.QtCore import QBuffer, QIODevice
            qbuf = QBuffer()
            qbuf.open(QIODevice.OpenModeFlag.WriteOnly)
            qimg.save(qbuf, "PNG")
            qbuf.close()
            overlay_pil = Image.open(io.BytesIO(bytes(qbuf.data()))).convert("RGBA")
            img = img.convert("RGBA")
            img.paste(overlay_pil, (0, 0), mask=overlay_pil.split()[3])

        return img

    # --------------------------------------------------------- events
    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._tool.press(QPointF(event.pos()))

    def mouseMoveEvent(self, event) -> None:
        self._tool.move(QPointF(event.pos()))
        self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            ann = self._tool.release(QPointF(event.pos()))
            if ann is not None:
                self._push_undo()
                self._annotations.append(ann)
                self.update()

    # --------------------------------------------------------- paint
    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Base image
        p.drawPixmap(0, 0, self._pixmap)
        # Committed annotations
        for ann in self._annotations:
            renderer = _RENDER_MAP.get(ann.kind)
            if renderer:
                renderer(p, ann)
        # In-progress preview
        self._tool.draw_preview(p)

    # --------------------------------------------------------- helpers
    def _make_tool(self, name: str) -> BaseTool:
        if name == TOOL_ARROW:
            return ArrowTool(self._color, self._stroke_width)
        if name == TOOL_LABEL:
            t = LabelTool(self._color, self._stroke_width)
            # Preserve counter across tool switches
            existing_count = sum(1 for a in self._annotations if a.kind == "label")
            t._counter = existing_count + 1
            return t
        if name == TOOL_RECT:
            return RectTool(self._color, self._stroke_width)
        if name == TOOL_TEXT:
            return TextTool(self._color, self._stroke_width, self,
                            self._text_font_size, self._text_font_bold)
        if name == TOOL_REDACT:
            return RedactTool(self._color, self._stroke_width)
        return RectTool(self._color, self._stroke_width)

    def _push_undo(self) -> None:
        self._undo_stack.append(copy.deepcopy(self._annotations))
        if len(self._undo_stack) > _MAX_UNDO:
            self._undo_stack.pop(0)
