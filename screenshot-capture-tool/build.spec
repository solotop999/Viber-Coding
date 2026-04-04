# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Capture
# Build: pyinstaller build.spec
# Output: dist/capture.exe

from pathlib import Path

block_cipher = None
_ASSET_DIR = Path('assets')
_ASSET_FILES = [
    (_ASSET_DIR / 'bg1.jpg', 'assets'),
    (_ASSET_DIR / 'bg2.jpg', 'assets'),
    (_ASSET_DIR / 'bg3.jpg', 'assets'),
    (_ASSET_DIR / 'logo.jpg', 'assets'),
    (_ASSET_DIR / 'x_icon.jpg', 'assets'),
]
_ICON_FILE = _ASSET_DIR / 'logo.ico'

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[(str(path), dest) for path, dest in _ASSET_FILES if path.exists()],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PyQt6.QtNetwork',
        'PyQt6.QtWebEngine',
        'PyQt6.QtWebEngineWidgets',
        'PyQt6.QtWebEngineCore',
        'PyQt6.QtWebSockets',
        'PyQt6.QtBluetooth',
        'PyQt6.QtNfc',
        'PyQt6.QtDBus',
        'PyQt6.QtLocation',
        'PyQt6.QtPositioning',
        'PyQt6.QtRemoteObjects',
        'urllib3',
        'http',
        'http.client',
        'http.server',
        'socket',
        'socketserver',
        'ssl',
        'requests',
        'httpx',
        'aiohttp',
        'ftplib',
        'imaplib',
        'poplib',
        'smtplib',
        'telnetlib',
        'xmlrpc',
        'email',
        'tkinter',
        'unittest',
        'test',
        'distutils',
        'setuptools',
        'pip',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    exclude_binaries=False,
    name='capture',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(_ICON_FILE) if _ICON_FILE.exists() else None,
    version_file=None,
)
