# Solotop Capture

- A Windows screenshot tool: lightweight, fast, and polished.
- Supports annotations, rounded corners, blurred/color backgrounds to make your content stand out.
- Automatically optimizes output into common social-media-friendly image layouts for X (Twitter).

100% open source. Runs offline, collects no data, does not track you, does not run in the background, has no ads, and stays clean and transparent.

![Screenshot 2026-03-31 113711](https://github.com/user-attachments/assets/791753f6-d48e-454e-80b8-b9cc235af507)

---

### Beautiful screenshots instantly, ready to post on X

This is the standout feature.

After you capture a screenshot, the image is automatically given **soft rounded corners**. Turn on **Background** and the app adds a clean layer behind the screenshot, turning a plain capture into a polished visual that is ready to share.

**Social-friendly layout presets:**
| Layout | Ratio | Best for |
|--------|--------|----------|
| Original | Keep original | Fast sharing |
| Portrait | 4:5 | Instagram posts, X posts |
| Landscape | 16:9 | Banners, headers |
| Phone | 9:16 | Stories, Reels |

The exported image includes shadow, rounded corners, and background styling, without needing Figma or Canva.

---

## Run from source

```bash
pip install -r requirements.txt
python main.py
```

## Build the `.exe`

```bash
pyinstaller --clean --noconfirm build.spec
```

Output: `dist/capture.exe`

## Prebuilt release

- Ready-to-use file: `Solotop Capture.exe`
- MD5: `DD50AC26D809A9AF59158398D2DB19FF`

## Supported platforms

- Windows 10
- Windows 11

---

### Security first

This tool **does not use the network** in its main workflow. There is no server, no account system, no analytics, no crash reporting, and no auto-update.

More specifically:
- Network-related modules (`socket`, `ssl`, `http`, `urllib`, `PyQt6.QtNetwork`, `PyQt6.QtWebEngine`) are **excluded from the build**. They are not just disabled; they are not included in the final `.exe`.
- There is no `eval`, `exec`, `subprocess`, or any mechanism for executing arbitrary external code.
- No auto-start with Windows. No system tray. No background process.
- Images only leave the app when you explicitly click **Copy** or **Save**.
- Settings are stored in `%LOCALAPPDATA%` as a simple JSON file containing only a few values: background color, style, and custom image path.
- Custom background images only accept **absolute local file paths**. UNC paths and network paths are blocked.

**Secure redact:**
When you use Redact to hide sensitive information, the selected region is **fully overwritten** with a solid fill. It is not blur and not mosaic. The original pixels are destroyed, and the exported image no longer contains the old data in that area.

### Open source and easy to inspect

The codebase is Python + PyQt6, compact and easy to read. You can inspect the whole project quickly without digging through hidden services or unnecessary layers.

Run it from source or build it into a `.exe`, whichever you prefer.

### Fast and lightweight

- Launch the app and go straight into capture. No splash screen, no loading screen.
- Press **New** to recapture, and the editor comes back almost instantly.
- Image conversion uses direct memory transfer instead of PNG encode/decode roundtrips, which makes it noticeably faster.
- Minimal dependencies: PyQt6, Pillow, mss. Nothing bloated.

---

## Features

- Region screenshot capture with multi-monitor support
- **Rect** - rectangle annotations
- **Arrow** - directional arrows
- **Label** - numbered markers
- **Text** - note-card style text annotations with drag and resize
- **Redact** - secure solid-fill redaction that cannot be visually recovered from exported output
- **Undo** / **Clear**
- **Copy** (`Ctrl+C`) / **Save** (`Ctrl+S`) / **New** (`Ctrl+N`)
- “Copied” toast to confirm clipboard success
- Remembers background color and style for the next app launch

---

## Tech stack

`Python` · `PyQt6` · `Pillow` · `mss` · `PyInstaller`
