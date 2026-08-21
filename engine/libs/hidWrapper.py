import hid

from engine.libs.models import Controller

# Generic Desktop (0x01): Joystick (0x04) and Gamepad (0x05)
_GENERIC_DESKTOP = 0x01
_JOYSTICK_USAGES = {0x04, 0x05}


def listDevices() -> list[Controller]:
    devices = []
    for device_dict in hid.enumerate():
        if device_dict.get("usage_page") != _GENERIC_DESKTOP:
            continue
        if device_dict.get("usage") not in _JOYSTICK_USAGES:
            continue
        name = device_dict.get("product_string") or "Unknown HID"
        devices.append(
            Controller(device_dict["path"], device_dict["product_id"], name)
        )
    return devices

        