from __future__ import annotations

import json
from pathlib import Path

_DIR = Path.home() / "AppData" / "Local" / "joystick-doctor"
_FILE = _DIR / "settings.json"
LANGS = ("system", "en", "es")


def load_language() -> str:
    if not _FILE.is_file():
        return "system"
    try:
        data = json.loads(_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "system"
    value = data.get("language", "system")
    return value if value in LANGS else "system"


def save_language(language: str) -> None:
    if language not in LANGS:
        language = "system"
    _DIR.mkdir(parents=True, exist_ok=True)
    data = {}
    if _FILE.is_file():
        try:
            data = json.loads(_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
    data["language"] = language
    _FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
