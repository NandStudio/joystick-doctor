from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from ui.assets import asset_path
from ui.window import LiveWindow


def main() -> None:
    app = QApplication([])
    icon = QIcon(str(asset_path("icon.png")))
    if not icon.isNull():
        app.setWindowIcon(icon)
    window = LiveWindow()
    if not icon.isNull():
        window.setWindowIcon(icon)
    window.show()
    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
