"""Local app settings persisted in a small JSON file."""
from __future__ import annotations

import json
import os
from pathlib import Path

_DEFAULT_PRESENTATION_BG = (180, 194, 220)
_SETTINGS_SUBDIR = "ScreenshotCaptureTool"
_SETTINGS_FILE = "settings.json"
_PRESENTATION_BG_KEY = "presentation_background_color"


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
