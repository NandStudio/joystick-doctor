from __future__ import annotations

import time

import hid

from engine.device.hid_util import (
    GENERIC_DESKTOP,
    JOYSTICK_USAGES,
    HidPathReader,
    apply_hat,
    apply_sticks_u8,
    print_loop,
    trigger_u8,
)
from engine.state import DeviceIdentity, NormalizedState

VID = 0x054C
PIDS = {0x0268, 0x042F}
# Cheap USB pads sold as "PS3": hat + Sony face order, not the Sony report.
CLONE_IDS = {
    (0x0810, 0x0001),
    (0x2563, 0x0575),
    (0x2563, 0x0523),
    (0x20D6, 0xCA6D),
}
_BACKEND = "ds3"
_ENABLE = bytes([0xF4, 0x42, 0x0C, 0x00, 0x00])
_NAMES = {
    0x0268: "DualShock 3",
    0x042F: "PS3 Navigation",
}


def enumerate_devices() -> list[DeviceIdentity]:
    devices: list[DeviceIdentity] = []
    seen: set[bytes | str] = set()
    gamepads: list[DeviceIdentity] = []
    others: list[DeviceIdentity] = []
    for info in hid.enumerate():
        vid = info.get("vendor_id") or 0
        pid = info.get("product_id") or 0
        if not _is_ds3_id(vid, pid):
            continue
        path = info["path"]
        if path in seen:
            continue
        seen.add(path)
        identity = DeviceIdentity(
            vendor_id=vid,
            product_id=pid,
            backend=_BACKEND,
            path=path,
            product_name=info.get("product_string") or _NAMES.get(pid, "PS3 controller"),
        )
        usage_page = info.get("usage_page")
        usage = info.get("usage")
        if usage_page == GENERIC_DESKTOP and usage in JOYSTICK_USAGES:
            gamepads.append(identity)
        else:
            others.append(identity)
    devices.extend(gamepads)
    if not devices:
        devices.extend(others)
    return devices


def _is_ds3_id(vendor_id: int, product_id: int) -> bool:
    if vendor_id == VID and product_id in PIDS:
        return True
    return (vendor_id, product_id) in CLONE_IDS


def _native_payload(data: bytes) -> bytes:
    if data and data[0] == 0x01 and len(data) >= 20:
        return data[1:]
    return data


def _looks_native(data: bytes) -> bool:
    payload = _native_payload(data)
    # Official USB/BT report is ~48 bytes and starts with padding 0x00.
    return len(payload) >= 20 and payload[0] == 0x00


def parse_native(data: bytes) -> NormalizedState:
    payload = _native_payload(data)
    state = NormalizedState()
    if len(payload) < 10:
        return state
    buttons = payload[1]
    face = payload[2]
    state.back = bool(buttons & 0x01)
    state.ls = bool(buttons & 0x02)
    state.rs = bool(buttons & 0x04)
    state.start = bool(buttons & 0x08)
    state.dpad_up = bool(buttons & 0x10)
    state.dpad_right = bool(buttons & 0x20)
    state.dpad_down = bool(buttons & 0x40)
    state.dpad_left = bool(buttons & 0x80)
    l2 = bool(face & 0x01)
    r2 = bool(face & 0x02)
    state.lb = bool(face & 0x04)
    state.rb = bool(face & 0x08)
    state.y = bool(face & 0x10)  # triangle
    state.b = bool(face & 0x20)  # circle
    state.a = bool(face & 0x40)  # cross
    state.x = bool(face & 0x80)  # square
    state.guide = bool(payload[3] & 0x01)
    apply_sticks_u8(state, payload, 5)
    if len(payload) > 19:
        state.lt = trigger_u8(payload[17])
        state.rt = trigger_u8(payload[18])
    if state.lt == 0.0 and l2:
        state.lt = 1.0
    if state.rt == 0.0 and r2:
        state.rt = 1.0
    state.timestamp = time.perf_counter()
    return state


def parse_clone_hid(data: bytes) -> NormalizedState:
    payload = data[1:] if data and data[0] == 0x01 and len(data) > 8 else data
    state = NormalizedState()
    if len(payload) < 5:
        return state
    apply_sticks_u8(state, payload)
    apply_hat(state, payload[4])
    bits = payload[5] if len(payload) > 5 else 0
    if len(payload) > 6:
        bits |= payload[6] << 8
    # Typical PC-PS3 HID: △ ○ × □ L1 R1 L2 R2 Select Start L3 R3
    state.y = bool(bits & 0x01)
    state.b = bool(bits & 0x02)
    state.a = bool(bits & 0x04)
    state.x = bool(bits & 0x08)
    state.lb = bool(bits & 0x10)
    state.rb = bool(bits & 0x20)
    state.lt = 1.0 if bits & 0x40 else 0.0
    state.rt = 1.0 if bits & 0x80 else 0.0
    state.back = bool(bits & 0x100)
    state.start = bool(bits & 0x200)
    state.ls = bool(bits & 0x400)
    state.rs = bool(bits & 0x800)
    state.timestamp = time.perf_counter()
    return state


def parse_report(data: bytes) -> NormalizedState:
    if _looks_native(data):
        return parse_native(data)
    return parse_clone_hid(data)


def enable_reports(reader: HidPathReader) -> None:
    """Sony USB Sixaxis stays silent until this feature report is sent."""
    try:
        reader.send_feature_report(_ENABLE)
    except (OSError, ValueError):
        pass


class Ds3Reader(HidPathReader):
    def open(self) -> None:
        super().open()
        if self.identity.vendor_id == VID and self.identity.product_id in PIDS:
            enable_reports(self)

    def read(self) -> NormalizedState | None:
        data = self.read_raw()
        if data is None:
            return None
        return parse_report(data)


if __name__ == "__main__":
    print_loop(enumerate_devices(), Ds3Reader, parse_report)
