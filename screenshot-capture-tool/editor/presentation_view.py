"""Preview wrapper that renders social-style screenshot backgrounds."""
from __future__ import annotations

from PyQt6.QtGui import QColor, QPainter, QPixmap
from PyQt6.QtWidgets import QWidget

from editor.canvas import AnnotationCanvas, _pil_to_qpixmap
from processing.presentation import (
    PresentationGeometry,
    PresentationSettings,
    compute_presentation_geometry,
    render_background,
)


class PresentationView(QWidget):
    """Shows the live annotation canvas on top of a generated background."""

    def __init__(self, canvas: AnnotationCanvas, parent=None) -> None:
        super().__init__(parent)
        self._canvas = canvas
        self._canvas.setParent(self)
        self._settings = PresentationSettings()
        self._geometry = PresentationGeometry(self._canvas.image_size(), (0, 0))
        self._background = QPixmap()
        self.setStyleSheet("background: #FFFFFF;")
        self._refresh_view()

    def settings(self) -> PresentationSettings:
        return PresentationSettings(
            enabled=self._settings.enabled,
            layout=self._settings.layout,
            style=self._settings.style,
            overlay_color=self._settings.overlay_color,
        )

    def output_size(self) -> tuple[int, int]:
        return self._geometry.canvas_size

    def set_enabled(self, enabled: bool) -> None:
        if self._settings.enabled == enabled:
            return
        self._settings.enabled = enabled
        self._refresh_view()

    def set_layout(self, layout: str) -> None:
        if self._settings.layout == layout:
            return
        self._settings.layout = layout  # type: ignore[assignment]
        self._refresh_view()

    def set_overlay_color(self, color: tuple[int, int, int]) -> None:
        if self._settings.overlay_color == color:
            return
        self._settings.overlay_color = color
        self._refresh_view()

    def refresh_for_image(self) -> None:
        self._refresh_view()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#FFFFFF"))
        if self._settings.enabled and not self._background.isNull():
            painter.drawPixmap(0, 0, self._background)

    def _refresh_view(self) -> None:
        self._geometry = compute_presentation_geometry(self._canvas.image_size(), self._settings)
        self.setFixedSize(*self._geometry.canvas_size)
        self._canvas.set_shadow_enabled(self._settings.enabled)
        self._canvas.move(*self._geometry.subject_pos)
        self._canvas.raise_()

        if self._settings.enabled:
            bg = render_background(
                self._canvas.base_image(),
                self._geometry.canvas_size,
                self._settings.style,
                self._settings.overlay_color,
            )
            self._background = _pil_to_qpixmap(bg)
        else:
            self._background = QPixmap()

        self.update()
