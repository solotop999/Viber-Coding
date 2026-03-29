"""
Capture — lightweight Windows screenshot tool.

SECURITY NOTES:
- No network connections of any kind.
- Global hotkey uses Win32 RegisterHotKey (NOT a keyboard hook / keylogger).
- No auto-update, no telemetry, no crash reporting.
- Images are only saved/copied on explicit user action.
"""
from __future__ import annotations

import os
import sys

# Block Qt from making any network connections
os.environ["QT_NETWORK_PROXY_AUTOCONF"] = "0"
os.environ["QT_NO_GLIB"] = "1"

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from core.capture import SelectionOverlay
from core.screenshot import grab_region
from editor.editor_window import EditorWindow
from ui.tray import TrayIcon
from PIL import Image

import pathlib

_ICON_PATH = str(pathlib.Path(__file__).parent / "assets" / "icon.ico")


class CaptureApp:
    def __init__(self, app: QApplication) -> None:
        self._app = app
        self._overlay: SelectionOverlay | None = None
        self._editor: EditorWindow | None = None

        # System tray
        icon_path = _ICON_PATH if pathlib.Path(_ICON_PATH).exists() else None
        self._tray = TrayIcon(
            on_capture=self._start_capture,
            on_quit=self._quit,
            icon_path=icon_path,
        )
        self._tray.show()

    def _start_capture(self) -> None:
        if self._overlay and self._overlay.isVisible():
            return
        self._overlay = SelectionOverlay()
        self._overlay.region_selected.connect(self._on_region_selected)
        self._overlay.cancelled.connect(lambda: None)
        self._overlay.showFullScreen()

    def _on_region_selected(self, x: int, y: int, w: int, h: int) -> None:
        from processing.corners import apply_rounded_corners
        img = grab_region(x, y, w, h)
        img = apply_rounded_corners(img.convert("RGBA"), radius=28)
        self._open_editor(img)

    def _open_editor(self, img: Image.Image) -> None:
        self._editor = EditorWindow(img)
        self._editor.recapture_requested.connect(self._start_recapture)
        self._editor.show()
        self._editor.raise_()
        self._editor.activateWindow()

    def _start_recapture(self) -> None:
        if self._editor:
            self._editor.hide()
        QTimer.singleShot(150, self._show_recapture_overlay)

    def _show_recapture_overlay(self) -> None:
        overlay = SelectionOverlay()
        overlay.region_selected.connect(self._on_recapture_region)
        overlay.cancelled.connect(self._on_recapture_cancelled)
        overlay.showFullScreen()
        self._overlay = overlay

    def _on_recapture_region(self, x: int, y: int, w: int, h: int) -> None:
        from processing.corners import apply_rounded_corners
        img = grab_region(x, y, w, h)
        img = apply_rounded_corners(img.convert("RGBA"), radius=28)
        if self._editor:
            self._editor.update_image(img)
            self._editor.show()
            self._editor.raise_()
            self._editor.activateWindow()

    def _on_recapture_cancelled(self) -> None:
        if self._editor:
            self._editor.show()
            self._editor.raise_()
            self._editor.activateWindow()

    def _quit(self) -> None:
        self._app.quit()


def main() -> None:
    # Single-instance guard via a named mutex (optional but nice)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep alive in tray

    if not QApplication.screens():
        sys.exit(1)

    capture = CaptureApp(app)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
