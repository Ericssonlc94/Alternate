> Para ler em português: [README_BR.md](README_BR.md)

# 🌀 Alternate

*The original names have been changed.

A Windows tool inspired by the TV series *Severance*. It switches your machine
between **Work Mode** and **Personal Mode**: closing the previous mode's apps,
launching the new ones, swapping the wallpaper and clearing temp files.

The interface is a **PySide6 GUI over a standalone engine** — `core.py` knows
nothing about Qt and talks to the frontend through the `Reporter` contract.

![Alternate boot sequence: the LUMEN INDUSTRIES startup with the motto "BUILDING BETTER WORKERS", the mainframe uplink and the credential check](assets/severance%20system%20intro.png)

---

## 📁 Project structure

```
Severance-System/
├── assets/                  read-only resources (bundled into the .exe)
│   ├── lang/
│   │   ├── pt.json
│   │   └── en.json
│   └── logo.ico
├── data/                    user data (lives NEXT TO the .exe)
│   ├── config.json
│   ├── work_apps.json
│   ├── personal_apps.json
│   └── virtual_desktops_backup.json
├── docs/
│   └── manual_python_estudo.md
├── logs/                    reserved (see "Known limitations")
├── packaging/
│   ├── severance_gui.spec
│   ├── installer.iss
│   └── build_installer.bat
├── src/
│   ├── core.py              engine: processes, wallpaper, registry, cleanup
│   ├── severance_gui.py     entry point used by the .spec
│   └── gui/                 graphical frontend (PySide6)
├── run_gui.bat              launches the GUI
└── requirements.txt
```

### Why `data/` and `assets/` are separate

This isn't cosmetic tidying — the two folders have different lifecycles once the
app is packaged with PyInstaller.

- **`assets/`** is read-only and ships *inside* the executable. At runtime
  PyInstaller unpacks it into a fresh temporary folder on every launch
  (`sys._MEIPASS`).
- **`data/`** is writable and must **survive** across runs. If `config.json`
  were bundled with the assets, every launch would start from an empty temp
  folder and your settings would be gone.

The path layer in `core.py` is what enforces this:

| Function | Returns | When frozen (`.exe`) |
|---|---|---|
| `get_project_root()` | project root | the executable's folder |
| `get_data_dir()` | `data/` (created if missing) | `data/` next to the `.exe` |
| `get_logs_dir()` | `logs/` (created if missing) | `logs/` next to the `.exe` |
| `get_asset_path(*p)` | `assets/...` | `sys._MEIPASS/assets/...` |

`get_project_root()` resolves from `__file__`, **never** from the working
directory. That's why the app finds `data/` and `assets/` no matter where it was
started from — a shortcut, a terminal or a scheduler.

---

## ⚙️ Setup

Requirements: **Windows** and **Python 3.13** (tested on 3.13.7 with PySide6
6.11). The project uses Windows-only APIs (`winreg`, `ctypes.windll`,
`winsound`).

```bash
python -m venv venv
venv\Scripts\pip install -r requirements.txt
```

---

## ▶️ Running

`run_gui.bat` starts the program — it uses `pythonw.exe`, so no console window
sits behind the interface. Manually:

```bash
cd src
..\venv\Scripts\python.exe -m gui
```

