from __future__ import annotations

import time

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


def enumerate_hid(vendor_id: int, product_ids: set[int], backend: str) -> list[DeviceIdentity]:
    devices: list[DeviceIdentity] = []
    seen: set[bytes | str] = set()
    for info in hid.enumerate(vendor_id):
        if info.get("product_id") not in product_ids:
            continue
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
