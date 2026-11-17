"""Build the exe icon from the light app icon, and the installer icon from the dark one."""

from __future__ import annotations

import struct
import sys
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QIODevice
from PySide6.QtGui import QGuiApplication, QImage

ROOT = Path(__file__).resolve().parents[1]
LIGHT = ROOT / "assets" / "app-icon-light.svg"
DARK = ROOT / "assets" / "app-icon-dark.svg"
EXE_ICON = ROOT / "assets" / "icon.ico"
SETUP_ICON = ROOT / "assets" / "setup-icon.ico"
SIZES = (16, 32, 48, 256)


def _png_bytes(image: QImage) -> bytes:
    blob = QByteArray()
    buffer = QBuffer(blob)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    if not image.save(buffer, "PNG"):
        raise RuntimeError("Could not encode PNG frame for the ICO.")
    return bytes(blob)


def write_ico(path: Path, frames: list[QImage]) -> None:
    pngs = [_png_bytes(frame) for frame in frames]
    offset = 6 + 16 * len(pngs)
    out = bytearray()
    out += struct.pack("<HHH", 0, 1, len(pngs))
    for frame, data in zip(frames, pngs, strict=True):
        width = 0 if frame.width() >= 256 else frame.width()
        height = 0 if frame.height() >= 256 else frame.height()
        out += struct.pack("<BBBBHHII", width, height, 0, 0, 1, 32, len(data), offset)
        offset += len(data)
    for data in pngs:
        out += data
    path.write_bytes(out)


def build(src: Path, dst: Path, render: Callable[[Path, int], QImage]) -> None:
    frames = [render(src, size) for size in SIZES]
    dst.parent.mkdir(parents=True, exist_ok=True)
    write_ico(dst, frames)
    print(f"Wrote {dst} ({', '.join(str(s) for s in SIZES)})")


def main() -> None:
    QGuiApplication.instance() or QGuiApplication(sys.argv)
    sys.path.insert(0, str(ROOT))
    from ui.assets import render_svg

    for src in (LIGHT, DARK):
        if not src.is_file():
            raise SystemExit(f"Missing {src}")
    build(LIGHT, EXE_ICON, render_svg)
    build(DARK, SETUP_ICON, render_svg)


if __name__ == "__main__":
    main()
