from __future__ import annotations

import ctypes
import json
import tempfile
import urllib.request
from pathlib import Path

_DRIVER = Path(r"C:\Windows\System32\drivers\ViGEmBus.sys")
_RELEASES = "https://api.github.com/repos/nefarius/ViGEmBus/releases/latest"
_UA = "joystick-doctor"


class ViGEmMissingError(RuntimeError):
    pass


def is_installed() -> bool:
    return _DRIVER.is_file()


def latest_installer_url() -> str:
    request = urllib.request.Request(_RELEASES, headers={"User-Agent": _UA})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    for asset in payload.get("assets", []):
        name = asset.get("name") or ""
        url = asset.get("browser_download_url") or ""
        if name.lower().endswith(".exe") and "vigembus" in name.lower():
            return url
    raise RuntimeError("Could not find the official ViGEmBus setup on GitHub.")


def download_installer() -> Path:
    url = latest_installer_url()
    request = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(request, timeout=120) as response:
        data = response.read()
    path = Path(tempfile.gettempdir()) / "ViGEmBus_setup.exe"
    path.write_bytes(data)
    if path.stat().st_size < 1000:
        raise RuntimeError("Downloaded ViGEmBus setup looks empty.")
    return path


def launch_installer(path: Path) -> None:
    status = ctypes.windll.shell32.ShellExecuteW(
        None, "runas", str(path), None, None, 1
    )
    if status <= 32:
        raise RuntimeError("ViGEmBus setup was cancelled or failed to start (UAC).")
