from __future__ import annotations

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
    controller = AppController(engine)
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
    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
