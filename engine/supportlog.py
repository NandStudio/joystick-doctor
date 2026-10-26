from __future__ import annotations

import sys
import threading
import traceback
from datetime import datetime
from pathlib import Path
from typing import Callable

from engine.version import APP_VERSION

_DIR = Path.home() / "AppData" / "Local" / "joystick-doctor" / "logs"
_lock = threading.Lock()
_writing = False
_snapshot: Callable[[], str] | None = None


def logs_dir() -> Path:
    _DIR.mkdir(parents=True, exist_ok=True)
    return _DIR


def set_snapshot(fn: Callable[[], str]) -> None:
    global _snapshot
    _snapshot = fn


def write_failure(context: str, exc: BaseException | None = None) -> Path | None:
    global _writing
    if _writing:
        return None
    _writing = True
    try:
        return _write(context, exc)
    except OSError:
        return None
    finally:
        _writing = False


def install_hooks() -> None:
    previous = sys.excepthook

    def _hook(exc_type, exc, tb) -> None:
        write_failure("uncaught", exc)
        previous(exc_type, exc, tb)

    sys.excepthook = _hook
    previous_thread = threading.excepthook

    def _thread_hook(args: threading.ExceptHookArgs) -> None:
        name = args.thread.name if args.thread is not None else "thread"
        write_failure(name, args.exc_value)
        previous_thread(args)

    threading.excepthook = _thread_hook


def _write(context: str, exc: BaseException | None) -> Path:
    folder = logs_dir()
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = folder / f"failure-{stamp}.log"
    with _lock:
        index = 1
        while path.exists():
            path = folder / f"failure-{stamp}-{index}.log"
            index += 1
        path.write_text(_body(context, exc), encoding="utf-8")
    return path


def _body(context: str, exc: BaseException | None) -> str:
    windows = "unknown"
    try:
        info = sys.getwindowsversion()
        windows = f"{info.major}.{info.minor}.{info.build}"
    except (AttributeError, OSError):
        pass
    lines = [
        "Joystick Doctor failure",
        f"when: {datetime.now().isoformat(timespec='seconds')}",
        f"context: {context}",
        f"app: {APP_VERSION}",
        f"frozen: {bool(getattr(sys, 'frozen', False))}",
        f"executable: {sys.executable}",
        f"windows: {windows}",
        f"python: {sys.version.split()[0]}",
        "",
        "drivers:",
        _drivers(),
        "",
        "snapshot:",
        _safe_snapshot(),
        "",
        "traceback:",
        _format_exc(exc),
    ]
    return "\n".join(lines).rstrip() + "\n"


def _drivers() -> str:
    parts = []
    try:
        from engine.vigem import is_installed as vigem_installed

        parts.append(f"vigem: {vigem_installed()}")
    except Exception as exc:
        parts.append(f"vigem: {exc}")
    try:
        from engine import hidhide

        parts.append(f"hidhide: {hidhide.is_installed()}")
    except Exception as exc:
        parts.append(f"hidhide: {exc}")
    try:
        from engine import ps3drv

        parts.append(f"ps3: {ps3drv.helper_installed()} ({ps3drv.package_name()})")
    except Exception as exc:
        parts.append(f"ps3: {exc}")
    return "\n".join(parts)


def _safe_snapshot() -> str:
    if _snapshot is None:
        return "(none)"
    try:
        return _snapshot() or "(empty)"
    except Exception:
        return traceback.format_exc()


def _format_exc(exc: BaseException | None) -> str:
    if exc is None:
        return "(no exception)"
    return "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)).rstrip()
