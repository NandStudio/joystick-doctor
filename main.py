from PySide6.QtWidgets import QApplication

from ui.window import LiveWindow


def main() -> None:
    app = QApplication([])
    window = LiveWindow()
    window.show()
    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
