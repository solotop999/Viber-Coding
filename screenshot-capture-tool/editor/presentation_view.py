"""Preview wrapper that renders social-style screenshot backgrounds."""
from __future__ import annotations

from PIL import Image
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPixmap
from PyQt6.QtWidgets import QLabel, QWidget

from editor.canvas import AnnotationCanvas, _pil_to_qpixmap
from processing.presentation import (
    PresentationGeometry,
    PresentationSettings,
    compute_presentation_geometry,
    render_background,
)


class PresentationView(QWidget):
    """Shows the live annotation canvas on top of a generated background."""
    _PREVIEW_MAX_DIMENSION = 1400

    def __init__(
        self,
        canvas: AnnotationCanvas,
        parent=None,
        settings: PresentationSettings | None = None,
    ) -> None:
        super().__init__(parent)
        self._canvas = canvas
        self._canvas.setParent(self)
        self._settings = settings or PresentationSettings()
        self._geometry = PresentationGeometry(self._canvas.image_size(), (0, 0))
        self._background = QPixmap()
        self._background_refresh_scheduled = False
        self._watermark_settings: dict = {}
        self._watermark = QLabel(self)
        self._watermark.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._watermark.setStyleSheet("background: transparent; color: rgba(255,255,255,140);")
        self._watermark.hide()
        self.setStyleSheet("background: #FFFFFF;")
        self._refresh_view(defer_background=True)

    def settings(self) -> PresentationSettings:
        return PresentationSettings(
            enabled=self._settings.enabled,
            layout=self._settings.layout,
            style=self._settings.style,
            overlay_color=self._settings.overlay_color,
            color_mode=self._settings.color_mode,
            gradient_preset=self._settings.gradient_preset,
            background_image_path=self._settings.background_image_path,
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

    def set_style(self, style: str) -> None:
        if self._settings.style == style:
            return
        self._settings.style = style  # type: ignore[assignment]
        self._refresh_view()

    def set_color_mode(self, mode: str) -> None:
        if self._settings.color_mode == mode:
            return
        self._settings.color_mode = mode  # type: ignore[assignment]
        self._refresh_view()

    def set_gradient_preset(self, preset: str) -> None:
        if self._settings.gradient_preset == preset:
            return
        self._settings.gradient_preset = preset  # type: ignore[assignment]
        self._refresh_view()

    def set_background_image_path(self, path: str | None) -> None:
        if self._settings.background_image_path == path:
            return
        self._settings.background_image_path = path
        self._refresh_view()

    def set_watermark_settings(self, settings: dict) -> None:
        self._watermark_settings = dict(settings)
        self._refresh_watermark()

    def refresh_for_image(self) -> None:
        self._refresh_view(defer_background=True)

    def set_settings(self, settings: PresentationSettings) -> None:
        self._settings = PresentationSettings(
            enabled=settings.enabled,
            layout=settings.layout,
            style=settings.style,
            overlay_color=settings.overlay_color,
            color_mode=settings.color_mode,
            gradient_preset=settings.gradient_preset,
            background_image_path=settings.background_image_path,
        )
        self._refresh_view()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#FFFFFF"))
        if self._settings.enabled and not self._background.isNull():
            painter.drawPixmap(0, 0, self._background)

    def _refresh_view(self, defer_background: bool = False) -> None:
        self._geometry = compute_presentation_geometry(self._canvas.image_size(), self._settings)
        self.setFixedSize(*self._geometry.canvas_size)
        self._canvas.set_shadow_enabled(self._settings.enabled)
        self._canvas.move(*self._geometry.subject_pos)
        self._canvas.raise_()

        if self._settings.enabled:
            if defer_background:
                self._background = QPixmap()
                self._schedule_background_refresh()
            else:
                self._refresh_background_now()
        else:
            self._background = QPixmap()

        self.update()
        self._refresh_watermark()

    def _refresh_watermark(self) -> None:
        text = str(self._watermark_settings.get("text", "")).strip()
        if not self._watermark_settings.get("enabled") or not text:
            self._watermark.hide()
            return
        available_below = self.height() - (
            self._geometry.subject_pos[1] + self._canvas.height()
        )
        if not self._settings.enabled or available_below < 12:
            self._watermark.hide()
            return
        size = max(8, min(20, round(min(self.width(), self.height()) * 0.02), available_below - 6))
        opacity = max(10, min(100, int(self._watermark_settings.get("opacity", 55))))
        self._watermark.setText(text)
        self._watermark.setFont(QFont("Segoe UI", size, QFont.Weight.Bold))
        self._watermark.setStyleSheet(
            f"background: transparent; color: rgba(255,255,255,{round(255 * opacity / 100)});"
        )
        self._watermark.adjustSize()
        margin = max(12, round(min(self.width(), self.height()) * 0.025))
        bottom_margin = 3
        x = self.width() - self._watermark.width() - margin
        y = self.height() - self._watermark.height() - bottom_margin
        self._watermark.move(max(0, x), max(0, y))
        self._watermark.show()
        self._watermark.raise_()

    def _schedule_background_refresh(self) -> None:
        if self._background_refresh_scheduled:
            return
        self._background_refresh_scheduled = True
        QTimer.singleShot(0, self._refresh_background_deferred)

    def _refresh_background_deferred(self) -> None:
        self._background_refresh_scheduled = False
        if not self._settings.enabled:
            return
        self._refresh_background_now()
        self.update()

    def _refresh_background_now(self) -> None:
        preview_size = self._preview_render_size(self._geometry.canvas_size)
        bg = render_background(
            self._canvas.base_image(),
            preview_size,
            self._settings,
        )
        if preview_size != self._geometry.canvas_size:
            bg = bg.resize(self._geometry.canvas_size, Image.Resampling.LANCZOS)
        self._background = _pil_to_qpixmap(bg)

    def _preview_render_size(self, canvas_size: tuple[int, int]) -> tuple[int, int]:
        width, height = canvas_size
        longest = max(width, height)
        if longest <= self._PREVIEW_MAX_DIMENSION:
            return canvas_size

        scale = self._PREVIEW_MAX_DIMENSION / longest
        return (
            max(1, round(width * scale)),
            max(1, round(height * scale)),
        )
