from __future__ import annotations

import time

import hid

from engine.device.ds4 import parse_report as parse_ds4
from engine.device.ds5 import parse_report as parse_ds5
from engine.state import DeviceIdentity, NormalizedState

_GENERIC_DESKTOP = 0x01
_JOYSTICK_USAGES = {0x04, 0x05}
_BACKEND = "hid_generic"
_SONY_VID = 0x054C
_DS4_PIDS = {0x05C4, 0x09CC, 0x0BA0}
_DS5_PIDS = {0x0CE6, 0x0DF2}
_LOGITECH_VID = 0x046D
_F310_PID = 0xC21D

_BUTTON_ORDER = (
    "a",
    "b",
    "x",
    "y",
    "lb",
    "rb",
    "back",
    "start",
    "ls",
    "rs",
    "guide",
)

_HAT_TO_DPAD = {
    0: (True, False, False, False),
    1: (True, False, False, True),
    2: (False, False, False, True),
    3: (False, True, False, True),
    4: (False, True, False, False),
    5: (False, True, True, False),
    6: (False, False, True, False),
    7: (True, False, True, False),
}


def enumerate_devices() -> list[DeviceIdentity]:
    devices: list[DeviceIdentity] = []
    for info in hid.enumerate():
        if info.get("usage_page") != _GENERIC_DESKTOP:
            continue
        if info.get("usage") not in _JOYSTICK_USAGES:
            continue
        devices.append(
            DeviceIdentity(
                vendor_id=info.get("vendor_id") or 0,
                product_id=info.get("product_id") or 0,
                backend=_BACKEND,
                path=info["path"],
                product_name=info.get("product_string") or "Unknown HID",
            )
        )
    return devices


def _axis_u8(value: int) -> float:
    return max(-1.0, min(1.0, (value / 255.0) * 2.0 - 1.0))


def _trigger_u8(value: int) -> float:
    return max(0.0, min(1.0, value / 255.0))


def _hat(nibble: int) -> tuple[bool, bool, bool, bool]:
    return _HAT_TO_DPAD.get(nibble & 0x0F, (False, False, False, False))


def _apply_hat(state: NormalizedState, nibble: int) -> None:
    up, down, left, right = _hat(nibble)
    state.dpad_up = up
    state.dpad_down = down
    state.dpad_left = left
    state.dpad_right = right


def _apply_buttons(state: NormalizedState, bits: int) -> None:
    for index, name in enumerate(_BUTTON_ORDER):
        setattr(state, name, bool(bits & (1 << index)))


def _apply_sticks(state: NormalizedState, data: bytes, offset: int = 0) -> None:
    state.lx = _axis_u8(data[offset])
    state.ly = -_axis_u8(data[offset + 1])
    state.rx = _axis_u8(data[offset + 2])
    state.ry = -_axis_u8(data[offset + 3])


def _payload(data: bytes) -> bytes:
    if len(data) > 8 and data[0] == 0x01:
        return data[1:]
    return data


def _axis_i16(value: int) -> float:
    return max(-1.0, min(1.0, value / 32767.0))


def _is_x360_report(data: bytes) -> bool:
    if len(data) < 14:
        return False
    if data[0] == 0x00 and data[1] == 0x14:
        return True
    return data[0] == 0x14 and len(data) >= 13


def _parse_x360(data: bytes) -> NormalizedState:
    off = 0 if data[0] == 0x00 and data[1] == 0x14 else -1
    state = NormalizedState(timestamp=time.perf_counter())
    digital = data[2 + off]
    face = data[3 + off]
    state.dpad_up = bool(digital & 0x01)
    state.dpad_down = bool(digital & 0x02)
    state.dpad_left = bool(digital & 0x04)
    state.dpad_right = bool(digital & 0x08)
    state.start = bool(digital & 0x10)
    state.back = bool(digital & 0x20)
    state.ls = bool(digital & 0x40)
    state.rs = bool(digital & 0x80)
    state.lb = bool(face & 0x01)
    state.rb = bool(face & 0x02)
    state.guide = bool(face & 0x04)
    state.a = bool(face & 0x10)
    state.b = bool(face & 0x20)
    state.x = bool(face & 0x40)
    state.y = bool(face & 0x80)
    state.lt = _trigger_u8(data[4 + off])
    state.rt = _trigger_u8(data[5 + off])
    state.lx = _axis_i16(int.from_bytes(data[6 + off : 8 + off], "little", signed=True))
    state.ly = _axis_i16(int.from_bytes(data[8 + off : 10 + off], "little", signed=True))
    state.rx = _axis_i16(int.from_bytes(data[10 + off : 12 + off], "little", signed=True))
    state.ry = _axis_i16(int.from_bytes(data[12 + off : 14 + off], "little", signed=True))
    return state


