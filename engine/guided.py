from __future__ import annotations

import math
import time
from dataclasses import replace

from engine.pipeline import Calibration
from engine.remap import BUTTONS
from engine.state import NormalizedState

STEPS = ("rest", "left", "right", "triggers", "buttons")

_BUTTON_LABEL = {
    "a": "A",
    "b": "B",
    "x": "X",
    "y": "Y",
    "lb": "LB",
    "rb": "RB",
    "ls": "LS",
    "rs": "RS",
    "back": "Back",
    "start": "Start",
    "guide": "Guide",
    "dpad_up": "Up",
    "dpad_down": "Down",
    "dpad_left": "Left",
    "dpad_right": "Right",
    "lt": "LT",
    "rt": "RT",
}


class GuidedSession:
    def __init__(self) -> None:
        self.active = False
        self.index = 0
        self.error = ""
        self._buckets = {name: [] for name in STEPS}

    def start(self) -> None:
        self.active = True
        self.index = 0
        self.error = ""
        self._buckets = {name: [] for name in STEPS}

    def stop(self) -> None:
        self.active = False
        self.error = ""

    def step(self) -> str:
        return STEPS[self.index]

    def feed(self, state: NormalizedState) -> None:
        if not self.active:
            return
        stamped = replace(state, timestamp=time.perf_counter())
        self._buckets[self.step()].append(stamped)

    def back(self) -> None:
        if self.index <= 0:
            return
        self.index -= 1
        self.error = ""
        for name in STEPS[self.index :]:
            self._buckets[name] = []

    def advance(self) -> str:
        problem = self._problem()
        if problem:
            self.error = problem
            return "stay"
        self.error = ""
        if self.index >= len(STEPS) - 1:
            return "done"
        self.index += 1
        return "ok"

    def phase(self) -> str:
        if self.error:
            return "error"
        if self._satisfied():
            return "ready"
        if self._buckets[self.step()]:
            return "measuring"
        return "empty"

    def measure(self) -> tuple[str, dict[str, object]] | None:
        if not self.active:
            return None
        step = self.step()
        samples = self._buckets[step]
        if step == "rest":
            window = self._quiet(samples)
            if not window:
                return None
            mx, my, noise = self._rest_stats(window)
            return ("rest_line", {"x": mx, "y": my, "drift": noise})
        if step == "left":
            peak = self._peak(samples, "lx", "ly")
            if peak < 0.85 or not self._full_circle(samples, "lx", "ly"):
                return None
            return ("circle_line", {"peak": peak})
        if step == "right":
            peak = self._peak(samples, "rx", "ry")
            if peak < 0.85 or not self._full_circle(samples, "rx", "ry"):
                return None
            return ("circle_line", {"peak": peak})
        if step == "triggers":
            if not samples or self._trigger_problem(samples):
                return None
            return (
                "trigger_line",
                {"lt": max(item.lt for item in samples), "rt": max(item.rt for item in samples)},
            )
        if not samples:
            return None
        missing = self.doubtful()
        if missing:
            names = ", ".join(_BUTTON_LABEL[name] for name in missing)
            return ("doubtful_line", {"names": names})
        return ("doubtful_none", {})

    def doubtful(self) -> list[str]:
        seen: set[str] = set()
        for state in self._buckets["buttons"]:
            for name in BUTTONS:
                if name in ("lt", "rt"):
                    if getattr(state, name) >= 0.5:
                        seen.add(name)
                elif getattr(state, name):
                    seen.add(name)
        return [name for name in BUTTONS if name not in seen]

    def summary(self) -> str:
        rest = self._quiet(self._buckets["rest"]) or []
        lmx, lmy, noise = self._rest_stats_axis(rest, "lx", "ly")
        rmx, rmy, _rnoise = self._rest_stats_axis(rest, "rx", "ry")
        left_peak = self._peak(self._buckets["left"], "lx", "ly")
        right_peak = self._peak(self._buckets["right"], "rx", "ry")
        triggers = self._buckets["triggers"]
        lt = max((item.lt for item in triggers), default=0.0)
        rt = max((item.rt for item in triggers), default=0.0)
        text = (
            f"LS {lmx:+.2f},{lmy:+.2f} RS {rmx:+.2f},{rmy:+.2f} "
            f"drift {noise:.3f} "
            f"radius L {left_peak:.2f} R {right_peak:.2f} "
            f"LT {lt:.2f} RT {rt:.2f}"
        )
        missing = self.doubtful()
        if missing:
            names = ", ".join(_BUTTON_LABEL[name] for name in missing)
            text += f" doubtful {names}"
        return text

    def apply(self, base: Calibration) -> Calibration:
        rest = self._quiet(self._buckets["rest"]) or self._buckets["rest"]
        lmx, lmy, lnoise = self._rest_stats_axis(rest, "lx", "ly")
        rmx, rmy, rnoise = self._rest_stats_axis(rest, "rx", "ry")
        left_peak = self._peak(self._buckets["left"], "lx", "ly")
        right_peak = self._peak(self._buckets["right"], "rx", "ry")
        triggers = self._buckets["triggers"]
        lt_peak = max((item.lt for item in triggers), default=base.lt.outer)
        rt_peak = max((item.rt for item in triggers), default=base.rt.outer)
        left_inner = _inner_from_noise(lnoise)
        right_inner = _inner_from_noise(rnoise)
        base.left.center_x = lmx
        base.left.center_y = lmy
        base.left.inner = left_inner
        base.left.outer = _outer_from_peak(left_peak, left_inner)
        base.right.center_x = rmx
        base.right.center_y = rmy
        base.right.inner = right_inner
        base.right.outer = _outer_from_peak(right_peak, right_inner)
        base.lt.outer = _outer_from_peak(lt_peak, base.lt.inner)
        base.rt.outer = _outer_from_peak(rt_peak, base.rt.inner)
        return base

    def _satisfied(self) -> bool:
        if self.step() == "buttons":
            return bool(self._buckets["buttons"])
        return self._problem() == ""

    def _problem(self) -> str:
        step = self.step()
        samples = self._buckets[step]
        if step == "rest":
            return "" if self._quiet(samples) else "rest"
        if step == "left":
            return "" if self._full_circle(samples, "lx", "ly") else "left"
        if step == "right":
            return "" if self._full_circle(samples, "rx", "ry") else "right"
        if step == "triggers":
            return self._trigger_problem(samples)
        return ""

    def _quiet(self, samples: list[NormalizedState]) -> list[NormalizedState] | None:
        if len(samples) < 2:
            return None
        end = samples[-1].timestamp
        window = [item for item in samples if end - item.timestamp <= 3.0]
        if not window or window[-1].timestamp - window[0].timestamp < 2.9:
            return None
        for xn, yn in (("lx", "ly"), ("rx", "ry")):
            xs = [getattr(item, xn) for item in window]
            ys = [getattr(item, yn) for item in window]
            mx = sum(xs) / len(xs)
            my = sum(ys) / len(ys)
            peak = max(math.hypot(x - mx, y - my) for x, y in zip(xs, ys))
            if peak > 0.12:
                return None
        if max(item.lt for item in window) > 0.2 or max(item.rt for item in window) > 0.2:
            return None
        return window

    def _full_circle(self, samples: list[NormalizedState], xn: str, yn: str) -> bool:
        if self._peak(samples, xn, yn) < 0.85:
            return False
        quadrants: set[tuple[bool, bool]] = set()
        for item in samples:
            x = getattr(item, xn)
            y = getattr(item, yn)
            if math.hypot(x, y) < 0.55:
                continue
            quadrants.add((x >= 0, y >= 0))
        return len(quadrants) >= 4

    def _trigger_problem(self, samples: list[NormalizedState]) -> str:
        if not samples:
            return "both"
        lt = max(item.lt for item in samples)
        rt = max(item.rt for item in samples)
        if lt < 0.9 and rt < 0.9:
            return "both"
        if lt < 0.9:
            return "lt"
        if rt < 0.9:
            return "rt"
        return ""

    def _peak(self, samples: list[NormalizedState], xn: str, yn: str) -> float:
        if not samples:
            return 0.0
        return max(math.hypot(getattr(item, xn), getattr(item, yn)) for item in samples)

    def _rest_stats_axis(
        self, window: list[NormalizedState], xn: str, yn: str
    ) -> tuple[float, float, float]:
        if not window:
            return 0.0, 0.0, 0.0
        xs = [getattr(item, xn) for item in window]
        ys = [getattr(item, yn) for item in window]
        mx = sum(xs) / len(xs)
        my = sum(ys) / len(ys)
        noise = math.hypot(
            math.sqrt(sum((x - mx) ** 2 for x in xs) / len(xs)),
            math.sqrt(sum((y - my) ** 2 for y in ys) / len(ys)),
        )
        return mx, my, noise

def _inner_from_noise(noise: float) -> float:
    return min(0.40, max(0.04, noise * 2.5 + 0.02))


def _outer_from_peak(peak: float, inner: float) -> float:
    outer = min(1.0, max(peak, inner + 0.01))
    return max(inner + 0.01, outer)
