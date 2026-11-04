# Joystick Doctor

Windows desktop app that diagnoses and calibrates a game controller, applies deadzones, curves and remaps, and exposes the result to games as a virtual Xbox 360 pad. Open source (see `LICENSE`), published by Nand Studio at `NandStudio/joystick-doctor`.

## Stack

- Python 3.10 (`.venv`), PySide6 with QML for the UI
- `hidapi` for HID controllers, `xinput1_4.dll` for XInput, `vgamepad` for the virtual pad
- External drivers, not bundled: ViGEmBus (virtual output), HidHide (hides the physical pad), DsHidMini or ScpToolkit (official DualShock 3)
- PyInstaller and Inno Setup 6 for packaging

## Commands

Windows only. Run from the repo root in PowerShell.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-build.txt
.\.venv\Scripts\python.exe main.py        # run from source
.\packaging\build.ps1                     # PyInstaller + Inno Setup installer
```

The installer lands in `dist\JoystickDoctorSetup-<version>.exe`. `build/` and `dist/` are ignored by git.

There is no test suite, linter config or CI. Check changes by compiling and running the app with a real controller.

## Layout

```text
main.py                 Entry point: QML engine, AppController, Palette
engine/                 Logic without UI
  device/               Controller readers, enumeration, hotplug, read loop
  state.py              DeviceIdentity and NormalizedState
  pipeline.py           Stick and trigger calibration
  remap.py              Button remap rules
  virtual.py            Virtual Xbox 360 output
  guided.py             Five-step guided calibration
  diagnose.py           Controller scoring
  profiles.py           Per-controller profiles
  prefs.py              App settings
  supportlog.py         Failure logs and crash hooks
  net.py                HTTPS with certificate verification
  vigem.py, hidhide.py, ps3drv.py   Driver detection, download and install
  update.py             App update check and install
  version.py            APP_VERSION
  libs/, joystick.py    Compatibility shims
ui/
  controller.py         AppController, the bridge between engine and QML
  i18n.py               en and es strings, tr()
  theme.py              Palette for light, dark and contrast themes
  assets.py             Bundle paths and logos
  qml/                  Main.qml plus controls/, glyphs/, screens/, shell/
packaging/              build.ps1, PyInstaller spec, Inno Setup script, icon generator
assets/                 Logos and icon
```

## How it works

Data path: a reader in `engine/device/` produces a `NormalizedState`. `DevicePump` runs that reader on a background thread and holds the latest state. `AppController` applies `apply_calibration`, then `RemapEngine`, and `VirtualXbox` sends the result to ViGEmBus.

- `engine/device/catalog.py` is the single place that classifies devices (`enumerate_all`) and picks a reader (`reader_for`). A new controller family needs a reader there and a hidden import in the spec.
- Hotplug callbacks arrive off the UI thread and cross through `_Bridge` signals.
- Long-running work in the UI goes through the `_Download` QThread in `ui/controller.py`, which logs failures with `write_failure` and reports them as a notice.
- Driver installers are downloaded from the official Nefarius GitHub releases and launched elevated with `ShellExecuteW(..., "runas", ...)`. The app installer in `update.py` follows the same path.

All HTTPS goes through `engine.net.urlopen`. Never call `urllib.request.urlopen` directly. It verifies with the Windows trust store through `truststore`, because OpenSSL alone misses roots that Windows downloads on demand, and retries with the `certifi` bundle only after a certificate failure. Never disable TLS verification: these downloads run elevated.

User data lives in `%LOCALAPPDATA%\joystick-doctor\`: `settings.json`, `profiles\` and `logs\failure-*.log`.

## Conventions

- Start Python modules with `from __future__ import annotations` and type public functions.
- Keep comments rare. Use them only for a non-obvious reason.
- `engine/` must not import from `ui/`.
- Every user-facing string goes through `tr()`, with the key in both `en` and `es` in `ui/i18n.py`. Keep `engine/` exceptions in plain English.
- QML reads colors from the `theme` context property and logic from `app`. Never hardcode a theme color.
- Add a new QML file under the existing folder for its role. The spec ships `ui/qml` as a whole.
- A new `engine` module loaded lazily must be added to `hiddenimports` in `packaging/joystick-doctor.spec`.
- Working tree files use CRLF. Preserve it when editing.

The visual direction is in `.cursor/docs/DESIGN.md`, which is local and not in git.

## Versioning and git

- Each release has its own branch named after the version (`0.2.3`). `main` is the default branch.
- A version bump touches three files: `engine/version.py`, `packaging/joystick-doctor.iss` (`MyAppVersion`) and the installer name in `packaging/build.ps1`.
- `engine/update.py` compares `APP_VERSION` with the latest GitHub release tag and expects an asset named `JoystickDoctorSetup*.exe`.
- Commits are small slices: one reviewable behaviour, the app still runs, and the message explains why it exists in one or two sentences. If the message needs "and", split it. Existing messages are full sentences in Spanish that describe the outcome.
- Do not commit or create branches unless asked.
