"""
System tray icon with right-click menu.
No network calls. Purely local.
"""
from __future__ import annotations

from typing import Callable

from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication


def _make_default_icon(size: int = 32) -> QIcon:
    """Generate a simple 'C' icon if no icon file is present."""
    px = QPixmap(size, size)
    px.fill(QColor("#5B5BFF"))
    p = QPainter(px)
    p.setPen(QColor("white"))
    p.setFont(QFont("Arial", 14, QFont.Weight.Bold))
    p.drawText(px.rect(), 0x0084, "C")  # AlignCenter
    p.end()
    return QIcon(px)


class TrayIcon(QSystemTrayIcon):
    def __init__(self, on_capture: Callable, on_quit: Callable,
                 icon_path: str | None = None) -> None:
        icon = QIcon(icon_path) if icon_path else _make_default_icon()
        super().__init__(icon)

        self.setToolTip("Capture — Ctrl+Shift+X to screenshot")

        menu = QMenu()
        capture_action = menu.addAction("Capture  (Ctrl+Shift+X)")
        capture_action.triggered.connect(on_capture)
        menu.addSeparator()
        quit_action = menu.addAction("Exit")
        quit_action.triggered.connect(on_quit)

        self.setContextMenu(menu)
        self.activated.connect(self._on_activated)
        self._on_capture = on_capture

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._on_capture()
