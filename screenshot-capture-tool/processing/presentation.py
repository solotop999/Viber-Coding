"""Presentation helpers for social-style screenshot backgrounds."""
from __future__ import annotations

import math
from functools import lru_cache
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageOps

from core.paths import asset_path
from core.settings import is_local_background_image_path
from processing.corners import rounded_corner_radius

PresentationLayout = Literal["fit", "wide", "post", "phone"]
PresentationStyle = Literal["color", "image1", "image2", "image3", "custom"]
PresentationColorMode = Literal["solid", "gradient"]
PresentationGradientPreset = Literal[
    "peach",
    "mint",
    "dusk",
    "ocean",
    "rose",
    "lemon",
    "sunset",
    "berry",
    "royal",
    "apple_pink",
    "apple_peach",
    "apple_sky",
    "apple_mint",
    "apple_lilac",
    "apple_blue",
]

_LAYOUT_RATIOS: dict[PresentationLayout, float] = {
    "fit": 1.0,
    "wide": 16 / 9,
    "post": 4 / 5,
    "phone": 9 / 16,
}

_FIT_PADDING = 24
_FRAME_RATIO = 0.068
_MIN_FRAME = 44
_BACKGROUND_IMAGE_SCALE = 0.86

_DEFAULT_BACKGROUND_COLOR = (180, 194, 220)
_DEFAULT_COLOR_MODE: PresentationColorMode = "solid"
_DEFAULT_GRADIENT_PRESET: PresentationGradientPreset = "apple_sky"
_ASSET_FILES = ("bg1.jpg", "bg2.jpg", "bg3.jpg")
_GRADIENT_PRESETS: dict[PresentationGradientPreset, tuple[tuple[int, int, int], tuple[int, int, int], str]] = {
    "peach": ((255, 245, 232), (248, 190, 155), "vertical"),
    "mint": ((236, 255, 247), (118, 213, 185), "diag_up"),
    "dusk": ((240, 232, 255), (149, 138, 225), "diag_down"),
    "ocean": ((232, 245, 255), (77, 142, 219), "horizontal"),
    "rose": ((255, 250, 252), (236, 166, 196), "vertical"),
    "lemon": ((255, 255, 255), (247, 221, 125), "vertical"),
    "sunset": ((255, 242, 232), (238, 96, 63), "vertical"),
    "berry": ((255, 243, 248), (191, 66, 126), "vertical"),
    "royal": ((241, 236, 255), (95, 71, 196), "vertical"),
    "apple_pink": ((255, 255, 255), (245, 211, 225), "vertical"),
    "apple_peach": ((255, 255, 255), (249, 215, 187), "vertical"),
    "apple_sky": ((255, 255, 255), (199, 221, 248), "vertical"),
    "apple_mint": ((255, 255, 255), (198, 234, 221), "vertical"),
    "apple_lilac": ((255, 255, 255), (218, 209, 242), "vertical"),
    "apple_blue": ((252, 253, 255), (171, 196, 232), "vertical"),
}


@dataclass(slots=True)
class PresentationSettings:
    enabled: bool = True
    layout: PresentationLayout = "fit"
    style: PresentationStyle = "color"
    overlay_color: tuple[int, int, int] = _DEFAULT_BACKGROUND_COLOR
    color_mode: PresentationColorMode = _DEFAULT_COLOR_MODE
    gradient_preset: PresentationGradientPreset = "apple_sky"
    background_image_path: str | None = None


@dataclass(slots=True)
class PresentationGeometry:
    canvas_size: tuple[int, int]
    subject_pos: tuple[int, int]


def compute_presentation_geometry(
    subject_size: tuple[int, int],
    settings: PresentationSettings,
) -> PresentationGeometry:
    """Return output canvas size and top-left subject position."""
    width, height = subject_size
    if not settings.enabled:
        return PresentationGeometry((width, height), (0, 0))

    if settings.layout == "fit":
        canvas_width = width + _FIT_PADDING * 2
        canvas_height = height + _FIT_PADDING * 2
        return PresentationGeometry((canvas_width, canvas_height), (_FIT_PADDING, _FIT_PADDING))

    ratio = _LAYOUT_RATIOS[settings.layout]
    frame = max(_MIN_FRAME, round(min(width, height) * _FRAME_RATIO))

    min_width = width + frame * 2
    min_height = height + frame * 2

    if min_width / min_height >= ratio:
        canvas_width = min_width
        canvas_height = math.ceil(canvas_width / ratio)
    else:
        canvas_height = min_height
        canvas_width = math.ceil(canvas_height * ratio)

    subject_x = (canvas_width - width) // 2
    subject_y = (canvas_height - height) // 2
    return PresentationGeometry((canvas_width, canvas_height), (subject_x, subject_y))


