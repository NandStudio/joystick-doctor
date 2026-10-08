from __future__ import annotations

from PySide6.QtCore import Property, QObject


class Palette(QObject):
    canvas = Property(str, lambda self: "#ebebeb", constant=True)
    surface = Property(str, lambda self: "#dedede", constant=True)
    ink = Property(str, lambda self: "#1e1e1e", constant=True)
    muted = Property(str, lambda self: "#5d5d5d", constant=True)
    stroke = Property(str, lambda self: "#7a7a7a", constant=True)
    wash = Property(str, lambda self: "#e8e8e8", constant=True)
    onInk = Property(str, lambda self: "#ebebeb", constant=True)
    radiusSmall = Property(int, lambda self: 8, constant=True)
    radiusControl = Property(int, lambda self: 16, constant=True)
    radiusCard = Property(int, lambda self: 28, constant=True)
