from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DeviceIdentity:
    vendor_id: int
    product_id: int
    backend: str
    path: bytes | str
    product_name: str
    index: int | None = None


@dataclass(slots=True)
class NormalizedState:
    lx: float = 0.0
    ly: float = 0.0
    rx: float = 0.0
    ry: float = 0.0
    lt: float = 0.0
    rt: float = 0.0
    a: bool = False
    b: bool = False
    x: bool = False
    y: bool = False
    lb: bool = False
    rb: bool = False
    ls: bool = False
    rs: bool = False
    back: bool = False
    start: bool = False
    guide: bool = False
    dpad_up: bool = False
    dpad_down: bool = False
    dpad_left: bool = False
    dpad_right: bool = False
    timestamp: float = 0.0

    def format_line(self) -> str:
        dpad = "".join(
            name
            for name, on in (
                ("U", self.dpad_up),
                ("D", self.dpad_down),
                ("L", self.dpad_left),
                ("R", self.dpad_right),
            )
            if on
        ) or "-"
        pressed = [
            name
            for name, on in (
                ("A", self.a),
                ("B", self.b),
                ("X", self.x),
                ("Y", self.y),
                ("LB", self.lb),
                ("RB", self.rb),
                ("LS", self.ls),
                ("RS", self.rs),
                ("Back", self.back),
                ("Start", self.start),
                ("Guide", self.guide),
            )
            if on
        ]
        btns = ",".join(pressed) if pressed else "-"
        return (
            f"LS {self.lx:+.2f},{self.ly:+.2f}  "
            f"RS {self.rx:+.2f},{self.ry:+.2f}  "
            f"LT {self.lt:.2f} RT {self.rt:.2f}  "
            f"DPAD {dpad}  [{btns}]"
        )