def render_background(
    background_source: Image.Image,
    canvas_size: tuple[int, int],
    settings: PresentationSettings,
) -> Image.Image:
    """Build the blurred presentation background for preview/export."""
    if background_source.mode not in {"RGB", "RGBA"}:
        background_source = background_source.convert("RGBA")

    if settings.style == "color":
        if settings.color_mode == "gradient":
            return render_gradient_background(canvas_size, settings.gradient_preset)
        return Image.new("RGB", canvas_size, settings.overlay_color or _DEFAULT_BACKGROUND_COLOR)

    fitted = _build_custom_background(canvas_size, settings.background_image_path) if settings.style == "custom" else None
    if fitted is None:
        fitted = _build_asset_background(canvas_size, settings.style)
    if fitted is None:
        rgb_source = _flatten_source(background_source)
        fitted = _build_zoomed_background(rgb_source, canvas_size)

    blur_radius = max(6, round(min(canvas_size) * 0.01))
    blurred = fitted.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    blurred = ImageEnhance.Color(blurred).enhance(1.18)
    blurred = ImageEnhance.Contrast(blurred).enhance(1.08)
    blurred = ImageEnhance.Brightness(blurred).enhance(0.94)
    return _apply_soft_focus(blurred)


def compose_presentation(
    subject_image: Image.Image,
    background_source: Image.Image,
    settings: PresentationSettings,
) -> Image.Image:
    """Render the final social-style image from a subject image."""
    subject = subject_image.convert("RGBA")
    if not settings.enabled:
        return subject

    geometry = compute_presentation_geometry(subject.size, settings)
    background = render_background(
        background_source,
        geometry.canvas_size,
        settings,
    ).convert("RGBA")

    shadow = _render_shadow(subject.getchannel("A"), geometry.canvas_size, geometry.subject_pos)
    neon_glow, neon_core = render_neon_frame(
        geometry.canvas_size,
        geometry.subject_pos,
        subject.size,
    )
    background.alpha_composite(shadow)
    background.alpha_composite(neon_glow)
    background.alpha_composite(subject, geometry.subject_pos)
    background.alpha_composite(neon_core)
    return background


