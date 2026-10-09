from __future__ import annotations

import ctypes
import sys

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle

from ui.assets import asset_path, bundle_root
from ui.controller import AppController
from ui.theme import Palette


def main() -> None:
    QQuickStyle.setStyle("Basic")
    app = QGuiApplication(sys.argv)
    icon = QIcon(str(asset_path("icon.png")))
    if not icon.isNull():
        app.setWindowIcon(icon)
    engine = QQmlApplicationEngine()
    palette = Palette(engine)
    controller = AppController(engine, palette)
    engine.rootContext().setContextProperty("theme", palette)
    engine.rootContext().setContextProperty("app", controller)

    def _warn(warnings) -> None:
        for item in warnings:
            print(item.toString(), file=sys.stderr)

    engine.warnings.connect(_warn)
    qml = bundle_root() / "ui" / "qml" / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml)))
    if not engine.rootObjects():
        raise SystemExit(1)
    _prefer_square_frame(engine.rootObjects()[0])
    raise SystemExit(app.exec())


def _prefer_square_frame(window) -> None:
    # The shell draws the radius. DWM's own corner would square it back.
    if sys.platform != "win32":
        return
    try:
        preference = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            int(window.winId()), 33, ctypes.byref(preference), 4
        )
    except (AttributeError, OSError):
        return


if __name__ == "__main__":
    main()
