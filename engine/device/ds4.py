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
PIDS = {0x05C4, 0x09CC, 0x0BA0}
_BACKEND = "ds4"


def enumerate_devices() -> list[DeviceIdentity]:
    return enumerate_hid(VID, PIDS, _BACKEND)


def parse_report(data: bytes) -> NormalizedState:
    payload = strip_report_id(data)
    state = NormalizedState()
    if len(payload) < 10:
        return state
    apply_sticks_u8(state, payload)
    apply_hat(state, payload[4])
    face = payload[4]
    state.x = bool(face & 0x10)
    state.a = bool(face & 0x20)
    state.b = bool(face & 0x40)
    state.y = bool(face & 0x80)
    mid = payload[5]
    state.lb = bool(mid & 0x01)
    state.rb = bool(mid & 0x02)
    state.back = bool(mid & 0x10)
    state.start = bool(mid & 0x20)
    state.ls = bool(mid & 0x40)
    state.rs = bool(mid & 0x80)
    state.guide = bool(payload[6] & 0x01)
    state.lt = trigger_u8(payload[8])
    state.rt = trigger_u8(payload[9])
    state.timestamp = time.perf_counter()
    return state


class Ds4Reader(HidPathReader):
    def read(self) -> NormalizedState | None:
        data = self.read_raw()
        if data is None:
            return None
        return parse_report(data)


if __name__ == "__main__":
    print_loop(enumerate_devices(), Ds4Reader, parse_report)
