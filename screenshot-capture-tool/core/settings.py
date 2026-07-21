"""Local app settings persisted in a small JSON file."""
from __future__ import annotations

import json
import os
from pathlib import Path, PureWindowsPath

_DEFAULT_PRESENTATION_BG = (180, 194, 220)
_DEFAULT_PRESENTATION_STYLE = "color"
_DEFAULT_PRESENTATION_COLOR_MODE = "solid"
_DEFAULT_PRESENTATION_GRADIENT_PRESET = "apple_sky"
_SETTINGS_SUBDIR = "ScreenshotCaptureTool"
_SETTINGS_FILE = "settings.json"
_PRESENTATION_BG_KEY = "presentation_background_color"
_PRESENTATION_STYLE_KEY = "presentation_background_style"
_PRESENTATION_COLOR_MODE_KEY = "presentation_background_color_mode"
_PRESENTATION_GRADIENT_PRESET_KEY = "presentation_background_gradient_preset"
_PRESENTATION_IMAGE_KEY = "presentation_background_image"
_WATERMARK_KEY = "watermark"
_ICON_VISIBLE_KEY = "icon_visible"
_ICON_SIZE_KEY = "icon_size"

_DEFAULT_WATERMARK = {
    "enabled": True,
    "text": "𝕏: @solotop999",
    "position": "bottom_right",
    "opacity": 55,
}


def is_local_background_image_path(path: str | None) -> bool:
    if not isinstance(path, str):
        return False

    candidate = path.strip()
    if not candidate or "://" in candidate:
        return False

    windows_path = PureWindowsPath(candidate)
    if candidate.startswith("\\\\") or str(windows_path.drive).startswith("\\\\"):
        return False

    return Path(candidate).is_absolute()


def load_presentation_background_color() -> tuple[int, int, int]:
    data = _read_settings()
    raw = data.get(_PRESENTATION_BG_KEY)
    if not isinstance(raw, list) or len(raw) != 3:
        return _DEFAULT_PRESENTATION_BG

    try:
        red, green, blue = [max(0, min(255, int(part))) for part in raw]
    except (TypeError, ValueError):
        return _DEFAULT_PRESENTATION_BG
    return red, green, blue


def save_presentation_background_color(color: tuple[int, int, int]) -> None:
    red, green, blue = [max(0, min(255, int(channel))) for channel in color]
    data = _read_settings()
    data[_PRESENTATION_BG_KEY] = [red, green, blue]
    payload = json.dumps(data, indent=2)

    for settings_path in (_preferred_settings_path(), _fallback_settings_path()):
        try:
            settings_path.parent.mkdir(parents=True, exist_ok=True)
            settings_path.write_text(payload, encoding="utf-8")
            return
        except OSError:
            continue


def load_presentation_background_style() -> str:
    data = _read_settings()
    raw = data.get(_PRESENTATION_STYLE_KEY)
    if isinstance(raw, str) and raw in {"color", "image1", "image2", "image3", "custom"}:
        return raw
    return _DEFAULT_PRESENTATION_STYLE


def save_presentation_background_style(style: str) -> None:
    if style not in {"color", "image1", "image2", "image3", "custom"}:
        style = _DEFAULT_PRESENTATION_STYLE

    data = _read_settings()
    data[_PRESENTATION_STYLE_KEY] = style
    payload = json.dumps(data, indent=2)

    for settings_path in (_preferred_settings_path(), _fallback_settings_path()):
        try:
            settings_path.parent.mkdir(parents=True, exist_ok=True)
            settings_path.write_text(payload, encoding="utf-8")
            return
        except OSError:
            continue


def load_presentation_background_color_mode() -> str:
    data = _read_settings()
    raw = data.get(_PRESENTATION_COLOR_MODE_KEY)
    if isinstance(raw, str) and raw in {"solid", "gradient"}:
        return raw
    return _DEFAULT_PRESENTATION_COLOR_MODE


def save_presentation_background_color_mode(mode: str) -> None:
    if mode not in {"solid", "gradient"}:
        mode = _DEFAULT_PRESENTATION_COLOR_MODE

    data = _read_settings()
    data[_PRESENTATION_COLOR_MODE_KEY] = mode
    payload = json.dumps(data, indent=2)

    for settings_path in (_preferred_settings_path(), _fallback_settings_path()):
        try:
            settings_path.parent.mkdir(parents=True, exist_ok=True)
            settings_path.write_text(payload, encoding="utf-8")
            return
        except OSError:
            continue


def load_presentation_background_gradient_preset() -> str:
    data = _read_settings()
    raw = data.get(_PRESENTATION_GRADIENT_PRESET_KEY)
    if isinstance(raw, str) and raw in {
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
    }:
        return raw
    return _DEFAULT_PRESENTATION_GRADIENT_PRESET


