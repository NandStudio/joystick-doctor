from __future__ import annotations

import threading
import time
from dataclasses import dataclass

import hid

from engine.device.ds3 import CLONE_IDS as _DS3_CLONES
from engine.device.ds3 import PIDS as _DS3_PIDS
from engine.device.ds3 import PS1_USB_ID as _PS1_USB_ID
from engine.device.ds3 import parse_ps1_usb
from engine.device.ds3 import parse_report as parse_ds3
from engine.device.ds4 import parse_report as parse_ds4
from engine.device.ds5 import parse_report as parse_ds5
from engine.device.hid_util import HidLayout, layout_from_descriptor, parse_hid_layout
from engine.state import DeviceIdentity, NormalizedState

_GENERIC_DESKTOP = 0x01
_JOYSTICK_USAGES = {0x04, 0x05}
_BACKEND = "hid_generic"
_SONY_VID = 0x054C
_DS4_PIDS = {0x05C4, 0x09CC, 0x0BA0}
_DS5_PIDS = {0x0CE6, 0x0DF2}
_LOGITECH_VID = 0x046D
_F310_PID = 0xC21D
_DRAGONRISE_ID = (0x0079, 0x0006)
_TRACE_CAP = 32
_PAGE_DESKTOP = 0x01
_USE_X = 0x30
_USE_Y = 0x31
_WIDE_AXES = {0x32, 0x33, 0x34, 0x35}
# DirectInput gamepads that share one report: hat, then X A B Y LB RB LT RT Back Start LS RS.
# RumblePad 2 is C218 (USB) and C219 (cordless). C216 is the Dual Action / F310 in D.
_LOGITECH_DINPUT = {0xC216, 0xC218, 0xC219}

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
    # A report id of 0x14 is not the Xbox 360 header. That header is 00 14.
    return len(data) >= 14 and data[0] == 0x00 and data[1] == 0x14


def _parse_x360(data: bytes) -> NormalizedState:
    state = NormalizedState(timestamp=time.perf_counter())
    digital = data[2]
    face = data[3]
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
    state.lt = _trigger_u8(data[4])
    state.rt = _trigger_u8(data[5])
    state.lx = _axis_i16(int.from_bytes(data[6:8], "little", signed=True))
    state.ly = _axis_i16(int.from_bytes(data[8:10], "little", signed=True))
    state.rx = _axis_i16(int.from_bytes(data[10:12], "little", signed=True))
    state.ry = _axis_i16(int.from_bytes(data[12:14], "little", signed=True))
    return state


def _logitech_body(data: bytes) -> bytes:
    # Numbered reports start with 0x01. The hat then sits at byte 5.
    if len(data) >= 7 and data[0] == 0x01:
        hat = data[5] & 0x0F
        if hat <= 8 or hat == 0x0F:
            return data[1:]
    return _payload(data)


def _parse_logitech_dinput(data: bytes) -> NormalizedState:
    payload = _logitech_body(data)
    state = NormalizedState(timestamp=time.perf_counter())
    if len(payload) < 6:
        return state
    _apply_sticks(state, payload)
    packed = payload[4]
    _apply_hat(state, packed)
    state.x = bool(packed & 0x10)
    state.a = bool(packed & 0x20)
    state.b = bool(packed & 0x40)
    state.y = bool(packed & 0x80)
    bits = payload[5]
    state.lb = bool(bits & 0x01)
    state.rb = bool(bits & 0x02)
    state.lt = 1.0 if bits & 0x04 else 0.0
    state.rt = 1.0 if bits & 0x08 else 0.0
    state.back = bool(bits & 0x10)
    state.start = bool(bits & 0x20)
    state.ls = bool(bits & 0x40)
    state.rs = bool(bits & 0x80)
    return state


def _is_hat_byte(value: int) -> bool:
    # 0-7 is a direction, 8 and 15 are centered. 0x80 is an axis, not a hat.
    return value <= 8 or value == 0x0F


def _apply_hat_byte(state: NormalizedState, value: int) -> None:
    if value <= 7:
        _apply_hat(state, value)


