from __future__ import annotations

import ctypes
import json
import os
import sys
import tempfile
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from engine.device.ds3 import PIDS as DS3_PIDS
from engine.device.ds3 import VID as DS3_VID
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


def needs_helper(device: DeviceIdentity) -> bool:
    if not is_official_ps3(device):
        return False
    if device.backend == "xinput":
        return False
    return not helper_installed()


def _github_json(url: str) -> dict | list:
    request = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(request, timeout=30) as response:
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
    with urllib.request.urlopen(request, timeout=180) as response:
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
