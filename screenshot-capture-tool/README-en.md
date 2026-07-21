# Solotop Capture

- A Windows screenshot tool: lightweight, fast, and polished.
- Supports annotations, rounded corners, blurred/color backgrounds to make your content stand out.
- Includes aspect-ratio guides and small-image warnings for clearer posts on X (Twitter).

100% open source. Runs offline, collects no data, does not track you, does not run in the background, has no ads, and stays clean and transparent.

![Screenshot 2026-03-31 113711](https://github.com/user-attachments/assets/791753f6-d48e-454e-80b8-b9cc235af507)

---

## Change the watermark

The text watermark is enabled by default as `𝕏: @solotop999`. It appears only in the bottom-right corner of the **Background** and never covers the captured image.

1. After capturing an image, keep **Background** enabled.
2. Click **Mark** on the toolbar.
3. Enable or disable the watermark, change its text, and adjust **Opacity**.
4. Click **Save** in the dialog. The preference is stored locally for future sessions.

The watermark is included in both **Copy** and **Save** output. It is hidden when **Background** is disabled.

---

## Add an icon to the image

After each capture, assets/icon.png is added automatically in the bottom-left corner of the final image.

- Drag the icon anywhere, including the **Background** outside the screenshot.
- Drag the top-right handle to resize it while preserving its aspect ratio.
- Click the **Icon** toolbar button to show or hide it.
- Visibility is remembered for future captures and app launches.
- The current icon size is remembered when you click **Copy**; its default position remains bottom-left.
- The icon is included in both **Copy** and **Save** output.

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
python -m PyInstaller --clean --noconfirm build.spec
```

Output: `dist/capture.exe`

## Prebuilt release

- **[⬇️ Download Solotop Capture for Windows](https://github.com/solotop999/Viber-Coding/raw/refs/heads/main/screenshot-capture-tool/Solotop%20Capture.exe)**
- Ready-to-use file: `Solotop Capture.exe` — download and run, no installation required
- Size: `39,612,200 bytes` (~37.8 MiB)
- MD5: `72AF5FB1D40B6A5B7DB11B92FF8ED50E`
- SHA-256: `E9E1B1B0049837764CEBD8C3DFEDAEC683772E5A734D8737E7A9AB1DF796FC26`

## Supported platforms

- Windows 10
- Windows 11

---

### Security first

This tool **does not use the network** in its main workflow. There is no server, no account system, no analytics, no crash reporting, and no auto-update.

More specifically:
- The application code sends no network requests; unused Python network clients and Qt WebEngine are excluded from the build.
- There is no `eval`, `exec`, `subprocess`, or any mechanism for executing arbitrary external code.
- No auto-start with Windows. No system tray. No background process.
- Images only leave the app when you explicitly click **Copy** or **Save**.
- Settings are stored in `%LOCALAPPDATA%` as plain JSON containing only UI and background preferences.
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
- Move and resize the selected region before pressing **Confirm**
- `16:9`, `1:1`, and `4:5` guides, plus a red warning below 300 px width
- Timed capture: no delay, 3 seconds, 5 seconds, or 10 seconds
- **Rect** - rectangle annotations that can be moved after drawing
- **Arrow** - directional arrows
- **Label** - numbered markers
- **Text** - note-card style text annotations with drag and resize
- **Redact** - secure solid-fill redaction that cannot be visually recovered from exported output
- **Icon** - draggable and resizable overlay across the image and background, with a persistent visibility toggle
- **Undo** / **Clear**
- **Copy** (`Ctrl+C`) / **Save** (`Ctrl+S`) / **New** (`Ctrl+N`)
- “Copied” toast to confirm clipboard success
- Remembers background color and style for the next app launch
- Custom text watermark stored locally and restricted to the background area

---

## Tech stack

`Python` · `PyQt6` · `Pillow` · `mss` · `PyInstaller`
