from __future__ import annotations

import ctypes
import json
import os
import subprocess
import tempfile
import urllib.request
from pathlib import Path

_DRIVER = Path(r"C:\Windows\System32\drivers\HidHide.sys")
_RELEASES = "https://api.github.com/repos/nefarius/HidHide/releases/latest"
_UA = "joystick-doctor"


class HidHideError(RuntimeError):
    pass


def is_installed() -> bool:
    return _DRIVER.is_file() or cli_path() is not None


def cli_path() -> Path | None:
    roots = [
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")),
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")),
    ]
    tails = (
        Path("Nefarius Software Solutions") / "HidHide" / "x64" / "HidHideCLI.exe",
        Path("Nefarius Software Solutions") / "HidHide" / "HidHideCLI.exe",
        Path("HidHide") / "x64" / "HidHideCLI.exe",
    )
    for root in roots:
        for tail in tails:
            candidate = root / tail
            if candidate.is_file():
                return candidate
    return None


def hidapi_to_instance(path: bytes | str) -> str:
    text = path.decode("ascii", errors="replace") if isinstance(path, bytes) else path
    text = text.replace("\\\\?\\", "").replace("\\\\?\\", "")
    if text.startswith("\\\\?\\"):
        text = text[4:]
    if text.startswith("?"):
        text = text[1:]
    text = text.split("{")[0]
    return text.replace("#", "\\").strip("\\")


def _run(args: list[str]) -> str:
    exe = cli_path()
    if exe is None:
        raise HidHideError("HidHide CLI not found. Install HidHide, then retry.")
    completed = subprocess.run(
        [str(exe), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise HidHideError(detail or f"HidHideCLI failed ({completed.returncode}). Need admin?")
    return completed.stdout


def register_app(app_path: str) -> None:
    _run(["--app-reg", app_path])


def hide_device(instance: str) -> None:
    _run(["--dev-hide", instance])


def unhide_device(instance: str) -> None:
    _run(["--dev-unhide", instance])


def cloak(enabled: bool) -> None:
    _run(["--cloak-on" if enabled else "--cloak-off"])


def latest_installer_url() -> str:
    request = urllib.request.Request(_RELEASES, headers={"User-Agent": _UA})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    for asset in payload.get("assets", []):
        name = (asset.get("name") or "").lower()
        url = asset.get("browser_download_url") or ""
        if name.endswith(".exe") and "hidhide" in name:
            return url
    raise HidHideError("Could not find the official HidHide setup on GitHub.")


def download_installer() -> Path:
    url = latest_installer_url()
    request = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(request, timeout=120) as response:
        data = response.read()
    path = Path(tempfile.gettempdir()) / "HidHide_setup.exe"
    path.write_bytes(data)
    if path.stat().st_size < 1000:
        raise HidHideError("Downloaded HidHide setup looks empty.")
    return path


def launch_installer(path: Path) -> None:
    status = ctypes.windll.shell32.ShellExecuteW(
        None, "runas", str(path), None, None, 1
    )
    if status <= 32:
        raise HidHideError("HidHide setup was cancelled or failed to start (UAC).")
