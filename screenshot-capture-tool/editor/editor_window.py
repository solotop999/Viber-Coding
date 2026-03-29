"""
Main annotation editor window — layout giống Paint:
  - Ribbon toolbar ở trên
  - Canvas scroll area chiếm toàn bộ phần dưới
  - Status bar nhỏ ở dưới cùng
"""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea,
    QFileDialog, QMessageBox, QLabel, QFrame,
)

from editor.canvas import AnnotationCanvas
from editor.toolbar import Toolbar
from core.clipboard import copy_to_clipboard
from PIL import Image


class EditorWindow(QWidget):
    recapture_requested = pyqtSignal()

    def __init__(self, pil_image: Image.Image) -> None:
        super().__init__()
        self._pil_image = pil_image
        self.setWindowTitle("Capture")
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setStyleSheet("QWidget { background: #FFFFFF; }")
        self.setMinimumSize(700, 500)

        self._canvas = AnnotationCanvas(pil_image)
        self._toolbar = Toolbar(self._canvas, self)

        # Scroll area — canvas nằm giữa nền xám như Paint
        scroll = QScrollArea()
        scroll.setWidget(self._canvas)
        scroll.setWidgetResizable(False)
        scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll.setStyleSheet("""
            QScrollArea { background: #FFFFFF; border: none; }
            QScrollBar:horizontal { height: 12px; background: #F0F0F0; }
            QScrollBar:vertical   { width:  12px; background: #F0F0F0; }
            QScrollBar::handle:horizontal,
            QScrollBar::handle:vertical {
                background: #C0C0C0; border-radius: 4px; min-width: 30px;
            }
            QScrollBar::handle:hover { background: #A0A0A0; }
            QScrollBar::add-line, QScrollBar::sub-line { width:0; height:0; }
        """)

        # Status bar
        self._status = QLabel()
        self._status.setFixedHeight(20)
        self._status.setStyleSheet(
            "background: #F0F0F0; color: #333; font-size: 11px;"
            " font-family: Segoe UI; padding-left: 8px;"
            " border-top: 1px solid #CCCCCC;"
        )
        w, h = pil_image.size
        self._status.setText(f"  {w} × {h} px")

        # Đường kẻ ngang ngăn cách toolbar và canvas
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFixedHeight(1)
        divider.setStyleSheet("background: #C0C0C0; border: none;")

        # Main vertical layout: ribbon → divider → canvas → status
        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)
        vbox.addWidget(self._toolbar)
        vbox.addWidget(divider)
        vbox.addWidget(scroll, 1)
        vbox.addWidget(self._status)

        # Size window to fit image + ribbon, capped at 90% of screen
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().availableGeometry()
        win_w = min(self._toolbar.sizeHint().width(), screen.width() - 80)
        win_w = max(win_w, w + 20)
        win_h = min(h + self._toolbar.height() + 22 + 40, screen.height() - 80)
        self.resize(min(win_w, screen.width() - 40),
                    min(win_h, screen.height() - 40))

    def _copy(self) -> None:
        try:
            copy_to_clipboard(self._canvas.flatten_to_pil())
            self._status.setText("  Copied to clipboard!")
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
                self._status.setText(f"  Saved: {path}")
            except Exception as e:
                QMessageBox.warning(self, "Save failed", str(e))

    def update_image(self, pil_image: Image.Image) -> None:
        from editor.canvas import _pil_to_qpixmap
        self._pil_image = pil_image
        self._canvas._original_pil = pil_image.copy()
        self._canvas._pil_image = pil_image
        self._canvas._annotations.clear()
        self._canvas._undo_stack.clear()
        self._canvas._pixmap = _pil_to_qpixmap(pil_image)
        self._canvas.setFixedSize(self._canvas._pixmap.size())
        self._canvas.update()
        w, h = pil_image.size
        self._status.setText(f"  {w} × {h} px")
