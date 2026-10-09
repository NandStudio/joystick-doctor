from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QIcon, QImage, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer


def bundle_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[1]


def asset_path(name: str) -> Path:
    return bundle_root() / "assets" / name


def logo_file(mode: str) -> Path:
    # The dark-theme file is the white mark. High contrast sits on black.
    name = "logo-theme-dark.svg" if mode in ("dark", "contrast") else "logo-theme-light.svg"
    return asset_path(name)


def render_logo(path: Path, size: int) -> QImage:
    renderer = QSvgRenderer(str(path))
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    if not renderer.isValid():
        return image
    box = renderer.viewBoxF()
    if box.isEmpty():
        box = QRectF(0, 0, renderer.defaultSize().width(), renderer.defaultSize().height())
    scale = min(size / box.width(), size / box.height()) * 0.86
    width = box.width() * scale
    height = box.height() * scale
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(
        painter,
        QRectF((size - width) / 2, (size - height) / 2, width, height),
    )
    painter.end()
    return image


def logo_icon(mode: str) -> QIcon:
    path = logo_file(mode)
    icon = QIcon()
    if not path.is_file():
        return icon
    for size in (16, 24, 32, 48, 256):
        icon.addPixmap(QPixmap.fromImage(render_logo(path, size)))
    return icon
