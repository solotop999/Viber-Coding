"""Helpers for locating bundled runtime assets."""
from __future__ import annotations

import sys
from pathlib import Path


def app_base_dir() -> Path:
    bundle_dir = getattr(sys, "_MEIPASS", None)
    if bundle_dir:
        return Path(bundle_dir)
    return Path(__file__).resolve().parent.parent


def asset_path(name: str) -> Path:
    return app_base_dir() / "assets" / name
