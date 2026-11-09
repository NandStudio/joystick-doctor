from __future__ import annotations

import ctypes
import json
import os
import sys
import tempfile
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from ctypes import wintypes

from engine.device.ds3 import PIDS as DS3_PIDS
from engine.device.ds3 import VID as DS3_VID
from engine.device.ds3 import connected_sony_instances
from engine.net import urlopen
from engine.state import DeviceIdentity

_UA = "joystick-doctor"
_DSHIDMINI_RELEASES = "https://api.github.com/repos/nefarius/DsHidMini/releases/latest"
_SCP_RELEASES = "https://api.github.com/repos/nefarius/ScpToolkit/releases"


class Ps3DriverError(RuntimeError):
    pass


def windows_version() -> tuple[int, int, int]:
    info = sys.getwindowsversion()
    return info.major, info.minor, info.build


def uses_dshidmini() -> bool:
    major, _minor, _build = windows_version()
    return major >= 10


def package_name() -> str:
    return "DsHidMini" if uses_dshidmini() else "ScpToolkit"


def is_official_ps3(device: DeviceIdentity) -> bool:
    return device.vendor_id == DS3_VID and device.product_id in DS3_PIDS


def _program_dirs() -> list[Path]:
    return [
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")),
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")),
    ]


def _dir_named(name: str) -> bool:
    tails = (
        Path("Nefarius Software Solutions") / name,
        Path(name),
    )
    for root in _program_dirs():
        for tail in tails:
            if (root / tail).is_dir():
                return True
    return False


def dshidmini_installed() -> bool:
    hints = (
        Path(r"C:\Windows\System32\drivers\dshidmini.sys"),
        Path(r"C:\Windows\System32\drivers\UMDF\dshidmini.dll"),
    )
    if any(path.is_file() for path in hints):
        return True
    return _dir_named("DsHidMini")


def scp_installed() -> bool:
    if Path(r"C:\Windows\System32\drivers\ScpVBus.sys").is_file():
        return True
    return _dir_named("ScpToolkit")


def helper_installed() -> bool:
    return dshidmini_installed() or scp_installed()


def helper_status() -> str:
    if dshidmini_installed():
        return "DsHidMini OK"
    if scp_installed():
        return "ScpToolkit OK"
    return f"{package_name()} missing"


MODES = ("SDF", "GPJ", "SXS", "DS4Windows", "XInput", "CGP", "CGS")


class _GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", wintypes.BYTE * 8),
    ]


class _DEVPROPKEY(ctypes.Structure):
    _fields_ = [
        ("fmtid", _GUID),
        ("pid", wintypes.ULONG),
    ]


def _mode_key() -> _DEVPROPKEY:
    key = _DEVPROPKEY()
    key.fmtid.Data1 = 0x6D293077
    key.fmtid.Data2 = 0xC3D6
    key.fmtid.Data3 = 0x4062
    key.fmtid.Data4 = (wintypes.BYTE * 8)(0x95, 0x97, 0xBE, 0x43, 0x89, 0x40, 0x4C, 0x02)
    key.pid = 2
    return key


def mode_index(name: str) -> int:
    try:
        return MODES.index(name)
    except ValueError:
        return MODES.index("XInput")


def _config_path() -> Path:
    root = os.environ.get("ProgramData", r"C:\ProgramData")
    return Path(root) / "DsHidMini" / "DsHidMini.json"


def _load_config() -> dict:
    path = _config_path()
    if not path.is_file():
        return {}
    try:
        loaded = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def configured_mode() -> str:
    global_node = _load_config().get("Global")
    if isinstance(global_node, dict):
        name = global_node.get("HidDeviceMode")
        if isinstance(name, str) and name in MODES:
            return name
    return "XInput"


def _mode_byte(instance: str) -> int | None:
    cfg = ctypes.windll.cfgmgr32
    locate = cfg.CM_Locate_DevNodeW
    locate.argtypes = [ctypes.POINTER(wintypes.DWORD), wintypes.LPCWSTR, wintypes.ULONG]
    locate.restype = wintypes.DWORD
    read = cfg.CM_Get_DevNode_PropertyW
    read.argtypes = [
        wintypes.DWORD,
        ctypes.POINTER(_DEVPROPKEY),
        ctypes.POINTER(wintypes.ULONG),
        ctypes.c_void_p,
        ctypes.POINTER(wintypes.ULONG),
        wintypes.ULONG,
    ]
    read.restype = wintypes.DWORD
    devinst = wintypes.DWORD()
    if locate(ctypes.byref(devinst), instance, 0) != 0:
        return None
    key = _mode_key()
    kind = wintypes.ULONG()
    size = wintypes.ULONG(1)
    buf = (ctypes.c_ubyte * 1)()
    if read(devinst, ctypes.byref(key), ctypes.byref(kind), ctypes.addressof(buf), ctypes.byref(size), 0) != 0:
        return None
    value = int(buf[0])
    if 1 <= value <= len(MODES):
        return value
    return None


