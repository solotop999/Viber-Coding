"""
Fast multi-monitor screen capture using mss.
No network calls. Purely local.
"""
from __future__ import annotations

import mss
import mss.tools
from PIL import Image


def grab_all_monitors() -> tuple[Image.Image, tuple[int, int]]:
    """
    Capture all monitors into a single PIL Image.
    Returns (image, (virtual_left, virtual_top)) — the top-left origin
    of the virtual desktop bounding rect.
    """
    with mss.mss() as sct:
        # monitors[0] is the bounding box of all monitors combined
        monitor = sct.monitors[0]
        raw = sct.grab(monitor)
        img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
        return img, (monitor["left"], monitor["top"])


def grab_region(left: int, top: int, width: int, height: int) -> Image.Image:
    """Capture a specific screen region (absolute coordinates)."""
    with mss.mss() as sct:
        region = {"left": left, "top": top, "width": width, "height": height}
        raw = sct.grab(region)
        return Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
