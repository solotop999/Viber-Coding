"""
Text annotation tool.
Places a floating, draggable, resizable QTextEdit over the canvas.
User can move it by dragging the top bar, and resize from any of the 8 handles.
On Enter (without Shift) or click-outside, the text is baked into an Annotation.
"""
from __future__ import annotations

from PyQt6.QtCore  import QPoint, QPointF, QRect, QRectF, Qt, QTimer
from PyQt6.QtGui   import QColor, QFont, QFontMetricsF, QPainter, QPainterPath, QPen, QTextOption
from PyQt6.QtWidgets import QApplication, QTextEdit, QWidget

from editor.tools.base_tool import Annotation, BaseTool

# ── geometry constants ──────────────────────────────────────────────────────
_HANDLE = 8     # thickness of resize-handle border (px)
_TITLE  = 18    # height of the drag bar at the top (px)
_MIN_W  = 120   # minimum inner width
_MIN_H  = 40    # minimum inner height
_TEXT_PAD_X = 12
_TEXT_PAD_Y = 10
_CARD_RADIUS = 12

# ── cursor mapping per handle name ──────────────────────────────────────────
_CURSORS: dict[str, Qt.CursorShape] = {
    "nw": Qt.CursorShape.SizeFDiagCursor,
    "n":  Qt.CursorShape.SizeVerCursor,
    "ne": Qt.CursorShape.SizeBDiagCursor,
    "w":  Qt.CursorShape.SizeHorCursor,
    "e":  Qt.CursorShape.SizeHorCursor,
    "sw": Qt.CursorShape.SizeBDiagCursor,
    "s":  Qt.CursorShape.SizeVerCursor,
    "se": Qt.CursorShape.SizeFDiagCursor,
}


# ── inner editor (captures focus-loss) ──────────────────────────────────────
class _InnerEditor(QTextEdit):
    def __init__(self, outer: "_ResizableTextWidget") -> None:
        super().__init__(outer)
        self._outer = outer

    def focusOutEvent(self, event) -> None:
        super().focusOutEvent(event)
        self._outer._on_te_focus_lost()

    def keyPressEvent(self, event) -> None:
        # Enter alone → commit; Shift+Enter → newline
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                self._outer._commit()
                return
        super().keyPressEvent(event)