def save_presentation_background_gradient_preset(preset: str) -> None:
    if preset not in {
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
    }:
        preset = _DEFAULT_PRESENTATION_GRADIENT_PRESET

    data = _read_settings()
    data[_PRESENTATION_GRADIENT_PRESET_KEY] = preset
    payload = json.dumps(data, indent=2)

    for settings_path in (_preferred_settings_path(), _fallback_settings_path()):
        try:
            settings_path.parent.mkdir(parents=True, exist_ok=True)
            settings_path.write_text(payload, encoding="utf-8")
            return
        except OSError:
            continue


def load_presentation_background_image() -> str | None:
    data = _read_settings()
    raw = data.get(_PRESENTATION_IMAGE_KEY)
    if is_local_background_image_path(raw):
        return raw
    return None


def save_presentation_background_image(path: str | None) -> None:
    data = _read_settings()
    if is_local_background_image_path(path):
        data[_PRESENTATION_IMAGE_KEY] = path
    else:
        data.pop(_PRESENTATION_IMAGE_KEY, None)

    payload = json.dumps(data, indent=2)
    for settings_path in (_preferred_settings_path(), _fallback_settings_path()):
        try:
            settings_path.parent.mkdir(parents=True, exist_ok=True)
            settings_path.write_text(payload, encoding="utf-8")
            return
        except OSError:
            continue


def load_icon_size() -> int:
    """Return the saved longest edge of the image icon in pixels."""
    raw = _read_settings().get(_ICON_SIZE_KEY, 77)
    try:
        return max(24, min(4096, int(raw)))
    except (TypeError, ValueError):
        return 77


def save_icon_size(size: int) -> None:
    """Persist the validated longest edge of the image icon."""
    data = _read_settings()
    data[_ICON_SIZE_KEY] = max(24, min(4096, int(size)))
    payload = json.dumps(data, indent=2, ensure_ascii=False)
    for settings_path in (_preferred_settings_path(), _fallback_settings_path()):
        try:
            settings_path.parent.mkdir(parents=True, exist_ok=True)
            settings_path.write_text(payload, encoding="utf-8")
            return
        except OSError:
            continue

def load_icon_visible() -> bool:
    """Return whether the image icon should be shown."""
    raw = _read_settings().get(_ICON_VISIBLE_KEY, True)
    return raw if isinstance(raw, bool) else True


def save_icon_visible(visible: bool) -> None:
    """Persist the image-icon visibility preference."""
    data = _read_settings()
    data[_ICON_VISIBLE_KEY] = bool(visible)
    payload = json.dumps(data, indent=2, ensure_ascii=False)
    for settings_path in (_preferred_settings_path(), _fallback_settings_path()):
        try:
            settings_path.parent.mkdir(parents=True, exist_ok=True)
            settings_path.write_text(payload, encoding="utf-8")
            return
        except OSError:
            continue

def load_watermark_settings() -> dict:
    """Load and validate the local text-watermark preferences."""
    raw = _read_settings().get(_WATERMARK_KEY)
    if not isinstance(raw, dict):
        return dict(_DEFAULT_WATERMARK)

    text = raw.get("text")
    if not isinstance(text, str):
        text = _DEFAULT_WATERMARK["text"]
    text = text.strip()[:200]

    position = raw.get("position")
    if position not in {"top_left", "top_right", "bottom_left", "bottom_right"}:
        position = _DEFAULT_WATERMARK["position"]

    try:
        opacity = max(10, min(100, int(raw.get("opacity", 55))))
    except (TypeError, ValueError):
        opacity = 55

    return {
        "enabled": bool(raw.get("enabled", True)) and bool(text),
        "text": text,
        "position": position,
        "opacity": opacity,
    }


def save_watermark_settings(settings: dict) -> None:
    """Persist only validated primitive values; no external resources are loaded."""
    position = settings.get("position", "bottom_right")
    if position not in {"top_left", "top_right", "bottom_left", "bottom_right"}:
        position = "bottom_right"
    text = str(settings.get("text", "")).strip()[:200]
    try:
        opacity = max(10, min(100, int(settings.get("opacity", 55))))
    except (TypeError, ValueError):
        opacity = 55

    data = _read_settings()
    data[_WATERMARK_KEY] = {
        "enabled": bool(settings.get("enabled", False)) and bool(text),
        "text": text,
        "position": position,
        "opacity": opacity,
    }
    payload = json.dumps(data, indent=2, ensure_ascii=False)
    for settings_path in (_preferred_settings_path(), _fallback_settings_path()):
        try:
            settings_path.parent.mkdir(parents=True, exist_ok=True)
            settings_path.write_text(payload, encoding="utf-8")
            return
        except OSError:
            continue


def _preferred_settings_path() -> Path:
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        return Path(local_appdata) / _SETTINGS_SUBDIR / _SETTINGS_FILE
    return Path.home() / f".{_SETTINGS_SUBDIR.lower()}" / _SETTINGS_FILE


def _fallback_settings_path() -> Path:
    return Path(__file__).resolve().parent.parent / ".screenshot-tool-settings.json"


def _read_settings() -> dict:
    for settings_path in (_preferred_settings_path(), _fallback_settings_path()):
        if not settings_path.exists():
            continue

        try:
            data = json.loads(settings_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict):
            return data
    return {}
