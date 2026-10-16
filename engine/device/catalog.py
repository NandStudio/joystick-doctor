from __future__ import annotations

import re
from dataclasses import replace

from engine.device.ds3 import CLONE_IDS as DS3_CLONES
from engine.device.ds3 import PIDS as DS3_PIDS
from engine.device.ds3 import VID as DS3_VID
from engine.device.ds3 import Ds3Reader
from engine.device.ds3 import enumerate_devices as enumerate_ds3
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

Reader = Ds3Reader | Ds4Reader | Ds5Reader | GenericHidReader | SwitchProReader | XInputReader


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


_IG_INSTANCE = re.compile(r"IG_(\d+)", re.IGNORECASE)


def _xinput_instance(path: bytes | str) -> int | None:
    text = path.decode("ascii", errors="replace") if isinstance(path, bytes) else path
    match = _IG_INSTANCE.search(text)
    if match is None:
        return None
    return int(match.group(1))


def _hidden_by_xinput(
    device: DeviceIdentity, xinput_devs: list[DeviceIdentity]
) -> bool:
    if device.vendor_id == 0x045E:
        return True
    if (device.vendor_id, device.product_id) in _XINPUT_ALSO_HID:
        return True
    return any(
        xi.vendor_id == device.vendor_id and xi.product_id == device.product_id
        for xi in xinput_devs
        if xi.vendor_id and xi.product_id
    )


def _classify_hid(device: DeviceIdentity) -> DeviceIdentity:
    if device.vendor_id == DS3_VID and device.product_id in DS3_PIDS:
        return replace(device, backend="ds3")
    if (device.vendor_id, device.product_id) in DS3_CLONES:
        return replace(device, backend="ds3")
    if device.vendor_id == DS4_VID and device.product_id in DS4_PIDS:
        return replace(device, backend="ds4")
    if device.vendor_id == DS5_VID and device.product_id in DS5_PIDS:
        return replace(device, backend="ds5")
    if device.vendor_id == SWITCH_VID and device.product_id in SWITCH_PIDS:
        return replace(device, backend="switch_pro")
    return replace(device, backend="hid_generic")


def enumerate_all() -> list[DeviceIdentity]:
    hid_devs = enumerate_hid()
    xinput_devs = _bind_xinput_identity(enumerate_xinput(), hid_devs)
    hide_xinput_hid = bool(xinput_devs)
    devices = list(xinput_devs)
    for hid_dev in hid_devs:
        if _xinput_instance(hid_dev.path) is not None:
            continue
        if hide_xinput_hid and _hidden_by_xinput(hid_dev, xinput_devs):
            continue
        devices.append(_classify_hid(hid_dev))
    seen = {_path_key(dev.path) for dev in devices}
    for ds3 in enumerate_ds3():
        if _path_key(ds3.path) in seen:
            continue
        if hide_xinput_hid and _hidden_by_xinput(ds3, xinput_devs):
            continue
        devices.append(ds3)
        seen.add(_path_key(ds3.path))
    return devices


def _path_key(path: bytes | str) -> str:
    if isinstance(path, bytes):
        return path.decode("ascii", errors="replace")
    return path


def _bind_xinput_identity(
    devices: list[DeviceIdentity], hid_devs: list[DeviceIdentity]
) -> list[DeviceIdentity]:
    """Copy VID/PID only from the HID interface of that XInput slot.

    A single IG_00 used to be stamped onto every slot. The second pad,
    including one that appears when ViGEm is installed, then opened the
    first pad's profile and its remaps.
    """
    interfaces: list[tuple[int, DeviceIdentity]] = []
    for hid_dev in hid_devs:
        instance = _xinput_instance(hid_dev.path)
        if instance is None:
            continue
        interfaces.append((instance, hid_dev))
    interfaces.sort(key=lambda item: item[0])

    assigned: dict[int, DeviceIdentity] = {}
    used: set[int] = set()
    for device in devices:
        if device.vendor_id or device.index is None:
            continue
        for instance, hid_dev in interfaces:
            if instance == device.index and instance not in used:
                assigned[device.index] = hid_dev
                used.add(instance)
                break
    pending = [
        device
        for device in devices
        if device.index is not None and device.index not in assigned and not device.vendor_id
    ]
    leftover = [(instance, hid_dev) for instance, hid_dev in interfaces if instance not in used]
    if len(pending) == 1 and len(leftover) == 1:
        assigned[pending[0].index] = leftover[0][1]

    bound: list[DeviceIdentity] = []
    for device in devices:
        extra = assigned.get(device.index) if device.index is not None else None
        if extra is None:
            bound.append(device)
            continue
        bound.append(
            replace(
                device,
                vendor_id=extra.vendor_id,
                product_id=extra.product_id,
                product_name=f"{extra.product_name} (XInput)",
            )
        )
    return bound


def hide_paths_for(identity: DeviceIdentity) -> list[bytes | str]:
    if identity.backend != "xinput":
        return [identity.path]
    matches = []
    for hid_dev in enumerate_hid():
        if _xinput_instance(hid_dev.path) is None:
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
    if identity.backend == "ds3":
        return Ds3Reader(identity)
    if identity.backend == "ds4":
        return Ds4Reader(identity)
    if identity.backend == "ds5":
        return Ds5Reader(identity)
    if identity.backend == "switch_pro":
        return SwitchProReader(identity)
    return GenericHidReader(identity)
