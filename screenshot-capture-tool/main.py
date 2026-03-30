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

os.environ["QT_NETWORK_PROXY_AUTOCONF"] = "0"
os.environ["QT_NO_GLIB"] = "1"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
os.environ["QT_SCALE_FACTOR"] = "1"

from PIL import Image
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from core.capture import SelectionOverlay
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


class CaptureApp:
    def __init__(self, app: QApplication) -> None:
        self._app = app
        self._overlay: SelectionOverlay | None = None
        self._editor: EditorWindow | None = None

    def start(self) -> None:
        self._start_capture()

    def _start_capture(self) -> None:
        if self._overlay and self._overlay.isVisible():
            return

        overlay = SelectionOverlay()
        overlay.region_selected.connect(self._on_region_selected)
        overlay.cancelled.connect(self._on_initial_capture_cancelled)
        overlay.showFullScreen()
        self._overlay = overlay

    def _start_recapture(self) -> None:
        if self._editor:
            self._editor.prepare_for_recapture()
            self._editor.hide()
        QTimer.singleShot(150, self._show_recapture_overlay)

    def _show_recapture_overlay(self) -> None:
        overlay = SelectionOverlay()
        overlay.region_selected.connect(self._on_recapture_region)
        overlay.cancelled.connect(self._on_recapture_cancelled)
        overlay.showFullScreen()
        self._overlay = overlay

    def _capture_image(self, x: int, y: int, w: int, h: int) -> Image.Image:
        from processing.corners import apply_rounded_corners

        image = grab_region(x, y, w, h)
        return apply_rounded_corners(image.convert("RGBA"), radius=28)

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
            self._editor.show()
            self._editor.raise_()
            self._editor.activateWindow()

    def _on_recapture_cancelled(self) -> None:
        self._overlay = None
        if self._editor:
            self._editor.show()
            self._editor.raise_()
            self._editor.activateWindow()

    def _open_editor(self, image: Image.Image) -> None:
        self._editor = EditorWindow(image)
        self._editor.recapture_requested.connect(self._start_recapture)
        self._editor.destroyed.connect(self._on_editor_destroyed)
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
    app.setQuitOnLastWindowClosed(True)

    if not QApplication.screens():
        sys.exit(1)

    capture = CaptureApp(app)
    QTimer.singleShot(0, capture.start)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
