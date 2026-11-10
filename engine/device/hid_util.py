from __future__ import annotations

import time
from dataclasses import dataclass

import hid

from engine.state import DeviceIdentity, NormalizedState

GENERIC_DESKTOP = 0x01
JOYSTICK_USAGES = {0x04, 0x05}

HAT_TO_DPAD = {
    0: (True, False, False, False),
    1: (True, False, False, True),
    2: (False, False, False, True),
    3: (False, True, False, True),
    4: (False, True, False, False),
    5: (False, True, True, False),
    6: (False, False, True, False),
    7: (True, False, True, False),
}


def axis_u8(value: int) -> float:
    return max(-1.0, min(1.0, (value / 255.0) * 2.0 - 1.0))


def trigger_u8(value: int) -> float:
    return max(0.0, min(1.0, value / 255.0))


def apply_hat(state: NormalizedState, nibble: int) -> None:
    up, down, left, right = HAT_TO_DPAD.get(nibble & 0x0F, (False, False, False, False))
    state.dpad_up = up
    state.dpad_down = down
    state.dpad_left = left
    state.dpad_right = right


def apply_sticks_u8(state: NormalizedState, data: bytes, offset: int = 0) -> None:
    state.lx = axis_u8(data[offset])
    state.ly = -axis_u8(data[offset + 1])
    state.rx = axis_u8(data[offset + 2])
    state.ry = -axis_u8(data[offset + 3])


def strip_report_id(data: bytes, report_id: int = 0x01) -> bytes:
    if data and data[0] == report_id and len(data) > 8:
        return data[1:]
    return data


def enumerate_hid(
    vendor_id: int,
    product_ids: set[int],
    backend: str,
    *,
    require_gamepad: bool = True,
) -> list[DeviceIdentity]:
    devices: list[DeviceIdentity] = []
    seen: set[bytes | str] = set()
    for info in hid.enumerate(vendor_id):
        if info.get("product_id") not in product_ids:
            continue
        if require_gamepad:
            if info.get("usage_page") != GENERIC_DESKTOP:
                continue
            if info.get("usage") not in JOYSTICK_USAGES:
                continue
        path = info["path"]
        if path in seen:
            continue
        seen.add(path)
        devices.append(
            DeviceIdentity(
                vendor_id=info.get("vendor_id") or 0,
                product_id=info.get("product_id") or 0,
                backend=backend,
                path=path,
                product_name=info.get("product_string") or backend,
            )
        )
    return devices


class HidPathReader:
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

    def write(self, data: bytes) -> int:
        if self._dev is None:
            raise RuntimeError("HID device is not open")
        return self._dev.write(data)

    def send_feature_report(self, data: bytes) -> int:
        if self._dev is None:
            raise RuntimeError("HID device is not open")
        return self._dev.send_feature_report(data)

    def read_raw(self) -> bytes | None:
        if self._dev is None:
            raise RuntimeError("HID device is not open")
        data = self._dev.read(64)
        if not data:
            return None
        return bytes(data)

    def __enter__(self) -> HidPathReader:
        self.open()
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


@dataclass(frozen=True, slots=True)
class HidField:
    report_id: int
    page: int
    usage: int
    bit_offset: int
    size: int
    logical_min: int
    logical_max: int
    null_state: bool


@dataclass(frozen=True, slots=True)
class HidLayout:
    fields: tuple[HidField, ...]
    numbered: bool


