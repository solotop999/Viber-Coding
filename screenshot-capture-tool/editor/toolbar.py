"""Ribbon toolbar for capture actions and annotation tools."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PyQt6.QtCore import QEvent, QPoint, QRect, QSize, Qt, QUrl
from PyQt6.QtGui import QBrush, QColor, QDesktopServices, QFont, QIcon, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QComboBox,
    QColorDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QMenu,
    QMessageBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from core.paths import asset_path
from core.settings import (
    is_local_background_image_path,
    save_presentation_background_color,
    save_presentation_background_color_mode,
    save_presentation_background_gradient_preset,
    save_presentation_background_image,
    save_presentation_background_style,
)
from editor.canvas import (
    AnnotationCanvas,
    TOOL_ARROW,
    TOOL_LABEL,
    TOOL_RECT,
    TOOL_REDACT,
    TOOL_TEXT,
)

_PALETTE_COLORS = [
    "#19C85B",
    "#FF3B30",
    "#000000",
    "#FFFFFF",
]

_RIBBON_H = 72
_BTN_W = 52
_BTN_H = 56
_CHIP_SZ = 16
_CHIP_ICON_SZ = 20
_X_PROFILE_URL = "https://x.com/solotop999"
_GRADIENT_PRESET_ITEMS = [
    ("apple_pink", "Apple Pink"),
    ("apple_peach", "Apple Peach"),
    ("apple_sky", "Apple Sky"),
    ("apple_mint", "Apple Mint"),
    ("apple_lilac", "Apple Lilac"),
    ("apple_blue", "Apple Blue"),
    ("rose", "Rose"),
    ("lemon", "Lemon"),
    ("sunset", "Sunset"),
    ("berry", "Berry"),
    ("royal", "Royal"),
    ("peach", "Peach"),
    ("mint", "Mint"),
    ("dusk", "Dusk"),
    ("ocean", "Ocean"),
]
_GRADIENT_PRESET_STYLES = {
    "apple_pink": ("Apple Pink", "#FFFFFF", "#F5D3E1", "#5F4661"),
    "apple_peach": ("Apple Peach", "#FFFFFF", "#F9D7BB", "#6C523B"),
    "apple_sky": ("Apple Sky", "#FFFFFF", "#C7DDF8", "#425A79"),
    "apple_mint": ("Apple Mint", "#FFFFFF", "#C6EADD", "#355A52"),
    "apple_lilac": ("Apple Lilac", "#FFFFFF", "#DAD1F2", "#554B74"),
    "apple_blue": ("Apple Blue", "#FCFDFF", "#ABC4E8", "#3E5472"),
    "rose": ("Rose", "#FFFAFC", "#ECA6C4", "#6A3750"),
    "lemon": ("Lemon", "#FFFFFF", "#F7DD7D", "#6A560C"),
    "sunset": ("Sunset", "#FFF2E8", "#EE603F", "#FFFFFF"),
    "berry": ("Berry", "#FFF3F8", "#BF427E", "#FFFFFF"),
    "royal": ("Royal", "#F1ECFF", "#5F47C4", "#FFFFFF"),
    "peach": ("Peach", "#FFF5E8", "#F8BE9B", "#7C4A31"),
    "mint": ("Mint", "#ECFFF7", "#76D5B9", "#21594B"),
    "dusk": ("Dusk", "#F0E8FF", "#958AE1", "#433B73"),
    "ocean": ("Ocean", "#E8F5FF", "#4D8EDB", "#FFFFFF"),
}


@lru_cache(maxsize=None)
def _make_tool_icon(symbol: str, size: int = 28) -> QIcon:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    color = QColor("#222222")
    pen = QPen(color, 2)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
    margin = 4

    if symbol == "rect":
        painter.drawRoundedRect(margin, margin + 2, size - margin * 2, size - margin * 2 - 4, 2, 2)
    elif symbol == "arrow":
        import math
        from PyQt6.QtCore import QPointF
        from PyQt6.QtGui import QPolygonF

        x1, y1 = margin + 2, size - margin - 2
        x2, y2 = size - margin - 2, margin + 2
        painter.drawLine(x1, y1, x2, y2)
        angle = math.atan2(y1 - y2, x1 - x2)
        head_len = 8
        head_angle = math.radians(25)
        painter.setBrush(QBrush(color))
        painter.drawPolygon(QPolygonF([
            QPointF(x2, y2),
            QPointF(x2 + head_len * math.cos(angle - head_angle), y2 + head_len * math.sin(angle - head_angle)),
            QPointF(x2 + head_len * math.cos(angle + head_angle), y2 + head_len * math.sin(angle + head_angle)),
        ]))
    elif symbol == "label":
        painter.setBrush(QBrush(color))
        cx, cy, radius = size // 2, size // 2, size // 2 - margin
        painter.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)
        painter.setPen(QPen(QColor("white"), 1))
        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "1")
    elif symbol == "text":
        painter.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        painter.setPen(QPen(color))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "A")
    elif symbol == "redact":
        square = (size - margin * 2) // 3
        for row in range(3):
            for col in range(3):
                shade = 80 + (row * 3 + col) * 18
                painter.setBrush(QBrush(QColor(shade, shade, shade)))
                painter.setPen(QPen(QColor("white"), 1))
                painter.drawRect(margin + col * square, margin + row * square, square - 1, square - 1)
    elif symbol == "new":
        pen2 = QPen(color, 2.5)
        pen2.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen2)
        cx, cy = size // 2, size // 2
        half_len = size // 2 - margin
        painter.drawLine(cx, cy - half_len, cx, cy + half_len)
        painter.drawLine(cx - half_len, cy, cx + half_len, cy)
    elif symbol == "undo":
        font = QFont("Segoe UI Symbol", 19)
        painter.setFont(font)
        painter.setPen(QPen(color))
        painter.drawText(pixmap.rect().adjusted(0, -1, 0, 0), Qt.AlignmentFlag.AlignCenter, "↶")
    elif symbol == "clear":
        bx, by = margin + 4, margin + 5
        bw = size - (margin + 4) * 2
        bh = size - margin * 2 - 6
        painter.drawRect(bx, by, bw, bh)
        painter.drawLine(margin + 2, by, size - margin - 2, by)
        painter.drawLine(size // 2, margin + 1, size // 2, by)
        for index in range(1, 3):
            x = bx + (bw * index) // 3
            painter.drawLine(x, by + 3, x, by + bh - 3)
    elif symbol == "copy":
        painter.drawRect(margin + 4, margin, size - margin * 2 - 4, size - margin * 2 - 4)
        painter.setBrush(QBrush(QColor("#F3F3F3")))
        painter.drawRect(margin, margin + 4, size - margin * 2 - 4, size - margin * 2 - 4)
    elif symbol == "save":
        painter.setBrush(QBrush(QColor("#D0D8F0")))
        painter.drawRect(margin, margin, size - margin * 2, size - margin * 2)
        painter.setBrush(QBrush(QColor("#8090C0")))
        painter.drawRect(margin + 3, margin, size - margin * 2 - 6, 8)
        painter.setBrush(QBrush(QColor("white")))
        painter.drawRect(margin + 3, margin + 14, size - margin * 2 - 6, size - margin * 2 - 14)
    else:
        painter.setFont(QFont("Segoe UI", 11))
        painter.setPen(QPen(color))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, symbol)

    painter.end()
    return QIcon(pixmap)


@lru_cache(maxsize=None)
def _load_asset_icon(name: str) -> QIcon:
    path = asset_path(name)
    if not path.exists():
        return QIcon()
    return QIcon(str(path))


def _vsep() -> QFrame:
    separator = QFrame()
    separator.setFrameShape(QFrame.Shape.VLine)
    separator.setStyleSheet("color: #CCCCCC;")
    separator.setFixedWidth(1)
    return separator


class _ToolBtn(QToolButton):
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
                padding: 2px 0 2px 0;
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
                padding: 2px 0 2px 0;
            }
            QToolButton:hover {
                background: #E5F3FF;
                border-color: #99CCFF;
            }
            QToolButton:pressed {
                background: #B3D9FF;
            }
        """)


