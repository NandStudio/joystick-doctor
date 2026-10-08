from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from engine.pipeline import Calibration, StickCal, TriggerCal
from engine.remap import RemapRule
from engine.state import DeviceIdentity

_DIR = Path.home() / "AppData" / "Local" / "joystick-doctor" / "profiles"


class ProfileReadError(OSError):
    pass


def profile_key(identity: DeviceIdentity) -> str:
    return f"{identity.backend}_{identity.vendor_id:04x}_{identity.product_id:04x}"


def profile_path(identity: DeviceIdentity) -> Path:
    _DIR.mkdir(parents=True, exist_ok=True)
    return _DIR / f"{profile_key(identity)}.json"


def save_profile(
    identity: DeviceIdentity,
    cal: Calibration,
    rules: list[RemapRule],
    measured: dict | None = None,
    clear_measured: bool = False,
) -> Path:
    path = profile_path(identity)
    previous: dict = {}
    if path.is_file():
        try:
            previous = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            previous = {}
    payload = {
        "vendor_id": identity.vendor_id,
        "product_id": identity.product_id,
        "backend": identity.backend,
        "calibration": asdict(cal),
        "remap": [asdict(rule) for rule in rules],
    }
    if clear_measured:
        pass
    elif measured is not None:
        payload["measured_at"] = measured.get("at", "")
        payload["summary"] = measured.get("summary", "")
    elif previous.get("measured_at"):
        payload["measured_at"] = previous.get("measured_at", "")
        payload["summary"] = previous.get("summary", "")
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def load_profile(identity: DeviceIdentity) -> tuple[Calibration, list[RemapRule], dict] | None:
    path = profile_path(identity)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        raw_cal = data.get("calibration") or {}
        cal = Calibration(
            left=StickCal(**raw_cal.get("left", {})),
            right=StickCal(**raw_cal.get("right", {})),
            lt=TriggerCal(**raw_cal.get("lt", {})),
            rt=TriggerCal(**raw_cal.get("rt", {})),
        )
        rules = [
            RemapRule(
                sources=tuple(item["sources"]),
                dest=item["dest"],
                toggle_hold=item.get("toggle_hold"),
            )
            for item in data.get("remap", [])
        ]
    except (OSError, json.JSONDecodeError, TypeError, KeyError):
        raise ProfileReadError(str(path)) from None
    measured = {
        "at": data.get("measured_at") or "",
        "summary": data.get("summary") or "",
    }
    return cal, rules, measured
