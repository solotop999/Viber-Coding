"""
Frosted-glass background blur composite.

Two modes
---------
MODE_FOCUS_RECT
    The user picks a "focus rectangle" inside the captured image.
    Everything outside that rect is blurred; the rect stays sharp.
    A feathered mask creates a soft depth-of-field transition.

MODE_PADDED_CANVAS
    The captured image is placed on a larger padded canvas whose
    background is a heavily blurred + darkened version of the image.
    This gives the "floating card on blurred background" look shown
    in the example screenshot.
"""
from __future__ import annotations

from PIL import Image, ImageDraw, ImageFilter

MODE_FOCUS_RECT    = "focus_rect"
MODE_PADDED_CANVAS = "padded_canvas"


def apply_focus_blur(
    img: Image.Image,
    focus_box: tuple[int, int, int, int],
    blur_radius: int = 28,
    feather: int = 12,
) -> Image.Image:
    """
    Blur everything outside *focus_box* (left, top, right, bottom).
    Returns an RGB image the same size as *img*.
    """
    img = img.convert("RGB")
    blurred = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    # Mask: white = keep sharp, black = use blurred
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rectangle(focus_box, fill=255)
    if feather > 0:
        mask = mask.filter(ImageFilter.GaussianBlur(radius=feather))

    return Image.composite(img, blurred, mask)


def apply_padded_canvas(
    img: Image.Image,
    padding: int = 60,
    blur_radius: int = 40,
    corner_radius: int = 18,
    bg_darken: float = 0.45,
) -> Image.Image:
    """
    Place *img* (with rounded corners) on a blurred + darkened background.
    Returns an RGBA image that is (w + 2*padding) × (h + 2*padding).

    This produces the "modal card on blurred background" effect.
    """
    from processing.corners import apply_rounded_corners

    w, h = img.size
    canvas_w, canvas_h = w + padding * 2, h + padding * 2

    # Build background: scale up, blur, darken
    bg = img.convert("RGB").resize((canvas_w, canvas_h), Image.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    # Darken background
    dark_overlay = Image.new("RGB", bg.size, (0, 0, 0))
    bg = Image.blend(bg, dark_overlay, alpha=bg_darken)

    # Rounded-corner foreground
    fg = apply_rounded_corners(img.convert("RGBA"), radius=corner_radius)

    # Compose
    result = bg.convert("RGBA")
    result.paste(fg, (padding, padding), mask=fg.split()[3])
    return result
