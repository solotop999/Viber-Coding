"""
QPainter-based annotation canvas.

Maintains a list of Annotation objects. Draws base image, committed
annotations, and in-progress preview. All annotations are non-destructive
until flatten_to_pil() is called.
"""
from __future__ import annotations

import copy
import io

from PIL import Image
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QImage, QPainter, QPixmap
from PyQt6.QtWidgets import QGraphicsDropShadowEffect, QWidget

from editor.tools.arrow_tool import ArrowTool, render_arrow
from editor.tools.base_tool import Annotation, BaseTool
from editor.tools.label_tool import LabelTool, render_label
from editor.tools.rect_tool import RectTool, render_rect
from editor.tools.redact_tool import RedactTool, render_redact
from editor.tools.text_tool import TextTool, render_text
from processing.presentation import PresentationSettings, compose_presentation

_RENDER_MAP = {
    "arrow": render_arrow,
    "label": render_label,
    "rect": render_rect,
    "text": render_text,
    "redact": render_redact,
}

TOOL_ARROW = "arrow"
TOOL_LABEL = "label"
TOOL_RECT = "rect"
TOOL_TEXT = "text"
TOOL_REDACT = "redact"

_MAX_UNDO = 50
_SHAPE_STROKE_WIDTH = 4
_DEFAULT_COLOR = "#19C85B"


def _pil_to_qpixmap(img: Image.Image) -> QPixmap:
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    raw = img.tobytes("raw", "RGBA")
    qimg = QImage(raw, img.width, img.height, img.width * 4,
                  QImage.Format.Format_RGBA8888).copy()
    return QPixmap.fromImage(qimg)


