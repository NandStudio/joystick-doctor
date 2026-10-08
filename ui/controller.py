from __future__ import annotations

import sys
import threading
from copy import deepcopy
from datetime import datetime

from PySide6.QtCore import Property, QObject, QThread, QTimer, QUrl, Signal, Slot

from engine import hidhide, ps3drv
from engine.device.catalog import device_key, enumerate_all, hide_paths_for
from engine.device.hotplug import HotplugMonitor
from engine.device.pump import DevicePump
from engine.device.xinput import enumerate_devices as enumerate_xinput
from engine.guided import GuidedSession
from engine.pipeline import Calibration, StickCal, apply_calibration, apply_stick
from engine.prefs import load_language
from engine.profiles import ProfileReadError, load_profile, profile_key, profile_path, save_profile
from engine.remap import RemapConfig, RemapEngine, RemapRule
from engine.state import DeviceIdentity, NormalizedState
from engine.vigem import ViGEmMissingError, download_installer, is_installed as vigem_installed
from engine.vigem import launch_installer
from engine.virtual import VirtualXbox
from ui.assets import bundle_root
from ui.i18n import set_language, tr


class _Bridge(QObject):
    # Hotplug callbacks arrive off the UI thread.
    added = Signal(object)
    removed = Signal(object)


class _Download(QThread):
    finished_ok = Signal(object)
    finished_err = Signal(str)

    def __init__(self, fn):
        super().__init__()
        self._fn = fn

    def run(self) -> None:
        try:
            self.finished_ok.emit(self._fn())
        except Exception as exc:
            self.finished_err.emit(str(exc))


