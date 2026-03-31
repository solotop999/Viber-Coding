"""
Capture - lightweight offline Windows screenshot tool.

SECURITY NOTES:
- No network connections of any kind.
- No global hotkeys.
- No system tray or background process.
- No auto-update, no telemetry, no crash reporting.
- Images are only saved/copied on explicit user action.
"""
from __future__ import annotations

import ctypes
import os
import sys
from pathlib import Path

os.environ["QT_NETWORK_PROXY_AUTOCONF"] = "0"
os.environ["QT_NO_GLIB"] = "1"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
os.environ["QT_SCALE_FACTOR"] = "1"

from PIL import Image
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QIcon, QPainter, QPainterPath, QPixmap
from PyQt6.QtWidgets import QApplication

from core.capture import SelectionOverlay
from core.paths import asset_path
from core.screenshot import grab_region
from editor.editor_window import EditorWindow


def _enable_windows_dpi_awareness() -> None:
    if sys.platform != "win32":
        return

    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        return
    except Exception:
        pass

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return
    except Exception:
        pass

    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def _load_app_icon() -> QIcon:
    icon_path = asset_path("logo.jpg")
    if not icon_path.exists():
        return QIcon()

    source = QPixmap(str(icon_path))
    if source.isNull():
        return QIcon()

    size = min(source.width(), source.height())
    cropped = source.copy(
        (source.width() - size) // 2,
        (source.height() - size) // 2,
        size,
        size,
    )

    circular = QPixmap(size, size)
    circular.fill(Qt.GlobalColor.transparent)

    painter = QPainter(circular)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = QPainterPath()
    path.addEllipse(0, 0, size, size)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, cropped)
    painter.end()
    return QIcon(circular)


class CaptureApp:
    def __init__(self, app: QApplication) -> None:
        self._app = app
        self._overlay: SelectionOverlay | None = None
        self._editor: EditorWindow | None = None
        self._editor_prewarm_scheduled = False

    def start(self) -> None:
        self._start_capture()

    def _start_capture(self) -> None:
        if self._overlay and self._overlay.isVisible():
            return

        overlay = SelectionOverlay()
        overlay.region_selected.connect(self._on_region_selected)
        overlay.cancelled.connect(self._on_initial_capture_cancelled)
        overlay.show()
        overlay.raise_()
        overlay.activateWindow()
        self._overlay = overlay
        self._schedule_editor_prewarm()

    def _schedule_editor_prewarm(self) -> None:
        if self._editor or self._editor_prewarm_scheduled:
            return
        self._editor_prewarm_scheduled = True
        QTimer.singleShot(0, self._prewarm_editor)

    def _prewarm_editor(self) -> None:
        self._editor_prewarm_scheduled = False
        if self._editor is not None:
            return

        placeholder = Image.new("RGBA", (64, 64), (255, 255, 255, 0))
        editor = EditorWindow(placeholder)
        editor.recapture_requested.connect(self._start_recapture)
        editor.destroyed.connect(self._on_editor_destroyed)
        editor.hide()
        self._editor = editor

    def _start_recapture(self) -> None:
        if self._editor:
            self._editor.hide_for_recapture()
        QTimer.singleShot(220, self._show_recapture_overlay)

    def _show_recapture_overlay(self) -> None:
        overlay = SelectionOverlay()
        overlay.region_selected.connect(self._on_recapture_region)
        overlay.cancelled.connect(self._on_recapture_cancelled)
        overlay.show()
        overlay.raise_()
        overlay.activateWindow()
        self._overlay = overlay

    def _capture_image(self, x: int, y: int, w: int, h: int) -> Image.Image:
        from processing.corners import apply_rounded_corners

        image = grab_region(x, y, w, h)
        return apply_rounded_corners(image.convert("RGBA"), radius=22)

    def _on_region_selected(self, x: int, y: int, w: int, h: int) -> None:
        self._overlay = None
        self._open_editor(self._capture_image(x, y, w, h))

    def _on_initial_capture_cancelled(self) -> None:
        self._overlay = None
        self._quit()

    def _on_recapture_region(self, x: int, y: int, w: int, h: int) -> None:
        self._overlay = None
        if self._editor:
            self._editor.update_image(self._capture_image(x, y, w, h))
            self._editor.restore_after_recapture()

    def _on_recapture_cancelled(self) -> None:
        self._overlay = None
        if self._editor:
            self._editor.restore_after_recapture()

    def _open_editor(self, image: Image.Image) -> None:
        if self._editor is None:
            self._editor = EditorWindow(image)
            self._editor.recapture_requested.connect(self._start_recapture)
            self._editor.destroyed.connect(self._on_editor_destroyed)
        else:
            self._editor.update_image(image)
        self._editor.show()
        self._editor.raise_()
        self._editor.activateWindow()

    def _on_editor_destroyed(self) -> None:
        self._editor = None

    def _quit(self) -> None:
        self._app.quit()


def main() -> None:
    _enable_windows_dpi_awareness()
    app = QApplication(sys.argv)
    app.setApplicationDisplayName("Solotop Capture")
    app_icon = _load_app_icon()
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)
    app.setQuitOnLastWindowClosed(True)

    if not QApplication.screens():
        sys.exit(1)

    capture = CaptureApp(app)
    QTimer.singleShot(0, capture.start)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
