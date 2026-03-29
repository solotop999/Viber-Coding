"""
Global hotkey using Win32 RegisterHotKey via ctypes.

SECURITY: This uses RegisterHotKey (WM_HOTKEY) — Windows only fires a message
when the *exact* registered combination is pressed. It does NOT install a
low-level keyboard hook and does NOT read any other keystrokes.
No third-party library needed.
"""
from __future__ import annotations

import ctypes
import threading
from ctypes import wintypes
from typing import Callable

user32 = ctypes.windll.user32

WM_HOTKEY   = 0x0312
MOD_ALT     = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT   = 0x0004
MOD_WIN     = 0x0008

# Virtual key codes
VK_MAP = {c: ord(c) for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"}
VK_MAP.update({
    "F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73,
    "F5": 0x74, "F6": 0x75, "F7": 0x76, "F8": 0x77,
    "F9": 0x78, "F10": 0x79, "F11": 0x7A, "F12": 0x7B,
    "PRINT": 0x2C, "HOME": 0x24, "END": 0x23,
})


class HotkeyManager:
    """
    Register one or more global hotkeys. Each runs its callback on a
    daemon thread so the Qt event loop is not blocked.

    Usage:
        mgr = HotkeyManager()
        mgr.register("ctrl+shift+x", on_capture)
        mgr.start()
        # ... app runs ...
        mgr.stop()
    """

    def __init__(self) -> None:
        self._entries: list[tuple[int, int, Callable]] = []  # (id, vk, cb)
        self._hwnd: int | None = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def register(self, combo: str, callback: Callable) -> None:
        """
        combo: e.g. "ctrl+shift+x", "ctrl+f12"
        Must be called BEFORE start().
        """
        mods, vk = _parse_combo(combo)
        hotkey_id = len(self._entries) + 1
        self._entries.append((hotkey_id, mods, vk, callback))

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._hwnd:
            # Post a quit message to unblock GetMessage
            ctypes.windll.user32.PostMessageW(self._hwnd, 0x0012, 0, 0)  # WM_QUIT

    def _run(self) -> None:
        # Create a message-only window to receive WM_HOTKEY
        self._hwnd = user32.CreateWindowExW(
            0, "STATIC", "capture_hotkey", 0,
            0, 0, 0, 0, None, None, None, None
        )
        if not self._hwnd:
            return

        for hotkey_id, mods, vk, _cb in self._entries:
            user32.RegisterHotKey(self._hwnd, hotkey_id, mods, vk)

        msg = wintypes.MSG()
        while not self._stop_event.is_set():
            ret = user32.GetMessageW(ctypes.byref(msg), self._hwnd, 0, 0)
            if ret <= 0:
                break
            if msg.message == WM_HOTKEY:
                hid = msg.wParam
                for hotkey_id, _mods, _vk, cb in self._entries:
                    if hotkey_id == hid:
                        threading.Thread(target=cb, daemon=True).start()

        for hotkey_id, _mods, _vk, _cb in self._entries:
            user32.UnregisterHotKey(self._hwnd, hotkey_id)


def _parse_combo(combo: str) -> tuple[int, int]:
    """Parse "ctrl+shift+x" → (mods_int, vk_int)."""
    parts = [p.strip().upper() for p in combo.split("+")]
    mods = 0
    vk = 0
    for p in parts:
        if p == "CTRL":
            mods |= MOD_CONTROL
        elif p == "SHIFT":
            mods |= MOD_SHIFT
        elif p == "ALT":
            mods |= MOD_ALT
        elif p == "WIN":
            mods |= MOD_WIN
        else:
            vk = VK_MAP.get(p, 0)
    return mods, vk