class AppController(QObject):
    chromeChanged = Signal()
    frame = Signal()
    languageChanged = Signal()
    fontFamiliesChanged = Signal()
    guideChanged = Signal()
    curveChanged = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._lang_tick = 0
        self._display_family = "Caprasimo"
        self._body_family = "Figtree"
        self._strong_family = "Figtree SemiBold"
        set_language(load_language())

        self._page = "diagnostico"
        self._devices: dict[str, DeviceIdentity] = {}
        self._pump: DevicePump | None = None
        self._session = "empty"
        self._session_detail = ""
        self._view = "physical"
        self._notice = ""
        self._profile_name: str | None = None
        self._virtual_on = False
        self._vigem_word = ""
        self._hid_word = ""
        self._ignore_xinput: set[int] = set()
        self._hidden_instances: list[str] = []
        self._ps3_offer_asked = False

        self._cal = Calibration.default()
        self._cal_lock = threading.Lock()
        self._measured = {"at": "", "summary": ""}
        self._profile_error = False
        self._guide = GuidedSession()
        self._draft: Calibration | None = None
        self._curve_error = ""
        self._rules: list[RemapRule] = []
        self._remap = RemapEngine()
        self._remap_lock = threading.Lock()
        self._virtual = VirtualXbox()

        self._lx = self._ly = self._rx = self._ry = 0.0
        self._lt = self._rt = 0.0
        self._pad = {name: False for name in (
            "a", "b", "x", "y", "lb", "rb", "ls", "rs",
            "back", "start", "guide",
            "dpad_up", "dpad_down", "dpad_left", "dpad_right",
        )}
        self._has_sample = False
        self._packets = 0
        self._poll_hz = -1.0

        self._confirm_open = False
        self._confirm_title = ""
        self._confirm_body = ""
        self._confirm_queue: list[tuple[str, str, object]] = []
        self._on_yes = None
        self._download: _Download | None = None

        self._refresh_drivers()
        self._bridge = _Bridge()
        self._bridge.added.connect(self._add_device)
        self._bridge.removed.connect(self._remove_device)
        self._monitor = HotplugMonitor(
            on_add=self._bridge.added.emit,
            on_remove=self._bridge.removed.emit,
        )
        self._monitor.start()
        for device in enumerate_all():
            self._add_device(device)
        QTimer.singleShot(400, self._maybe_offer_ps3)

        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)
        self._timer.start()
        self._driver_timer = QTimer(self)
        self._driver_timer.setInterval(2000)
        self._driver_timer.timeout.connect(self._refresh_drivers)
        self._driver_timer.start()

    def _destinations(self) -> list[dict[str, str]]:
        return [
            {"id": "diagnostico", "label": tr("nav_diagnostico")},
            {"id": "calibracion", "label": tr("nav_calibracion")},
            {"id": "curvas", "label": tr("nav_curvas")},
        ]

    def _device_rows(self) -> list[dict[str, object]]:
        open_key = device_key(self._pump.identity) if self._pump else ""
        return [
            {"key": key, "name": device.product_name, "open": key == open_key}
            for key, device in self._devices.items()
        ]

    def _emit_chrome(self) -> None:
        self.chromeChanged.emit()
        self.curveChanged.emit()

    def _ask(self, title: str, body: str, on_yes) -> None:
        self._confirm_queue.append((title, body, on_yes))
        self._show_next_confirm()

    def _show_next_confirm(self) -> None:
        if self._confirm_open or not self._confirm_queue:
            return
        title, body, on_yes = self._confirm_queue.pop(0)
        self._confirm_title = title
        self._confirm_body = body
        self._on_yes = on_yes
        self._confirm_open = True
        self._emit_chrome()

    def _close_confirm(self) -> None:
        self._confirm_open = False
        self._on_yes = None
        self._emit_chrome()
        self._show_next_confirm()

    def _refresh_drivers(self) -> None:
        vigem = tr("word_active") if vigem_installed() else tr("word_absent")
        hide = tr("word_active") if hidhide.is_installed() else tr("word_absent")
        if vigem == self._vigem_word and hide == self._hid_word:
            return
        self._vigem_word = vigem
        self._hid_word = hide
        self._emit_chrome()

    def _set_notice(self, text: str) -> None:
        self._notice = text
        self._emit_chrome()

    def _filtered(self, raw: NormalizedState) -> NormalizedState:
        with self._cal_lock:
            cal = self._cal
        calibrated = apply_calibration(raw, cal)
        with self._remap_lock:
            return self._remap.apply(calibrated)

    def _load_profile(self, device: DeviceIdentity) -> None:
        self._draft = None
        self._curve_error = ""
        try:
            loaded = load_profile(device)
        except ProfileReadError:
            self._profile_error = True
            self._measured = {"at": "", "summary": ""}
            with self._cal_lock:
                self._cal = Calibration.default()
            self._rules = []
            with self._remap_lock:
                self._remap = RemapEngine()
            self._profile_name = None
            return
        self._profile_error = False
        if loaded is None:
            with self._cal_lock:
                self._cal = Calibration.default()
            self._rules = []
            with self._remap_lock:
                self._remap = RemapEngine()
            self._profile_name = None
            self._measured = {"at": "", "summary": ""}
            return
        cal, rules, measured = loaded
        with self._cal_lock:
            self._cal = cal
        self._rules = list(rules)
        with self._remap_lock:
            self._remap = RemapEngine(RemapConfig(list(self._rules)))
        self._profile_name = f"{profile_key(device)}.json"
        self._measured = measured

    def _stop_pump(self) -> None:
        if self._pump is not None:
            self._pump.stop()
            self._pump = None
        self._has_sample = False
        self._packets = 0
        self._poll_hz = -1.0

    def _open_device(self, device: DeviceIdentity) -> None:
        self._stop_pump()
        self._session = "loading"
        self._session_detail = tr("opening_pad")
        self._pump = DevicePump(device)
        self._pump.start()
        self._load_profile(device)
        self._emit_chrome()
        self.frame.emit()
        if ps3drv.needs_helper(device):
            self._maybe_offer_ps3()

    def _add_device(self, device: DeviceIdentity) -> None:
        if device.backend == "xinput" and device.index in self._ignore_xinput:
            return
        key = device_key(device)
        if key in self._devices:
            return
        self._devices[key] = device
        self._emit_chrome()
        if self._pump is None:
            self._open_device(device)
        if ps3drv.needs_helper(device):
            QTimer.singleShot(400, self._maybe_offer_ps3)

    def _remove_device(self, device: DeviceIdentity) -> None:
        key = device_key(device)
        self._devices.pop(key, None)
        if self._pump and device_key(self._pump.identity) == key:
            self._stop_pump()
            self._session = "error"
            self._session_detail = tr("lost_device")
            self.frame.emit()
        if self._pump is None and not self._devices:
            self._session = "empty"
            self._session_detail = ""
            self._profile_name = None
        self._emit_chrome()

    def _maybe_offer_ps3(self) -> None:
        if self._ps3_offer_asked:
            return
        if not any(ps3drv.needs_helper(dev) for dev in self._devices.values()):
            return
        self._ps3_offer_asked = True
        name = ps3drv.package_name()
        detail = tr("ps3_dshidmini") if name == "DsHidMini" else tr("ps3_scp")
        self._ask(name, detail, lambda: self._start_download(name, ps3drv.download_installer, self._run_ps3))

    def _start_download(self, name: str, fn, on_ok) -> None:
        self._set_notice(tr("dl_setup", name=name))
        self._download = _Download(fn)
        self._download.finished_ok.connect(on_ok)
        self._download.finished_err.connect(self._set_notice)
        self._download.start()

    def _run_ps3(self, path) -> None:
        name = ps3drv.package_name()
        try:
            ps3drv.launch_installer(path)
        except ps3drv.Ps3DriverError as exc:
            self._set_notice(str(exc))
            return
        self._set_notice(tr("finish_ps3", name=name))
        self._refresh_drivers()

    def _offer_vigem(self) -> None:
        self._ask("ViGEmBus", tr("vigem_body"), lambda: self._start_download(
            "ViGEmBus", download_installer, self._run_vigem
        ))

    def _run_vigem(self, path) -> None:
        try:
            launch_installer(path)
        except RuntimeError as exc:
            self._set_notice(str(exc))
            return
        self._set_notice(tr("finish_vigem"))
        self._refresh_drivers()

    def _offer_hidhide(self) -> None:
        self._ask("HidHide", tr("hidhide_body"), lambda: self._start_download(
            "HidHide", hidhide.download_installer, self._run_hidhide
        ))

    def _run_hidhide(self, path) -> None:
        try:
            hidhide.launch_installer(path)
        except hidhide.HidHideError as exc:
            self._set_notice(str(exc))
            return
        self._set_notice(tr("finish_hidhide"))
        self._refresh_drivers()

    def _hide_physical(self, identity: DeviceIdentity) -> str:
        if not hidhide.is_installed():
            self._offer_hidhide()
            return tr("hide_missing")
        try:
            hidhide.register_app(sys.executable)
            hidden = []
            for path in hide_paths_for(identity):
                instance = hidhide.hidapi_to_instance(path)
                hidhide.hide_device(instance)
                hidden.append(instance)
            hidhide.cloak(True)
            self._hidden_instances = hidden
            if not hidden:
                return tr("hide_xinput")
            return tr("hide_ok")
        except hidhide.HidHideError as exc:
            return tr("hide_fail", error=exc)

    def _unhide_physical(self) -> None:
        for instance in self._hidden_instances:
            try:
                hidhide.unhide_device(instance)
            except hidhide.HidHideError:
                pass
        if self._hidden_instances:
            try:
                hidhide.cloak(False)
            except hidhide.HidHideError:
                pass
        self._hidden_instances = []

    def _current_state(self) -> NormalizedState | None:
        if self._pump is None:
            return None
        raw = self._pump.latest()
        if raw is None:
            return None
        return self._filtered(raw)

    def _read_pad(self, state: NormalizedState) -> None:
        self._lx = state.lx
        self._ly = state.ly
        self._rx = state.rx
        self._ry = state.ry
        self._lt = state.lt
        self._rt = state.rt
        for name in self._pad:
            self._pad[name] = bool(getattr(state, name))

    def _tick(self) -> None:
        if self._pump is None:
            return
        if self._virtual.error():
            self._notice = tr("virtual_err", error=self._virtual.error())
            self._virtual.stop()
            self._unhide_physical()
            self._virtual_on = False
            self._ignore_xinput.clear()
            self._emit_chrome()
        if self._pump.error() or not self._pump.connected():
            detail = str(self._pump.error()) if self._pump.error() else tr("lost_device")
            if self._guide.active:
                self._guide.stop()
                self.guideChanged.emit()
            if self._session != "error" or self._session_detail != detail:
                self._session = "error"
                self._session_detail = detail
                self._emit_chrome()
            return
        raw = self._pump.latest()
        if raw is None:
            return
        if self._session != "ready":
            self._session = "ready"
            self._session_detail = ""
            self._emit_chrome()
        if self._guide.active:
            self._guide.feed(raw)
            self.guideChanged.emit()
        shown = raw if self._view == "physical" else self._filtered(raw)
        self._read_pad(shown)
        packets, gap = self._pump.traffic()
        self._packets = packets
        self._poll_hz = (1.0 / gap) if gap and gap > 0 else -1.0
        self._has_sample = True
        self.frame.emit()

    @Slot(str, result=str)
    def fontUrl(self, name: str) -> str:
        path = bundle_root() / "ui" / "fonts" / name
        return QUrl.fromLocalFile(str(path)).toString()

    @Slot(str, str, str)
    def setFontFamilies(self, display: str, body: str, strong: str) -> None:
        if display:
            self._display_family = display
        if body:
            self._body_family = body
        if strong:
            self._strong_family = strong
        self.fontFamiliesChanged.emit()

    @Slot(str, result=str)
    def label(self, key: str) -> str:
        return tr(key)

    @Slot(str)
    def setPage(self, page_id: str) -> None:
        if page_id == self._page:
            return
        if not any(item["id"] == page_id for item in self._destinations()):
            return
        self._page = page_id
        self._emit_chrome()

    @Slot(str)
    def selectDevice(self, key: str) -> None:
        device = self._devices.get(key)
        if device is None:
            return
        if self._pump and device_key(self._pump.identity) == key and self._session == "ready":
            return
        self._open_device(device)

    @Slot(str)
    def setViewMode(self, mode: str) -> None:
        if mode not in ("physical", "virtual") or mode == self._view:
            return
        self._view = mode
        self._emit_chrome()
        self.frame.emit()

    @Slot()
    def reopenDevice(self) -> None:
        if self._pump is None:
            self._set_notice(tr("need_pad"))
            return
        self._open_device(self._pump.identity)

    @Slot()
    def toggleVirtual(self) -> None:
        if self._virtual_on:
            self._virtual.stop()
            self._unhide_physical()
            self._ignore_xinput.clear()
            self._virtual_on = False
            self._set_notice(tr("virtual_stopped"))
            self._refresh_drivers()
            return
        if self._pump is None:
            self._set_notice(tr("need_pad"))
            return
        before = {dev.index for dev in enumerate_xinput() if dev.index is not None}
        try:
            self._virtual.start(self._current_state)
        except ViGEmMissingError as exc:
            self._set_notice(str(exc))
            self._offer_vigem()
            return
        except RuntimeError as exc:
            self._set_notice(str(exc))
            return
        after = {dev.index for dev in enumerate_xinput() if dev.index is not None}
        self._ignore_xinput = after - before
        note = self._hide_physical(self._pump.identity)
        self._virtual_on = True
        self._set_notice(tr("virtual_running", note=note))
        self._refresh_drivers()

    @Slot()
    def confirmYes(self) -> None:
        fn = self._on_yes
        self._close_confirm()
        if fn is not None:
            fn()

    @Slot()
    def confirmNo(self) -> None:
        self._close_confirm()

    def _write_profile(self, clear_measured: bool = False) -> None:
        if self._pump is None:
            return
        with self._cal_lock:
            cal = self._cal
        path = save_profile(
            self._pump.identity,
            cal,
            self._rules,
            measured=None if clear_measured else self._measured,
            clear_measured=clear_measured,
        )
        self._profile_name = path.name
        self._profile_error = False

    @Slot()
    def startGuide(self) -> None:
        if self._pump is None or self._session != "ready":
            self._set_notice(tr("need_pad"))
            return
        self._guide.start()
        self.guideChanged.emit()

    @Slot()
    def exitGuide(self) -> None:
        if not self._guide.active:
            return
        self._guide.stop()
        self.guideChanged.emit()

    @Slot()
    def guideBack(self) -> None:
        self._guide.back()
        self.guideChanged.emit()

    @Slot()
    def guideNext(self) -> None:
        result = self._guide.advance()
        if result == "done":
            self._save_guide()
            return
        self.guideChanged.emit()

    def _save_guide(self) -> None:
        if self._pump is None:
            self._guide.stop()
            self.guideChanged.emit()
            return
        with self._cal_lock:
            self._guide.apply(self._cal)
        self._measured = {
            "at": datetime.now().isoformat(timespec="seconds"),
            "summary": self._guide.summary(),
        }
        self._write_profile()
        self._draft = None
        self._guide.stop()
        self._set_notice(tr("guide_saved"))
        self.curveChanged.emit()
        self.guideChanged.emit()
        self.frame.emit()

    @Slot()
    def restoreFactory(self) -> None:
        if self._pump is None:
            self._set_notice(tr("need_pad"))
            return
        with self._cal_lock:
            self._cal = Calibration.default()
        self._measured = {"at": "", "summary": ""}
        self._draft = None
        self._write_profile(clear_measured=True)
        self._set_notice(tr("factory_done"))
        self.curveChanged.emit()
        self.guideChanged.emit()
        self.frame.emit()

    @Slot()
    def exportReport(self) -> None:
        if self._pump is None or not self._measured.get("at"):
            self._set_notice(tr("no_export"))
            return
        target = profile_path(self._pump.identity).with_name(
            f"{profile_key(self._pump.identity)}-calibration.txt"
        )
        lines = [
            self._measured.get("at", ""),
            self._measured.get("summary", ""),
        ]
        target.write_text("\n".join(lines) + "\n", encoding="utf-8")
        self._set_notice(tr("export_done", name=target.name))

    @Slot()
    def shutdown(self) -> None:
        self._guide.stop()
        self._timer.stop()
        self._driver_timer.stop()
        self._virtual.stop()
        self._unhide_physical()
        self._stop_pump()
        self._monitor.stop()

    def _draft_cal(self) -> Calibration:
        if self._draft is None:
            with self._cal_lock:
                self._draft = deepcopy(self._cal)
        return self._draft

    def _sync_stick_pair(self, inner: float | None = None, outer: float | None = None, curve: float | None = None) -> None:
        draft = self._draft_cal()
        for stick in (draft.left, draft.right):
            if inner is not None:
                stick.inner = inner
            if outer is not None:
                stick.outer = max(stick.inner + 0.01, min(outer, 1.0))
            if curve is not None:
                stick.curve = curve
        self._curve_error = ""
        self.curveChanged.emit()

    @Slot(float)
    def setInner(self, percent: float) -> None:
        inner = max(0.0, min(percent / 100.0, 0.95))
        draft = self._draft_cal()
        outer = max(draft.left.outer, inner + 0.01)
        self._sync_stick_pair(inner=inner, outer=outer)

    @Slot(float)
    def setOuter(self, percent: float) -> None:
        draft = self._draft_cal()
        outer = max(draft.left.inner + 0.01, min(percent / 100.0, 1.0))
        self._sync_stick_pair(outer=outer)

    @Slot(float)
    def setTriggerInner(self, percent: float) -> None:
        draft = self._draft_cal()
        inner = max(0.0, min(percent / 100.0, 0.95))
        for trigger in (draft.lt, draft.rt):
            trigger.inner = inner
            trigger.outer = max(trigger.outer, inner + 0.01)
        self._curve_error = ""
        self.curveChanged.emit()

    @Slot(float)
    def setTriggerOuter(self, percent: float) -> None:
        draft = self._draft_cal()
        for trigger in (draft.lt, draft.rt):
            trigger.outer = max(trigger.inner + 0.01, min(percent / 100.0, 1.0))
        self._curve_error = ""
        self.curveChanged.emit()

    @Slot(str)
    def setCurvePreset(self, preset: str) -> None:
        curve = {"linear": 1.0, "aggressive": 0.55, "smooth": 1.8}.get(preset)
        if curve is None:
            return
        self._sync_stick_pair(curve=curve)

    @Slot()
    def applyCurve(self) -> None:
        if self._pump is None:
            self._curve_error = "missing"
            self._set_notice(tr("need_device_curve"))
            self.curveChanged.emit()
            return
        draft = deepcopy(self._draft_cal())
        with self._cal_lock:
            previous = deepcopy(self._cal)
            self._cal = draft
        try:
            self._write_profile()
        except OSError:
            with self._cal_lock:
                self._cal = previous
            self._curve_error = "write"
            self._set_notice(tr("curve_write_error"))
            self.curveChanged.emit()
            return
        self._draft = deepcopy(draft)
        self._curve_error = ""
        self._set_notice(tr("curve_applied"))
        self.curveChanged.emit()
        self.frame.emit()

    @Slot()
    def discardCurve(self) -> None:
        self._draft = None
        self._curve_error = ""
        self.curveChanged.emit()
        self.frame.emit()

    def _curve_preset(self) -> str:
        curve = self._draft_cal().left.curve
        if abs(curve - 1.0) < 0.05:
            return "linear"
        if abs(curve - 0.55) < 0.05:
            return "aggressive"
        if abs(curve - 1.8) < 0.05:
            return "smooth"
        return "custom"

    def _curve_name(self) -> str:
        preset = self._curve_preset()
        if preset == "linear":
            return tr("preset_linear")
        if preset == "aggressive":
            return tr("preset_aggressive")
        if preset == "smooth":
            return tr("preset_smooth")
        return tr("curve_named", value=f"{self._draft_cal().left.curve:.1f}")

    def _curve_points(self) -> list:
        draft = self._draft_cal()
        sample = StickCal(
            inner=draft.left.inner,
            outer=draft.left.outer,
            curve=draft.left.curve,
        )
        points = []
        for index in range(33):
            incoming = index / 32
            outgoing, _y = apply_stick(incoming, 0.0, sample)
            points.append(round(outgoing, 4))
        return points

    def _inner_percent(self) -> float:
        return self._draft_cal().left.inner * 100

    def _outer_percent(self) -> float:
        return self._draft_cal().left.outer * 100

    def _trigger_inner_percent(self) -> float:
        return self._draft_cal().lt.inner * 100

    def _trigger_outer_percent(self) -> float:
        return self._draft_cal().lt.outer * 100

    def _curve_state(self) -> str:
        if self._session == "loading":
            return "loading"
        if self._curve_error == "write":
            return "error"
        if self._pump is None:
            return "empty"
        return "ready"

    def _curve_detail(self) -> str:
        state = self._curve_state()
        if state == "loading":
            return tr("curve_loading")
        if state == "error":
            return tr("curve_write_error")
        if state == "empty":
            return tr("need_device_curve")
        return ""

    def _guide_open(self) -> bool:
        return self._guide.active

    def _guide_index(self) -> int:
        return self._guide.index

    def _guide_step_text(self) -> str:
        return tr("guide_step", n=self._guide.index + 1)

    def _guide_heading(self) -> str:
        return tr(f"step{self._guide.index + 1}_title")

    def _guide_body(self) -> str:
        return tr(f"step{self._guide.index + 1}_body")

    def _guide_measure_text(self) -> str:
        found = self._guide.measure()
        if not found:
            return ""
        key, params = found
        return tr(key, **params)

    def _guide_error_text(self) -> str:
        if not self._guide.error:
            return ""
        return tr(f"err_{self._guide.error}")

    def _guide_phase_value(self) -> str:
        if not self._guide.active:
            return "empty"
        return self._guide.phase()

    def _guide_focus(self) -> str:
        return {
            "rest": "all",
            "left": "left",
            "right": "right",
            "triggers": "triggers",
            "buttons": "buttons",
        }.get(self._guide.step(), "all")

    def _guide_next_label(self) -> str:
        if self._guide.index >= 4:
            return tr("guide_save")
        return tr("guide_next")

    def _guide_show_back(self) -> bool:
        return self._guide.index > 0

    def _cal_state(self) -> str:
        if self._session == "loading":
            return "loading"
        if self._profile_error:
            return "error"
        if self._measured.get("at"):
            return "ready"
        return "empty"

    def _cal_word(self) -> str:
        if self._cal_state() == "ready":
            return tr("cal_valid")
        return ""

    def _cal_detail(self) -> str:
        state = self._cal_state()
        if state == "loading":
            return tr("cal_loading")
        if state == "error":
            return tr("cal_read_error")
        if state == "ready":
            return f"{self._measured.get('summary', '')}  {self._measured.get('at', '')}"
        return tr("cal_empty")

    def _lang_tick_value(self) -> int:
        return self._lang_tick

    def _display_family_value(self) -> str:
        return self._display_family

    def _body_family_value(self) -> str:
        return self._body_family

    def _strong_family_value(self) -> str:
        return self._strong_family

    def _page_value(self) -> str:
        return self._page

    def _destinations_value(self) -> list:
        return self._destinations()

    def _devices_value(self) -> list:
        return self._device_rows()

    def _device_name_value(self) -> str:
        if self._pump is None:
            return tr("no_device")
        return self._pump.identity.product_name

    def _session_value(self) -> str:
        return self._session

    def _session_detail_value(self) -> str:
        return self._session_detail

    def _view_value(self) -> str:
        return self._view

    def _notice_value(self) -> str:
        return self._notice

    def _has_sample_value(self) -> bool:
        return self._has_sample

    def _axis(self, name: str) -> float:
        return getattr(self, name)

    def _pad_value(self, name: str) -> bool:
        return self._pad[name]

    def _poll_text(self) -> str:
        if not self._has_sample or self._poll_hz < 0:
            return tr("no_sample")
        return tr("hertz", n=int(round(self._poll_hz)))

    def _packet_text(self) -> str:
        if self._packets <= 0:
            return tr("no_sample")
        return str(self._packets)

    def _deadzone_text(self) -> str:
        with self._cal_lock:
            inner = self._cal.left.inner
        return tr("percent", n=int(round(inner * 100)))

    def _stick_text(self) -> str:
        if not self._has_sample:
            return tr("no_sample")
        return f"{self._lx:+.2f}, {self._ly:+.2f}"

    def _lt_text(self) -> str:
        if not self._has_sample:
            return tr("no_sample")
        return tr("percent", n=int(round(max(0.0, self._lt) * 100)))

    def _rt_text(self) -> str:
        if not self._has_sample:
            return tr("no_sample")
        return tr("percent", n=int(round(max(0.0, self._rt) * 100)))

    def _vigem_word(self) -> str:
        return self._vigem_word

    def _hid_word_value(self) -> str:
        return self._hid_word

    def _poll_status(self) -> str:
        return self._poll_text()

    def _profile_word(self) -> str:
        return self._profile_name or tr("status_no_profile")

    def _virtual_running(self) -> bool:
        return self._virtual_on

    def _virtual_label(self) -> str:
        return tr("virtual_off") if self._virtual_on else tr("virtual_on")

    def _confirm_open_value(self) -> bool:
        return self._confirm_open

    def _confirm_title_value(self) -> str:
        return self._confirm_title

    def _confirm_body_value(self) -> str:
        return self._confirm_body

    langTick = Property(int, _lang_tick_value, notify=languageChanged)
    displayFamily = Property(str, _display_family_value, notify=fontFamiliesChanged)
    bodyFamily = Property(str, _body_family_value, notify=fontFamiliesChanged)
    strongFamily = Property(str, _strong_family_value, notify=fontFamiliesChanged)
    page = Property(str, _page_value, notify=chromeChanged)
    destinations = Property("QVariantList", _destinations_value, notify=chromeChanged)
    devices = Property("QVariantList", _devices_value, notify=chromeChanged)
    deviceName = Property(str, _device_name_value, notify=chromeChanged)
    session = Property(str, _session_value, notify=chromeChanged)
    sessionDetail = Property(str, _session_detail_value, notify=chromeChanged)
    viewMode = Property(str, _view_value, notify=chromeChanged)
    notice = Property(str, _notice_value, notify=chromeChanged)
    hasSample = Property(bool, _has_sample_value, notify=frame)
    lx = Property(float, lambda self: self._lx, notify=frame)
    ly = Property(float, lambda self: self._ly, notify=frame)
    rx = Property(float, lambda self: self._rx, notify=frame)
    ry = Property(float, lambda self: self._ry, notify=frame)
    lt = Property(float, lambda self: self._lt, notify=frame)
    rt = Property(float, lambda self: self._rt, notify=frame)
    padA = Property(bool, lambda self: self._pad["a"], notify=frame)
    padB = Property(bool, lambda self: self._pad["b"], notify=frame)
    padX = Property(bool, lambda self: self._pad["x"], notify=frame)
    padY = Property(bool, lambda self: self._pad["y"], notify=frame)
    padLb = Property(bool, lambda self: self._pad["lb"], notify=frame)
    padRb = Property(bool, lambda self: self._pad["rb"], notify=frame)
    padLs = Property(bool, lambda self: self._pad["ls"], notify=frame)
    padRs = Property(bool, lambda self: self._pad["rs"], notify=frame)
    padBack = Property(bool, lambda self: self._pad["back"], notify=frame)
    padStart = Property(bool, lambda self: self._pad["start"], notify=frame)
    padGuide = Property(bool, lambda self: self._pad["guide"], notify=frame)
    padUp = Property(bool, lambda self: self._pad["dpad_up"], notify=frame)
    padDown = Property(bool, lambda self: self._pad["dpad_down"], notify=frame)
    padLeft = Property(bool, lambda self: self._pad["dpad_left"], notify=frame)
    padRight = Property(bool, lambda self: self._pad["dpad_right"], notify=frame)
    pollText = Property(str, _poll_text, notify=frame)
    packetText = Property(str, _packet_text, notify=frame)
    deadzoneText = Property(str, _deadzone_text, notify=frame)
    stickText = Property(str, _stick_text, notify=frame)
    ltText = Property(str, _lt_text, notify=frame)
    rtText = Property(str, _rt_text, notify=frame)
    vigemWord = Property(str, _vigem_word, notify=chromeChanged)
    hidHideWord = Property(str, _hid_word_value, notify=chromeChanged)
    pollStatus = Property(str, _poll_status, notify=frame)
    profileWord = Property(str, _profile_word, notify=chromeChanged)
    virtualRunning = Property(bool, _virtual_running, notify=chromeChanged)
    virtualLabel = Property(str, _virtual_label, notify=chromeChanged)
    confirmOpen = Property(bool, _confirm_open_value, notify=chromeChanged)
    confirmTitle = Property(str, _confirm_title_value, notify=chromeChanged)
    confirmBody = Property(str, _confirm_body_value, notify=chromeChanged)
    guideOpen = Property(bool, _guide_open, notify=guideChanged)
    guideIndex = Property(int, _guide_index, notify=guideChanged)
    guideStep = Property(str, _guide_step_text, notify=guideChanged)
    guideHeading = Property(str, _guide_heading, notify=guideChanged)
    guideBody = Property(str, _guide_body, notify=guideChanged)
    guideMeasure = Property(str, _guide_measure_text, notify=guideChanged)
    guideError = Property(str, _guide_error_text, notify=guideChanged)
    guidePhase = Property(str, _guide_phase_value, notify=guideChanged)
    guideFocus = Property(str, _guide_focus, notify=guideChanged)
    guideNextLabel = Property(str, _guide_next_label, notify=guideChanged)
    guideShowBack = Property(bool, _guide_show_back, notify=guideChanged)
    calState = Property(str, _cal_state, notify=chromeChanged)
    calWord = Property(str, _cal_word, notify=chromeChanged)
    calDetail = Property(str, _cal_detail, notify=chromeChanged)
    curvePreset = Property(str, _curve_preset, notify=curveChanged)
    curveName = Property(str, _curve_name, notify=curveChanged)
    curvePoints = Property("QVariantList", _curve_points, notify=curveChanged)
    innerPercent = Property(float, _inner_percent, notify=curveChanged)
    outerPercent = Property(float, _outer_percent, notify=curveChanged)
    triggerInnerPercent = Property(float, _trigger_inner_percent, notify=curveChanged)
    triggerOuterPercent = Property(float, _trigger_outer_percent, notify=curveChanged)
    curveState = Property(str, _curve_state, notify=curveChanged)
    curveDetail = Property(str, _curve_detail, notify=curveChanged)