def _apply_trigger_pair(
    state: NormalizedState,
    primary: int,
    secondary: int,
    trigger_mode: dict[str, str | None] | None,
) -> None:
    # One byte around 128 is both triggers. A second byte near 0 is not RT.
    if trigger_mode is not None and secondary <= 8:
        kind = trigger_mode.get("kind")
        axis = max(-1.0, min(1.0, (primary / 255.0) * 2.0 - 1.0))
        if kind != "split" and abs(axis) <= 0.2:
            trigger_mode["kind"] = "split"
            kind = "split"
        if kind == "split":
            if axis >= 0:
                state.lt, state.rt = axis, 0.0
            else:
                state.lt, state.rt = 0.0, -axis
            return
    state.lt = _trigger_u8(primary)
    state.rt = _trigger_u8(secondary)


def _parse_generic_u8(
    payload: bytes, trigger_mode: dict[str, str | None] | None = None
) -> NormalizedState:
    state = NormalizedState(timestamp=time.perf_counter())
    if len(payload) >= 4:
        _apply_sticks(state, payload)
    # Once the shared trigger is known, byte 4 stays that axis even at 0.
    # Otherwise 0 looks like a hat and RT never registers.
    if (
        trigger_mode is not None
        and trigger_mode.get("kind") == "split"
        and len(payload) >= 5
    ):
        secondary = payload[5] if len(payload) > 5 else 0
        _apply_trigger_pair(state, payload[4], secondary, trigger_mode)
        if len(payload) >= 7 and _is_hat_byte(payload[6]):
            _apply_hat_byte(state, payload[6])
            bits = payload[7] if len(payload) > 7 else 0
            if len(payload) > 8:
                bits |= payload[8] << 8
            _apply_buttons(state, bits)
        return state
    # A hat in byte 4 means this report has no analog triggers.
    if (
        len(payload) >= 8
        and not _is_hat_byte(payload[4])
        and _is_hat_byte(payload[6])
    ):
        _apply_trigger_pair(state, payload[4], payload[5], trigger_mode)
        _apply_hat_byte(state, payload[6])
        bits = payload[7] if len(payload) > 7 else 0
        if len(payload) > 8:
            bits |= payload[8] << 8
        _apply_buttons(state, bits)
        return state
    if len(payload) >= 6 and _is_hat_byte(payload[4]):
        _apply_hat_byte(state, payload[4])
        bits = payload[5]
        if len(payload) >= 7:
            bits |= payload[6] << 8
        _apply_buttons(state, bits)
    elif len(payload) >= 6:
        secondary = payload[5]
        _apply_trigger_pair(state, payload[4], secondary, trigger_mode)
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


def _keeps_own_parser(identity: DeviceIdentity | None) -> bool:
    if identity is None:
        return False
    vid = identity.vendor_id
    pid = identity.product_id
    if (vid, pid) == _PS1_USB_ID:
        return True
    if vid == _LOGITECH_VID and pid in _LOGITECH_DINPUT:
        return True
    if vid == _LOGITECH_VID and pid == _F310_PID:
        return True
    if vid == _SONY_VID and pid in _DS3_PIDS | _DS4_PIDS | _DS5_PIDS:
        return True
    return (vid, pid) in _DS3_CLONES


def parse_report(
    data: bytes,
    identity: DeviceIdentity | None = None,
    trigger_mode: dict[str, str | None] | None = None,
) -> NormalizedState:
    if _is_x360_report(data):
        return _parse_x360(data)
    vid = identity.vendor_id if identity else 0
    pid = identity.product_id if identity else 0
    if (vid, pid) == _PS1_USB_ID:
        return parse_ps1_usb(data)
    if vid == _LOGITECH_VID and pid in _LOGITECH_DINPUT:
        return _parse_logitech_dinput(data)
    if vid == _LOGITECH_VID and pid == _F310_PID:
        return _parse_dup16(data)
    if _looks_like_dup16(data):
        return _parse_dup16(data)
    if vid == _SONY_VID and pid in _DS3_PIDS:
        return parse_ds3(data)
    if (vid, pid) in _DS3_CLONES:
        return parse_ds3(data)
    if vid == _SONY_VID and pid in _DS5_PIDS:
        return parse_ds5(data)
    if vid == _SONY_VID and pid in _DS4_PIDS:
        return parse_ds4(data)
    return _parse_generic_u8(_payload(data), trigger_mode)