class AnnotationCanvas(QWidget):
    """Widget that displays the captured image and annotation tools."""

    def __init__(self, pil_image: Image.Image, parent=None) -> None:
        super().__init__(parent)
        self._pil_image = pil_image
        self._pixmap = _pil_to_qpixmap(pil_image)
        self.setFixedSize(self._pixmap.size())

        self._annotations: list[Annotation] = []
        self._undo_stack: list[list[Annotation]] = []
        self._moving_rect_index: int | None = None
        self._move_start = QPointF()
        self._move_original_start = QPointF()
        self._move_original_end = QPointF()
        self._move_undo_pushed = False

        self._color = QColor(_DEFAULT_COLOR)
        self._stroke_width = 3
        self._text_font_size = 14
        self._text_font_bold = False

        self._active_tool_name = TOOL_RECT
        self._tool: BaseTool = self._make_tool(TOOL_RECT)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(6, 10, 18, 92))
        self._shadow = shadow
        self.setGraphicsEffect(self._shadow)
        self.set_shadow_enabled(True)

    def image_size(self) -> tuple[int, int]:
        return self._pil_image.size

    def base_image(self) -> Image.Image:
        return self._pil_image.copy()

    def set_image(self, pil_image: Image.Image) -> None:
        self._reset_rect_move()
        self._pil_image = pil_image
        self._annotations.clear()
        self._undo_stack.clear()
        self._pixmap = _pil_to_qpixmap(pil_image)
        self.setFixedSize(self._pixmap.size())
        if isinstance(self._tool, LabelTool):
            self._tool.reset_counter()
        self.update()

    def set_shadow_enabled(self, enabled: bool) -> None:
        if enabled:
            self._shadow.setBlurRadius(18)
            self._shadow.setOffset(0, 8)
            self._shadow.setColor(QColor(6, 10, 18, 76))
            return

        self._shadow.setBlurRadius(1)
        self._shadow.setOffset(0, 0)
        self._shadow.setColor(QColor(0, 0, 0, 0))

    def set_tool(self, name: str) -> None:
        self._reset_rect_move()
        self.cancel_active_tool()
        self._active_tool_name = name
        self._tool = self._make_tool(name)
        self.update()

    def set_color(self, color: QColor) -> None:
        self._color = color
        self._tool = self._make_tool(self._active_tool_name)

    def set_text_format(self, font_size: int, bold: bool) -> None:
        self._text_font_size = font_size
        self._text_font_bold = bold
        self._tool = self._make_tool(self._active_tool_name)

    def add_annotation(self, ann: Annotation) -> None:
        self._push_undo()
        self._annotations.append(ann)
        self.update()

    def commit_active_tool(self) -> None:
        if hasattr(self._tool, "commit"):
            self._tool.commit()  # type: ignore[attr-defined]

    def cancel_active_tool(self) -> None:
        if hasattr(self._tool, "cancel"):
            self._tool.cancel()  # type: ignore[attr-defined]

    def undo(self) -> None:
        if not self._undo_stack:
            return

        self._annotations = self._undo_stack.pop()
        label_count = sum(1 for ann in self._annotations if ann.kind == "label")
        if isinstance(self._tool, LabelTool):
            self._tool._counter = label_count + 1
        self.update()

    def clear(self) -> None:
        self._push_undo()
        self._annotations.clear()
        if isinstance(self._tool, LabelTool):
            self._tool.reset_counter()
        self.update()

    def flatten_subject_to_pil(self) -> Image.Image:
        from PyQt6.QtCore import QBuffer, QIODevice

        image = self._render_redacted_image().convert("RGBA")

        if any(ann.kind != "redact" for ann in self._annotations):
            qimg = QImage(image.width, image.height, QImage.Format.Format_ARGB32)
            qimg.fill(Qt.GlobalColor.transparent)

            painter = QPainter(qimg)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            for ann in self._annotations:
                if ann.kind == "redact":
                    continue
                renderer = _RENDER_MAP.get(ann.kind)
                if renderer:
                    renderer(painter, ann)
            painter.end()

            buffer = QBuffer()
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            qimg.save(buffer, "PNG")
            buffer.close()

            overlay = Image.open(io.BytesIO(bytes(buffer.data()))).convert("RGBA")
            image.paste(overlay, (0, 0), mask=overlay.getchannel("A"))

        return image

    def flatten_to_pil(self, settings: PresentationSettings | None = None) -> Image.Image:
        image = self.flatten_subject_to_pil()
        if settings and settings.enabled:
            return compose_presentation(image, self._pil_image, settings)
        return image

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            pos = QPointF(event.pos())
            if self._active_tool_name == TOOL_RECT:
                index = self._rect_border_at(pos)
                if index is not None:
                    ann = self._annotations[index]
                    self._moving_rect_index = index
                    self._move_start = pos
                    self._move_original_start = QPointF(ann.start)
                    self._move_original_end = QPointF(ann.end)
                    self._move_undo_pushed = False
                    self.setCursor(Qt.CursorShape.SizeAllCursor)
                    return
            self._reset_rect_move()
            self._tool.press(pos)

    def mouseMoveEvent(self, event) -> None:
        pos = QPointF(event.pos())
        if self._moving_rect_index is not None:
            delta = pos - self._move_start
            if not self._move_undo_pushed and delta.manhattanLength() > 2:
                self._push_undo()
                self._move_undo_pushed = True
            if self._move_undo_pushed:
                delta = self._constrained_rect_delta(delta)
                ann = self._annotations[self._moving_rect_index]
                ann.start = self._move_original_start + delta
                ann.end = self._move_original_end + delta
            self.update()
            return

        self._tool.move(pos)
        self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return

        if self._moving_rect_index is not None:
            self._reset_rect_move()
            self.update()
            return

        ann = self._tool.release(QPointF(event.pos()))
        if ann is not None:
            self._push_undo()
            self._annotations.append(ann)
            self.update()

    def _rect_border_at(self, pos: QPointF) -> int | None:
        for index in range(len(self._annotations) - 1, -1, -1):
            ann = self._annotations[index]
            if ann.kind != "rect":
                continue
            rect = QRectF(ann.start, ann.end).normalized()
            tolerance = max(7.0, float(ann.stroke_width) + 4.0)
            outer = rect.adjusted(-tolerance, -tolerance, tolerance, tolerance)
            inner = rect.adjusted(tolerance, tolerance, -tolerance, -tolerance)
            if outer.contains(pos) and (not inner.isValid() or not inner.contains(pos)):
                return index
        return None

    def _constrained_rect_delta(self, delta: QPointF) -> QPointF:
        rect = QRectF(self._move_original_start, self._move_original_end).normalized()
        dx = max(-rect.left(), min(delta.x(), self.width() - rect.right()))
        dy = max(-rect.top(), min(delta.y(), self.height() - rect.bottom()))
        return QPointF(dx, dy)

    def _reset_rect_move(self) -> None:
        self._moving_rect_index = None
        self._move_undo_pushed = False
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.drawPixmap(0, 0, self._redacted_base_pixmap())

        for ann in self._annotations:
            renderer = _RENDER_MAP.get(ann.kind)
            if renderer:
                renderer(painter, ann)

        self._tool.draw_preview(painter)

    def _make_tool(self, name: str) -> BaseTool:
        if name == TOOL_ARROW:
            return ArrowTool(self._color, max(self._stroke_width, _SHAPE_STROKE_WIDTH))
        if name == TOOL_LABEL:
            tool = LabelTool(self._color, self._stroke_width)
            tool._counter = sum(1 for ann in self._annotations if ann.kind == "label") + 1
            return tool
        if name == TOOL_TEXT:
            return TextTool(
                self._color,
                self._stroke_width,
                self,
                self._text_font_size,
                self._text_font_bold,
            )
        if name == TOOL_REDACT:
            return RedactTool(self._color, self._stroke_width)
        return RectTool(self._color, max(self._stroke_width, _SHAPE_STROKE_WIDTH))

    def _push_undo(self) -> None:
        self._undo_stack.append(copy.deepcopy(self._annotations))
        if len(self._undo_stack) > _MAX_UNDO:
            self._undo_stack.pop(0)

    def _render_redacted_image(self) -> Image.Image:
        from processing.blur import redact_region

        image = self._pil_image.copy().convert("RGBA")
        for ann in self._annotations:
            if ann.kind != "redact" or not ann.box:
                continue

            width, height = image.size
            left, top, right, bottom = ann.box
            left, top = max(0, left), max(0, top)
            right, bottom = min(width, right), min(height, bottom)
            if right <= left or bottom <= top:
                continue

            image = redact_region(image, (left, top, right, bottom))
        return image

    def _redacted_base_pixmap(self) -> QPixmap:
        if any(ann.kind == "redact" for ann in self._annotations):
            return _pil_to_qpixmap(self._render_redacted_image())
        return self._pixmap