def render_neon_frame(
    canvas_size: tuple[int, int],
    subject_pos: tuple[int, int],
    subject_size: tuple[int, int],
) -> tuple[Image.Image, Image.Image]:
    """Return separate glow and crisp border layers for a screenshot."""
    x, y = subject_pos
    width, height = subject_size
    empty = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    if width < 4 or height < 4:
        return empty, empty.copy()

    stroke = max(3, round(min(width, height) * 0.004))
    radius = rounded_corner_radius(subject_size)
    box = (x, y, x + width - 1, y + height - 1)

    ring_mask = _render_rounded_mask(
        canvas_size,
        subject_pos,
        subject_size,
        radius,
        outline_width=stroke,
    )

    gradient = _render_neon_gradient(canvas_size)

    # Build the bloom from wider source bands. Blurring the thin core directly
    # makes the halo disappear on detailed backgrounds.
    scale = min(width, height)
    tight_width = max(3, round(scale * 0.005))
    broad_width = max(6, round(scale * 0.010))
    tight_source = Image.new("L", canvas_size, 0)
    broad_source = Image.new("L", canvas_size, 0)
    ImageDraw.Draw(tight_source).rounded_rectangle(
        box,
        radius=radius,
        outline=255,
        width=tight_width,
    )
    ImageDraw.Draw(broad_source).rounded_rectangle(
        box,
        radius=radius,
        outline=220,
        width=broad_width,
    )

    broad_blur = min(9, max(5, round(scale * 0.010)))
    tight_blur = min(4, max(2, round(scale * 0.004)))
    broad_mask = broad_source.filter(ImageFilter.GaussianBlur(broad_blur))
    tight_mask = tight_source.filter(ImageFilter.GaussianBlur(tight_blur))

    broad_glow = gradient.copy()
    broad_glow.putalpha(broad_mask.point(lambda value: min(255, round(value * 1.05))))
    tight_glow = gradient.copy()
    tight_glow.putalpha(tight_mask.point(lambda value: min(255, round(value * 1.18))))
    glow = Image.alpha_composite(broad_glow, tight_glow)

    # Keep a restrained part of the bloom inside the rounded screenshot. This
    # is composited after the subject, while the outer glow stays behind it.
    subject_mask = _render_rounded_mask(
        canvas_size,
        subject_pos,
        subject_size,
        radius,
        filled=True,
    )
    inner_broad = broad_mask.point(lambda value: min(255, round(value * 0.48)))
    inner_tight = tight_mask.point(lambda value: min(255, round(value * 0.82)))
    inner_mask = ImageChops.multiply(ImageChops.lighter(inner_broad, inner_tight), subject_mask)
    inner_glow = gradient.copy()
    inner_glow.putalpha(inner_mask)

    colored_core = gradient.copy()
    colored_core.putalpha(ring_mask)
    core = Image.alpha_composite(inner_glow, colored_core)

    # The white-hot center is intentionally much thinner than the colored
    # shoulders. A full-width white mask makes the tube look like a flat line.
    hot_mask = _render_rounded_mask(
        canvas_size,
        subject_pos,
        subject_size,
        radius,
        outline_width=max(2, stroke // 2),
        opacity=225,
    )
    highlight = Image.new("RGBA", canvas_size, (249, 252, 255, 0))
    highlight.putalpha(hot_mask)
    core = Image.alpha_composite(core, highlight)
    return glow, core


def _render_rounded_mask(
    canvas_size: tuple[int, int],
    subject_pos: tuple[int, int],
    subject_size: tuple[int, int],
    radius: int,
    *,
    outline_width: int = 0,
    opacity: int = 255,
    filled: bool = False,
) -> Image.Image:
    """Render an anti-aliased rounded mask at 4x, limited to the subject."""
    width, height = subject_size
    scale = 4
    large_size = (max(1, width * scale), max(1, height * scale))
    large = Image.new("L", large_size, 0)
    draw = ImageDraw.Draw(large)
    kwargs = {"radius": radius * scale}
    if filled:
        kwargs["fill"] = opacity
    else:
        kwargs["outline"] = opacity
        kwargs["width"] = max(1, outline_width * scale)
    draw.rounded_rectangle(
        (0, 0, large_size[0] - 1, large_size[1] - 1),
        **kwargs,
    )
    local = large.resize(subject_size, Image.Resampling.LANCZOS)
    mask = Image.new("L", canvas_size, 0)
    mask.paste(local, subject_pos)
    return mask


def _render_neon_gradient(canvas_size: tuple[int, int]) -> Image.Image:
    """Render a compact angular color map, then scale it to the output."""
    width, height = canvas_size
    longest = max(width, height)
    sample_width = max(2, round(width * min(1.0, 256 / longest)))
    sample_height = max(2, round(height * min(1.0, 256 / longest)))
    gradient = Image.new("RGBA", (sample_width, sample_height))
    pixels = gradient.load()
    stops = (
        (0.00, (82, 151, 255)),
        (0.13, (145, 72, 255)),
        (0.25, (229, 74, 255)),
        (0.43, (219, 67, 255)),
        (0.56, (121, 91, 255)),
        (0.68, (54, 190, 255)),
        (0.78, (58, 143, 255)),
        (0.89, (146, 68, 255)),
        (1.00, (82, 151, 255)),
    )
    center_x = (sample_width - 1) / 2
    center_y = (sample_height - 1) / 2
    norm_x = max(1.0, sample_width / 2)
    norm_y = max(1.0, sample_height / 2)
    for py in range(sample_height):
        dy = (py - center_y) / norm_y
        for px in range(sample_width):
            dx = (px - center_x) / norm_x
            position = (math.atan2(dx, -dy) / (2 * math.pi)) % 1.0
            for index in range(1, len(stops)):
                end_stop, end_color = stops[index]
                if position <= end_stop:
                    start_stop, start_color = stops[index - 1]
                    mix = (position - start_stop) / max(0.0001, end_stop - start_stop)
                    pixels[px, py] = (*_blend_rgb(start_color, end_color, mix), 255)
                    break
    return gradient.resize(canvas_size, Image.Resampling.BICUBIC)


def _flatten_source(img: Image.Image) -> Image.Image:
    avg_color = img.convert("RGBA").resize((1, 1), Image.Resampling.BILINEAR).getpixel((0, 0))
    backdrop = Image.new("RGB", img.size, avg_color[:3])
    if "A" in img.getbands():
        backdrop.paste(img.convert("RGB"), mask=img.getchannel("A"))
    else:
        backdrop.paste(img.convert("RGB"))
    return backdrop


@lru_cache(maxsize=1)
def _load_asset_backgrounds() -> tuple[Image.Image, ...]:
    images: list[Image.Image] = []
    for name in _ASSET_FILES:
        path = asset_path(name)
        if not path.exists():
            continue
        with Image.open(path) as image:
            images.append(image.convert("RGB"))
    return tuple(images)


@lru_cache(maxsize=4)
def _load_custom_background(path: str) -> Image.Image | None:
    image_path = Path(path)
    if not image_path.exists():
        return None

    try:
        with Image.open(image_path) as image:
            return image.convert("RGB")
    except (OSError, ValueError):
        return None


def _build_asset_background(
    canvas_size: tuple[int, int],
    style: PresentationStyle,
) -> Image.Image | None:
    assets = _load_asset_backgrounds()
    if not assets:
        return None

    if style == "image1":
        index = 0
    elif style == "image2":
        index = 1
    else:
        index = 2

    if len(assets) <= index:
        index = 0

    return _build_zoomed_background(assets[index], canvas_size)


def _build_custom_background(
    canvas_size: tuple[int, int],
    background_image_path: str | None,
) -> Image.Image | None:
    if not is_local_background_image_path(background_image_path):
        return None

    custom = _load_custom_background(background_image_path)
    if custom is None:
        return None

    return _build_zoomed_background(custom, canvas_size)


def _build_zoomed_background(
    image: Image.Image,
    canvas_size: tuple[int, int],
) -> Image.Image:
    base = ImageOps.fit(
        image,
        canvas_size,
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )
    scaled_size = (
        max(1, round(canvas_size[0] * _BACKGROUND_IMAGE_SCALE)),
        max(1, round(canvas_size[1] * _BACKGROUND_IMAGE_SCALE)),
    )
    contained = ImageOps.contain(
        image,
        scaled_size,
        method=Image.Resampling.LANCZOS,
    )
    offset = (
        (canvas_size[0] - contained.width) // 2,
        (canvas_size[1] - contained.height) // 2,
    )
    base.paste(contained, offset)
    return base


def render_gradient_background(
    canvas_size: tuple[int, int],
    preset: PresentationGradientPreset,
) -> Image.Image:
    start_color, end_color, direction = _GRADIENT_PRESETS.get(
        preset,
        _GRADIENT_PRESETS[_DEFAULT_GRADIENT_PRESET],
    )
    width, height = canvas_size
    gradient = Image.new("RGB", canvas_size)
    pixels = gradient.load()
    max_x = max(1, width - 1)
    max_y = max(1, height - 1)

    for y in range(height):
        y_ratio = y / max_y
        for x in range(width):
            x_ratio = x / max_x
            if direction == "horizontal":
                mix = x_ratio
            elif direction == "diag_up":
                mix = (x_ratio + (1.0 - y_ratio)) * 0.5
            elif direction == "diag_down":
                mix = (x_ratio + y_ratio) * 0.5
            else:
                mix = y_ratio
            pixels[x, y] = _blend_rgb(start_color, end_color, mix)

    return gradient


def _blend_rgb(
    start_color: tuple[int, int, int],
    end_color: tuple[int, int, int],
    mix: float,
) -> tuple[int, int, int]:
    ratio = max(0.0, min(1.0, mix))
    return tuple(
        round(start + (end - start) * ratio)
        for start, end in zip(start_color, end_color)
    )


def _apply_soft_focus(image: Image.Image) -> Image.Image:
    glow = image.filter(ImageFilter.GaussianBlur(radius=2))
    return Image.blend(image, glow, 0.01)


def _render_shadow(
    alpha: Image.Image,
    canvas_size: tuple[int, int],
    subject_pos: tuple[int, int],
) -> Image.Image:
    mask = Image.new("L", canvas_size, 0)
    shadow_pos = (subject_pos[0], subject_pos[1] + 8)
    mask.paste(alpha, shadow_pos, alpha)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=18))
    shadow = Image.new("RGBA", canvas_size, (7, 11, 18, 0))
    shadow.putalpha(mask.point(lambda value: min(255, int(value * 0.30))))
    return shadow
