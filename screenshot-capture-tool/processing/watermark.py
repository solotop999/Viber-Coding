"""Local-only text watermark rendering."""
from __future__ import annotations

from PIL import Image, ImageChops, ImageDraw, ImageFont


def apply_background_watermark(
    image: Image.Image,
    settings: dict,
    subject_box: tuple[int, int, int, int],
) -> Image.Image:
    """Add a faint diagonal ownership pattern only to background pixels."""
    text = str(settings.get("text", "")).strip()
    if not settings.get("enabled") or not text:
        return image

    result = image.convert("RGBA")
    width, height = result.size
    subject_x, subject_y, subject_width, subject_height = subject_box
    font_size = max(18, round(min(width, height) * 0.055))
    font = _load_font(font_size)

    probe = ImageDraw.Draw(Image.new("L", (1, 1)))
    bounds = probe.textbbox((0, 0), text, font=font, stroke_width=1)
    text_width = max(1, bounds[2] - bounds[0])
    text_height = max(1, bounds[3] - bounds[1])
    tile_width = text_width + max(54, font_size * 2)
    tile_height = text_height + max(36, font_size)
    tile = Image.new("RGBA", (tile_width, tile_height), (0, 0, 0, 0))
    tile_draw = ImageDraw.Draw(tile)
    # Intentionally capped: this mark should be discoverable, not distracting.
    configured = max(10, min(100, int(settings.get("opacity", 55))))
    alpha = max(10, min(25, round(255 * configured / 100 * 0.16)))
    tile_draw.text(
        (tile_width // 2, tile_height // 2),
        text,
        font=font,
        anchor="mm",
        fill=(255, 255, 255, alpha),
        stroke_width=1,
        stroke_fill=(0, 0, 0, max(5, alpha // 2)),
    )
    tile = tile.rotate(-24, resample=Image.Resampling.BICUBIC, expand=True)

    pattern = Image.new("RGBA", result.size, (0, 0, 0, 0))
    step_x = max(1, tile.width + font_size)
    step_y = max(1, tile.height + font_size // 2)
    for row, y in enumerate(range(-tile.height, height + tile.height, step_y)):
        offset = -(step_x // 2) if row % 2 else 0
        for x in range(-tile.width + offset, width + tile.width, step_x):
            pattern.alpha_composite(tile, (x, y))

    background_mask = Image.new("L", result.size, 255)
    ImageDraw.Draw(background_mask).rectangle(
        (
            subject_x,
            subject_y,
            subject_x + subject_width - 1,
            subject_y + subject_height - 1,
        ),
        fill=0,
    )
    pattern.putalpha(ImageChops.multiply(pattern.getchannel("A"), background_mask))
    result.alpha_composite(pattern)
    return result


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
    # Arial Bold does not contain Mathematical Alphanumeric Symbols such as
    # U+1D54F (𝕏). Segoe UI Symbol keeps those glyphs intact in Copy/Save.
    for name in ("seguisym.ttf", "cambria.ttc", "arialbd.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)
