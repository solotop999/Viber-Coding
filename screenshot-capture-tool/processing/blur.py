"""Gaussian blur helpers for Pillow images."""
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
    blurred = region.filter(ImageFilter.GaussianBlur(radius=radius))
    img.paste(blurred, box)
    return img
