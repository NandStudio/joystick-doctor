from __future__ import annotations

import ctypes
import time
from ctypes import wintypes
from dataclasses import replace

import hid

from engine.device.hid_util import (
    GENERIC_DESKTOP,
    JOYSTICK_USAGES,
    HidPathReader,
    apply_hat,
    apply_sticks_u8,
    axis_u8,
    HidLayout,
    layout_from_descriptor,
    parse_hid_layout,
    print_loop,
    trigger_u8,
)
from engine.state import DeviceIdentity, NormalizedState

VID = 0x054C
PIDS = {0x0268, 0x042F}
# Cheap USB pads sold as "PS3": hat + Sony face order, not the Sony report.
# 0810:0001 is the adapter Steam calls a PS1 controller; parse_ps1_usb reads it.
PS1_USB_ID = (0x0810, 0x0001)
CLONE_IDS = {
    PS1_USB_ID,
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


def is_official_ps3(vendor_id: int, product_id: int) -> bool:
    return vendor_id == VID and product_id in PIDS


def _is_ds3_id(vendor_id: int, product_id: int) -> bool:
    if is_official_ps3(vendor_id, product_id):
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
    # Bytes 18 and 19 are triangle and circle pressure. L2 and R2 are 14 and 15.
    if len(payload) > 14:
        state.lt = trigger_u8(payload[13])
    if len(payload) > 15:
        state.rt = trigger_u8(payload[14])
    if state.lt == 0.0 and l2:
        state.lt = 1.0
    if state.rt == 0.0 and r2:
        state.rt = 1.0
    state.timestamp = time.perf_counter()
    return state


def is_ps1_usb(vendor_id: int, product_id: int) -> bool:
    return (vendor_id, product_id) == PS1_USB_ID


def _ps1_payload(data: bytes) -> bytes:
    # Windows leaves report id 0x01 or 0x02 on an 8-byte read. That byte is not an axis.
    if data and data[0] in (0x01, 0x02):
        return data[1:]
    return data


def parse_ps1_usb(data: bytes) -> NormalizedState:
    payload = _ps1_payload(data)
    state = NormalizedState()
    if len(payload) < 5:
        state.timestamp = time.perf_counter()
        return state
    state.lx = axis_u8(payload[0])
    state.ly = -axis_u8(payload[1])
    state.ry = -axis_u8(payload[2])
    state.rx = axis_u8(payload[3])
    apply_hat(state, payload[4])
    bits = payload[5] if len(payload) > 5 else 0
    if len(payload) > 6:
        bits |= payload[6] << 8
    # SDL map for this PID: △ ○ × □ L2 R2 L1 R1 Select Start L3 R3.
    state.y = bool(bits & 0x01)
    state.b = bool(bits & 0x02)
    state.a = bool(bits & 0x04)
    state.x = bool(bits & 0x08)
    state.lt = 1.0 if bits & 0x10 else 0.0
    state.rt = 1.0 if bits & 0x20 else 0.0
    state.lb = bool(bits & 0x40)
    state.rb = bool(bits & 0x80)
    state.back = bool(bits & 0x100)
    state.start = bool(bits & 0x200)
    state.ls = bool(bits & 0x400)
    state.rs = bool(bits & 0x800)
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


_PAD_FIELDS = (
    "lx",
    "ly",
    "rx",
    "ry",
    "lt",
    "rt",
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
)


def _same_pad(left: NormalizedState, right: NormalizedState) -> bool:
    return all(getattr(left, name) == getattr(right, name) for name in _PAD_FIELDS)


def _ps1_report_id(data: bytes) -> int:
    if data and data[0] in (0x01, 0x02):
        return data[0]
    return 0x01


def track_ps1_port(
    ports: dict[int, NormalizedState],
    active: int,
    data: bytes,
) -> tuple[int, NormalizedState]:
    """Keep each report id. An unchanged port must not replace the one in use."""
    report_id = _ps1_report_id(data)
    state = parse_ps1_usb(data)
    previous = ports.get(report_id)
    ports[report_id] = state
    if previous is not None and not _same_pad(previous, state):
        active = report_id
    shown = ports.get(active, state)
    return active, replace(shown, timestamp=time.perf_counter())


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


_XBOX_ONE_ID = (0x045E, 0x02FF)
_SONY_MARK = {
    0x0268: "VID_054C&PID_0268",
    0x042F: "VID_054C&PID_042F",
}
_disguise_cache: dict[str, int | None] = {}


def _path_text(path: bytes | str) -> str:
    if isinstance(path, bytes):
        return path.decode("ascii", errors="replace")
    return path


def _hid_instance(path: bytes | str) -> str:
    text = _path_text(path)
    prefix = "\\\\?\\"
    if text.startswith(prefix):
        text = text[len(prefix) :]
    text = text.split("{", 1)[0]
    return text.replace("#", "\\").strip("\\")


def _parent_ids(instance: str) -> list[str]:
    cfg = ctypes.windll.cfgmgr32
    locate = cfg.CM_Locate_DevNodeW
    locate.argtypes = [ctypes.POINTER(wintypes.DWORD), wintypes.LPCWSTR, wintypes.ULONG]
    locate.restype = wintypes.DWORD
    parent_of = cfg.CM_Get_Parent
    parent_of.argtypes = [ctypes.POINTER(wintypes.DWORD), wintypes.DWORD, wintypes.ULONG]
    parent_of.restype = wintypes.DWORD
    device_id = cfg.CM_Get_Device_IDW
    device_id.argtypes = [wintypes.DWORD, wintypes.LPWSTR, wintypes.ULONG, wintypes.ULONG]
    device_id.restype = wintypes.DWORD
    current = wintypes.DWORD()
    if locate(ctypes.byref(current), instance, 0) != 0:
        return []
    found: list[str] = []
    for _ in range(6):
        parent = wintypes.DWORD()
        if parent_of(ctypes.byref(parent), current, 0) != 0:
            break
        current = parent
        name = ctypes.create_unicode_buffer(512)
        if device_id(current, name, 512, 0) != 0:
            break
        if not name.value:
            break
        found.append(name.value)
    return found


def connected_sony_instances() -> list[str]:
    """Devnodes of a connected official PS3, including the DsHidMini parent."""
    found: list[str] = []
    seen: set[str] = set()
    try:
        listed = hid.enumerate()
    except OSError:
        return found
    for info in listed:
        path = info.get("path") or b""
        nodes = [_hid_instance(path)]
        try:
            nodes.extend(_parent_ids(nodes[0]))
        except OSError:
            pass
        for inst in nodes:
            upper = inst.upper()
            if upper in seen:
                continue
            if not any(mark in upper for mark in _SONY_MARK.values()):
                continue
            seen.add(upper)
            found.append(inst)
    return found


def disguised_sony_pid(device: DeviceIdentity) -> int | None:
    """DsHidMini XInput mode publishes the DS3 as an Xbox One (045E:02FF)."""
    if (device.vendor_id, device.product_id) != _XBOX_ONE_ID:
        return None
    key = _path_text(device.path)
    cached = _disguise_cache.get(key)
    if key in _disguise_cache:
        return cached
    sony: int | None = None
    try:
        parents = " ".join(_parent_ids(_hid_instance(device.path))).upper()
    except OSError:
        parents = ""
    for pid, mark in _SONY_MARK.items():
        if mark in parents:
            sony = pid
            break
    _disguise_cache[key] = sony
    return sony


class Ds3Reader(HidPathReader):
    def __init__(self, identity: DeviceIdentity):
        super().__init__(identity)
        self._ps1_ports: dict[int, NormalizedState] = {}
        self._ps1_active = 0x01
        self._layout: HidLayout | None = None
        self._held: NormalizedState | None = None
        self._trigger_mode: dict[str, str | None] = {"kind": None}

    def open(self) -> None:
        super().open()
        self._layout = None
        self._held = None
        self._trigger_mode = {"kind": None}
        if self.identity.vendor_id == VID and self.identity.product_id in PIDS:
            enable_reports(self)
        if self._dev is None:
            return
        try:
            raw = self._dev.get_report_descriptor()
        except (OSError, ValueError, TypeError):
            return
        if raw:
            self._layout = layout_from_descriptor(bytes(raw))

    def read(self) -> NormalizedState | None:
        data = self.read_raw()
        if data is None:
            return None
        if is_ps1_usb(self.identity.vendor_id, self.identity.product_id):
            self._ps1_active, shown = track_ps1_port(
                self._ps1_ports, self._ps1_active, data
            )
            return shown
        if self._layout is not None and not _looks_native(data):
            parsed = parse_hid_layout(
                data, self._layout, self._held, self._trigger_mode
            )
            if parsed is not None:
                self._held = parsed
                return parsed
        state = parse_report(data)
        self._held = state
        return state


if __name__ == "__main__":
    print_loop(enumerate_devices(), Ds3Reader, parse_report)
