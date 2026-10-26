from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from engine.pipeline import Calibration, StickCal, TriggerCal
from engine.supportlog import write_failure
from engine.remap import BUTTONS, RemapRule
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
        except (OSError, json.JSONDecodeError) as exc:
            write_failure("profile file unreadable before save", exc)
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
        rules = _rules_from(data.get("remap"))
    except (OSError, json.JSONDecodeError, TypeError, KeyError):
        raise ProfileReadError(str(path)) from None
    measured = {
        "at": data.get("measured_at") or "",
        "summary": data.get("summary") or "",
    }
    return cal, rules, measured


def _rules_from(raw: object) -> list[RemapRule]:
    if not isinstance(raw, list):
        return []
    rules: list[RemapRule] = []
    for item in raw:
        rule = _rule_from(item)
        if rule is not None:
            rules.append(rule)
    return rules


def _rule_from(item: object) -> RemapRule | None:
    if not isinstance(item, dict):
        return None
    sources = item.get("sources")
    dest = item.get("dest")
    if isinstance(sources, str):
        sources = (sources,)
    elif isinstance(sources, (list, tuple)):
        sources = tuple(src for src in sources if isinstance(src, str))
    else:
        return None
    if not isinstance(dest, str) or not sources:
        return None
    hold = item.get("toggle_hold")
    if hold is not None and not isinstance(hold, str):
        return None
    if dest not in BUTTONS or any(src not in BUTTONS for src in sources):
        return None
    if hold is not None and hold not in BUTTONS:
        return None
    return RemapRule(sources, dest, hold)
