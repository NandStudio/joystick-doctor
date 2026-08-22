from __future__ import annotations

import threading
import time
from collections.abc import Callable

from engine.state import NormalizedState

StateSource = Callable[[], NormalizedState | None]


class VirtualXbox:
    """Xbox 360 virtual pad. Passthrough until the calibration pipeline exists."""

    def __init__(self):
        self._pad = None
        self._source: StateSource | None = None
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._error: BaseException | None = None
        self._lock = threading.Lock()

    def running(self) -> bool:
        return self._thread is not None

    def error(self) -> BaseException | None:
        with self._lock:
            return self._error

    def start(self, source: StateSource) -> None:
        if self._thread is not None:
            return
        try:
            import vgamepad
        except ImportError as exc:
            raise RuntimeError("vgamepad is not installed") from exc
        try:
            self._pad = vgamepad.VX360Gamepad()
        except Exception as exc:
            raise RuntimeError(
                "ViGEmBus is missing or failed. Install it, then retry."
            ) from exc
        self._source = source
        self._stop.clear()
        with self._lock:
            self._error = None
        self._thread = threading.Thread(target=self._run, name="virtual-xbox", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        if self._pad is not None:
            try:
                self._pad.reset()
                self._pad.update()
            except Exception:
                pass
            self._pad = None
        self._source = None

    def _run(self) -> None:
        import vgamepad

        buttons = (
            ("a", vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_A),
            ("b", vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_B),
            ("x", vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_X),
            ("y", vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_Y),
            ("lb", vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER),
            ("rb", vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER),
            ("ls", vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB),
            ("rs", vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB),
            ("back", vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_BACK),
            ("start", vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_START),
            ("guide", vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE),
            ("dpad_up", vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP),
            ("dpad_down", vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN),
            ("dpad_left", vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT),
            ("dpad_right", vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT),
        )
        period = 1.0 / 250.0
        while not self._stop.is_set():
            started = time.perf_counter()
            state = self._source() if self._source else None
            if state is not None and self._pad is not None:
                try:
                    self._apply(state, buttons)
                except Exception as exc:
                    with self._lock:
                        self._error = exc
                    return
            elapsed = time.perf_counter() - started
            remaining = period - elapsed
            if remaining > 0:
                time.sleep(remaining)

    def _apply(self, state: NormalizedState, buttons: tuple) -> None:
        pad = self._pad
        pad.left_joystick_float(
            x_value_float=_stick(state.lx),
            y_value_float=_stick(state.ly),
        )
        pad.right_joystick_float(
            x_value_float=_stick(state.rx),
            y_value_float=_stick(state.ry),
        )
        pad.left_trigger_float(_trigger(state.lt))
        pad.right_trigger_float(_trigger(state.rt))
        for name, button in buttons:
            if getattr(state, name):
                pad.press_button(button=button)
            else:
                pad.release_button(button=button)
        pad.update()


def _stick(value: float) -> float:
    return max(-1.0, min(1.0, value))


def _trigger(value: float) -> float:
    return max(0.0, min(1.0, value))