class _ColorChip(QToolButton):
    def __init__(self, color: QColor) -> None:
        super().__init__()
        self._color = color
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(_CHIP_ICON_SZ, _CHIP_ICON_SZ)
        self.setIconSize(QSize(_CHIP_ICON_SZ, _CHIP_ICON_SZ))
        self.setStyleSheet("""
            QToolButton {
                border: none;
                background: transparent;
                padding: 0;
            }
        """)
        self._apply_icon(False)
        self.toggled.connect(self._apply_icon)

    def _apply_icon(self, checked: bool) -> None:
        pixmap = QPixmap(_CHIP_ICON_SZ, _CHIP_ICON_SZ)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        outer_rect = QRect(1, 1, _CHIP_ICON_SZ - 2, _CHIP_ICON_SZ - 2)
        if checked:
            painter.setBrush(QBrush(QColor("#2AA7FF")))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(outer_rect)

            white_rect = outer_rect.adjusted(3, 3, -3, -3)
            painter.setBrush(QBrush(QColor("white")))
            painter.drawEllipse(white_rect)

            color_rect = white_rect.adjusted(2, 2, -2, -2)
        else:
            painter.setBrush(QBrush(self._color))
            painter.setPen(QPen(QColor(0, 0, 0, 45), 1))
            painter.drawEllipse(outer_rect)
            color_rect = QRect()

        if checked:
            painter.setBrush(QBrush(self._color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(color_rect)

        painter.end()
        self.setIcon(QIcon(pixmap))


class _TextFormatPopup(QWidget):
    def __init__(self, canvas: AnnotationCanvas, parent: QWidget) -> None:
        super().__init__(
            parent,
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint,
        )
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

        self._size_combo = QComboBox()
        for size in [8, 10, 12, 14, 16, 18, 20, 24, 28, 32, 36, 48, 64, 72]:
            self._size_combo.addItem(str(size), size)
        self._size_combo.setCurrentIndex(3)
        self._size_combo.setFixedHeight(38)
        self._size_combo.setFont(QFont("Segoe UI", 13))
        self._size_combo.activated.connect(self._update)

        btn_style = """
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

        self._bold_btn = QToolButton()
        self._bold_btn.setText("B")
        self._bold_btn.setCheckable(True)
        self._bold_btn.setFixedSize(38, 38)
        bold_font = QFont("Segoe UI", 13)
        bold_font.setBold(True)
        self._bold_btn.setFont(bold_font)
        self._bold_btn.setStyleSheet(btn_style)
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
        event_type = event.type()
        if event_type == QEvent.Type.MouseButtonPress:
            if self._size_combo.view().isVisible():
                return False
            global_pos = event.globalPosition().toPoint()
            popup_rect = QRect(self.mapToGlobal(QPoint(0, 0)), self.size())
            if not popup_rect.contains(global_pos):
                self.hide()
        elif event_type == QEvent.Type.ApplicationDeactivated:
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
    def __init__(
        self,
        canvas: AnnotationCanvas,
        editor,
        presentation_color: tuple[int, int, int],
        presentation_color_mode: str,
        presentation_gradient_preset: str,
        presentation_style: str,
        background_image_path: str | None,
    ) -> None:
        super().__init__()
        self._canvas = canvas
        self._editor = editor
        self._color = QColor("#19C85B")
        self._background_color = QColor(*presentation_color)
        self._background_color_mode = (
            presentation_color_mode if presentation_color_mode in {"solid", "gradient"} else "solid"
        )
        self._background_gradient_preset = (
            presentation_gradient_preset
            if presentation_gradient_preset in dict(_GRADIENT_PRESET_ITEMS)
            else "apple_sky"
        )
        self._background_style = (
            presentation_style
            if presentation_style in {"color", "image1", "image2", "image3", "custom"}
            else "color"
        )
        self._background_image_path = background_image_path

        self.setFixedHeight(_RIBBON_H)
        self.setStyleSheet("QWidget { background: #F3F3F3; }")

        main = QHBoxLayout(self)
        main.setContentsMargins(8, 4, 8, 0)
        main.setSpacing(0)

        main.addLayout(self._recapture_group())
        main.addWidget(_vsep())
        main.addSpacing(4)

        main.addLayout(self._tools_group())
        main.addWidget(_vsep())
        main.addSpacing(4)

        main.addLayout(self._colors_group())
        main.addWidget(_vsep())
        main.addSpacing(4)

        main.addLayout(self._presentation_group())
        main.addWidget(_vsep())
        main.addSpacing(4)

        main.addLayout(self._actions_group())
        main.addStretch()

    def _recapture_group(self) -> QVBoxLayout:
        vbox = QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        row = QHBoxLayout()
        row.setSpacing(1)
        row.setContentsMargins(0, 0, 0, 0)

        button = _ActionBtn("new", "New", "New screenshot  Ctrl+N")
        button.clicked.connect(self._editor.request_recapture)
        row.addWidget(button)

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
            (TOOL_RECT, "rect", "Rect", "Rectangle"),
            (TOOL_ARROW, "arrow", "Arrow", "Arrow"),
            (TOOL_LABEL, "label", "Label", "Numbered Label"),
            (TOOL_TEXT, "text", "Text", "Add Text"),
            (TOOL_REDACT, "redact", "Redact", "Blur / Redact"),
        ]
        for tool_name, symbol, label, tooltip in tools:
            button = _ToolBtn(symbol, label, tooltip)
            if tool_name == TOOL_TEXT:
                button.clicked.connect(self._on_text_btn_clicked)
            else:
                button.clicked.connect(lambda _, name=tool_name: self._on_tool_clicked(name))
            self._btn_group.addButton(button)
            self._tool_btns[tool_name] = button
            row.addWidget(button)

        self._tool_btns[TOOL_RECT].setChecked(True)
        self._text_popup = _TextFormatPopup(self._canvas, self.window())

        vbox.addLayout(row)
        return vbox

    def _on_tool_clicked(self, name: str) -> None:
        self._text_popup.hide()
        self._canvas.set_tool(name)

    def _on_text_btn_clicked(self) -> None:
        self._canvas.set_tool(TOOL_TEXT)
        button = self._tool_btns[TOOL_TEXT]
        pos = button.mapToGlobal(button.rect().bottomLeft())
        self._text_popup.move(pos)
        self._text_popup.show()
        self._text_popup.raise_()

    def _colors_group(self) -> QVBoxLayout:
        vbox = QVBoxLayout()
        vbox.setContentsMargins(6, 0, 6, 0)
        vbox.setSpacing(0)

        panel = QWidget()
        panel.setFixedSize(_BTN_W, _BTN_H)

        grid = QGridLayout(panel)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)

        self._color_group = QButtonGroup(self)
        self._color_group.setExclusive(True)

        for index, value in enumerate(_PALETTE_COLORS):
            color = QColor(value)
            chip = _ColorChip(color)
            chip.setToolTip(value)
            chip.clicked.connect(lambda _, picked=color: self._set_color(picked))
            self._color_group.addButton(chip)
            grid.addWidget(chip, index // 2, index % 2, Qt.AlignmentFlag.AlignCenter)
            if color.name().lower() == self._color.name().lower():
                chip.setChecked(True)

        vbox.addWidget(panel)
        return vbox

    def _actions_group(self) -> QVBoxLayout:
        vbox = QVBoxLayout()
        vbox.setContentsMargins(4, 0, 4, 0)
        vbox.setSpacing(0)

        row = QHBoxLayout()
        row.setSpacing(1)
        row.setContentsMargins(0, 0, 0, 0)

        undo_btn = _ActionBtn("undo", "Undo", "Undo  Ctrl+Z")
        undo_btn.clicked.connect(self._editor.undo_annotations)

        clear_btn = _ActionBtn("clear", "Clear", "Clear all annotations")
        clear_btn.clicked.connect(self._editor.clear_annotations)

        copy_btn = _ActionBtn("copy", "Copy", "Copy to clipboard  Ctrl+C")
        copy_btn.clicked.connect(self._editor.copy_image)

        save_btn = _ActionBtn("save", "Save", "Save to file  Ctrl+S")
        save_btn.clicked.connect(self._editor.save_image)

        x_btn = QToolButton()
        x_btn.setFixedSize(_BTN_W, _BTN_H)
        x_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        x_btn.setIcon(_load_asset_icon("x_icon.jpg"))
        x_btn.setIconSize(QSize(28, 28))
        x_btn.setText("😘")
        x_btn.setToolTip("@solotop999 on X")
        x_btn.clicked.connect(self._open_x_profile)
        x_btn.setStyleSheet("""
            QToolButton {
                border: 1px solid transparent;
                border-radius: 3px;
                background: transparent;
                color: #1A1A1A;
                padding: 2px 0 2px 0;
            }
            QToolButton:hover {
                background: #E5F3FF;
                border-color: #99CCFF;
            }
            QToolButton:pressed {
                background: #B3D9FF;
            }
        """)

        for button in (undo_btn, clear_btn, copy_btn, save_btn, x_btn):
            row.addWidget(button)

        vbox.addLayout(row)
        return vbox

    def _presentation_group(self) -> QVBoxLayout:
        vbox = QVBoxLayout()
        vbox.setContentsMargins(8, 6, 8, 6)
        vbox.setSpacing(4)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(0)

        self._bg_btn = QToolButton()
        self._bg_btn.setText("Background")
        self._bg_btn.setCheckable(True)
        self._bg_btn.setChecked(True)
        self._bg_btn.setFixedWidth(122)
        self._bg_btn.setFixedHeight(24)
        self._bg_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self._bg_btn.setToolTip("Toggle social background")
        self._bg_btn.clicked.connect(self._on_bg_toggled)
        self._bg_btn.setStyleSheet("""
            QToolButton {
                border: 1px solid #9CB9D8;
                border-radius: 5px;
                background: #FFFFFF;
                color: #1A1A1A;
                font: 700 9pt "Segoe UI";
                padding: 0 10px;
                text-align: left;
            }
            QToolButton:hover {
                background: #E8F3FF;
                border-color: #7FAFDD;
            }
            QToolButton:checked {
                background: #CCE8FF;
                border-color: #0078D4;
            }
        """)

        self._layout_combo = self._make_presentation_combo(58)
        self._layout_combo.addItem("Original", "fit")
        self._layout_combo.addItem("Portrait", "post")
        self._layout_combo.addItem("Landscape", "wide")
        self._layout_combo.addItem("Phone", "phone")
        self._layout_combo.setPlaceholderText("Style")
        self._layout_combo.setCurrentIndex(-1)
        self._layout_combo.view().setMinimumWidth(120)
        self._layout_combo.setStyleSheet("""
            QComboBox {
                background: #FFFFFF;
                border: 1px solid #B9C7D6;
                border-radius: 5px;
                padding: 2px 6px 2px 6px;
                color: #1A1A1A;
            }
            QComboBox:hover {
                border-color: #7FAFDD;
                background: #F8FBFF;
            }
            QComboBox::drop-down {
                border: none;
                width: 0px;
            }
            QComboBox::down-arrow {
                image: none;
                width: 0px;
                height: 0px;
            }
        """)
        self._layout_combo.currentIndexChanged.connect(self._on_layout_changed)

        self._bg_color_btn = QToolButton()
        self._bg_color_btn.setText("Color")
        self._bg_color_btn.setFixedWidth(58)
        self._bg_color_btn.setFixedHeight(24)
        self._bg_color_btn.setToolTip("Choose background source")
        self._bg_color_btn.clicked.connect(self._show_background_source_menu)
        self._bg_color_btn.setStyleSheet("""
            QToolButton {
                background: #FFFFFF;
                border: 1px solid #B9C7D6;
                border-radius: 5px;
                color: #1A1A1A;
                padding: 0 10px;
            }
            QToolButton:hover {
                border-color: #7FAFDD;
                background: #F8FBFF;
            }
            QToolButton:pressed {
                background: #E8F3FF;
            }
        """)
        self._sync_background_button()

        top_row.addWidget(self._bg_btn)

        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.setSpacing(6)
        bottom_row.addWidget(self._layout_combo)
        bottom_row.addWidget(self._bg_color_btn)

        vbox.addLayout(top_row)
        vbox.addLayout(bottom_row)
        return vbox

    def _make_presentation_combo(self, width: int) -> QComboBox:
        combo = QComboBox()
        combo.setFixedSize(width, 24)
        combo.setFont(QFont("Segoe UI", 8))
        combo.setStyleSheet("""
            QComboBox {
                background: #FFFFFF;
                border: 1px solid #B9C7D6;
                border-radius: 5px;
                padding: 2px 20px 2px 7px;
                color: #1A1A1A;
            }
            QComboBox:hover {
                border-color: #7FAFDD;
                background: #F8FBFF;
            }
            QComboBox::drop-down {
                border: none;
                width: 18px;
            }
        """)
        return combo

    def _set_color(self, color: QColor) -> None:
        self._color = color
        self._canvas.set_color(color)

    def _on_bg_toggled(self, checked: bool) -> None:
        self._layout_combo.setEnabled(checked)
        self._bg_color_btn.setEnabled(checked)
        self._editor.set_presentation_enabled(checked)

    def _on_layout_changed(self, _index: int) -> None:
        self._editor.set_presentation_layout(str(self._layout_combo.currentData()))

    def _pick_background_color(self) -> bool:
        color = QColorDialog.getColor(
            self._background_color,
            self,
            "Chon mau background",
        )
        if not color.isValid():
            return False

        self._background_color = color
        self._editor.set_presentation_overlay_color((color.red(), color.green(), color.blue()))
        save_presentation_background_color((color.red(), color.green(), color.blue()))
        self._sync_background_button()
        return True

    def _open_x_profile(self) -> None:
        QDesktopServices.openUrl(QUrl(_X_PROFILE_URL))

    def _sync_background_button(self) -> None:
        if self._background_style == "image1":
            self._bg_color_btn.setText("BG 1")
            self._bg_color_btn.setStyleSheet("""
                QToolButton {
                    background: #FFF6E9;
                    border: 1px solid #D3B27C;
                    border-radius: 5px;
                    color: #6A4A17;
                    padding: 0 8px;
                }
                QToolButton:hover {
                    border-color: #B88F4D;
                    background: #FFF1DB;
                }
                QToolButton:pressed {
                    background: #F7E3BF;
                }
            """)
            return

        if self._background_style == "image2":
            self._bg_color_btn.setText("BG 2")
            self._bg_color_btn.setStyleSheet("""
                QToolButton {
                    background: #EEF0FF;
                    border: 1px solid #98A7D6;
                    border-radius: 5px;
                    color: #33406B;
                    padding: 0 8px;
                }
                QToolButton:hover {
                    border-color: #7385C2;
                    background: #E6EAFF;
                }
                QToolButton:pressed {
                    background: #DCE3FF;
                }
            """)
            return

        if self._background_style == "image3":
            self._bg_color_btn.setText("BG 3")
            self._bg_color_btn.setStyleSheet("""
                QToolButton {
                    background: #F1EEFF;
                    border: 1px solid #A999D6;
                    border-radius: 5px;
                    color: #49376F;
                    padding: 0 8px;
                }
                QToolButton:hover {
                    border-color: #856EC2;
                    background: #EAE4FF;
                }
                QToolButton:pressed {
                    background: #DDD5FF;
                }
            """)
            return

        if self._background_style == "custom":
            self._bg_color_btn.setText("Image")
            self._bg_color_btn.setToolTip(self._background_image_path or "Custom background image")
            self._bg_color_btn.setStyleSheet("""
                QToolButton {
                    background: #E9FFF5;
                    border: 1px solid #79C7A0;
                    border-radius: 5px;
                    color: #1F5D45;
                    padding: 0 8px;
                }
                QToolButton:hover {
                    border-color: #4FA178;
                    background: #E0F9EE;
                }
                QToolButton:pressed {
                    background: #D2F2E3;
                }
            """)
            return

        if self._background_color_mode == "gradient":
            preset_label, start_color, end_color, text_color = _GRADIENT_PRESET_STYLES.get(
                self._background_gradient_preset,
                _GRADIENT_PRESET_STYLES["apple_sky"],
            )
            self._bg_color_btn.setText("Grad")
            self._bg_color_btn.setToolTip(f"Gradient: {preset_label}")
            self._bg_color_btn.setStyleSheet(f"""
                QToolButton {{
                    background: qlineargradient(
                        x1: 0, y1: 0, x2: 1, y2: 1,
                        stop: 0 {start_color},
                        stop: 1 {end_color}
                    );
                    border: 1px solid #7A8EA6;
                    border-radius: 5px;
                    color: {text_color};
                    padding: 0 10px;
                }}
                QToolButton:hover {{
                    border-color: #4D6F95;
                }}
                QToolButton:pressed {{
                    background: {end_color};
                }}
            """)
            return

        self._bg_color_btn.setText("Color")
        self._bg_color_btn.setToolTip("Choose background source")
        text_color = "#FFFFFF" if self._background_color.lightness() < 140 else "#1A1A1A"
        self._bg_color_btn.setStyleSheet(f"""
            QToolButton {{
                background: {self._background_color.name()};
                border: 1px solid #7A8EA6;
                border-radius: 5px;
                color: {text_color};
                padding: 0 10px;
            }}
            QToolButton:hover {{
                border-color: #4D6F95;
            }}
            QToolButton:pressed {{
                background: {self._background_color.darker(108).name()};
            }}
        """)

    def _show_background_source_menu(self) -> None:
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: #FFFFFF;
                border: 1px solid #B9C7D6;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 12px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background: #E8F3FF;
            }
        """)

        solid_color_action = menu.addAction("Solid Color...")
        gradient_menu = menu.addMenu("Gradient")
        gradient_actions = {
            gradient_menu.addAction(label): preset
            for preset, label in _GRADIENT_PRESET_ITEMS
        }
        bg1_action = menu.addAction("BG 1")
        bg2_action = menu.addAction("BG 2")
        bg3_action = menu.addAction("BG 3")
        custom_action = menu.addAction("Custom")
        selected = menu.exec(self._bg_color_btn.mapToGlobal(self._bg_color_btn.rect().bottomLeft()))
        if selected is solid_color_action:
            self._background_style = "color"
            self._background_color_mode = "solid"
            self._editor.set_presentation_style("color")
            self._editor.set_presentation_color_mode("solid")
            save_presentation_background_style("color")
            save_presentation_background_color_mode("solid")
            if not self._pick_background_color():
                self._sync_background_button()
                return
        elif selected in gradient_actions:
            self._background_style = "color"
            self._background_color_mode = "gradient"
            self._background_gradient_preset = gradient_actions[selected]
            self._editor.set_presentation_style("color")
            self._editor.set_presentation_color_mode("gradient")
            self._editor.set_presentation_gradient_preset(self._background_gradient_preset)
            save_presentation_background_style("color")
            save_presentation_background_color_mode("gradient")
            save_presentation_background_gradient_preset(self._background_gradient_preset)
        elif selected is bg1_action:
            self._background_style = "image1"
            self._editor.set_presentation_style("image1")
            save_presentation_background_style("image1")
        elif selected is bg2_action:
            self._background_style = "image2"
            self._editor.set_presentation_style("image2")
            save_presentation_background_style("image2")
        elif selected is bg3_action:
            self._background_style = "image3"
            self._editor.set_presentation_style("image3")
            save_presentation_background_style("image3")
        elif selected is custom_action:
            path = self._pick_background_image()
            if not path:
                self._sync_background_button()
                return
            self._background_image_path = path
            self._background_style = "custom"
            self._editor.set_presentation_background_image_path(path)
            self._editor.set_presentation_style("custom")
            save_presentation_background_image(path)
            save_presentation_background_style("custom")
        else:
            return

        self._sync_background_button()

    def _pick_background_image(self) -> str | None:
        path, _selected_filter = QFileDialog.getOpenFileName(
            self,
            "Choose background image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.webp *.bmp)",
        )
        if not path:
            return None

        if not is_local_background_image_path(path):
            QMessageBox.warning(
                self,
                "Invalid image location",
                "Please choose an image stored on this computer. Network paths are not allowed.",
            )
            return None

        return path
