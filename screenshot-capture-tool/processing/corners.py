"""Rounded-corner alpha mask for PIL images."""
from __future__ import annotations

from PIL import Image, ImageChops, ImageDraw


def apply_rounded_corners(
    img: Image.Image,
    radius: int | None = None,
    border_width: int = 1,
    border_color: tuple[int, int, int, int] = (255, 255, 255, 82),
) -> Image.Image:
    """
    Apply rounded corners to *img* with anti-aliased edges (4x supersampling).
    The default radius adapts to the image size, and a subtle inner border
    keeps the edge defined against both light and dark backgrounds.
    Returns an RGBA image; areas outside the corners are transparent.
    """
    img = img.convert("RGBA")
    w, h = img.size
    if radius is None:
        radius = min(14, max(6, round(min(w, h) * 0.08)))

    scale = 4
    big = Image.new("L", (w * scale, h * scale), 0)
    draw = ImageDraw.Draw(big)
    draw.rounded_rectangle(
        [(0, 0), (w * scale - 1, h * scale - 1)],
        radius=radius * scale,
        fill=255,
    )
    mask = big.resize((w, h), Image.LANCZOS)
    img.putalpha(ImageChops.multiply(img.getchannel("A"), mask))

    if border_width > 0 and border_color[3] > 0:
        border_big = Image.new("L", big.size, 0)
        border_draw = ImageDraw.Draw(border_big)
        border_draw.rounded_rectangle(
            [(0, 0), (w * scale - 1, h * scale - 1)],
            radius=radius * scale,
            outline=255,
            width=max(1, border_width * scale),
        )
        border_mask = border_big.resize((w, h), Image.LANCZOS)
        border_alpha = border_mask.point(lambda value: value * border_color[3] // 255)
        border = Image.new("RGBA", (w, h), (*border_color[:3], 0))
        border.putalpha(border_alpha)
        img = Image.alpha_composite(img, border)

    return img
