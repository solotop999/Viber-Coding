"""Presentation helpers for social-style screenshot backgrounds."""
from __future__ import annotations

import math
from functools import lru_cache
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

from core.paths import asset_path
from core.settings import is_local_background_image_path

PresentationLayout = Literal["fit", "wide", "post", "phone"]
PresentationStyle = Literal["color", "image1", "image2", "image3", "custom"]

_LAYOUT_RATIOS: dict[PresentationLayout, float] = {
    "fit": 1.0,
    "wide": 16 / 9,
    "post": 4 / 5,
    "phone": 9 / 16,
}

_FIT_PADDING = 36

_DEFAULT_BACKGROUND_COLOR = (180, 194, 220)
_ASSET_FILES = ("bg1.jpg", "bg2.jpg", "bg3.jpg")


@dataclass(slots=True)
class PresentationSettings:
    enabled: bool = True
    layout: PresentationLayout = "fit"
    style: PresentationStyle = "color"
    overlay_color: tuple[int, int, int] = _DEFAULT_BACKGROUND_COLOR
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
    frame = max(56, round(min(width, height) * 0.09))

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
    style: PresentationStyle,
    overlay_color: tuple[int, int, int] | None = None,
    background_image_path: str | None = None,
) -> Image.Image:
    """Build the blurred presentation background for preview/export."""
    if background_source.mode not in {"RGB", "RGBA"}:
        background_source = background_source.convert("RGBA")

    if style == "color":
        return Image.new("RGB", canvas_size, overlay_color or _DEFAULT_BACKGROUND_COLOR)

    fitted = _build_custom_background(canvas_size, background_image_path) if style == "custom" else None
    if fitted is None:
        fitted = _build_asset_background(canvas_size, style)
    if fitted is None:
        rgb_source = _flatten_source(background_source)
        fitted = ImageOps.fit(
            rgb_source,
            canvas_size,
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )

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
        settings.style,
        settings.overlay_color,
        settings.background_image_path,
    ).convert("RGBA")

    shadow = _render_shadow(subject.getchannel("A"), geometry.canvas_size, geometry.subject_pos)
    background.alpha_composite(shadow)
    background.alpha_composite(subject, geometry.subject_pos)
    return background


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

    return ImageOps.fit(
        assets[index],
        canvas_size,
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )


def _build_custom_background(
    canvas_size: tuple[int, int],
    background_image_path: str | None,
) -> Image.Image | None:
    if not is_local_background_image_path(background_image_path):
        return None

    custom = _load_custom_background(background_image_path)
    if custom is None:
        return None

    return ImageOps.fit(
        custom,
        canvas_size,
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
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
    shadow_pos = (subject_pos[0], subject_pos[1] + 14)
    mask.paste(alpha, shadow_pos, alpha)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=26))
    shadow = Image.new("RGBA", canvas_size, (7, 11, 18, 0))
    shadow.putalpha(mask.point(lambda value: min(255, int(value * 0.42))))
    return shadow
