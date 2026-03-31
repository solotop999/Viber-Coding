"""Main annotation editor window."""
from __future__ import annotations

import ctypes
import sys
from datetime import datetime
from pathlib import Path

from PIL import Image
from PyQt6.QtCore import QEasingCurve, QEventLoop, QPropertyAnimation, Qt, pyqtSignal
from PyQt6.QtGui import QCloseEvent, QFont, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QGraphicsOpacityEffect,
    QLabel,
    QMessageBox,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.clipboard import copy_to_clipboard
from core.settings import (
    is_local_background_image_path,
    load_presentation_background_color,
    load_presentation_background_image,
    load_presentation_background_style,
)
from editor.canvas import AnnotationCanvas
from editor.presentation_view import PresentationView
from editor.toolbar import Toolbar
from processing.presentation import PresentationSettings


def _desktop_dir() -> Path:
    desktop = Path.home() / "Desktop"
    return desktop if desktop.exists() else Path.home()


def _default_save_path() -> Path:
    stamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    return _desktop_dir() / f"Screenshot-{stamp}.png"


class EditorWindow(QWidget):
    recapture_requested = pyqtSignal()

    def __init__(self, pil_image: Image.Image) -> None:
        super().__init__()

        self.setWindowTitle("Solotop Capture")
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
        )
        app_icon = QApplication.windowIcon()
        if not app_icon.isNull():
            self.setWindowIcon(app_icon)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setStyleSheet("QWidget { background: #FFFFFF; }")
        self.setMinimumSize(700, 500)

        self._presentation_color = load_presentation_background_color()
        self._presentation_style = load_presentation_background_style()
        self._presentation_background_image = load_presentation_background_image()
        if self._presentation_background_image and (
            not is_local_background_image_path(self._presentation_background_image)
            or not Path(self._presentation_background_image).exists()
        ):
            self._presentation_background_image = None
        if self._presentation_style == "custom" and not self._presentation_background_image:
            self._presentation_style = "color"

        self._canvas = AnnotationCanvas(pil_image)
        self._presentation_view = PresentationView(
            self._canvas,
            settings=PresentationSettings(
                enabled=True,
                layout="fit",
                style=self._presentation_style,
                overlay_color=self._presentation_color,
                background_image_path=self._presentation_background_image,
            ),
        )
        self._toolbar = Toolbar(
            self._canvas,
            self,
            self._presentation_color,
            self._presentation_style,
            self._presentation_background_image,
        )
        self._toolbar.setMinimumWidth(self._toolbar.sizeHint().width())
        self._install_shortcuts()

        self._scroll = QScrollArea()
        self._scroll.setWidget(self._presentation_view)
        self._scroll.setWidgetResizable(False)
        self._scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._scroll.setStyleSheet("""
            QScrollArea { background: #FFFFFF; border: none; }
            QScrollBar:horizontal { height: 12px; background: #F0F0F0; }
            QScrollBar:vertical   { width: 12px; background: #F0F0F0; }
            QScrollBar::handle:horizontal,
            QScrollBar::handle:vertical {
                background: #C0C0C0; border-radius: 4px; min-width: 30px;
            }
            QScrollBar::handle:hover { background: #A0A0A0; }
            QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
        """)
        self._init_copy_toast()

        self._status = QLabel()
        self._status.setFixedHeight(20)
        self._status.setStyleSheet(
            "background: #F0F0F0; color: #333; font-size: 11px;"
            " font-family: Segoe UI; padding-left: 8px;"
            " border-top: 1px solid #CCCCCC;"
        )
        self._set_image_status(pil_image.size)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFixedHeight(1)
        divider.setStyleSheet("background: #C0C0C0; border: none;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._toolbar)
        layout.addWidget(divider)
        layout.addWidget(self._scroll, 1)
        layout.addWidget(self._status)

        screen = QApplication.primaryScreen().availableGeometry()
        self._update_minimum_width()
        self._resize_to_content(screen)

    def _install_shortcuts(self) -> None:
        self._copy_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
        self._copy_shortcut.activated.connect(self.copy_image)

        self._save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        self._save_shortcut.activated.connect(self.save_image)

        self._undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        self._undo_shortcut.activated.connect(self.undo_annotations)

        self._new_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        self._new_shortcut.activated.connect(self.request_recapture)

    def _init_copy_toast(self) -> None:
        self._copy_toast = QLabel("Copied", self._scroll.viewport())
        self._copy_toast.hide()
        self._copy_toast.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._copy_toast.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._copy_toast.setFont(QFont("Segoe UI", 39, QFont.Weight.DemiBold))
        self._copy_toast.setStyleSheet("""
            QLabel {
                background: rgba(20, 24, 32, 220);
                color: white;
                border-radius: 24px;
                padding: 18px 36px;
            }
        """)

        self._copy_toast_effect = QGraphicsOpacityEffect(self._copy_toast)
        self._copy_toast_effect.setOpacity(0.0)
        self._copy_toast.setGraphicsEffect(self._copy_toast_effect)

        self._copy_toast_anim = QPropertyAnimation(self._copy_toast_effect, b"opacity", self)
        self._copy_toast_anim.setDuration(2000)
        self._copy_toast_anim.setStartValue(1.0)
        self._copy_toast_anim.setEndValue(0.0)
        self._copy_toast_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._copy_toast_anim.finished.connect(self._copy_toast.hide)

    def _show_copy_toast(self) -> None:
        self._copy_toast_anim.stop()
        self._copy_toast_effect.setOpacity(1.0)
        self._copy_toast.adjustSize()
        self._position_copy_toast()
        self._copy_toast.show()
        self._copy_toast.raise_()
        self._copy_toast_anim.start()

    def _position_copy_toast(self) -> None:
        viewport = self._scroll.viewport()
        x = max(0, (viewport.width() - self._copy_toast.width()) // 2)
        y = max(0, (viewport.height() - self._copy_toast.height()) // 2)
        self._copy_toast.move(x, y)

    def _set_image_status(self, size: tuple[int, int]) -> None:
        width, height = size
        settings = self._presentation_view.settings()
        if settings.enabled:
            out_width, out_height = self._presentation_view.output_size()
            self._status.setText(f"  {width} x {height} px  ->  {out_width} x {out_height} px")
            return
        self._status.setText(f"  {width} x {height} px")

    def _resize_to_content(self, screen=None) -> None:
        screen = screen or QApplication.primaryScreen().availableGeometry()
        self._update_minimum_width()
        width, height = self._presentation_view.output_size()
        min_width = max(self.minimumWidth(), self._toolbar.sizeHint().width())
        win_w = min(max(min_width, width + 20), screen.width() - 40)
        win_h = min(height + self._toolbar.height() + 62, screen.height() - 40)
        self.resize(win_w, win_h)

    def _update_minimum_width(self) -> None:
        toolbar_width = self._toolbar.sizeHint().width()
        window_min_width = max(700, toolbar_width + 20)
        self.setMinimumWidth(window_min_width)

    def prepare_for_recapture(self) -> None:
        self._canvas.cancel_active_tool()

    def hide_for_recapture(self) -> None:
        self.prepare_for_recapture()
        self.setWindowOpacity(0.0)
        self.hide()

        if sys.platform == "win32":
            try:
                ctypes.windll.user32.ShowWindow(int(self.winId()), 0)
            except Exception:
                pass

        QApplication.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 80)

    def restore_after_recapture(self) -> None:
        self.setWindowOpacity(1.0)
        self.show()
        self.raise_()
        self.activateWindow()

    def request_recapture(self) -> None:
        self.prepare_for_recapture()
        self.recapture_requested.emit()

    def copy_image(self) -> None:
        focused = QApplication.focusWidget()
        if isinstance(focused, QTextEdit) and focused.textCursor().hasSelection():
            focused.copy()
            return

        self._canvas.commit_active_tool()
        try:
            copy_to_clipboard(self._canvas.flatten_to_pil(self._presentation_view.settings()))
            self._status.setText("  Copied to clipboard!")
            self._show_copy_toast()
        except Exception as exc:
            QMessageBox.warning(self, "Copy failed", str(exc))

    def save_image(self) -> None:
        self._canvas.commit_active_tool()

        path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Save Screenshot",
            str(_default_save_path()),
            "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg)",
            "PNG Image (*.png)",
        )
        if not path:
            return

        save_path = Path(path)
        if not save_path.suffix:
            save_path = save_path.with_suffix(".jpg" if "JPEG" in selected_filter else ".png")

        try:
            settings = self._presentation_view.settings()
            image = self._canvas.flatten_to_pil(settings)
            if save_path.suffix.lower() in {".jpg", ".jpeg"}:
                if settings.enabled:
                    image.convert("RGB").save(save_path, quality=95)
                else:
                    background = Image.new("RGB", image.size, (255, 255, 255))
                    background.paste(image, mask=image.getchannel("A"))
                    background.save(save_path, quality=95)
            else:
                image.save(save_path)
            self._status.setText(f"  Saved: {save_path}")
        except Exception as exc:
            QMessageBox.warning(self, "Save failed", str(exc))

    def undo_annotations(self) -> None:
        focused = QApplication.focusWidget()
        if isinstance(focused, QTextEdit):
            focused.undo()
            return

        self._canvas.undo()
        self._status.setText("  Undid last annotation")

    def clear_annotations(self) -> None:
        self._canvas.cancel_active_tool()
        self._canvas.clear()
        self._status.setText("  Cleared annotations")

    def update_image(self, pil_image: Image.Image) -> None:
        self._canvas.cancel_active_tool()
        self._canvas.set_image(pil_image)
        self._presentation_view.refresh_for_image()
        self._resize_to_content()
        self._set_image_status(pil_image.size)

    def set_presentation_enabled(self, enabled: bool) -> None:
        self._canvas.commit_active_tool()
        self._presentation_view.set_enabled(enabled)
        self._resize_to_content()
        self._set_image_status(self._canvas.image_size())

    def set_presentation_layout(self, layout: str) -> None:
        self._canvas.commit_active_tool()
        self._presentation_view.set_layout(layout)
        self._resize_to_content()
        self._set_image_status(self._canvas.image_size())

    def set_presentation_overlay_color(self, color: tuple[int, int, int]) -> None:
        self._canvas.commit_active_tool()
        self._presentation_color = color
        self._presentation_view.set_overlay_color(color)

    def set_presentation_style(self, style: str) -> None:
        self._canvas.commit_active_tool()
        self._presentation_style = style
        self._presentation_view.set_style(style)

    def set_presentation_background_image_path(self, path: str | None) -> None:
        self._canvas.commit_active_tool()
        self._presentation_background_image = path
        self._presentation_view.set_background_image_path(path)

    def closeEvent(self, event: QCloseEvent) -> None:
        self._canvas.cancel_active_tool()
        super().closeEvent(event)
        if event.isAccepted():
            QApplication.instance().quit()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "_copy_toast") and self._copy_toast.isVisible():
            self._position_copy_toast()
