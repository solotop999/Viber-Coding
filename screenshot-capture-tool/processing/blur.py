"""Image blur and irreversible-looking redact helpers for Pillow images."""
from __future__ import annotations

import random

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


def redact_region(img: Image.Image, box: tuple[int, int, int, int],
                  cell_size: int = 12, palette_size: int = 24) -> Image.Image:
    """
    Apply a blocky, shuffled mosaic redact to *box*.
    The effect is deterministic for the same region, and is intended
    to be much harder to visually recover than a plain blur.
    """
    img = img.copy()
    source_region = img.crop(box)
    region = source_region.convert("RGB")
    if region.width == 0 or region.height == 0:
        return img

    coarse_w = max(1, region.width // cell_size)
    coarse_h = max(1, region.height // cell_size)

    mosaic = region.resize((coarse_w, coarse_h), Image.Resampling.BILINEAR)
    mosaic = mosaic.convert("P", palette=Image.Palette.ADAPTIVE, colors=palette_size).convert("RGB")

    shuffled = Image.new("RGB", (coarse_w, coarse_h))
    tile_positions = [(x, y) for y in range(coarse_h) for x in range(coarse_w)]
    source_positions = tile_positions[:]

    seed = (
        box[0] * 73856093
        ^ box[1] * 19349663
        ^ box[2] * 83492791
        ^ box[3] * 15485863
        ^ region.width * 31
        ^ region.height * 17
    )
    random.Random(seed).shuffle(source_positions)

    for (dst_x, dst_y), (src_x, src_y) in zip(tile_positions, source_positions):
        shuffled.putpixel((dst_x, dst_y), mosaic.getpixel((src_x, src_y)))

    redacted = shuffled.resize(region.size, Image.Resampling.NEAREST)
    if "A" in source_region.getbands():
        alpha = source_region.getchannel("A")
        redacted = redacted.convert("RGBA")
        redacted.putalpha(alpha)

    img.paste(redacted, box, redacted if redacted.mode == "RGBA" else None)
    return img
