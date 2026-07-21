"""Copy PIL images to the clipboard as PNG data."""
from __future__ import annotations

import io

from PIL import Image
from PyQt6.QtCore import QByteArray, QMimeData
from PyQt6.QtGui import QGuiApplication, QImage


def copy_to_clipboard(image: Image.Image) -> None:
    """Copy an image using Qt's standard cross-application clipboard support."""
    if image.mode not in {"RGB", "RGBA"}:
        image = image.convert("RGBA")

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    png_data = buffer.getvalue()

    qimage = QImage.fromData(png_data, "PNG")
    mime_data = QMimeData()
    mime_data.setData("image/png", QByteArray(png_data))
    mime_data.setImageData(qimage)
    QGuiApplication.clipboard().setMimeData(mime_data)
