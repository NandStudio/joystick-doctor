from __future__ import annotations

from dataclasses import dataclass, replace

from engine.state import NormalizedState

BUTTONS = (
    "a",
    "b",
    "x",
    "y",
    "lb",
    "rb",
    "ls",
    "rs",
    "back",
    "start",
    "guide",
    "dpad_up",
    "dpad_down",
    "dpad_left",
    "dpad_right",
    "lt",
    "rt",
)


@dataclass(frozen=True, slots=True)
class RemapRule:
    sources: tuple[str, ...]
    dest: str
    toggle_hold: str | None = None


@dataclass(slots=True)
class RemapConfig:
    rules: list[RemapRule]
    trigger_threshold: float = 0.5
    consume_sources: bool = True


class RemapEngine:
    def __init__(self, config: RemapConfig | None = None):
        self.config = config or RemapConfig([])
        self._hold_prev: dict[str, bool] = {}
        self._rule_on: dict[int, bool] = {}

    def apply(self, state: NormalizedState) -> NormalizedState:
        digital = _digital(state, self.config.trigger_threshold)
        out = dict(digital)
        consumed: set[str] = set()
        forced_on: set[str] = set()
        rules = sorted(self.config.rules, key=lambda rule: len(rule.sources), reverse=True)
        for index, rule in enumerate(rules):
            if not _valid(rule):
                continue
            if rule.toggle_hold:
                held = digital.get(rule.toggle_hold, False)
                prev = self._hold_prev.get(rule.toggle_hold, False)
                if held and not prev:
                    self._rule_on[index] = not self._rule_on.get(index, False)
                self._hold_prev[rule.toggle_hold] = held
                if not self._rule_on.get(index, False):
                    continue
            if not all(digital.get(src, False) for src in rule.sources):
                continue
            out[rule.dest] = True
            forced_on.add(rule.dest)
            if self.config.consume_sources:
                consumed.update(rule.sources)
        for name in consumed:
            out[name] = False
        return _write(state, out, consumed, forced_on)


def _valid(rule: RemapRule) -> bool:
    return rule.dest in BUTTONS and all(src in BUTTONS for src in rule.sources)


def _digital(state: NormalizedState, threshold: float) -> dict[str, bool]:
    values = {name: bool(getattr(state, name)) for name in BUTTONS if name not in ("lt", "rt")}
    values["lt"] = state.lt >= threshold
    values["rt"] = state.rt >= threshold
    return values


def _write(
    state: NormalizedState,
    digital: dict[str, bool],
    consumed: set[str],
    forced_on: set[str],
) -> NormalizedState:
    updates = {name: digital[name] for name in BUTTONS if name not in ("lt", "rt")}
    lt = state.lt
    rt = state.rt
    if "lt" in consumed:
        lt = 0.0
    if "rt" in consumed:
        rt = 0.0
    if "lt" in forced_on:
        lt = 1.0
    if "rt" in forced_on:
        rt = 1.0
    return replace(state, lt=lt, rt=rt, **updates)