@dataclass(frozen=True, slots=True)
class DragonRiseLayout:
    name: str
    descriptor: bytes
    buttons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class HidTrace:
    kind: str
    maker: str = ""
    product: str = ""
    descriptor: str = ""
    report: str = ""
    parsed: str = ""


# buttons[0] is HID button 1. An entry is added only after a captured report names that board.
DRAGONRISE_LAYOUTS: tuple[DragonRiseLayout, ...] = ()


def dragonrise_layout(descriptor: bytes) -> DragonRiseLayout | None:
    found = [item for item in DRAGONRISE_LAYOUTS if item.descriptor == descriptor]
    if len(found) != 1:
        return None
    return found[0]


def _is_dragonrise(identity: DeviceIdentity) -> bool:
    return (identity.vendor_id, identity.product_id) == _DRAGONRISE_ID


_A1WC_BUTTONS = ("a", "b", "x", "y", "lb", "rb", "back", "start", "ls", "rs")
_A1WC_DESCRIPTOR = bytes.fromhex(
    "05 01 09 05 a1 01 09 00 a1 00 09 30 09 31 15 00 25 ff 35 00 45 ff "
    "75 10 95 02 81 02 c0 09 00 a1 00 09 33 09 34 15 00 25 ff 75 10 95 02 "
    "81 02 c0 09 00 a1 00 09 32 15 00 25 ff 75 10 95 01 81 02 c0 05 09 19 01 "
    "29 10 15 00 25 01 75 01 95 10 45 00 81 02 05 01 09 39 15 01 25 08 35 00 "
    "46 3b 10 65 0e 75 04 95 01 81 42 75 04 95 01 81 03 75 08 95 02 81 03 c0"
)
MAP_GENERIC = "generic"
MAP_A1WC = "a1wc"


@dataclass(frozen=True, slots=True)
class GenericMap:
    id: str
    name: str
    descriptor: bytes
    buttons: tuple[str, ...]


GENERIC_MAPS: tuple[GenericMap, ...] = (
    GenericMap(MAP_A1WC, "DualShock 3 A1 WC", _A1WC_DESCRIPTOR, _A1WC_BUTTONS),
)


def generic_map_for(descriptor: bytes) -> GenericMap | None:
    found = [item for item in GENERIC_MAPS if item.descriptor == descriptor]
    if len(found) != 1:
        return None
    return found[0]


def map_buttons(map_id: str) -> tuple[str, ...] | None:
    for item in GENERIC_MAPS:
        if item.id == map_id:
            return item.buttons
    return None


def _hid_string(read) -> str:
    try:
        value = read()
    except (OSError, ValueError, TypeError, AttributeError, UnicodeError):
        return ""
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    return (value or "").strip()


