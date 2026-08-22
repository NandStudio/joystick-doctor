from __future__ import annotations

import ctypes
import time
from ctypes import wintypes

from engine.state import DeviceIdentity, NormalizedState

_BACKEND = "xinput"
_ERROR_SUCCESS = 0
_MAX_USERS = 4

_DPAD_UP = 0x0001
_DPAD_DOWN = 0x0002
_DPAD_LEFT = 0x0004
_DPAD_RIGHT = 0x0008
_START = 0x0010
_BACK = 0x0020
_LEFT_THUMB = 0x0040
_RIGHT_THUMB = 0x0080
_LEFT_SHOULDER = 0x0100
_RIGHT_SHOULDER = 0x0200
_GUIDE = 0x0400
_A = 0x1000
_B = 0x2000
_X = 0x4000
_Y = 0x8000


class XINPUT_GAMEPAD(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("wButtons", wintypes.WORD),
        ("bLeftTrigger", wintypes.BYTE),
        ("bRightTrigger", wintypes.BYTE),
        ("sThumbLX", wintypes.SHORT),
        ("sThumbLY", wintypes.SHORT),
        ("sThumbRX", wintypes.SHORT),
        ("sThumbRY", wintypes.SHORT),
    ]


class XINPUT_STATE(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("dwPacketNumber", wintypes.DWORD),
        ("Gamepad", XINPUT_GAMEPAD),
    ]


def _load_xinput() -> ctypes.WinDLL:
    last_error: OSError | None = None
    for name in ("xinput1_4.dll", "xinput1_3.dll", "xinput9_1_0.dll"):
        try:
            return ctypes.WinDLL(name)
        except OSError as exc:
            last_error = exc
    raise OSError("XInput DLL not found") from last_error


_dll = _load_xinput()
_get_state = _dll.XInputGetState
_get_state.argtypes = [wintypes.DWORD, ctypes.POINTER(XINPUT_STATE)]
_get_state.restype = wintypes.DWORD

try:
    _get_state_ex = _dll[100]
    _get_state_ex.argtypes = [wintypes.DWORD, ctypes.POINTER(XINPUT_STATE)]
    _get_state_ex.restype = wintypes.DWORD
except (AttributeError, ValueError, OSError):
    _get_state_ex = _get_state


def _axis_i16(value: int) -> float:
    if value < 0:
        return max(-1.0, value / 32768.0)
    return min(1.0, value / 32767.0)


def _poll(index: int) -> XINPUT_STATE | None:
    state = XINPUT_STATE()
    if _get_state_ex(index, ctypes.byref(state)) != _ERROR_SUCCESS:
        return None
    return state


def enumerate_devices() -> list[DeviceIdentity]:
    devices: list[DeviceIdentity] = []
    for index in range(_MAX_USERS):
        if _poll(index) is None:
            continue
        devices.append(
            DeviceIdentity(
                vendor_id=0,
                product_id=index,
                backend=_BACKEND,
                path=f"xinput:{index}",
                product_name=f"XInput player {index + 1}",
                index=index,
            )
        )
    return devices


def parse_state(packet: XINPUT_STATE) -> NormalizedState:
    pad = packet.Gamepad
    buttons = pad.wButtons
    return NormalizedState(
        lx=_axis_i16(pad.sThumbLX),
        ly=_axis_i16(pad.sThumbLY),
        rx=_axis_i16(pad.sThumbRX),
        ry=_axis_i16(pad.sThumbRY),
        lt=(pad.bLeftTrigger & 0xFF) / 255.0,
        rt=(pad.bRightTrigger & 0xFF) / 255.0,
        a=bool(buttons & _A),
        b=bool(buttons & _B),
        x=bool(buttons & _X),
        y=bool(buttons & _Y),
        lb=bool(buttons & _LEFT_SHOULDER),
        rb=bool(buttons & _RIGHT_SHOULDER),
        ls=bool(buttons & _LEFT_THUMB),
        rs=bool(buttons & _RIGHT_THUMB),
        back=bool(buttons & _BACK),
        start=bool(buttons & _START),
        guide=bool(buttons & _GUIDE),
        dpad_up=bool(buttons & _DPAD_UP),
        dpad_down=bool(buttons & _DPAD_DOWN),
        dpad_left=bool(buttons & _DPAD_LEFT),
        dpad_right=bool(buttons & _DPAD_RIGHT),
        timestamp=time.perf_counter(),
    )


class XInputReader:
    def __init__(self, identity: DeviceIdentity):
        if identity.index is None:
            raise ValueError("XInputReader needs DeviceIdentity.index")
        self.identity = identity
        self._index = identity.index

    def open(self) -> None:
        return None

    def close(self) -> None:
        return None

    def read(self) -> NormalizedState | None:
        packet = _poll(self._index)
        if packet is None:
            return None
        return parse_state(packet)

    def __enter__(self) -> XInputReader:
        self.open()
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def _print_loop() -> None:
    devices = enumerate_devices()
    if not devices:
        print("No XInput pads found. Flip the F310 to X, or plug in an Xbox pad.")
        return
    for i, identity in enumerate(devices):
        print(f"[{i}] {identity.product_name}", flush=True)
    chosen = devices[0]
    print(f"Reading {chosen.product_name} (Ctrl+C to stop)", flush=True)
    reader = XInputReader(chosen)
    last = None
    while True:
        state = reader.read()
        if state is None:
            print("disconnected")
            return
        line = state.format_line()
        if line == last:
            time.sleep(0.004)
            continue
        last = line
        print(line, flush=True)


if __name__ == "__main__":
    _print_loop()
