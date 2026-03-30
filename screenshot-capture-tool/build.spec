# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Capture
# Build: pyinstaller build.spec
# Output: dist/capture.exe

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
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
        'urllib',
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
    [],
    exclude_binaries=True,
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
    icon=None,
    version_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='capture',
)