def _read_bits(data: bytes | bytearray, start: int, size: int) -> int | None:
    if size <= 0 or start < 0 or start + size > len(data) * 8:
        return None
    value = 0
    for bit in range(size):
        cursor = start + bit
        if data[cursor // 8] & (1 << (cursor % 8)):
            value |= 1 << bit
    return value


def _write_bits(data: bytearray, start: int, size: int, value: int) -> None:
    for bit in range(size):
        cursor = start + bit
        index = cursor // 8
        if index >= len(data):
            return
        mask = 1 << (cursor % 8)
        if value & (1 << bit):
            data[index] |= mask
        else:
            data[index] &= ~mask


def _trace_key(data: bytes, layout: HidLayout | None) -> bytes:
    masked = bytearray(data)
    if layout is None:
        if len(masked) >= 1:
            masked[0] = 0
        if len(masked) >= 2:
            masked[1] = 0
        return bytes(masked)
    origin = 8 if layout.numbered else 0
    for field in layout.fields:
        if field.page != _PAGE_DESKTOP:
            continue
        start = origin + field.bit_offset
        if field.usage in (_USE_X, _USE_Y):
            _write_bits(masked, start, field.size, 0)
        elif field.usage in _WIDE_AXES and field.size >= 8:
            value = _read_bits(masked, start, field.size)
            if value is None:
                continue
            # Nearest 32, so a center that flickers between 127 and 128 stays one line.
            step = 32
            coarse = min((1 << field.size) - 1, ((value + step // 2) // step) * step)
            _write_bits(masked, start, field.size, coarse)
    return bytes(masked)


class GenericHidReader:
    def __init__(self, identity: DeviceIdentity):
        self.identity = identity
        self._dev: hid.device | None = None
        self._layout: HidLayout | None = None
        self._last: NormalizedState | None = None
        self._trigger_mode: dict[str, str | None] = {"kind": None}
        self._dragon: DragonRiseLayout | None = None
        self._trace: list[HidTrace] = []
        self._seen: set[bytes] = set()
        self._tracing = False
        self._descriptor_hex = ""
        self._buttons: tuple[str, ...] | None = None
        self._buttons_lock = threading.Lock()

    def open(self) -> None:
        device = hid.device()
        path = self.identity.path
        if isinstance(path, str):
            path = path.encode("ascii")
        device.open_path(path)
        device.set_nonblocking(True)
        self._dev = device
        self._layout = None
        self._last = None
        self._trigger_mode = {"kind": None}
        self._dragon = None
        self._trace = []
        self._seen = set()
        self._tracing = False
        self._descriptor_hex = ""
        with self._buttons_lock:
            self._buttons = None
        if _keeps_own_parser(self.identity):
            return
        raw = b""
        try:
            got = device.get_report_descriptor()
            if got:
                raw = bytes(got)
        except (OSError, ValueError, TypeError):
            raw = b""
        if raw:
            self._descriptor_hex = raw.hex()
            self._layout = layout_from_descriptor(raw)
        if _is_dragonrise(self.identity):
            self._dragon = dragonrise_layout(raw)
            if self._dragon is not None:
                return
        self._tracing = True
        self._trace.append(
            HidTrace(
                kind="pad",
                maker=_hid_string(device.get_manufacturer_string),
                product=self.identity.product_name or _hid_string(device.get_product_string),
                descriptor=raw.hex(" ") if raw else "-",
            )
        )

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

    def descriptor_hex(self) -> str:
        return self._descriptor_hex

    def set_buttons(self, names: tuple[str, ...] | None) -> None:
        with self._buttons_lock:
            self._buttons = names

    def trace(self) -> list[HidTrace]:
        return list(self._trace)

    def read(self) -> NormalizedState | None:
        data = self.read_raw()
        if data is None:
            return None
        state = self._parse(data)
        self._last = state
        if self._tracing:
            self._note(data, state)
        return state

    def _chosen_buttons(self) -> tuple[str, ...] | None:
        with self._buttons_lock:
            chosen = self._buttons
        if chosen is not None:
            return chosen
        if self._dragon is not None:
            return self._dragon.buttons
        return None

    def _parse(self, data: bytes) -> NormalizedState:
        names = self._chosen_buttons()
        if self._layout is not None and not _is_x360_report(data):
            parsed = parse_hid_layout(
                data, self._layout, self._last, self._trigger_mode, names
            )
            if parsed is not None:
                return parsed
        return parse_report(data, self.identity, self._trigger_mode)

    def _note(self, data: bytes, state: NormalizedState) -> None:
        if len(self._trace) >= _TRACE_CAP:
            return
        key = _trace_key(data, self._layout)
        if key in self._seen:
            return
        self._seen.add(key)
        self._trace.append(
            HidTrace(kind="report", report=data.hex(" "), parsed=state.format_line())
        )

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