def _parse_generic_u8(payload: bytes) -> NormalizedState:
    state = NormalizedState(timestamp=time.perf_counter())
    if len(payload) >= 4:
        _apply_sticks(state, payload)
    # Hat is a low nibble 0-8; high nibble must be 0 so 0x80 is not "up".
    if len(payload) >= 6 and payload[4] <= 8:
        _apply_hat(state, payload[4])
        bits = payload[5]
        if len(payload) >= 7:
            bits |= payload[6] << 8
        _apply_buttons(state, bits)
    return state


def _looks_like_dup16(data: bytes) -> bool:
    if len(data) < 8:
        return False
    return all(data[i] == data[i + 1] for i in (0, 2, 4, 6))


def _parse_dup16(data: bytes) -> NormalizedState:
    """8-bit axes stuffed into 16-bit slots (Logitech F310 D-input, etc.)."""
    state = NormalizedState(timestamp=time.perf_counter())
    state.lx = _axis_u8(data[0])
    state.ly = -_axis_u8(data[2])
    state.rx = _axis_u8(data[4])
    state.ry = -_axis_u8(data[6])
    if len(data) >= 10:
        hat16 = int.from_bytes(data[8:10], "little")
        if hat16 != 0x8000 and hat16 != 0xFFFF:
            if hat16 <= 8:
                _apply_hat(state, hat16)
            elif hat16 % 4500 == 0 and hat16 <= 31500:
                _apply_hat(state, hat16 // 4500)
    bits = 0
    if len(data) > 10:
        bits = data[10]
    if len(data) > 11:
        bits |= data[11] << 8
    # F310 D-input: A B X Y LB RB Back Start LS RS (LT/RT are those same
    # digital buttons on some firmware; they are not bits 6-7).
    _apply_buttons(state, bits)
    return state


def parse_report(data: bytes, identity: DeviceIdentity | None = None) -> NormalizedState:
    if _is_x360_report(data):
        return _parse_x360(data)
    vid = identity.vendor_id if identity else 0
    pid = identity.product_id if identity else 0
    if vid == _LOGITECH_VID and pid == _F310_PID:
        return _parse_dup16(data)
    if _looks_like_dup16(data):
        return _parse_dup16(data)
    if vid == _SONY_VID and pid in _DS5_PIDS:
        return parse_ds5(data)
    if vid == _SONY_VID and pid in _DS4_PIDS:
        return parse_ds4(data)
    return _parse_generic_u8(_payload(data))


class GenericHidReader:
    def __init__(self, identity: DeviceIdentity):
        self.identity = identity
        self._dev: hid.device | None = None

    def open(self) -> None:
        device = hid.device()
        path = self.identity.path
        if isinstance(path, str):
            path = path.encode("ascii")
        device.open_path(path)
        device.set_nonblocking(True)
        self._dev = device

    def close(self) -> None:
        if self._dev is not None:
            self._dev.close()
            self._dev = None

    def read_raw(self) -> bytes | None:
        if self._dev is None:
            raise RuntimeError("GenericHidReader is not open")
        data = self._dev.read(64)
        if not data:
            return None
        return bytes(data)

    def read(self) -> NormalizedState | None:
        data = self.read_raw()
        if data is None:
            return None
        return parse_report(data, self.identity)

    def __enter__(self) -> GenericHidReader:
        self.open()
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def listDevices():
    """Back-compat name used by engine.libs.hidWrapper."""
    from engine.libs.models import Controller

    return [
        Controller(dev.path, dev.product_id, dev.product_name)
        for dev in enumerate_devices()
    ]


def _print_loop() -> None:
    devices = enumerate_devices()
    if not devices:
        print("No HID joysticks/gamepads found.")
        return
    for i, identity in enumerate(devices):
        print(
            f"[{i}] {identity.product_name} "
            f"VID={identity.vendor_id:04X} PID={identity.product_id:04X}",
            flush=True,
        )
    chosen = devices[0]
    print(f"Reading {chosen.product_name} (Ctrl+C to stop)", flush=True)
    with GenericHidReader(chosen) as reader:
        last = None
        while True:
            data = reader.read_raw()
            if data is None:
                time.sleep(0.004)
                continue
            line = f"{data[:18].hex(' ')} | {parse_report(data, chosen).format_line()}"
            if line == last:
                continue
            last = line
            print(line, flush=True)


if __name__ == "__main__":
    _print_loop()
