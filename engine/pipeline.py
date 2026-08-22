from __future__ import annotations

import math
from dataclasses import dataclass, replace

from engine.state import NormalizedState


@dataclass(slots=True)
class StickCal:
    inner: float = 0.10
    outer: float = 0.98
    center_x: float = 0.0
    center_y: float = 0.0
    curve: float = 1.0
    invert_x: bool = False
    invert_y: bool = False


@dataclass(slots=True)
class TriggerCal:
    inner: float = 0.04
    outer: float = 0.98
    curve: float = 1.0


@dataclass(slots=True)
class Calibration:
    left: StickCal
    right: StickCal
    lt: TriggerCal
    rt: TriggerCal

    @staticmethod
    def default() -> Calibration:
        return Calibration(StickCal(), StickCal(), TriggerCal(), TriggerCal())


def _clamp(value: float, low: float = -1.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def apply_stick(x: float, y: float, cal: StickCal) -> tuple[float, float]:
    x -= cal.center_x
    y -= cal.center_y
    inner = max(0.0, min(cal.inner, 0.95))
    outer = max(inner + 0.01, min(cal.outer, 1.0))
    mag = math.hypot(x, y)
    if mag <= inner:
        return 0.0, 0.0
    if mag < 1e-9:
        return 0.0, 0.0
    scaled = (min(mag, outer) - inner) / (outer - inner)
    scaled = _clamp(scaled, 0.0, 1.0)
    gamma = max(0.2, min(cal.curve, 4.0))
    scaled = scaled**gamma
    x = (x / mag) * scaled
    y = (y / mag) * scaled
    if cal.invert_x:
        x = -x
    if cal.invert_y:
        y = -y
    return _clamp(x), _clamp(y)


def apply_trigger(value: float, cal: TriggerCal) -> float:
    inner = max(0.0, min(cal.inner, 0.95))
    outer = max(inner + 0.01, min(cal.outer, 1.0))
    if value <= inner:
        return 0.0
    scaled = (min(value, outer) - inner) / (outer - inner)
    gamma = max(0.2, min(cal.curve, 4.0))
    return _clamp(scaled**gamma, 0.0, 1.0)


def apply_calibration(state: NormalizedState, cal: Calibration) -> NormalizedState:
    lx, ly = apply_stick(state.lx, state.ly, cal.left)
    rx, ry = apply_stick(state.rx, state.ry, cal.right)
    return replace(
        state,
        lx=lx,
        ly=ly,
        rx=rx,
        ry=ry,
        lt=apply_trigger(state.lt, cal.lt),
        rt=apply_trigger(state.rt, cal.rt),
    )
