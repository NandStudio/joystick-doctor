from __future__ import annotations

from PySide6.QtCore import Property, QObject, Signal


class Palette(QObject):
    changed = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._dark = False

    def set_dark(self, dark: bool) -> None:
        dark = bool(dark)
        if dark == self._dark:
            return
        self._dark = dark
        self.changed.emit()

    def is_dark(self) -> bool:
        return self._dark

    def _canvas(self) -> str:
        return "#1e1e1e" if self._dark else "#ebebeb"

    def _surface(self) -> str:
        return "#2b2b2b" if self._dark else "#dedede"

    def _ink(self) -> str:
        return "#ebebeb" if self._dark else "#1e1e1e"

    def _muted(self) -> str:
        return "#989898" if self._dark else "#5d5d5d"

    def _stroke(self) -> str:
        return "#7a7a7a"

    def _wash(self) -> str:
        return "#424242" if self._dark else "#e8e8e8"

    def _on_ink(self) -> str:
        return "#1e1e1e" if self._dark else "#ebebeb"

    def _ink_pressed(self) -> str:
        return "#d4d4d4" if self._dark else "#2b2b2b"

    def _hover_wash(self) -> str:
        return "#383838" if self._dark else "#d0d0d0"

    def _veil(self) -> str:
        return "#99000000" if self._dark else "#802b2b2b"

    def _shadow(self) -> str:
        return "#80000000" if self._dark else "#381e1e1e"

    isDark = Property(bool, is_dark, notify=changed)
    canvas = Property(str, _canvas, notify=changed)
    surface = Property(str, _surface, notify=changed)
    ink = Property(str, _ink, notify=changed)
    muted = Property(str, _muted, notify=changed)
    stroke = Property(str, _stroke, notify=changed)
    wash = Property(str, _wash, notify=changed)
    onInk = Property(str, _on_ink, notify=changed)
    inkPressed = Property(str, _ink_pressed, notify=changed)
    hoverWash = Property(str, _hover_wash, notify=changed)
    veil = Property(str, _veil, notify=changed)
    shadow = Property(str, _shadow, notify=changed)
    radiusSmall = Property(int, lambda self: 8, constant=True)
    radiusControl = Property(int, lambda self: 16, constant=True)
    radiusCard = Property(int, lambda self: 28, constant=True)