def active_mode() -> str:
    for instance in connected_sony_instances():
        value = _mode_byte(instance)
        if value is not None:
            return MODES[value - 1]
    return configured_mode()


def _with_mode(name: str) -> dict:
    data = _load_config()
    global_node = data.get("Global")
    if not isinstance(global_node, dict):
        global_node = {}
        data["Global"] = global_node
    global_node["HidDeviceMode"] = name
    return data


def _write_config(name: str) -> None:
    path = _config_path()
    payload = json.dumps(_with_mode(name), indent=2) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def _write_config_elevated(name: str) -> None:
    try:
        payload = json.dumps(_with_mode(name), indent=2) + "\n"
    except PermissionError:
        payload = json.dumps({"Global": {"HidDeviceMode": name}}, indent=2) + "\n"
    blob = Path(tempfile.gettempdir()) / "joystick-doctor-dshidmini.json"
    script = Path(tempfile.gettempdir()) / "joystick-doctor-dshidmini.ps1"
    blob.write_text(payload, encoding="utf-8")
    dest = str(_config_path())
    script.write_text(
        "\n".join(
            [
                f"$dest = '{dest}'",
                f"$src = '{blob}'",
                "New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dest) | Out-Null",
                "Copy-Item -LiteralPath $src -Destination $dest -Force",
            ]
        ),
        encoding="utf-8",
    )
    status = ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        "powershell.exe",
        f'-NoProfile -ExecutionPolicy Bypass -File "{script}"',
        None,
        0,
    )
    if status <= 32:
        raise Ps3DriverError("DsHidMini setup was cancelled or failed to start (UAC).")


def set_mode(name: str) -> None:
    if name not in MODES:
        raise Ps3DriverError("Unknown DsHidMini mode.")
    try:
        _write_config(name)
    except PermissionError:
        _write_config_elevated(name)


def needs_helper(device: DeviceIdentity) -> bool:
    if not is_official_ps3(device):
        return False
    if device.backend == "xinput":
        return False
    return not helper_installed()


def _github_json(url: str) -> dict | list:
    request = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _asset_url(assets: list[dict], *needles: str, suffixes: tuple[str, ...] = (".exe", ".msi")) -> str:
    for asset in assets:
        name = (asset.get("name") or "").lower()
        url = asset.get("browser_download_url") or ""
        if not url or not any(name.endswith(suffix) for suffix in suffixes):
            continue
        if all(needle in name for needle in needles):
            return url
    raise Ps3DriverError("Could not find the official setup on GitHub.")


def latest_installer_url() -> str:
    if uses_dshidmini():
        payload = _github_json(_DSHIDMINI_RELEASES)
        return _asset_url(payload.get("assets", []), "dshidmini", suffixes=(".msi",))
    releases = _github_json(_SCP_RELEASES)
    if not isinstance(releases, list):
        raise Ps3DriverError("Unexpected ScpToolkit release list from GitHub.")
    for release in releases:
        if release.get("prerelease"):
            continue
        try:
            return _asset_url(release.get("assets", []), "scptoolkit")
        except Ps3DriverError:
            continue
    for release in releases:
        try:
            return _asset_url(release.get("assets", []), "scp")
        except Ps3DriverError:
            continue
    raise Ps3DriverError("Could not find the official ScpToolkit setup on GitHub.")


def download_installer() -> Path:
    url = latest_installer_url()
    request = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urlopen(request, timeout=180) as response:
        data = response.read()
    name = Path(urlparse(url).path).name or f"{package_name()}_setup.exe"
    path = Path(tempfile.gettempdir()) / name
    path.write_bytes(data)
    if path.stat().st_size < 1000:
        raise Ps3DriverError(f"Downloaded {package_name()} setup looks empty.")
    return path


def launch_installer(path: Path) -> None:
    if path.suffix.lower() == ".msi":
        status = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", "msiexec", f'/i "{path}"', None, 1
        )
    else:
        status = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", str(path), None, None, 1
        )
    if status <= 32:
        raise Ps3DriverError(
            f"{package_name()} setup was cancelled or failed to start (UAC)."
        )
