"""Local-only text watermark rendering."""
from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont


def apply_text_watermark(
    image: Image.Image,
    settings: dict,
    subject_box: tuple[int, int, int, int] | None = None,
) -> Image.Image:
    text = str(settings.get("text", "")).strip()
    if not settings.get("enabled") or not text:
        return image

    result = image.convert("RGBA")
    width, height = result.size
    # Keep the mark compact and, when a subject box is supplied, small enough
    # to fit entirely inside the background strip below the screenshot.
    available_below = height - (subject_box[1] + subject_box[3]) if subject_box else height
    font_size = max(8, min(20, round(min(width, height) * 0.02), available_below - 6))
    if available_below < 12:
        return result
    font = _load_font(font_size)
    draw = ImageDraw.Draw(result)
    box = draw.textbbox((0, 0), text, font=font, stroke_width=1)
    text_width, text_height = box[2] - box[0], box[3] - box[1]
    margin = max(12, round(min(width, height) * 0.025))
    bottom_margin = 3
    x = max(margin, width - text_width - margin)
    y = max(0, height - text_height - bottom_margin)
    opacity = max(10, min(100, int(settings.get("opacity", 55))))
    alpha = round(255 * opacity / 100)
    draw.text(
        (x, y), text, font=font, fill=(255, 255, 255, alpha),
        stroke_width=1, stroke_fill=(0, 0, 0, min(190, alpha)),
    )
    return result


def _load_font(size: int):
    # Arial is available on supported Windows installations. Pillow's bundled
    # fallback keeps export working if the system font is unavailable.
    try:
        return ImageFont.truetype("arialbd.ttf", size)
    except OSError:
        return ImageFont.load_default(size=size)
