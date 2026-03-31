"""Image blur and secure redact helpers for Pillow images."""
from __future__ import annotations

from PIL import Image, ImageFilter


def gaussian_blur(img: Image.Image, radius: int = 20) -> Image.Image:
    """Return a blurred copy of *img*."""
    return img.filter(ImageFilter.GaussianBlur(radius=radius))


def blur_region(img: Image.Image, box: tuple[int, int, int, int],
                radius: int = 18) -> Image.Image:
    """
    Blur a rectangular sub-region of *img* in-place (returns a copy).
    box: (left, top, right, bottom) in image coordinates.
    """
    img = img.copy()
    region = img.crop(box)
    if region.width == 0 or region.height == 0:
        return img

    # Strong redact: pixelate first, then apply a final blur pass.
    shrink_w = max(1, region.width // 12)
    shrink_h = max(1, region.height // 12)
    blurred = region.resize((shrink_w, shrink_h), Image.Resampling.BILINEAR)
    blurred = blurred.resize(region.size, Image.Resampling.NEAREST)
    blurred = blurred.filter(ImageFilter.GaussianBlur(radius=radius))
    img.paste(blurred, box)
    return img


def redact_region(img: Image.Image, box: tuple[int, int, int, int]) -> Image.Image:
    """
    Apply a solid secure redact to *box*.
    The source pixels are overwritten with opaque black while preserving
    the original alpha channel when present.
    """
    img = img.copy()
    source_region = img.crop(box)
    if source_region.width == 0 or source_region.height == 0:
        return img

    redacted = Image.new("RGB", source_region.size, (0, 0, 0))
    if "A" in source_region.getbands():
        alpha = source_region.getchannel("A")
        redacted = redacted.convert("RGBA")
        redacted.putalpha(alpha)

    img.paste(redacted, box, redacted if redacted.mode == "RGBA" else None)
    return img
