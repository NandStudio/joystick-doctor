from __future__ import annotations

import time

from engine.device.hid_util import (
    HidPathReader,
    apply_hat,
    apply_sticks_u8,
    enumerate_hid,
    print_loop,
    strip_report_id,
    trigger_u8,
)
from engine.state import DeviceIdentity, NormalizedState

VID = 0x054C
PIDS = {0x0CE6, 0x0DF2}
_BACKEND = "ds5"


def enumerate_devices() -> list[DeviceIdentity]:
    return enumerate_hid(VID, PIDS, _BACKEND)


def parse_report(data: bytes) -> NormalizedState:
    if data and data[0] == 0x31:
        payload = data[2:] if len(data) > 10 else data
    else:
        payload = strip_report_id(data)
    state = NormalizedState()
    if len(payload) < 10:
        return state
    apply_sticks_u8(state, payload)
    state.lt = trigger_u8(payload[4])
    state.rt = trigger_u8(payload[5])
    apply_hat(state, payload[7])
    face = payload[7]
    state.x = bool(face & 0x10)
    state.a = bool(face & 0x20)
    state.b = bool(face & 0x40)
    state.y = bool(face & 0x80)
    mid = payload[8]
    state.lb = bool(mid & 0x01)
    state.rb = bool(mid & 0x02)
    state.back = bool(mid & 0x10)
    state.start = bool(mid & 0x20)
    state.ls = bool(mid & 0x40)
    state.rs = bool(mid & 0x80)
    state.guide = bool(payload[9] & 0x01)
    state.timestamp = time.perf_counter()
    return state


class Ds5Reader(HidPathReader):
    def read(self) -> NormalizedState | None:
        data = self.read_raw()
        if data is None:
            return None
        return parse_report(data)


if __name__ == "__main__":
    print_loop(enumerate_devices(), Ds5Reader, parse_report)
