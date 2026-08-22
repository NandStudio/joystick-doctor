from __future__ import annotations

import time

from engine.device.hid_util import HidPathReader, enumerate_hid, print_loop
from engine.state import DeviceIdentity, NormalizedState

VID = 0x057E
PIDS = {0x2009}
_BACKEND = "switch_pro"
_CENTER = 2048.0


class SwitchProInitError(RuntimeError):
    pass


def enumerate_devices() -> list[DeviceIdentity]:
    return enumerate_hid(VID, PIDS, _BACKEND)


def _stick12(data: bytes, offset: int) -> tuple[float, float]:
    raw_x = data[offset] | ((data[offset + 1] & 0x0F) << 8)
    raw_y = (data[offset + 1] >> 4) | (data[offset + 2] << 4)
    x = max(-1.0, min(1.0, (raw_x - _CENTER) / _CENTER))
    y = max(-1.0, min(1.0, (raw_y - _CENTER) / _CENTER))
    return x, y


def parse_report(data: bytes) -> NormalizedState:
    if data and data[0] == 0x30:
        payload = data
    elif data and data[0] == 0x00 and len(data) > 1 and data[1] == 0x30:
        payload = data[1:]
    else:
        return NormalizedState()
    if len(payload) < 12:
        return NormalizedState()
    right = payload[3]
    shared = payload[4]
    left = payload[5]
    lx, ly = _stick12(payload, 6)
    rx, ry = _stick12(payload, 9)
    return NormalizedState(
        lx=lx,
        ly=ly,
        rx=rx,
        ry=ry,
        lt=1.0 if left & 0x80 else 0.0,
        rt=1.0 if right & 0x80 else 0.0,
        a=bool(right & 0x08),
        b=bool(right & 0x04),
        x=bool(right & 0x02),
        y=bool(right & 0x01),
        lb=bool(left & 0x40),
        rb=bool(right & 0x40),
        ls=bool(shared & 0x08),
        rs=bool(shared & 0x04),
        back=bool(shared & 0x01),
        start=bool(shared & 0x02),
        guide=bool(shared & 0x10),
        dpad_down=bool(left & 0x01),
        dpad_up=bool(left & 0x02),
        dpad_right=bool(left & 0x04),
        dpad_left=bool(left & 0x08),
    )


def _usb_cmd(dev: HidPathReader, cmd: bytes) -> None:
    buf = bytearray(64)
    buf[: len(cmd)] = cmd
    dev.write(bytes(buf))


def handshake(reader: HidPathReader) -> None:
    """Put a USB Pro Controller into full 0x30 input reports."""
    try:
        for cmd in (b"\x80\x02", b"\x80\x03", b"\x80\x02", b"\x80\x04"):
            _usb_cmd(reader, cmd)
            time.sleep(0.05)
        packet = bytearray(64)
        packet[0] = 0x01
        packet[10] = 0x03
        packet[11] = 0x30
        reader.write(bytes(packet))
    except OSError as exc:
        raise SwitchProInitError(
            "Switch Pro handshake failed. Use USB (not only BT) and "
            "close other programs using the pad."
        ) from exc

    deadline = time.perf_counter() + 1.0
    while time.perf_counter() < deadline:
        data = reader.read_raw()
        if data and (data[0] == 0x30 or (len(data) > 1 and data[1] == 0x30)):
            return
        time.sleep(0.01)
    raise SwitchProInitError(
        "Switch Pro opened but never sent report 0x30 after handshake."
    )


class SwitchProReader(HidPathReader):
    def open(self) -> None:
        super().open()
        handshake(self)

    def read(self) -> NormalizedState | None:
        data = self.read_raw()
        if data is None:
            return None
        return parse_report(data)


if __name__ == "__main__":
    devices = enumerate_devices()
    if not devices:
        print("No Switch Pro found (VID 057E PID 2009).")
    else:
        try:
            print_loop(devices, SwitchProReader, parse_report)
        except SwitchProInitError as exc:
            print(exc)
