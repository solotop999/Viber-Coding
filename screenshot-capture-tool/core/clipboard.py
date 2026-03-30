"""
Copy a PIL image to the Windows clipboard.

Uses PNG mime data so apps that support transparency can preserve
rounded corners and alpha.
"""
from __future__ import annotations

import io

from PIL import Image
from PyQt6.QtCore import QByteArray, QMimeData
from PyQt6.QtGui import QGuiApplication, QImage


def copy_to_clipboard(img: Image.Image) -> None:
    """
    Copy image as PNG mime data with alpha preserved when available.
    Apps that only read legacy bitmap clipboard formats may still flatten
    transparency on paste, but apps that support image/png can keep it.
    """
    if img.mode not in {"RGBA", "RGB"}:
        img = img.convert("RGBA")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    data = buffer.getvalue()

    qimg = QImage()
    qimg.loadFromData(data, "PNG")

    mime = QMimeData()
    mime.setData("image/png", QByteArray(data))
    mime.setImageData(qimg)

    clipboard = QGuiApplication.clipboard()
    clipboard.setMimeData(mime)