# ── resizable/draggable container ───────────────────────────────────────────
class _ResizableTextWidget(QWidget):
    """Floating widget with drag bar and 8 resize handles."""

    def __init__(
        self,
        parent: QWidget,
        pos: QPointF,
        font: QFont,
        color: QColor,
        on_finish,          # callable(txt: str, start: QPointF, end: QPointF)
    ) -> None:
        super().__init__(parent)
        self._color     = color
        self._on_finish = on_finish
        self._committed = False

        # Inner text editor
        self._te = _InnerEditor(self)
        self._te.setFont(font)
        self._te.setAcceptRichText(False)
        self._te.setPlaceholderText("Type note...")
        self._te.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._te.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._te.document().setDocumentMargin(0)
        self._te.setStyleSheet(
            f"""
            QTextEdit {{
                background: transparent;
                border: none;
                color: {color.name()};
                padding: {_TEXT_PAD_Y}px {_TEXT_PAD_X}px;
                selection-background-color: rgba(45, 137, 239, 90);
            }}
            """
        )
        self._te.setFrameStyle(0)
        self._te.setWordWrapMode(QTextOption.WrapMode.WordWrap)

        # Interaction state
        self._mode: str | None = None          # None / 'move' / 'resize-<dir>'
        self._press_global: QPoint | None = None
        self._press_geom:   QRect  | None = None
        self._interacting  = False             # True while dragging/resizing

        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        pt      = font.pointSize()
        text_h  = max(_MIN_H, pt * 2 + 8)   # tall enough for 1 line + padding
        text_w  = max(_MIN_W, min(400, pt * 10))  # wider for big fonts, capped
        init_w  = text_w + 2 * _HANDLE
        init_h  = text_h + _TITLE + _HANDLE
        self.move(int(pos.x()), int(pos.y()))
        self.resize(init_w, init_h)
        self._layout_inner()
        self.show()
        self._te.setFocus()

    # ── layout ───────────────────────────────────────────────────────────────
    def _layout_inner(self) -> None:
        self._te.setGeometry(
            _HANDLE, _TITLE,
            self.width()  - 2 * _HANDLE,
            self.height() - _TITLE - _HANDLE,
        )

    def resizeEvent(self, _event) -> None:
        self._layout_inner()

    # ── handle geometry ───────────────────────────────────────────────────────
    def _handle_rects(self) -> dict[str, QRect]:
        w, h = self.width(), self.height()
        s    = _HANDLE
        cx   = (w - s) // 2
        cy   = (h - s) // 2
        return {
            "nw": QRect(0,     0,     s, s),
            "n":  QRect(cx,    0,     s, s),
            "ne": QRect(w - s, 0,     s, s),
            "w":  QRect(0,     cy,    s, s),
            "e":  QRect(w - s, cy,    s, s),
            "sw": QRect(0,     h - s, s, s),
            "s":  QRect(cx,    h - s, s, s),
            "se": QRect(w - s, h - s, s, s),
        }

    def _hit_handle(self, pos: QPoint) -> str | None:
        for name, r in self._handle_rects().items():
            if r.contains(pos):
                return name
        return None

    def _in_title(self, pos: QPoint) -> bool:
        return QRect(_HANDLE, 0, self.width() - 2 * _HANDLE, _TITLE).contains(pos)

    # ── paint ─────────────────────────────────────────────────────────────────
    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = self._color
        frame = QRectF(_HANDLE / 2, _HANDLE / 2, self.width() - _HANDLE, self.height() - _HANDLE)
        content = QRectF(frame.left(), frame.top() + _TITLE - 2, frame.width(), frame.height() - _TITLE + 2)

        surface, border, title_fill, handle_fill, label_fill, label_text = _note_palette(c)

        shadow_rect = QRectF(content.left(), content.top() + 3, content.width(), content.height())
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(8, 12, 20, 34))
        p.drawRoundedRect(shadow_rect, _CARD_RADIUS, _CARD_RADIUS)

        p.setBrush(surface)
        p.drawRoundedRect(content, _CARD_RADIUS, _CARD_RADIUS)

        title_rect = QRectF(frame.left(), frame.top(), frame.width(), _TITLE + 8)
        title_path = QPainterPath()
        title_path.addRoundedRect(title_rect, _CARD_RADIUS, _CARD_RADIUS)
        p.setBrush(title_fill)
        p.drawPath(title_path)

        p.setPen(QPen(border, 1.2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(content, _CARD_RADIUS, _CARD_RADIUS)

        drag_chip = QRectF(frame.left() + 8, frame.top() + 4, 46, 12)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(label_fill)
        p.drawRoundedRect(drag_chip, 6, 6)
        p.setPen(QPen(label_text))
        p.setFont(QFont("Arial", 7, QFont.Weight.DemiBold))
        p.drawText(drag_chip, Qt.AlignmentFlag.AlignCenter, "DRAG")

        p.setBrush(handle_fill)
        p.setPen(QPen(border, 1))
        for r in self._handle_rects().values():
            p.drawRoundedRect(QRectF(r), 2, 2)

    # ── mouse events ─────────────────────────────────────────────────────────
    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        local  = event.pos()
        handle = self._hit_handle(local)
        if handle:
            self._mode = f"resize-{handle}"
        elif self._in_title(local):
            self._mode = "move"
        else:
            event.ignore()
            return
        self._interacting  = True
        self._press_global = event.globalPosition().toPoint()
        self._press_geom   = self.geometry()
        event.accept()

    def mouseMoveEvent(self, event) -> None:
        local = event.pos()
        if self._mode is None:
            handle = self._hit_handle(local)
            if handle:
                self.setCursor(_CURSORS[handle])
            elif self._in_title(local):
                self.setCursor(Qt.CursorShape.SizeAllCursor)
            else:
                self.unsetCursor()
            return
        delta = event.globalPosition().toPoint() - self._press_global
        g     = self._press_geom
        if self._mode == "move":
            self.move(g.x() + delta.x(), g.y() + delta.y())
        else:
            self._apply_resize(delta, g)
        event.accept()

    def mouseReleaseEvent(self, event) -> None:
        if self._mode:
            self._mode        = None
            self._interacting = False
            self._te.setFocus()   # restore typing focus
        event.accept()

    # ── resize logic ──────────────────────────────────────────────────────────
    def _apply_resize(self, delta: QPoint, g: QRect) -> None:
        direction = self._mode[7:]           # strip "resize-"
        x, y, w, h = g.x(), g.y(), g.width(), g.height()
        dx, dy     = delta.x(), delta.y()
        min_w      = _MIN_W + 2 * _HANDLE
        min_h      = _MIN_H + _TITLE + _HANDLE

        # Horizontal
        if "w" in direction:
            new_w = max(min_w, w - dx)
            x     = x + w - new_w
            w     = new_w
        elif "e" in direction:
            w = max(min_w, w + dx)

        # Vertical
        if "n" in direction:
            new_h = max(min_h, h - dy)
            y     = y + h - new_h
            h     = new_h
        elif "s" in direction:
            h = max(min_h, h + dy)

        self.setGeometry(x, y, w, h)

    # ── commit / cancel ───────────────────────────────────────────────────────
    def _on_te_focus_lost(self) -> None:
        QTimer.singleShot(40, self._check_and_maybe_finish)

    def _check_and_maybe_finish(self) -> None:
        if self._committed or self._interacting:
            return
        focused = QApplication.focusWidget()
        if focused is None or (focused is not self._te and not self.isAncestorOf(focused)):
            self._commit()

    def _commit(self) -> None:
        if self._committed:
            return
        self._committed = True
        txt   = self._te.toPlainText().strip()
        pos   = self.pos()
        size  = self.size()
        self.hide()
        self.deleteLater()
        start = QPointF(pos)
        end   = QPointF(pos.x() + size.width(), pos.y() + size.height())
        self._on_finish(txt, start, end)

    def cancel(self) -> None:
        self._committed = True
        self.hide()
        self.deleteLater()


# ── tool ──────────────────────────────────────────────────────────────────────
class TextTool(BaseTool):
    def __init__(
        self,
        color: QColor,
        stroke_width: int,
        parent_widget,
        font_size: int = 14,
        font_bold: bool = False,
    ) -> None:
        super().__init__(color, stroke_width)
        self._parent     = parent_widget
        self._widget: _ResizableTextWidget | None = None
        self._font_size  = font_size
        self._font_bold  = font_bold

    def press(self, pos: QPointF) -> None:
        font = QFont("Arial", self._font_size)
        font.setBold(self._font_bold)
        self._widget = _ResizableTextWidget(
            self._parent, pos, font, self.color, self._on_finish
        )

    def move(self, pos: QPointF) -> None:
        pass

    def release(self, pos: QPointF) -> Annotation | None:
        return None

    def draw_preview(self, painter: QPainter) -> None:
        pass

    def _on_finish(self, txt: str, start: QPointF, end: QPointF) -> None:
        self._widget = None
        if txt:
            ann = Annotation(
                kind="text",
                start=start,
                end=end,
                text=txt,
                color=self.color,
                stroke_width=self.stroke_width,
                font_size=self._font_size,
                font_bold=self._font_bold,
            )
            self._parent.add_annotation(ann)

    def cancel(self) -> None:
        if self._widget:
            self._widget.cancel()
            self._widget = None

    def commit(self) -> None:
        if self._widget:
            self._widget._commit()
            self._widget = None


# ── renderer ──────────────────────────────────────────────────────────────────
def render_text(painter: QPainter, ann: Annotation) -> None:
    """Render a committed text annotation onto the canvas."""
    font = QFont("Arial", ann.font_size)
    font.setBold(ann.font_bold)
    painter.setFont(font)

    sx, sy = ann.start.x(), ann.start.y()
    ex, ey = ann.end.x(),   ann.end.y()
    box_w  = ex - sx
    box_h  = ey - sy

    if box_w > _HANDLE * 2 and box_h > _TITLE + _HANDLE:
        outer_rect = QRectF(
            sx + _HANDLE,
            sy + _TITLE,
            box_w - 2 * _HANDLE,
            box_h - _TITLE - _HANDLE,
        )
        _draw_note_card(painter, outer_rect, ann.text, ann.color, font)
    else:
        # Fallback for old single-point annotations
        fallback = QRectF(ann.start.x(), ann.start.y(), 220, ann.font_size * 2.4)
        _draw_note_card(painter, fallback, ann.text, ann.color, font)


def _note_palette(color: QColor) -> tuple[QColor, QColor, QColor, QColor, QColor, QColor]:
    light_text = color.lightness() > 165
    if light_text:
        surface = QColor(16, 20, 28, 228)
        border = QColor(255, 255, 255, 90)
        title_fill = QColor(255, 255, 255, 26)
        handle_fill = QColor(255, 255, 255, 205)
        label_fill = QColor(255, 255, 255, 220)
        label_text = QColor(18, 22, 30)
    else:
        surface = QColor(255, 255, 255, 232)
        border = QColor(color.red(), color.green(), color.blue(), 135)
        title_fill = QColor(color.red(), color.green(), color.blue(), 34)
        handle_fill = QColor(255, 255, 255, 220)
        label_fill = QColor(18, 22, 30, 208)
        label_text = QColor(255, 255, 255)
    return surface, border, title_fill, handle_fill, label_fill, label_text


def _draw_note_card(
    painter: QPainter,
    rect: QRectF,
    text: str,
    color: QColor,
    font: QFont,
) -> None:
    if not text.strip():
        return

    metrics = QFontMetricsF(font)
    available = rect.adjusted(_TEXT_PAD_X, _TEXT_PAD_Y, -_TEXT_PAD_X, -_TEXT_PAD_Y)
    text_flags = int(Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
    text_bounds = metrics.boundingRect(available, text_flags, text)

    card_width = max(84.0, min(rect.width(), text_bounds.width() + _TEXT_PAD_X * 2))
    card_height = max(metrics.height() + _TEXT_PAD_Y * 2, min(rect.height(), text_bounds.height() + _TEXT_PAD_Y * 2))
    card_rect = QRectF(rect.left(), rect.top(), card_width, card_height)
    text_rect = card_rect.adjusted(_TEXT_PAD_X, _TEXT_PAD_Y - 1, -_TEXT_PAD_X, -_TEXT_PAD_Y)

    surface, border, _title_fill, _handle_fill, _label_fill, _label_text = _note_palette(color)

    shadow_rect = QRectF(card_rect.left(), card_rect.top() + 3, card_rect.width(), card_rect.height())
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(8, 12, 20, 42))
    painter.drawRoundedRect(shadow_rect, _CARD_RADIUS, _CARD_RADIUS)

    painter.setBrush(surface)
    painter.drawRoundedRect(card_rect, _CARD_RADIUS, _CARD_RADIUS)
    painter.setPen(QPen(border, 1.15))
    painter.drawRoundedRect(card_rect, _CARD_RADIUS, _CARD_RADIUS)

    painter.setFont(font)
    painter.setPen(QPen(color))
    painter.drawText(text_rect, text_flags, text)