_PAGE_DESKTOP = 0x01
_PAGE_SIM = 0x02
_PAGE_BUTTON = 0x09
_USE_X = 0x30
_USE_Y = 0x31
_USE_Z = 0x32
_USE_RX = 0x33
_USE_RY = 0x34
_USE_RZ = 0x35
_USE_HAT = 0x39
_USE_ACCEL = 0xC4
_USE_BRAKE = 0xC5
_BUTTON_NAMES = (
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


def _item_unsigned(data: bytes) -> int:
    if not data:
        return 0
    return int.from_bytes(data, "little", signed=False)


def _item_signed(data: bytes) -> int:
    if not data:
        return 0
    bits = len(data) * 8
    value = _item_unsigned(data)
    if value & (1 << (bits - 1)):
        value -= 1 << bits
    return value


def _logical_range(raw_min: bytes, raw_max: bytes) -> tuple[int, int]:
    low = _item_signed(raw_min)
    high = _item_signed(raw_max)
    if high < low:
        high = _item_unsigned(raw_max)
    return low, high


def layout_from_descriptor(desc: bytes) -> HidLayout | None:
    """Map input fields from a HID report descriptor. Returns None when it has none."""
    page = 0
    size = 0
    count = 0
    raw_min = b"\x00"
    raw_max = b"\x00"
    report_id = 0
    numbered = False
    bit_offset = 0
    usages: list[tuple[int, int]] = []
    usage_min: int | None = None
    usage_max: int | None = None
    stack: list[tuple] = []
    fields: list[HidField] = []
    index = 0
    while index < len(desc):
        prefix = desc[index]
        index += 1
        if prefix == 0xFE:
            if index + 2 > len(desc):
                break
            long_size = desc[index]
            index += 2 + long_size
            continue
        data_size = prefix & 0x03
        if data_size == 3:
            data_size = 4
        kind = (prefix >> 2) & 0x03
        tag = (prefix >> 4) & 0x0F
        data = desc[index : index + data_size]
        index += data_size
        if kind == 1:
            if tag == 0x0:
                page = _item_unsigned(data)
            elif tag == 0x1:
                raw_min = data or b"\x00"
            elif tag == 0x2:
                raw_max = data or b"\x00"
            elif tag == 0x7:
                size = _item_unsigned(data)
            elif tag == 0x8:
                report_id = _item_unsigned(data)
                numbered = True
                bit_offset = 0
            elif tag == 0x9:
                count = _item_unsigned(data)
            elif tag == 0xA:
                stack.append((page, size, count, raw_min, raw_max, report_id, bit_offset))
            elif tag == 0xB and stack:
                page, size, count, raw_min, raw_max, report_id, bit_offset = stack.pop()
            continue
        if kind == 2:
            usage = _item_unsigned(data)
            if tag == 0x0:
                usages.append((page, usage))
            elif tag == 0x1:
                usage_min = usage
            elif tag == 0x2:
                usage_max = usage
            continue
        if kind != 0:
            continue
        if tag == 0x8:
            flags = _item_unsigned(data)
            low, high = _logical_range(raw_min, raw_max)
            chosen = _expand_usages(page, usages, usage_min, usage_max, count)
            constant = bool(flags & 0x01)
            variable = bool(flags & 0x02)
            null_state = bool(flags & 0x40)
            if not constant and variable and size and count:
                for slot in range(count):
                    field_page, field_usage = chosen[min(slot, len(chosen) - 1)]
                    fields.append(
                        HidField(
                            report_id,
                            field_page,
                            field_usage,
                            bit_offset,
                            size,
                            low,
                            high,
                            null_state,
                        )
                    )
                    bit_offset += size
            else:
                bit_offset += size * count
        usages = []
        usage_min = None
        usage_max = None
    if not fields:
        return None
    return HidLayout(tuple(fields), numbered)


def _expand_usages(
    page: int,
    usages: list[tuple[int, int]],
    usage_min: int | None,
    usage_max: int | None,
    count: int,
) -> list[tuple[int, int]]:
    if usage_min is not None and usage_max is not None and usage_max >= usage_min:
        seq = [(page, usage) for usage in range(usage_min, usage_max + 1)]
    else:
        seq = list(usages)
    if not seq:
        seq = [(page, 0)]
    if count > len(seq):
        seq = seq + [seq[-1]] * (count - len(seq))
    return seq


def _read_bits(data: bytes, start: int, size: int) -> int | None:
    if size <= 0 or start < 0 or start + size > len(data) * 8:
        return None
    value = 0
    for bit in range(size):
        cursor = start + bit
        if data[cursor // 8] & (1 << (cursor % 8)):
            value |= 1 << bit
    return value


def _wide_high(value: int, field: HidField) -> int:
    """A 16-bit axis whose descriptor says 255 still carries byte*257."""
    high = field.logical_max
    if field.size > 8 and field.logical_min >= 0 and high <= 0xFF and value > high:
        return (1 << field.size) - 1
    return high


def _axis_from_field(value: int, field: HidField) -> float:
    low = field.logical_min
    high = _wide_high(value, field)
    if high <= low:
        return 0.0
    if low < 0:
        span = max(abs(low), abs(high)) or 1
        return max(-1.0, min(1.0, value / span))
    half = (high - low) / 2.0
    if half == 0:
        return 0.0
    mid = (low + high) / 2.0
    return max(-1.0, min(1.0, (value - mid) / half))


def _trigger_from_field(value: int, field: HidField) -> float:
    if value <= 0:
        return 0.0
    # byte*257 stores the same 0-255 sample in both bytes. 0 stays released.
    if (
        field.size == 16
        and field.logical_min >= 0
        and field.logical_max <= 0xFF
        and value == (value & 0xFF) * 257
    ):
        return max(0.0, min(1.0, (value // 257) / 255.0))
    low = field.logical_min
    high = _wide_high(value, field)
    if high <= low:
        return 0.0
    return max(0.0, min(1.0, (value - low) / (high - low)))


def _hat_from_field(value: int, field: HidField) -> int | None:
    if field.null_state and (value < field.logical_min or value > field.logical_max):
        return None
    if value < field.logical_min or value > field.logical_max:
        return None
    index = value - field.logical_min
    if index > 7:
        return None
    return index


def _split_centered_trigger(value: int, field: HidField) -> tuple[float, float]:
    axis = _axis_from_field(value, field)
    if axis >= 0:
        return axis, 0.0
    return 0.0, -axis


def _remember_trigger(
    value: int, field: HidField, trigger_mode: dict[str, str | None]
) -> str | None:
    # A zero report must not lock the unipolar scale. The shared axis
    # shows itself when its rest sits at the center.
    if trigger_mode.get("kind") == "split":
        return "split"
    if abs(_axis_from_field(value, field)) <= 0.2:
        trigger_mode["kind"] = "split"
        return "split"
    return None


def _write_button(state: NormalizedState, name: str, pressed: bool) -> None:
    if name in ("lt", "rt"):
        setattr(state, name, 1.0 if pressed else 0.0)
        return
    setattr(state, name, pressed)


def parse_hid_layout(
    data: bytes,
    layout: HidLayout,
    previous: NormalizedState | None = None,
    trigger_mode: dict[str, str | None] | None = None,
    button_names: tuple[str, ...] | None = None,
) -> NormalizedState | None:
    """Read one report. Bits that do not fit keep the previous sticks and buttons."""
    if not data or layout is None:
        return None
    report_id = data[0] if layout.numbered else 0
    origin = 8 if layout.numbered else 0
    matching = [field for field in layout.fields if field.report_id == report_id]
    if not matching:
        return None
    state = NormalizedState() if previous is None else NormalizedState(
        lx=previous.lx,
        ly=previous.ly,
        rx=previous.rx,
        ry=previous.ry,
        lt=previous.lt,
        rt=previous.rt,
        a=previous.a,
        b=previous.b,
        x=previous.x,
        y=previous.y,
        lb=previous.lb,
        rb=previous.rb,
        ls=previous.ls,
        rs=previous.rs,
        back=previous.back,
        start=previous.start,
        guide=previous.guide,
        dpad_up=previous.dpad_up,
        dpad_down=previous.dpad_down,
        dpad_left=previous.dpad_left,
        dpad_right=previous.dpad_right,
    )
    present: dict[tuple[int, int], tuple[int, HidField]] = {}
    complete = True
    for field in matching:
        raw = _read_bits(data, origin + field.bit_offset, field.size)
        if raw is None:
            complete = False
            continue
        present[(field.page, field.usage)] = (raw, field)
    if not present:
        return None
    # A short trigger packet must not replace sticks or buttons with zeros.

    def take(page: int, usage: int) -> tuple[int, HidField] | None:
        return present.get((page, usage))

    left_x = take(_PAGE_DESKTOP, _USE_X) if complete else None
    left_y = take(_PAGE_DESKTOP, _USE_Y) if complete else None
    if left_x is not None:
        state.lx = _axis_from_field(left_x[0], left_x[1])
    if left_y is not None:
        state.ly = -_axis_from_field(left_y[0], left_y[1])
    right_x = take(_PAGE_DESKTOP, _USE_RX) if complete else None
    right_y = take(_PAGE_DESKTOP, _USE_RY) if complete else None
    axis_z = take(_PAGE_DESKTOP, _USE_Z)
    axis_rz = take(_PAGE_DESKTOP, _USE_RZ)
    if right_x is not None and right_y is not None:
        state.rx = _axis_from_field(right_x[0], right_x[1])
        state.ry = -_axis_from_field(right_y[0], right_y[1])
    elif (
        complete
        and right_x is None
        and right_y is None
        and axis_z is not None
        and axis_rz is not None
    ):
        state.rx = _axis_from_field(axis_z[0], axis_z[1])
        state.ry = -_axis_from_field(axis_rz[0], axis_rz[1])
        axis_z = None
        axis_rz = None
    accel = take(_PAGE_SIM, _USE_ACCEL)
    brake = take(_PAGE_SIM, _USE_BRAKE)
    if accel is not None or brake is not None:
        if brake is not None:
            state.lt = _trigger_from_field(brake[0], brake[1])
        if accel is not None:
            state.rt = _trigger_from_field(accel[0], accel[1])
    elif trigger_mode is not None and axis_z is not None:
        kind = _remember_trigger(axis_z[0], axis_z[1], trigger_mode)
        other_idle = axis_rz is None
        if axis_rz is not None:
            other_idle = (
                abs(_axis_from_field(axis_rz[0], axis_rz[1])) <= 0.2
                or _trigger_from_field(axis_rz[0], axis_rz[1]) <= 0.05
            )
        if kind == "split" and other_idle:
            state.lt, state.rt = _split_centered_trigger(axis_z[0], axis_z[1])
        else:
            state.lt = _trigger_from_field(axis_z[0], axis_z[1])
            if axis_rz is not None:
                state.rt = _trigger_from_field(axis_rz[0], axis_rz[1])
    else:
        if axis_z is not None:
            state.lt = _trigger_from_field(axis_z[0], axis_z[1])
        if axis_rz is not None:
            state.rt = _trigger_from_field(axis_rz[0], axis_rz[1])
    hat = take(_PAGE_DESKTOP, _USE_HAT) if complete else None
    if hat is not None:
        index = _hat_from_field(hat[0], hat[1])
        if index is None:
            state.dpad_up = state.dpad_down = state.dpad_left = state.dpad_right = False
        else:
            apply_hat(state, index)
    button_fields = [field for field in matching if field.page == _PAGE_BUTTON] if complete else []
    button_fields.sort(key=lambda field: field.usage)
    names = button_names if button_names is not None else _BUTTON_NAMES
    for slot, field in enumerate(button_fields):
        if slot >= len(names):
            break
        found = present.get((field.page, field.usage))
        if found is None:
            continue
        _write_button(state, names[slot], bool(found[0]))
    state.timestamp = time.perf_counter()
    return state


def print_loop(devices: list[DeviceIdentity], open_reader, parse) -> None:
    if not devices:
        print("No matching pads found.")
        return
    for i, identity in enumerate(devices):
        print(
            f"[{i}] {identity.product_name} "
            f"VID={identity.vendor_id:04X} PID={identity.product_id:04X}",
            flush=True,
        )
    chosen = devices[0]
    print(f"Reading {chosen.product_name} (Ctrl+C to stop)", flush=True)
    with open_reader(chosen) as reader:
        last = None
        while True:
            data = reader.read_raw()
            if data is None:
                time.sleep(0.004)
                continue
            line = parse(data).format_line()
            if line == last:
                continue
            last = line
            print(line, flush=True)
