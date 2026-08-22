from __future__ import annotations

from dataclasses import replace

from engine.device.ds4 import PIDS as DS4_PIDS
from engine.device.ds4 import VID as DS4_VID
from engine.device.ds4 import Ds4Reader
from engine.device.ds5 import PIDS as DS5_PIDS
from engine.device.ds5 import VID as DS5_VID
from engine.device.ds5 import Ds5Reader
from engine.device.hid_generic import GenericHidReader
from engine.device.hid_generic import enumerate_devices as enumerate_hid
from engine.device.switch_pro import PIDS as SWITCH_PIDS
from engine.device.switch_pro import VID as SWITCH_VID
from engine.device.switch_pro import SwitchProReader
from engine.device.xinput import XInputReader
from engine.device.xinput import enumerate_devices as enumerate_xinput
from engine.state import DeviceIdentity

Reader = Ds4Reader | Ds5Reader | GenericHidReader | SwitchProReader | XInputReader


def device_key(identity: DeviceIdentity) -> str:
    path = identity.path
    if isinstance(path, bytes):
        path = path.decode("ascii", errors="replace")
    return f"{identity.backend}:{path}"


def _is_xinput_hid_path(path: bytes | str) -> bool:
    text = path.decode("ascii", errors="replace") if isinstance(path, bytes) else path
    return "IG_00" in text.upper()


def _classify_hid(device: DeviceIdentity) -> DeviceIdentity:
    if device.vendor_id == DS4_VID and device.product_id in DS4_PIDS:
        return replace(device, backend="ds4")
    if device.vendor_id == DS5_VID and device.product_id in DS5_PIDS:
        return replace(device, backend="ds5")
    if device.vendor_id == SWITCH_VID and device.product_id in SWITCH_PIDS:
        return replace(device, backend="switch_pro")
    return replace(device, backend="hid_generic")


def enumerate_all() -> list[DeviceIdentity]:
    devices = list(enumerate_xinput())
    for hid_dev in enumerate_hid():
        if _is_xinput_hid_path(hid_dev.path):
            continue
        devices.append(_classify_hid(hid_dev))
    return devices


def reader_for(identity: DeviceIdentity) -> Reader:
    if identity.backend == "xinput":
        return XInputReader(identity)
    if identity.backend == "ds4":
        return Ds4Reader(identity)
    if identity.backend == "ds5":
        return Ds5Reader(identity)
    if identity.backend == "switch_pro":
        return SwitchProReader(identity)
    return GenericHidReader(identity)
