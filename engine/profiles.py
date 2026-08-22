from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from engine.pipeline import Calibration, StickCal, TriggerCal
from engine.remap import RemapRule
from engine.state import DeviceIdentity

_DIR = Path.home() / "AppData" / "Local" / "joystick-doctor" / "profiles"


def profile_key(identity: DeviceIdentity) -> str:
    return f"{identity.backend}_{identity.vendor_id:04x}_{identity.product_id:04x}"


def profile_path(identity: DeviceIdentity) -> Path:
    _DIR.mkdir(parents=True, exist_ok=True)
    return _DIR / f"{profile_key(identity)}.json"


def save_profile(identity: DeviceIdentity, cal: Calibration, rules: list[RemapRule]) -> Path:
    payload = {
        "vendor_id": identity.vendor_id,
        "product_id": identity.product_id,
        "backend": identity.backend,
        "calibration": asdict(cal),
        "remap": [asdict(rule) for rule in rules],
    }
    path = profile_path(identity)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def load_profile(identity: DeviceIdentity) -> tuple[Calibration, list[RemapRule]] | None:
    path = profile_path(identity)
    if not path.is_file():
        return None
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
    return cal, rules