The working directory is `src\` so that `-m gui` finds the package and
`import core` resolves without `PYTHONPATH`. The `data/` and `assets/` paths do
not depend on it.

---

## 🖥️ The graphical interface

**Boot sequence** — the LUMEN INDUSTRIES startup, with phosphor glow,
scanlines and typing effects. Skippable.

**Control tab** — start Work Mode, start Personal Mode, clear cache and temp
files. A log panel reports every process terminated and launched.

![Main window in the Severance theme: ALTERNATE header, Control and Database tabs, the mode buttons, maintenance and the activity log](assets/severance%20system%20menu%20theme%201.png)

*The active mode is highlighted above the buttons, and the activity log shows
what the engine is doing in real time.*

**Database tab** — lists each mode's apps, with add, edit and delete. *Edit* (or
a double click on the item) opens the same form prefilled: name, path and the
administrator / "close after launch" flags can be fixed — and switching the
database in the form moves the app between WORK and PERSONAL.

![Database tab with WORK MODE selected: each entry shows the name, the "Requires Admin" and "Close window after launch" flags, and the full executable path](assets/work%20mode.png)

![The same tab with PERSONAL MODE selected, listing that mode's apps](assets/personal%20mode.png)

*The dropdown picks which database is on screen. Each row carries the name, the
flags in effect and the full path — so `.vbs` entries and apps that need a UAC
prompt are visible without opening the form. An app listed in **both** modes,
like Drive above, survives a switch: only what is exclusive to the previous mode
gets terminated.*

**Settings (⚙)** — user name, language, theme, sound effects, minimize to tray on
close, start locked, wallpaper and restore defaults.

**Themes** — `severance` (default) and `fallout`, switchable on the fly from
Settings.

![The same main window in the Fallout theme: green phosphor on a dark background, with the padlock button next to the gear](assets/severance%20system%20menu%20theme%202.png)

*The Fallout theme swaps cyan for green phosphor and adds the **padlock button**
(🔒) next to the gear — it appears only in this theme, because it is what opens
the Termlink terminal.*

**Lock screen — Fallout only.** Behind that padlock is the TecCo Termlink
password minigame: words hidden in a memory dump, four attempts, and the
*likeness* hint. Besides the padlock, Settings › "Start locked" makes it come up
on the next launch.

![Lock screen in the Fallout theme: the TecCo INDUSTRIES (TM) TERMLINK PROTOCOL header, the attempts left, the memory dump in two columns of hex addresses and garbled characters, and the attempt log on the right](assets/lockscreen.png)

*The header carries the TecCo brand — the Fallout theme's counterpart to Lumen.
Words hide in the dump (`STORAGE`, `CAPSULE`, `REACTOR`…); each wrong guess
answers with the* likeness *count instead of a plain rejection.*

⚠️ **It is a joke, not security.** It protects and hides nothing: anyone who
opens `data/config.json` walks straight past it.

**Tray** — by default the X minimizes the window to the system tray instead of
quitting, and the real exit lives in the tray menu. Unchecking *"Minimize to tray
on close"* in Settings makes the X quit the program. Hovering the icon shows the
active mode in the tooltip (`WORK`, `PERSONAL` or `NONE`) — no need to open the
window.

**First run** — with no name on record, the boot sequence grants no access: it
checks the credentials and hands over to the enrollment screen. The menu only
appears once the name is given, followed by *access granted* and the greeting.

No action runs on the UI thread: everything goes through a `Worker` and comes
back as Qt signals, so the window never freezes during a mode switch.

---

## 🗂️ Configuration and data

### `data/config.json`

| Field | Description |
|---|---|
| `language` | `pt` or `en` |
| `user_name` | your name (*innie*) |
| `active_mode` / `active_mode_key` | last mode started |
| `work_wallpaper` / `personal_wallpaper` | `{ "path": ..., "style": "1".."6" }` |
| `theme` | `severance` or `fallout` |
| `start_locked` | open on the lock screen |
| `sound_enabled` | terminal sound effects |
| `close_to_tray` | the X minimizes to the tray instead of quitting (default: `true`) |
| `wallpaper_walk_desktops` | walk the virtual desktops when applying the wallpaper (default: `true`) |

### `data/work_apps.json` and `data/personal_apps.json`

```json
[
    {
        "name": "DROPBOX",
        "path": "C:/Program Files (x86)/Dropbox/Client/Dropbox.exe",
        "close_after_launch": true,
        "requires_admin": true
    }
]
```

| Field | Effect |
|---|---|
| `name` | display label; also matches the window for `close_after_launch` |
| `path` | path to the `.exe` or `.vbs` (`.vbs` runs via `wscript.exe`) |
| `close_after_launch` | closes the app's **window** after launch (Alt+F4), leaving the background process alive |
| `requires_admin` | launches elevated (`runas`), triggering a UAC prompt |

Apps present in **both** modes are not terminated on a switch — only those
exclusive to the previous mode. Steam and Dropbox get special handling
(`-silent`, more aggressive termination, output silencing).

### Wallpaper styles

| Code | Style |
|---|---|
| `1` | Fill |
| `2` | Fit |
| `3` | Stretch |
| `4` | Tile |
| `5` | Center |
| `6` | Span (multiple monitors) |

#### Multiple virtual desktops

The wallpaper is applied to **every** virtual desktop, not just the active one.
That takes a detour: `SystemParametersInfoW` only repaints the active desktop,
and writing each GUID's `Wallpaper` registry key is **not enough** — Explorer
keeps every desktop's wallpaper in memory and only reads those keys at session
start.

So the system does both: it writes the registry (so the value is correct at the
next login) and **walks the desktops** with `Ctrl+Win+Arrow`, actually applying
the wallpaper on each one and returning to the starting desktop. The visible
effect is the screen cycling for a few seconds during a mode switch.

The walk only happens when there is something to change: if the target wallpaper
(and style) is already in effect on every desktop, the step is skipped entirely.
Starting the same mode twice in a row cycles nothing.

To disable the walk — keeping only the active desktop plus the registry — add
this to `data/config.json`:

```json
"wallpaper_walk_desktops": false
```

### Translations

Every file in `assets/lang/` becomes a language automatically (the filename is
the language code). To add one, copy `pt.json`, translate the values and save it
as e.g. `es.json`.

---

## 🧱 Architecture

The engine knows nothing about Qt or languages. It reports what it is doing
through the `core.Reporter` contract, and the frontend implements it:

```
gui/ ──── QtReporter ──→ core.Reporter ──→ core.py
                                           (processes, registry,
                                            wallpaper, cleanup)
