# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

ROOT = Path(SPECPATH).resolve().parent

datas: list = []
binaries: list = []
hiddenimports: list = []
for package in ("PySide6", "shiboken6", "hid", "vgamepad"):
    extra_datas, extra_binaries, extra_hidden = collect_all(package)
    datas += extra_datas
    binaries += extra_binaries
    hiddenimports += extra_hidden

datas += [(str(ROOT / "assets"), "assets")]

hiddenimports += [
    "engine.device.ds3",
    "engine.device.ds4",
    "engine.device.ds5",
    "engine.device.switch_pro",
    "engine.device.xinput",
    "engine.device.hid_generic",
    "engine.ps3drv",
    "engine.vigem",
    "engine.hidhide",
    "engine.virtual",
    "engine.prefs",
    "ui.i18n",
]

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "unittest"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="JoystickDoctor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    icon=str(ROOT / "assets" / "icon.ico"),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="JoystickDoctor",
)
