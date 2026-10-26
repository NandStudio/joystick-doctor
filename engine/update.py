from __future__ import annotations

import ctypes
import json
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from engine.version import APP_VERSION

_RELEASES = "https://api.github.com/repos/NandStudio/joystick-doctor/releases/latest"
_UA = "joystick-doctor"


class UpdateError(RuntimeError):
    pass


@dataclass(frozen=True)
class Release:
    version: str
    asset_url: str
    asset_name: str


def parse_version(text: str) -> tuple[int, ...]:
    raw = text.strip()
    if raw[:1] in ("v", "V"):
        raw = raw[1:]
    raw = raw.split("-", 1)[0].split("+", 1)[0]
    if not raw:
        raise UpdateError(f"Unrecognized version: {text}")
    parts: list[int] = []
    for piece in raw.split("."):
        if not piece.isdigit():
            raise UpdateError(f"Unrecognized version: {text}")
        parts.append(int(piece))
    return tuple(parts)


def is_newer(remote: str, local: str = APP_VERSION) -> bool:
    left = parse_version(remote)
    right = parse_version(local)
    width = max(len(left), len(right))
    left = left + (0,) * (width - len(left))
    right = right + (0,) * (width - len(right))
    return left > right


def fetch_latest() -> Release | str:
    request = urllib.request.Request(
        _RELEASES,
        headers={"User-Agent": _UA, "Accept": "application/vnd.github+json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise UpdateError(f"GitHub returned {exc.code}.") from exc
    except (OSError, json.JSONDecodeError, TimeoutError) as exc:
        raise UpdateError(str(exc)) from exc
    if not isinstance(payload, dict):
        raise UpdateError("Unexpected release payload.")
    tag = str(payload.get("tag_name") or "")
    if not is_newer(tag):
        return ""
    url = ""
    name = ""
    for asset in payload.get("assets") or []:
        if not isinstance(asset, dict):
            continue
        asset_name = str(asset.get("name") or "")
        lowered = asset_name.lower()
        if "joystickdoctorsetup" in lowered and lowered.endswith(".exe"):
            url = str(asset.get("browser_download_url") or "")
            name = asset_name
            break
    if not url:
        raise UpdateError("The release has no JoystickDoctorSetup executable.")
    safe = Path(name).name
    if not safe or safe in {".", ".."}:
        raise UpdateError("The release asset name is not a file.")
    shown = tag[1:] if tag[:1] in ("v", "V") else tag
    return Release(version=shown.split("-", 1)[0], asset_url=url, asset_name=safe)


def download_installer(release: Release) -> Path:
    request = urllib.request.Request(release.asset_url, headers={"User-Agent": _UA})
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            data = response.read()
    except OSError as exc:
        raise UpdateError(str(exc)) from exc
    path = Path(tempfile.gettempdir()) / release.asset_name
    path.write_bytes(data)
    if path.stat().st_size < 1000:
        raise UpdateError("Downloaded installer looks empty.")
    return path


def launch_installer(path: Path) -> None:
    status = ctypes.windll.shell32.ShellExecuteW(
        None, "runas", str(path), None, None, 1
    )
    if status <= 32:
        raise UpdateError("The installer was cancelled or failed to start (UAC).")
