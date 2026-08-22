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


_XINPUT_ALSO_HID = {
    (0x045E, 0x028E),
    (0x045E, 0x028F),
    (0x045E, 0x02D1),
    (0x045E, 0x02DD),
    (0x045E, 0x02E0),
    (0x045E, 0x02EA),
    (0x045E, 0x0B12),
    (0x046D, 0xC21D),
}


def _is_xinput_hid_path(path: bytes | str) -> bool:
    text = path.decode("ascii", errors="replace") if isinstance(path, bytes) else path
    return "IG_00" in text.upper()


def _hidden_by_xinput(device: DeviceIdentity) -> bool:
    if device.vendor_id == 0x045E:
        return True
    return (device.vendor_id, device.product_id) in _XINPUT_ALSO_HID


def _classify_hid(device: DeviceIdentity) -> DeviceIdentity:
    if device.vendor_id == DS4_VID and device.product_id in DS4_PIDS:
        return replace(device, backend="ds4")
    if device.vendor_id == DS5_VID and device.product_id in DS5_PIDS:
        return replace(device, backend="ds5")
    if device.vendor_id == SWITCH_VID and device.product_id in SWITCH_PIDS:
        return replace(device, backend="switch_pro")
    return replace(device, backend="hid_generic")


def enumerate_all() -> list[DeviceIdentity]:
    xinput_devs = [_enrich_xinput(dev) for dev in enumerate_xinput()]
    hide_xinput_hid = bool(xinput_devs)
    devices = list(xinput_devs)
    for hid_dev in enumerate_hid():
        if _is_xinput_hid_path(hid_dev.path):
            continue
        if hide_xinput_hid and _hidden_by_xinput(hid_dev):
            continue
        devices.append(_classify_hid(hid_dev))
    return devices


def _enrich_xinput(device: DeviceIdentity) -> DeviceIdentity:
    if device.vendor_id:
        return device
    ig = [dev for dev in enumerate_hid() if _is_xinput_hid_path(dev.path)]
    if len(ig) != 1:
        return device
    extra = ig[0]
    return replace(
        device,
        vendor_id=extra.vendor_id,
        product_id=extra.product_id,
        product_name=f"{extra.product_name} (XInput)",
    )


def hide_paths_for(identity: DeviceIdentity) -> list[bytes | str]:
    if identity.backend != "xinput":
        return [identity.path]
    matches = []
    for hid_dev in enumerate_hid():
        if not _is_xinput_hid_path(hid_dev.path):
            continue
        if identity.vendor_id and (
            hid_dev.vendor_id != identity.vendor_id
            or hid_dev.product_id != identity.product_id
        ):
            continue
        matches.append(hid_dev.path)
    return matches


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
