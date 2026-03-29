"""Rounded-corner alpha mask for PIL images."""
from __future__ import annotations

from PIL import Image, ImageDraw


def apply_rounded_corners(img: Image.Image, radius: int = 18) -> Image.Image:
    """
    Apply rounded corners to *img* with anti-aliased edges (4x supersampling).
    Returns an RGBA image; areas outside the corners are transparent.
    """
    img = img.convert("RGBA")
    w, h = img.size
    scale = 4
    big = Image.new("L", (w * scale, h * scale), 0)
    draw = ImageDraw.Draw(big)
    draw.rounded_rectangle(
        [(0, 0), (w * scale - 1, h * scale - 1)],
        radius=radius * scale,
        fill=255,
    )
    mask = big.resize((w, h), Image.LANCZOS)
    img.putalpha(mask)
    return img