```

The split is deliberate: another frontend only has to implement `Reporter` —
`core.py` needs no changes.

| Module in `src/gui/` | Role |
|---|---|
| `__main__.py` / `app.py` | entry point (`python -m gui`) |
| `main_window.py` | `QStackedWidget`: boot → lock → tabs |
| `boot.py` | LUMEN startup sequence |
| `lockscreen.py` | Termlink terminal minigame |
| `dialogs.py` | app forms (add and edit), settings and wallpaper forms |
| `effects.py` | CRT overlay: phosphor, scanlines, sweep |
| `theme.py` | Severance/Fallout palettes (QSS via `string.Template`) |
| `sound.py` | async in-memory WAV tones |
| `reporter.py` | `Worker` + engine → Qt signal bridge |
| `i18n.py` | runtime translation, stripping the `rich` markup the language files still carry |

---

## 📦 Building the executable and installer

The short path is `packaging\build_installer.bat`, which runs both steps and
reports clearly if anything is missing. Manually:

```bash
venv\Scripts\pyinstaller packaging\severance_gui.spec   # -> dist\Alternate.exe
iscc packaging\installer.iss                            # installer -> dist\Alternate-2.0.0-setup.exe
```

The executable is **~60 MB**: it carries all of Python and PySide6 inside,
which is why it runs on machines with nothing installed.

The installer needs [Inno Setup 6](https://jrsoftware.org/isdl.php), which is
free. Without it the `.bat` still produces the executable in `dist\`, which works
on its own — the installer only adds shortcuts and uninstall support.

**Per-user install, deliberately.** The default target is
`%LOCALAPPDATA%\Programs\Alternate`, not Program Files. That avoids a UAC
prompt at install time and keeps the target writable, so `data/` lives beside the
executable and the whole folder can be carried to another PC.

**Where the data ends up.** The `.spec` file bundles `assets/` and leaves `data/`
out — PyInstaller wipes its temp folder on every exit, so anything written there
would be lost. If the program still ends up in a protected folder it does not
break: `core._writable_dir` probes for write access and falls back to
`%APPDATA%\Alternate\`.

**A fresh install starts empty.** Neither the executable nor the installer
carries `config.json` or the app databases — the `.spec` leaves `data/` out and
the installer ships only the `.exe` and the READMEs. With no `user_name` on
record the boot sequence grants no access and hands over to the enrollment
screen, so each user defines their own profile.

> The installer uses an `AppId` of its own, different from the old Severance
> System one. Windows therefore treats Alternate as a separate product: it
> installs into its own folder and does not inherit the previous install's
> `data/`. The old entry, if present, stays in Apps & Features and can be
> uninstalled separately.

Uninstalling preserves `data/` on purpose — updating does not wipe your settings.
To start clean, delete the folder manually.

---

## ⚠️ Known limitations

- **The installer is not code-signed.** Windows SmartScreen will warn on first
  run ("More info" → "Run anyway"). Fixing that requires a paid code-signing
  certificate.
- **`assets/logo.ico` is not in the repository**, so the executable and installer
  ship with the default Windows icon and the GUI draws a themed square instead.
  The `.spec` file handles its absence without breaking; put the file back in
  `assets/` and the icon returns (also uncomment `SetupIconFile` in
  `installer.iss`).
- **`logs/` is unused.** The folder and `core.get_logs_dir()` exist, but the
  project has no logging system — it is scaffolding, not a working feature.
- **Orphan virtual desktop cleanup is unreachable.** The CLI was the only caller
  of `core.clean_orphan_virtual_desktops()`; with it gone, the function is still
  in the engine but nothing invokes it. The GUI's maintenance button clears cache
  and temp files only.
- **Windows only.** `winreg`, `ctypes.windll` and `winsound` have no equivalent
  on other platforms.
- Temp cleanup skips files locked by the system — seeing several "permission
  denied" entries in the log is expected.
