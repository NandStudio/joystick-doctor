"""Build assets/icon.ico from assets/icon.png (nearest-neighbor, several sizes)."""

from __future__ import annotations

import struct
import sys
from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, Qt
from PySide6.QtGui import QGuiApplication, QImage

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets" / "icon.png"
DST = ROOT / "assets" / "icon.ico"
SIZES = (16, 32, 48, 256)


def _png_bytes(image: QImage) -> bytes:
    blob = QByteArray()
    buffer = QBuffer(blob)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    if not image.save(buffer, "PNG"):
        raise RuntimeError("Could not encode PNG frame for the ICO.")
    return bytes(blob)


def _scale(source: QImage, size: int) -> QImage:
    if source.width() == size and source.height() == size:
        return source.convertToFormat(QImage.Format.Format_ARGB32)
    return source.scaled(
        size,
        size,
        Qt.AspectRatioMode.IgnoreAspectRatio,
        Qt.TransformationMode.FastTransformation,
    ).convertToFormat(QImage.Format.Format_ARGB32)


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


def main() -> None:
    QGuiApplication.instance() or QGuiApplication(sys.argv)
    if not SRC.is_file():
        raise SystemExit(f"Missing {SRC}")
    source = QImage(str(SRC))
    if source.isNull():
        raise SystemExit(f"Could not read {SRC}")
    frames = [_scale(source, size) for size in SIZES]
    DST.parent.mkdir(parents=True, exist_ok=True)
    write_ico(DST, frames)
    print(f"Wrote {DST} ({', '.join(str(s) for s in SIZES)})")


if __name__ == "__main__":
    main()
