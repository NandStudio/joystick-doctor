from __future__ import annotations

from PySide6.QtCore import Property, QObject, Signal

_MODES = ("light", "dark", "contrast")


class Palette(QObject):
    changed = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._mode = "light"

    def set_mode(self, mode: str) -> None:
        if mode not in _MODES or mode == self._mode:
            return
        self._mode = mode
        self.changed.emit()

    def mode(self) -> str:
        return self._mode

    def set_dark(self, dark: bool) -> None:
        self.set_mode("dark" if dark else "light")

    def is_dark(self) -> bool:
        return self._mode == "dark"

    def is_contrast(self) -> bool:
        return self._mode == "contrast"

    def _pick(self, light: str, dark: str, contrast: str) -> str:
        if self._mode == "contrast":
            return contrast
        if self._mode == "dark":
            return dark
        return light

    def _canvas(self) -> str:
        return self._pick("#ebebeb", "#1e1e1e", "#000000")

    def _surface(self) -> str:
        return self._pick("#dedede", "#2b2b2b", "#3a3a3a")

    def _ink(self) -> str:
        return self._pick("#1e1e1e", "#ebebeb", "#ffffff")

    def _muted(self) -> str:
        return self._pick("#5d5d5d", "#989898", "#ffffff")

    def _stroke(self) -> str:
        return self._pick("#7a7a7a", "#7a7a7a", "#ffffff")

    def _wash(self) -> str:
        return self._pick("#e8e8e8", "#424242", "#ffffff")

    def _on_ink(self) -> str:
        return self._pick("#ebebeb", "#1e1e1e", "#000000")

    def _on_wash(self) -> str:
        return self._pick("#1e1e1e", "#ebebeb", "#000000")

    def _ink_pressed(self) -> str:
        return self._pick("#2b2b2b", "#d4d4d4", "#d4d4d4")

    def _hover_wash(self) -> str:
        return self._pick("#d0d0d0", "#383838", "#5a5a5a")

    def _veil(self) -> str:
        return self._pick("#802b2b2b", "#99000000", "#e6000000")

    def _shadow(self) -> str:
        return self._pick("#381e1e1e", "#80000000", "#ffffffff")

    isDark = Property(bool, is_dark, notify=changed)
    isContrast = Property(bool, is_contrast, notify=changed)
    canvas = Property(str, _canvas, notify=changed)
    surface = Property(str, _surface, notify=changed)
    ink = Property(str, _ink, notify=changed)
    muted = Property(str, _muted, notify=changed)
    stroke = Property(str, _stroke, notify=changed)
    wash = Property(str, _wash, notify=changed)
    onInk = Property(str, _on_ink, notify=changed)
    onWash = Property(str, _on_wash, notify=changed)
    inkPressed = Property(str, _ink_pressed, notify=changed)
    hoverWash = Property(str, _hover_wash, notify=changed)
    veil = Property(str, _veil, notify=changed)
    shadow = Property(str, _shadow, notify=changed)
    radiusSmall = Property(int, lambda self: 8, constant=True)
    radiusControl = Property(int, lambda self: 16, constant=True)
    radiusCard = Property(int, lambda self: 28, constant=True)
