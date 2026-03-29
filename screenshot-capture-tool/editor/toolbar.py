"""
Ribbon toolbar — horizontal strip at the top, giống Paint.
Groups: Tools | Stroke | Colors | Effects | Actions
"""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, QSize, QEvent, QPoint, QRect
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap, QFont, QBrush, QPen
from PyQt6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QToolButton, QButtonGroup,
    QColorDialog, QComboBox, QLabel, QFrame, QFileDialog, QMessageBox,
)

from editor.canvas import (
    AnnotationCanvas,
    TOOL_ARROW, TOOL_LABEL,
    TOOL_RECT, TOOL_REDACT, TOOL_TEXT,
)
from core.clipboard import copy_to_clipboard

# Màu sắc nhanh hiển thị trong ribbon (giống Paint)
_QUICK_COLORS = [
    "#000000", "#FFFFFF", "#7F7F7F", "#C3C3C3",
    "#FF0000", "#FF6600", "#FFFF00", "#00FF00",
    "#00FFFF", "#0000FF", "#FF00FF", "#FF80C0",
    "#FF4444", "#804000", "#008000", "#004080",
]

_RIBBON_H   = 72   # chiều cao ribbon
_BTN_W      = 52   # tool button width
_BTN_H      = 56   # tool button height (icon + label)
_COLOR_SZ   = 18   # color swatch size


def _color_swatch(color: QColor, size: int = _COLOR_SZ, selected: bool = False) -> QPixmap:
    px = QPixmap(size, size)
    px.fill(color)
    p = QPainter(px)
    border = QColor("#0078D4") if selected else QColor(0, 0, 0, 60)
    p.setPen(QPen(border, 2 if selected else 1))
    p.drawRect(0, 0, size - 1, size - 1)
    p.end()
    return px


