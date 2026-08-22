from __future__ import annotations

import math
import time
from dataclasses import dataclass

from engine.state import NormalizedState

_PHASES = (
    ("rest", 3.0, "Keep the pad still"),
    ("range", 5.0, "Move both sticks in full circles"),
    ("triggers", 4.0, "Press LT and RT all the way"),
)


@dataclass(slots=True)
class AxisScore:
    name: str
    score: int
    detail: str
    deadzone_hint: float | None = None
    center_x: float | None = None
    center_y: float | None = None


@dataclass(slots=True)
class Rec:
    key: str
    params: dict[str, object]


@dataclass(slots=True)
class Diagnosis:
    scores: list[AxisScore]
    global_score: int
    recommendations: list[Rec]


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _rms(values: list[float], center: float) -> float:
    if not values:
        return 0.0
    return math.sqrt(sum((v - center) ** 2 for v in values) / len(values))


def _score_rest(offset: float, noise: float) -> int:
    penalty = offset * 180 + noise * 220
    return max(0, min(100, int(round(100 - penalty))))


def _score_reach(peak: float) -> int:
    return max(0, min(100, int(round(peak * 100))))


def analyze(rest: list[NormalizedState], motion: list[NormalizedState], triggers: list[NormalizedState]) -> Diagnosis:
    scores: list[AxisScore] = []
    recs: list[Rec] = []
    if not rest:
        return Diagnosis(
            [AxisScore("all", 0, "No rest samples")],
            0,
            [Rec("rec_rest_again", {})],
        )

    pairs = (
        ("LS", "lx", "ly"),
        ("RS", "rx", "ry"),
    )
    for name, xn, yn in pairs:
        xs = [getattr(s, xn) for s in rest]
        ys = [getattr(s, yn) for s in rest]
        mx, my = _mean(xs), _mean(ys)
        offset = math.hypot(mx, my)
        noise = math.hypot(_rms(xs, mx), _rms(ys, my))
        hint = min(0.40, max(0.04, offset + noise * 2.5 + 0.02))
        score = _score_rest(offset, noise)
        scores.append(
            AxisScore(
                name,
                score,
                f"center {mx:+.3f},{my:+.3f}  noise {noise:.3f}",
                hint,
                mx,
                my,
            )
        )
        if score < 80:
            recs.append(Rec("rec_deadzone", {"name": name, "pct": int(round(hint * 100))}))
            if offset > 0.04:
                recs.append(Rec("rec_recenter", {"name": name, "offset": offset}))

    if motion:
        for name, xn, yn in pairs:
            peak = max(math.hypot(getattr(s, xn), getattr(s, yn)) for s in motion)
            scores.append(AxisScore(f"{name} range", _score_reach(peak), f"peak {peak:.2f}"))
            if peak < 0.85:
                recs.append(Rec("rec_range", {"name": name, "peak": peak}))

    if triggers:
        for name, attr in (("LT", "lt"), ("RT", "rt")):
            peak = max(getattr(s, attr) for s in triggers)
            scores.append(AxisScore(name, _score_reach(peak), f"peak {peak:.2f}"))
            if peak < 0.9:
                recs.append(Rec("rec_trigger", {"name": name, "peak": peak}))

    global_score = int(round(sum(item.score for item in scores) / len(scores)))
    if not recs:
        recs.append(Rec("rec_none", {}))
    return Diagnosis(scores, global_score, recs)


class DiagnoseRunner:
    def __init__(self):
        self.phase: str | None = None
        self._index = -1
        self._started = 0.0
        self._buckets: dict[str, list[NormalizedState]] = {}
        self.result: Diagnosis | None = None

    def running(self) -> bool:
        return self.phase is not None

    def start(self) -> None:
        self._index = 0
        self._started = time.perf_counter()
        self._buckets = {name: [] for name, _dur, _hint in _PHASES}
        self.result = None
        self.phase = _PHASES[0][0]

    def remaining(self) -> float:
        if self.phase is None:
            return 0.0
        duration = _PHASES[self._index][1]
        return max(0.0, duration - (time.perf_counter() - self._started))

    def instruction(self) -> str:
        if self.phase is None:
            return "Diagnosis idle"
        _name, _duration, hint = _PHASES[self._index]
        return f"{hint} ({self.remaining():.1f}s)"

    def feed(self, state: NormalizedState) -> None:
        if self.phase is None:
            return
        name, duration, _hint = _PHASES[self._index]
        self._buckets[name].append(state)
        if time.perf_counter() - self._started < duration:
            return
        self._index += 1
        if self._index >= len(_PHASES):
            self.result = analyze(
                self._buckets["rest"],
                self._buckets["range"],
                self._buckets["triggers"],
            )
            self.phase = None
            return
        self.phase = _PHASES[self._index][0]
        self._started = time.perf_counter()
