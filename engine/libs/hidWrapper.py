import hid
from models import Controller


"""bus_type : 1
interface_number : 0
manufacturer_string : Microsoft
path : b'\\\\?\\HID#VID_046D&PID_C21D&IG_00#9&1b493451&0&0000#{4d1e55b2-f16f-11cf-88cb-001111000030}'
product_id : 49693
product_string : Controller (Gamepad F310)
release_number : 16404
serial_number : BAD58EC9
usage : 5
usage_page : 1
vendor_id : 1133"""

def listDevices() -> list[Controller]:
    devices = list()
    for device_dict in hid.enumerate():
        keys = list(device_dict.keys())
        keys.sort()
        if "Controller" in device_dict["product_string"]:
            devices.append(Controller(device_dict["path"], device_dict["product_id"], device_dict["product_string"]))
    return devices
        