def _make_tool_icon(symbol: str, size: int = 28) -> QIcon:
    """Draw proper tool icons using QPainter instead of unicode."""
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    c = QColor("#222222")
    pen = QPen(c, 2)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    p.setBrush(QBrush(Qt.BrushStyle.NoBrush))
    m = 4  # margin

    if symbol == "rect":
        p.drawRoundedRect(m, m + 2, size - m*2, size - m*2 - 4, 2, 2)

    elif symbol == "circle":
        p.drawEllipse(m, m + 2, size - m*2, size - m*2 - 4)

    elif symbol == "arrow":
        import math
        x1, y1 = m + 2, size - m - 2
        x2, y2 = size - m - 2, m + 2
        p.drawLine(x1, y1, x2, y2)
        angle = math.atan2(y1 - y2, x1 - x2)
        hl = 8
        ha = math.radians(25)
        p.setBrush(QBrush(c))
        from PyQt6.QtGui import QPolygonF
        from PyQt6.QtCore import QPointF
        poly = QPolygonF([
            QPointF(x2, y2),
            QPointF(x2 + hl * math.cos(angle - ha), y2 + hl * math.sin(angle - ha)),
            QPointF(x2 + hl * math.cos(angle + ha), y2 + hl * math.sin(angle + ha)),
        ])
        p.drawPolygon(poly)

    elif symbol == "label":
        p.setBrush(QBrush(c))
        cx, cy, r = size // 2, size // 2, size // 2 - m
        p.drawEllipse(cx - r, cy - r, r * 2, r * 2)
        p.setPen(QPen(QColor("white"), 1))
        p.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        p.drawText(px.rect(), Qt.AlignmentFlag.AlignCenter, "1")

    elif symbol == "text":
        p.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        p.setPen(QPen(c))
        p.drawText(px.rect(), Qt.AlignmentFlag.AlignCenter, "A")

    elif symbol == "redact":
        # Mosaic / blur icon
        sq = (size - m * 2) // 3
        for row in range(3):
            for col in range(3):
                shade = 80 + (row * 3 + col) * 18
                p.setBrush(QBrush(QColor(shade, shade, shade)))
                p.setPen(QPen(QColor("white"), 1))
                p.drawRect(m + col * sq, m + row * sq, sq - 1, sq - 1)

    elif symbol == "new":
        pen2 = QPen(c, 2.5)
        pen2.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen2)
        cx, cy = size // 2, size // 2
        hl = size // 2 - m
        p.drawLine(cx, cy - hl, cx, cy + hl)
        p.drawLine(cx - hl, cy, cx + hl, cy)

    elif symbol == "undo":
        from PyQt6.QtCore import QRectF
        import math
        # Arc arrow
        pen2 = QPen(c, 2)
        pen2.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen2)
        r = size // 2 - m - 1
        cx, cy = size // 2, size // 2 + 2
        p.drawArc(int(cx - r), int(cy - r), r * 2, r * 2, 30 * 16, 240 * 16)
        # Arrowhead tip
        ax = int(cx - r * math.cos(math.radians(30)))
        ay = int(cy - r * math.sin(math.radians(30)))
        p.setBrush(QBrush(c))
        from PyQt6.QtGui import QPolygonF
        from PyQt6.QtCore import QPointF
        p.drawPolygon(QPolygonF([
            QPointF(ax, ay),
            QPointF(ax - 6, ay - 2),
            QPointF(ax - 2, ay + 5),
        ]))

    elif symbol == "clear":
        # Trash bin
        bx, by, bw, bh = m + 4, m + 5, size - (m+4)*2, size - m*2 - 6
        p.drawRect(bx, by, bw, bh)
        p.drawLine(m + 2, by, size - m - 2, by)
        p.drawLine(size//2, m + 1, size//2, by)
        for i in range(1, 3):
            x = bx + (bw * i) // 3
            p.drawLine(x, by + 3, x, by + bh - 3)

    elif symbol == "copy":
        # Two overlapping squares
        p.drawRect(m + 4, m, size - m*2 - 4, size - m*2 - 4)
        p.setBrush(QBrush(QColor("#F3F3F3")))
        p.drawRect(m, m + 4, size - m*2 - 4, size - m*2 - 4)

    elif symbol == "save":
        # Floppy disk
        p.setBrush(QBrush(QColor("#D0D8F0")))
        p.drawRect(m, m, size - m*2, size - m*2)
        p.setBrush(QBrush(QColor("#8090C0")))
        p.drawRect(m + 3, m, size - m*2 - 6, 8)
        p.setBrush(QBrush(QColor("white")))
        p.drawRect(m + 3, m + 14, size - m*2 - 6, size - m*2 - 14)

    else:
        # Fallback text
        p.setFont(QFont("Segoe UI", 11))
        p.setPen(QPen(c))
        p.drawText(px.rect(), Qt.AlignmentFlag.AlignCenter, symbol)

    p.end()
    return QIcon(px)


def _vsep() -> QFrame:
    sep = QFrame()
    sep.setFrameShape(QFrame.Shape.VLine)
    sep.setStyleSheet("color: #CCCCCC;")
    sep.setFixedWidth(1)
    return sep


def _group_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setStyleSheet("color: #555555; font-size: 9px; font-family: Segoe UI;")
    lbl.setFixedHeight(13)
    return lbl


class _ToolBtn(QToolButton):
    """Tool button: icon on top, label below — kiểu Paint."""
    def __init__(self, symbol: str, label: str, tooltip: str) -> None:
        super().__init__()
        self.setCheckable(True)
        self.setFixedSize(_BTN_W, _BTN_H)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.setIcon(_make_tool_icon(symbol))
        self.setIconSize(QSize(28, 28))
        self.setText(label)
        self.setToolTip(tooltip)
        self.setFont(QFont("Segoe UI", 8))
        self.setStyleSheet("""
            QToolButton {
                border: 1px solid transparent;
                border-radius: 3px;
                background: transparent;
                color: #1A1A1A;
                padding: 2px 0px 2px 0px;
            }
            QToolButton:hover {
                background: #E5F3FF;
                border-color: #99CCFF;
            }
            QToolButton:checked {
                background: #CCE8FF;
                border-color: #0078D4;
            }
            QToolButton:pressed {
                background: #B3D9FF;
            }
        """)


class _ActionBtn(QToolButton):
    """Action button (no checkable): icon + label."""
    def __init__(self, symbol: str, label: str, tooltip: str) -> None:
        super().__init__()
        self.setFixedSize(_BTN_W, _BTN_H)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.setIcon(_make_tool_icon(symbol))
        self.setIconSize(QSize(28, 28))
        self.setText(label)
        self.setToolTip(tooltip)
        self.setFont(QFont("Segoe UI", 8))
        self.setStyleSheet("""
            QToolButton {
                border: 1px solid transparent;
                border-radius: 3px;
                background: transparent;
                color: #1A1A1A;
                padding: 2px 0px 2px 0px;
            }
            QToolButton:hover {
                background: #E5F3FF;
                border-color: #99CCFF;
            }
            QToolButton:pressed {
                background: #B3D9FF;
            }
        """)


class _TextFormatPopup(QWidget):
    """Floating popup with font size + bold toggle, shown below the Text button."""
    def __init__(self, canvas: AnnotationCanvas, parent: QWidget) -> None:
        super().__init__(parent,
                         Qt.WindowType.Tool
                         | Qt.WindowType.FramelessWindowHint
                         | Qt.WindowType.WindowStaysOnTopHint)
        self._canvas = canvas
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedSize(168, 58)

        outer = QFrame(self)
        outer.setGeometry(0, 0, 168, 58)
        outer.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border: 1px solid #BBBBBB;
                border-radius: 6px;
            }
        """)

        layout = QHBoxLayout(outer)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        # Font size dropdown
        self._size_combo = QComboBox()
        for s in [8, 10, 12, 14, 16, 18, 20, 24, 28, 32, 36, 48, 64, 72]:
            self._size_combo.addItem(str(s), s)
        self._size_combo.setCurrentIndex(3)  # 14
        self._size_combo.setFixedHeight(38)
        self._size_combo.setFont(QFont("Segoe UI", 13))
        self._size_combo.activated.connect(self._update)

        _btn_style = """
            QToolButton {
                border: 1px solid #AAAAAA;
                border-radius: 4px;
                background: white;
                color: #1A1A1A;
            }
            QToolButton:checked {
                background: #CCE8FF;
                border-color: #0078D4;
            }
            QToolButton:hover { background: #E5F3FF; }
        """

        # Bold button
        self._bold_btn = QToolButton()
        self._bold_btn.setText("B")
        self._bold_btn.setCheckable(True)
        self._bold_btn.setFixedSize(38, 38)
        bf = QFont("Segoe UI", 13)
        bf.setBold(True)
        self._bold_btn.setFont(bf)
        self._bold_btn.setStyleSheet(_btn_style)
        self._bold_btn.clicked.connect(self._update)

        layout.addWidget(self._size_combo)
        layout.addWidget(self._bold_btn)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        QApplication.instance().installEventFilter(self)

    def hideEvent(self, event) -> None:
        super().hideEvent(event)
        QApplication.instance().removeEventFilter(self)

    def eventFilter(self, obj, event) -> bool:
        t = event.type()
        if t == QEvent.Type.MouseButtonPress:
            # If the combo's dropdown list is open, let the combo handle the
            # click so it can confirm the selection and emit activated().
            if self._size_combo.view().isVisible():
                return False
            global_pos = event.globalPosition().toPoint()
            popup_rect = QRect(self.mapToGlobal(QPoint(0, 0)), self.size())
            if not popup_rect.contains(global_pos):
                self.hide()
        elif t == QEvent.Type.ApplicationDeactivated:
            self.hide()
        return False

    def _update(self) -> None:
        size = int(self._size_combo.currentData() or 14)
        bold = self._bold_btn.isChecked()
        self._size_combo.blockSignals(True)
        self._bold_btn.blockSignals(True)
        self._canvas.set_text_format(size, bold)
        self.hide()
        self._size_combo.blockSignals(False)
        self._bold_btn.blockSignals(False)


class Toolbar(QWidget):
    def __init__(self, canvas: AnnotationCanvas, editor) -> None:
        super().__init__()
        self._canvas = canvas
        self._editor = editor
        self._color = QColor("#FF4444")

        self.setFixedHeight(_RIBBON_H)
        self.setStyleSheet("QWidget { background: #F3F3F3; }")

        main = QHBoxLayout(self)
        main.setContentsMargins(8, 4, 8, 0)
        main.setSpacing(0)

        # ── GROUP: Recapture ──────────────────────────────────────────
        main.addLayout(self._recapture_group())
        main.addWidget(_vsep())
        main.addSpacing(4)

        # ── GROUP: Tools ──────────────────────────────────────────────
        main.addLayout(self._tools_group())
        main.addWidget(_vsep())
        main.addSpacing(4)

        # ── GROUP: Colors ─────────────────────────────────────────────
        main.addLayout(self._colors_group())
        main.addWidget(_vsep())
        main.addSpacing(4)

        # ── GROUP: Actions ────────────────────────────────────────────
        main.addLayout(self._actions_group())

        main.addStretch()

    # ──────────────────────────────────────── group builders

    def _recapture_group(self) -> QVBoxLayout:
        vbox = QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)
        row = QHBoxLayout()
        row.setSpacing(1)
        row.setContentsMargins(0, 0, 0, 0)
        btn = _ActionBtn("new", "New", "New screenshot  Ctrl+N")
        btn.clicked.connect(self._editor.recapture_requested.emit)
        row.addWidget(btn)
        vbox.addLayout(row)
        return vbox

    def _tools_group(self) -> QVBoxLayout:
        vbox = QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        row = QHBoxLayout()
        row.setSpacing(1)
        row.setContentsMargins(0, 0, 0, 0)

        self._btn_group = QButtonGroup(self)
        self._btn_group.setExclusive(True)
        self._tool_btns: dict[str, _ToolBtn] = {}

        tools = [
            (TOOL_RECT,   "rect",   "Rect",   "Rectangle"),
            (TOOL_ARROW,  "arrow",  "Arrow",  "Arrow"),
            (TOOL_LABEL,  "label",  "Label",  "Numbered Label"),
            (TOOL_TEXT,   "text",   "Text",   "Add Text"),
            (TOOL_REDACT, "redact", "Redact", "Blur / Redact"),
        ]
        for tool_name, sym, lbl, tip in tools:
            btn = _ToolBtn(sym, lbl, tip)
            if tool_name == TOOL_TEXT:
                btn.clicked.connect(self._on_text_btn_clicked)
            else:
                btn.clicked.connect(lambda _, n=tool_name: self._on_tool_clicked(n))
            self._btn_group.addButton(btn)
            self._tool_btns[tool_name] = btn
            row.addWidget(btn)

        self._tool_btns[TOOL_RECT].setChecked(True)

        # Text format popup (hidden by default)
        self._text_popup = _TextFormatPopup(self._canvas, self.window())

        vbox.addLayout(row)
        return vbox

    def _on_tool_clicked(self, name: str) -> None:
        self._text_popup.hide()
        self._canvas.set_tool(name)

    def _on_text_btn_clicked(self) -> None:
        self._canvas.set_tool(TOOL_TEXT)
        btn = self._tool_btns[TOOL_TEXT]
        pos = btn.mapToGlobal(btn.rect().bottomLeft())
        self._text_popup.move(pos)
        self._text_popup.show()
        self._text_popup.raise_()

    def _colors_group(self) -> QVBoxLayout:
        vbox = QVBoxLayout()
        vbox.setContentsMargins(6, 0, 6, 0)
        vbox.setSpacing(2)

        # Current color swatch (big) + "More colors" button
        top_row = QHBoxLayout()
        top_row.setSpacing(4)

        # Big active color swatch
        self._active_swatch = QLabel()
        self._active_swatch.setFixedSize(32, 32)
        self._active_swatch.setPixmap(_color_swatch(self._color, 32, True))
        self._active_swatch.setToolTip("Current color — click to change")
        self._active_swatch.mousePressEvent = lambda _: self._pick_color()
        self._active_swatch.setCursor(Qt.CursorShape.PointingHandCursor)
        top_row.addWidget(self._active_swatch)

        # Quick color grid (2 rows × 8 cols)
        grid_widget = QWidget()
        grid_widget.setStyleSheet("background: transparent; border: none;")
        grid_layout = QVBoxLayout(grid_widget)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(2)

        colors = _QUICK_COLORS
        for row_idx in range(2):
            row = QHBoxLayout()
            row.setSpacing(2)
            for col_idx in range(8):
                i = row_idx * 8 + col_idx
                if i >= len(colors):
                    break
                c = QColor(colors[i])
                swatch = QLabel()
                swatch.setFixedSize(_COLOR_SZ, _COLOR_SZ)
                swatch.setPixmap(_color_swatch(c, _COLOR_SZ))
                swatch.setToolTip(colors[i])
                swatch.setCursor(Qt.CursorShape.PointingHandCursor)
                swatch.mousePressEvent = (
                    lambda _, color=c: self._set_color(color)
                )
                row.addWidget(swatch)
            grid_layout.addLayout(row)

        top_row.addWidget(grid_widget)
        vbox.addSpacing(4)
        vbox.addLayout(top_row)
        return vbox

    def _actions_group(self) -> QVBoxLayout:
        vbox = QVBoxLayout()
        vbox.setContentsMargins(4, 0, 4, 0)
        vbox.setSpacing(0)

        row = QHBoxLayout()
        row.setSpacing(1)
        row.setContentsMargins(0, 0, 0, 0)

        undo_btn = _ActionBtn("undo",  "Undo",  "Undo  Ctrl+Z")
        undo_btn.clicked.connect(self._canvas.undo)

        clear_btn = _ActionBtn("clear", "Clear", "Clear all annotations")
        clear_btn.clicked.connect(self._canvas.clear)

        copy_btn = _ActionBtn("copy",  "Copy",  "Copy to clipboard  Ctrl+C")
        copy_btn.clicked.connect(self._copy)

        save_btn = _ActionBtn("save",  "Save",  "Save to file  Ctrl+S")
        save_btn.clicked.connect(self._save)

        for btn in (undo_btn, clear_btn, copy_btn, save_btn):
            row.addWidget(btn)

        vbox.addLayout(row)
        return vbox

    # ──────────────────────────────────────── color helpers

    def _pick_color(self) -> None:
        color = QColorDialog.getColor(self._color, self, "Choose color")
        if color.isValid():
            self._set_color(color)

    def _set_color(self, color: QColor) -> None:
        self._color = color
        self._active_swatch.setPixmap(_color_swatch(color, 32, True))
        self._canvas.set_color(color)

    # ──────────────────────────────────────── file actions

    def _copy(self) -> None:
        try:
            copy_to_clipboard(self._canvas.flatten_to_pil())
        except Exception as e:
            QMessageBox.warning(self, "Copy failed", str(e))

    def _save(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Screenshot",
            str(Path.home() / "Pictures"),
            "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg)",
        )
        if path:
            try:
                self._canvas.flatten_to_pil().save(path)
            except Exception as e:
                QMessageBox.warning(self, "Save failed", str(e))
