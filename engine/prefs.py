from __future__ import annotations

import json
from pathlib import Path

_DIR = Path.home() / "AppData" / "Local" / "joystick-doctor"
_FILE = _DIR / "settings.json"
LANGS = ("system", "en", "es")
THEMES = ("light", "dark", "contrast")


def _read() -> dict:
    if not _FILE.is_file():
        return {}
    try:
        data = json.loads(_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _write(data: dict) -> None:
    _DIR.mkdir(parents=True, exist_ok=True)
    _FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_language() -> str:
    value = _read().get("language", "system")
    return value if value in LANGS else "system"


def save_language(language: str) -> None:
    if language not in LANGS:
        language = "system"
    data = _read()
    data["language"] = language
    _write(data)


def load_theme() -> str:
    value = _read().get("theme", "light")
    return value if value in THEMES else "light"


def save_theme(theme: str) -> None:
    if theme not in THEMES:
        theme = "light"
    data = _read()
    data["theme"] = theme
    _write(data)


def load_debug() -> bool:
    return bool(_read().get("debug", False))


def save_debug(enabled: bool) -> None:
    data = _read()
    data["debug"] = bool(enabled)
    _write(data)


def load_thanks_hidden() -> bool:
    return bool(_read().get("thanks_hidden", False))


def save_thanks_hidden(hidden: bool) -> None:
    data = _read()
    data["thanks_hidden"] = bool(hidden)
    _write(data)
