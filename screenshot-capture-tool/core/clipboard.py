"""
Copy a PIL Image to the Windows clipboard.
Uses PyQt6's QGuiApplication.clipboard() which produces CF_DIB / CF_BITMAP
compatible data — works in Slack, Teams, browsers, etc.
"""
from __future__ import annotations

from PIL import Image
from PyQt6.QtGui import QImage, QGuiApplication
import io


def copy_to_clipboard(img: Image.Image) -> None:
    """
    Flatten RGBA onto white, then copy as QImage to clipboard.
    Flattening is necessary because most apps don't accept transparent PNGs
    from clipboard (CF_DIB has no alpha channel).
    """
    if img.mode == "RGBA":
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])
        img = background
    elif img.mode != "RGB":
        img = img.convert("RGB")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    data = buf.getvalue()

    qimg = QImage()
    qimg.loadFromData(data, "PNG")

    cb = QGuiApplication.clipboard()
    cb.setImage(qimg)
