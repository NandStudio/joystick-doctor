from __future__ import annotations

import sys
import threading

from PySide6.QtCore import QObject, QPointF, QThread, QTimer, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QCheckBox,
    QComboBox,
    QMessageBox,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QPlainTextEdit,
    QSlider,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from engine.diagnose import DiagnoseRunner
from engine.pipeline import Calibration, apply_calibration
from engine.prefs import load_language, save_language
from engine.remap import BUTTONS, RemapConfig, RemapEngine, RemapRule
from engine.device.catalog import device_key, enumerate_all, hide_paths_for
from engine import hidhide
from engine import ps3drv
from engine.profiles import load_profile, profile_key, save_profile
from ui.i18n import set_language, tr
from engine.device.hotplug import HotplugMonitor
from engine.device.pump import DevicePump
from engine.device.xinput import enumerate_devices as enumerate_xinput
from engine.state import DeviceIdentity, NormalizedState
from engine.vigem import ViGEmMissingError, download_installer, is_installed as vigem_installed
from engine.vigem import launch_installer
from engine.virtual import VirtualXbox


class _Bridge(QObject):
    added = Signal(object)
    removed = Signal(object)


class _InstallerDownload(QThread):
    finished_ok = Signal(object)
    finished_err = Signal(str)

    def run(self) -> None:
        try:
            self.finished_ok.emit(download_installer())
        except Exception as exc:
            self.finished_err.emit(str(exc))


class _HidHideDownload(QThread):
    finished_ok = Signal(object)
    finished_err = Signal(str)

    def run(self) -> None:
        try:
            self.finished_ok.emit(hidhide.download_installer())
        except Exception as exc:
            self.finished_err.emit(str(exc))


class _Ps3DrvDownload(QThread):
    finished_ok = Signal(object)
    finished_err = Signal(str)

    def run(self) -> None:
        try:
            self.finished_ok.emit(ps3drv.download_installer())
        except Exception as exc:
            self.finished_err.emit(str(exc))


class StickView(QWidget):
    def __init__(self, title: str):
        super().__init__()
        self._title = title
        self._x = 0.0
        self._y = 0.0
        self.setMinimumSize(140, 160)

    def set_value(self, x: float, y: float) -> None:
        self._x = x
        self._y = y
        self.update()

    def set_title(self, title: str) -> None:
        self._title = title
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.drawText(8, 16, self._title)
        side = min(self.width() - 16, self.height() - 28)
        cx = self.width() / 2
        cy = 20 + side / 2
        radius = side / 2 - 4
        painter.setPen(QPen(QColor("#888"), 2))
        painter.setBrush(QColor("#1e1e1e"))
        painter.drawEllipse(QPointF(cx, cy), radius, radius)
        painter.drawLine(QPointF(cx - radius, cy), QPointF(cx + radius, cy))
        painter.drawLine(QPointF(cx, cy - radius), QPointF(cx, cy + radius))
        dot = QPointF(cx + self._x * radius, cy - self._y * radius)
        painter.setBrush(QColor("#4caf50"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(dot, 7, 7)


class ButtonLamp(QLabel):
    def __init__(self, name: str):
        super().__init__(name)
        self._name = name
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(44, 28)
        self.set_on(False)

    def set_on(self, on: bool) -> None:
        bg = "#2e7d32" if on else "#2a2a2a"
        fg = "#ffffff" if on else "#aaaaaa"
        self.setStyleSheet(
            f"background:{bg}; color:{fg}; border-radius:4px; padding:4px; font-weight:600;"
        )


class ButtonPad(QWidget):
    _KEYS = (
        ("Y", "y"),
        ("X", "x"),
        ("A", "a"),
        ("B", "b"),
        ("LB", "lb"),
        ("RB", "rb"),
        ("LT", "lt"),
        ("RT", "rt"),
        ("LS", "ls"),
        ("RS", "rs"),
        ("Back", "back"),
        ("Start", "start"),
        ("Guide", "guide"),
        ("U", "dpad_up"),
        ("D", "dpad_down"),
        ("L", "dpad_left"),
        ("R", "dpad_right"),
    )

    def __init__(self):
        super().__init__()
        self._lamps = {key: ButtonLamp(label) for label, key in self._KEYS}
        grid = QGridLayout(self)
        grid.setContentsMargins(0, 0, 0, 0)
        layout = (
            (0, 1, "Y"),
            (1, 0, "X"),
            (1, 1, "A"),
            (1, 2, "B"),
            (0, 3, "LB"),
            (0, 4, "RB"),
            (1, 3, "LT"),
            (1, 4, "RT"),
            (2, 0, "Back"),
            (2, 1, "Guide"),
            (2, 2, "Start"),
            (3, 0, "LS"),
            (3, 2, "RS"),
            (4, 1, "U"),
            (5, 0, "L"),
            (5, 1, "D"),
            (5, 2, "R"),
        )
        for row, col, label in layout:
            key = next(k for lab, k in self._KEYS if lab == label)
            grid.addWidget(self._lamps[key], row, col)

    def set_state(self, state: NormalizedState) -> None:
        analog = {"lt": state.lt > 0.15, "rt": state.rt > 0.15}
        for _label, key in self._KEYS:
            if key in analog:
                self._lamps[key].set_on(analog[key])
            else:
                self._lamps[key].set_on(bool(getattr(state, key)))


class LiveWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Joystick Doctor")
        self.resize(1040, 640)
        self._pump: DevicePump | None = None
        self._virtual = VirtualXbox()
        self._ignore_xinput: set[int] = set()
        self._hidden_instances: list[str] = []
        self._loading_profile = False
        self._ps3_offer_asked = False
        self._diag_result_shown = False
        self._profile_name: str | None = None
        self._lang_pref = load_language()
        set_language(self._lang_pref)
        self._devices: dict[str, DeviceIdentity] = {}

        self._list = QListWidget()
        self._list.currentItemChanged.connect(self._on_pick)
        self._cal = Calibration.default()
        self._cal_lock = threading.Lock()
        self._diag = DiagnoseRunner()
        self._remap = RemapEngine()
        self._remap_lock = threading.Lock()
        self._ls = StickView(tr("stick_left"))
        self._rs = StickView(tr("stick_right"))
        self._lt = QProgressBar()
        self._rt = QProgressBar()
        for bar in (self._lt, self._rt):
            bar.setRange(0, 100)
            bar.setTextVisible(True)
        self._pad = ButtonPad()
        self._virtual_btn = QPushButton()
        self._virtual_btn.setCheckable(True)
        self._virtual_btn.clicked.connect(self._toggle_virtual)
        self._save_btn = QPushButton()
        self._save_btn.clicked.connect(self._save_current_profile)
        self._status = QLabel()
        self._status.setWordWrap(True)
        self._vigem_status = QLabel()
        self._hidhide_status = QLabel()
        self._ps3_status = QLabel()
        self._profile_lbl = QLabel()
        self._profile_lbl.setWordWrap(True)
        self._diag_step = QLabel()
        self._diag_step.setWordWrap(True)
        self._diag_step.setStyleSheet("font-size:16px; font-weight:600;")
        self._refresh_drivers()
        self._ls_dz = self._slider(0, 40, 10)
        self._rs_dz = self._slider(0, 40, 10)
        self._curve = self._slider(20, 200, 100)
        self._invert_ly = QCheckBox()
        self._invert_ry = QCheckBox()
        self._recenter = QPushButton()
        self._ls_dz.valueChanged.connect(self._sync_cal)
        self._rs_dz.valueChanged.connect(self._sync_cal)
        self._curve.valueChanged.connect(self._sync_cal)
        self._invert_ly.toggled.connect(self._sync_cal)
        self._invert_ry.toggled.connect(self._sync_cal)
        self._recenter.clicked.connect(self._recenter_sticks)
        self._rules: list[RemapRule] = []
        self._src_list = QListWidget()
        self._src_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self._src_list.setMaximumHeight(110)
        self._dest = QComboBox()
        self._hold = QComboBox()
        for key in BUTTONS:
            label = key.upper().replace("_", " ")
            self._src_list.addItem(label)
            self._src_list.item(self._src_list.count() - 1).setData(
                Qt.ItemDataRole.UserRole, key
            )
            self._dest.addItem(label, key)
        self._fill_hold()
        self._rule_list = QListWidget()
        self._add_rule = QPushButton()
        self._del_rule = QPushButton()
        self._diag_btn = QPushButton()
        self._apply_diag = QPushButton()
        self._lang = QComboBox()
        self._lang.currentIndexChanged.connect(self._on_language)
        self._diag_out = QPlainTextEdit()
        self._diag_out.setReadOnly(True)
        self._diag_btn.clicked.connect(self._start_diag)
        self._apply_diag.clicked.connect(self._apply_diag_recs)
        self._add_rule.clicked.connect(self._add_custom_rule)
        self._del_rule.clicked.connect(self._remove_custom_rule)

        live = QWidget()
        live_lay = QVBoxLayout(live)
        sticks = QHBoxLayout()
        sticks.addWidget(self._ls)
        sticks.addWidget(self._rs)
        live_lay.addLayout(sticks)
        self._lbl_lt = QLabel("LT")
        self._lbl_rt = QLabel("RT")
        self._lbl_buttons = QLabel()
        live_lay.addWidget(self._lbl_lt)
        live_lay.addWidget(self._lt)
        live_lay.addWidget(self._lbl_rt)
        live_lay.addWidget(self._rt)
        live_lay.addWidget(self._lbl_buttons)
        live_lay.addWidget(self._pad)
        live_lay.addStretch()

        diag = QWidget()
        diag_lay = QVBoxLayout(diag)
        self._lbl_diag_steps = QLabel()
        diag_lay.addWidget(self._lbl_diag_steps)
        diag_lay.addWidget(self._diag_step)
        diag_lay.addWidget(self._diag_btn)
        diag_lay.addWidget(self._apply_diag)
        diag_lay.addWidget(self._diag_out)
        diag_lay.addStretch()

        settings = QWidget()
        set_lay = QVBoxLayout(settings)
        self._lbl_ls_dz = QLabel()
        self._lbl_rs_dz = QLabel()
        self._lbl_curve = QLabel()
        self._lbl_sources = QLabel()
        self._lbl_dest = QLabel()
        self._lbl_lang = QLabel()
        set_lay.addWidget(self._lbl_lang)
        set_lay.addWidget(self._lang)
        set_lay.addWidget(self._lbl_ls_dz)
        set_lay.addWidget(self._ls_dz)
        set_lay.addWidget(self._lbl_rs_dz)
        set_lay.addWidget(self._rs_dz)
        set_lay.addWidget(self._lbl_curve)
        set_lay.addWidget(self._curve)
        set_lay.addWidget(self._invert_ly)
        set_lay.addWidget(self._invert_ry)
        set_lay.addWidget(self._recenter)
        set_lay.addWidget(self._lbl_sources)
        set_lay.addWidget(self._src_list)
        set_lay.addWidget(self._lbl_dest)
        set_lay.addWidget(self._dest)
        set_lay.addWidget(self._hold)
        set_lay.addWidget(self._add_rule)
        set_lay.addWidget(self._rule_list)
        set_lay.addWidget(self._del_rule)
        set_lay.addStretch()

        self._tabs = QTabWidget()
        self._tabs.addTab(live, "")
        self._tabs.addTab(diag, "")
        self._tabs.addTab(settings, "")

        side = QWidget()
        side.setMaximumWidth(280)
        side_lay = QVBoxLayout(side)
        self._lbl_device = QLabel()
        self._lbl_drivers = QLabel()
        side_lay.addWidget(self._lbl_device)
        side_lay.addWidget(self._list)
        side_lay.addWidget(self._lbl_drivers)
        side_lay.addWidget(self._vigem_status)
        side_lay.addWidget(self._hidhide_status)
        side_lay.addWidget(self._ps3_status)
        side_lay.addWidget(self._profile_lbl)
        side_lay.addWidget(self._save_btn)
        side_lay.addWidget(self._virtual_btn)
        side_lay.addWidget(self._status)
        side_lay.addStretch()

        root = QHBoxLayout(self)
        root.addWidget(side, 0)
        root.addWidget(self._tabs, 1)
        self._retranslate()

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
        if self._list.count():
            self._list.setCurrentRow(0)
        QTimer.singleShot(400, self._maybe_offer_ps3_helper)

        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def closeEvent(self, event) -> None:
        self._timer.stop()
        self._virtual.stop()
        self._unhide_physical()
        self._stop_pump()
        self._monitor.stop()
        super().closeEvent(event)

    def _fill_hold(self) -> None:
        current = self._hold.currentData() if self._hold.count() else None
        self._hold.blockSignals(True)
        self._hold.clear()
        self._hold.addItem(tr("hold_none"), None)
        for key in BUTTONS:
            label = key.upper().replace("_", " ")
            self._hold.addItem(tr("hold_item", label=label), key)
        index = self._hold.findData(current)
        self._hold.setCurrentIndex(max(0, index))
        self._hold.blockSignals(False)

    def _fill_language(self) -> None:
        self._lang.blockSignals(True)
        self._lang.clear()
        self._lang.addItem(tr("lang_system"), "system")
        self._lang.addItem(tr("lang_en"), "en")
        self._lang.addItem(tr("lang_es"), "es")
        index = self._lang.findData(self._lang_pref)
        self._lang.setCurrentIndex(max(0, index))
        self._lang.blockSignals(False)

    def _on_language(self) -> None:
        pref = self._lang.currentData() or "system"
        self._lang_pref = pref
        save_language(pref)
        set_language(pref)
        self._retranslate()

    def _retranslate(self) -> None:
        self._fill_language()
        self._fill_hold()
        self._save_btn.setText(tr("save_profile"))
        self._virtual_btn.setText(
            tr("virtual_off") if self._virtual_btn.isChecked() else tr("virtual_on")
        )
        self._invert_ly.setText(tr("invert_ly"))
        self._invert_ry.setText(tr("invert_ry"))
        self._recenter.setText(tr("recenter"))
        self._add_rule.setText(tr("add_remap"))
        self._del_rule.setText(tr("del_remap"))
        self._diag_btn.setText(tr("run_diag"))
        self._apply_diag.setText(tr("apply_diag"))
        self._ls.set_title(tr("stick_left"))
        self._rs.set_title(tr("stick_right"))
        self._lbl_buttons.setText(tr("buttons"))
        self._lbl_diag_steps.setText(tr("diag_steps"))
        self._lbl_ls_dz.setText(tr("ls_dz"))
        self._lbl_rs_dz.setText(tr("rs_dz"))
        self._lbl_curve.setText(tr("curve"))
        self._lbl_sources.setText(tr("remap_sources"))
        self._lbl_dest.setText(tr("destination"))
        self._lbl_lang.setText(tr("language"))
        self._lbl_device.setText(tr("device"))
        self._lbl_drivers.setText(tr("drivers"))
        self._tabs.setTabText(0, tr("tab_live"))
        self._tabs.setTabText(1, tr("tab_diag"))
        self._tabs.setTabText(2, tr("tab_settings"))
        if self._diag.running():
            self._diag_step.setText(self._diag_hint())
        elif self._diag.result is not None:
            result = self._diag.result
            lines = [tr("diag_score", score=result.global_score)]
            lines.extend(f"{item.name}: {item.score}  {item.detail}" for item in result.scores)
            lines.extend(tr(item.key, **item.params) for item in result.recommendations)
            self._diag_out.setPlainText("\n".join(lines))
            self._diag_step.setText(tr("diag_done", score=result.global_score))
        else:
            self._diag_step.setText(tr("diag_idle"))
        if self._pump is None:
            self._status.setText(tr("no_pad"))
        self._refresh_drivers()
        if self._profile_name:
            self._profile_lbl.setText(tr("profile_named", name=self._profile_name))
        else:
            self._profile_lbl.setText(tr("profile_none"))

    def _diag_hint(self) -> str:
        if not self._diag.running() or self._diag.phase is None:
            return tr("diag_idle")
        key = {
            "rest": "diag_rest",
            "range": "diag_range",
            "triggers": "diag_triggers",
        }.get(self._diag.phase, "diag_idle")
        return tr(key, t=self._diag.remaining())

    def _ask_yes(self, title: str, body: str) -> bool:
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setText(body)
        box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        yes = box.button(QMessageBox.StandardButton.Yes)
        no = box.button(QMessageBox.StandardButton.No)
        if yes is not None:
            yes.setText(tr("yes"))
        if no is not None:
            no.setText(tr("no"))
        return box.exec() == QMessageBox.StandardButton.Yes

    def _toggle_virtual(self, checked: bool) -> None:
        if not checked:
            self._virtual.stop()
            self._unhide_physical()
            self._ignore_xinput.clear()
            self._virtual_btn.setText(tr("virtual_on"))
            self._status.setText(tr("virtual_stopped"))
            self._refresh_drivers()
            return
        if self._pump is None:
            self._virtual_btn.setChecked(False)
            self._status.setText(tr("select_pad"))
            return
        before = {dev.index for dev in enumerate_xinput() if dev.index is not None}
        try:
            self._virtual.start(self._current_state)
        except ViGEmMissingError as exc:
            self._virtual_btn.setChecked(False)
            self._status.setText(str(exc))
            self._offer_vigem_install()
            return
        except RuntimeError as exc:
            self._virtual_btn.setChecked(False)
            self._status.setText(str(exc))
            return
        after = {dev.index for dev in enumerate_xinput() if dev.index is not None}
        self._ignore_xinput = after - before
        hide_note = self._hide_physical(self._pump.identity)
        self._virtual_btn.setText(tr("virtual_off"))
        self._status.setText(tr("virtual_running", note=hide_note))
        self._refresh_drivers()

    def _offer_vigem_install(self) -> None:
        if not self._ask_yes("ViGEmBus", tr("vigem_body")):
            return
        self._status.setText(tr("dl_setup", name="ViGEmBus"))
        self._virtual_btn.setEnabled(False)
        self._dl = _InstallerDownload(self)
        self._dl.finished_ok.connect(self._run_vigem_setup)
        self._dl.finished_err.connect(self._vigem_download_failed)
        self._dl.start()

    def _run_vigem_setup(self, path) -> None:
        self._virtual_btn.setEnabled(True)
        try:
            launch_installer(path)
        except RuntimeError as exc:
            self._status.setText(str(exc))
            return
        self._status.setText(tr("finish_vigem"))
        self._refresh_drivers()

    def _vigem_download_failed(self, message: str) -> None:
        self._virtual_btn.setEnabled(True)
        self._status.setText(message)

    def _add_device(self, device: DeviceIdentity) -> None:
        if device.backend == "xinput" and device.index in self._ignore_xinput:
            return
        key = device_key(device)
        if key in self._devices:
            return
        self._devices[key] = device
        item = QListWidgetItem(f"{device.product_name}  [{device.backend}]")
        item.setData(Qt.ItemDataRole.UserRole, key)
        self._list.addItem(item)
        if ps3drv.needs_helper(device):
            QTimer.singleShot(400, self._maybe_offer_ps3_helper)

    def _remove_device(self, device: DeviceIdentity) -> None:
        key = device_key(device)
        self._devices.pop(key, None)
        for row in range(self._list.count()):
            item = self._list.item(row)
            if item and item.data(Qt.ItemDataRole.UserRole) == key:
                self._list.takeItem(row)
                break
        if self._pump and device_key(self._pump.identity) == key:
            self._stop_pump()
            self._status.setText(tr("disconnected"))

    def _on_pick(self, current: QListWidgetItem | None, _prev: QListWidgetItem | None) -> None:
        if current is None:
            self._stop_pump()
            return
        key = current.data(Qt.ItemDataRole.UserRole)
        device = self._devices.get(key)
        if device is None:
            return
        self._stop_pump()
        self._pump = DevicePump(device)
        self._pump.start()
        loaded = self._load_current_profile(device)
        extra = tr("profile_loaded") if loaded else ""
        self._status.setText(tr("live_pad", name=device.product_name, extra=extra))
        self._set_profile_label(device, loaded)
        if ps3drv.needs_helper(device):
            self._maybe_offer_ps3_helper()

    def _refresh_drivers(self) -> None:
        vigem = tr("driver_ok") if vigem_installed() else tr("driver_missing")
        hide = tr("driver_ok") if hidhide.is_installed() else tr("driver_missing")
        self._vigem_status.setText(f"ViGEmBus: {vigem}")
        self._hidhide_status.setText(f"HidHide: {hide}")
        if ps3drv.dshidmini_installed():
            self._ps3_status.setText(tr("ps3_ok", name="DsHidMini"))
        elif ps3drv.scp_installed():
            self._ps3_status.setText(tr("ps3_ok", name="ScpToolkit"))
        else:
            self._ps3_status.setText(tr("ps3_missing", name=ps3drv.package_name()))

    def _set_profile_label(self, device: DeviceIdentity, loaded: bool) -> None:
        if loaded:
            self._profile_name = f"{profile_key(device)}.json"
            self._profile_lbl.setText(tr("profile_named", name=self._profile_name))
        else:
            self._profile_name = None
            self._profile_lbl.setText(tr("profile_none"))

    def _slider(self, low: int, high: int, value: int) -> QSlider:
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(low, high)
        slider.setValue(value)
        return slider

    def _hide_physical(self, identity: DeviceIdentity) -> str:
        if not hidhide.is_installed():
            self._offer_hidhide_install()
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

    def _maybe_offer_ps3_helper(self) -> None:
        if self._ps3_offer_asked:
            return
        if not any(ps3drv.needs_helper(dev) for dev in self._devices.values()):
            return
        self._ps3_offer_asked = True
        self._offer_ps3_helper()

    def _offer_ps3_helper(self) -> None:
        name = ps3drv.package_name()
        detail = tr("ps3_dshidmini") if name == "DsHidMini" else tr("ps3_scp")
        if not self._ask_yes(name, detail):
            return
        self._status.setText(tr("dl_setup", name=name))
        self._ps3_dl = _Ps3DrvDownload(self)
        self._ps3_dl.finished_ok.connect(self._run_ps3_setup)
        self._ps3_dl.finished_err.connect(self._status.setText)
        self._ps3_dl.start()

    def _run_ps3_setup(self, path) -> None:
        name = ps3drv.package_name()
        try:
            ps3drv.launch_installer(path)
        except ps3drv.Ps3DriverError as exc:
            self._status.setText(str(exc))
            return
        self._status.setText(tr("finish_ps3", name=name))
        self._refresh_drivers()

    def _offer_hidhide_install(self) -> None:
        if not self._ask_yes("HidHide", tr("hidhide_body")):
            return
        self._status.setText(tr("dl_setup", name="HidHide"))
        self._hh_dl = _HidHideDownload(self)
        self._hh_dl.finished_ok.connect(self._run_hidhide_setup)
        self._hh_dl.finished_err.connect(self._status.setText)
        self._hh_dl.start()

    def _run_hidhide_setup(self, path) -> None:
        try:
            hidhide.launch_installer(path)
        except hidhide.HidHideError as exc:
            self._status.setText(str(exc))
            return
        self._status.setText(tr("finish_hidhide"))
        self._refresh_drivers()

    def _save_current_profile(self) -> None:
        if self._pump is None:
            return
        with self._cal_lock:
            cal = self._cal
        path = save_profile(self._pump.identity, cal, self._rules)
        self._status.setText(tr("saved", name=path.name))
        self._profile_name = path.name
        self._profile_lbl.setText(tr("profile_named", name=path.name))

    def _load_current_profile(self, device: DeviceIdentity) -> bool:
        loaded = load_profile(device)
        if loaded is None:
            return False
        cal, rules = loaded
        self._loading_profile = True
        with self._cal_lock:
            self._cal = cal
        self._ls_dz.setValue(int(round(cal.left.inner * 100)))
        self._rs_dz.setValue(int(round(cal.right.inner * 100)))
        self._curve.setValue(int(round(cal.left.curve * 100)))
        self._invert_ly.setChecked(cal.left.invert_y)
        self._invert_ry.setChecked(cal.right.invert_y)
        self._rules = list(rules)
        self._rule_list.clear()
        for rule in self._rules:
            self._rule_list.addItem(self._rule_label(rule))
        self._sync_remap()
        self._loading_profile = False
        return True

    def _sync_cal(self) -> None:
        with self._cal_lock:
            self._cal.left.inner = self._ls_dz.value() / 100.0
            self._cal.right.inner = self._rs_dz.value() / 100.0
            self._cal.left.curve = max(0.2, self._curve.value() / 100.0)
            self._cal.right.curve = self._cal.left.curve
            self._cal.left.invert_y = self._invert_ly.isChecked()
            self._cal.right.invert_y = self._invert_ry.isChecked()

    def _filtered(self, raw: NormalizedState | None) -> NormalizedState | None:
        if raw is None:
            return None
        with self._cal_lock:
            cal = self._cal
        calibrated = apply_calibration(raw, cal)
        with self._remap_lock:
            return self._remap.apply(calibrated)

    def _sync_remap(self) -> None:
        with self._remap_lock:
            self._remap = RemapEngine(RemapConfig(list(self._rules)))

    def _rule_label(self, rule: RemapRule) -> str:
        sources = "+".join(src.upper() for src in rule.sources)
        text = f"{sources} → {rule.dest.upper()}"
        if rule.toggle_hold:
            text += f"  (hold {rule.toggle_hold.upper()})"
        return text

    def _add_custom_rule(self) -> None:
        sources = tuple(
            item.data(Qt.ItemDataRole.UserRole)
            for item in self._src_list.selectedItems()
            if item.data(Qt.ItemDataRole.UserRole)
        )
        dest = self._dest.currentData()
        if not sources or not dest:
            self._status.setText(tr("select_remap"))
            return
        rule = RemapRule(sources, dest, self._hold.currentData())
        self._rules.append(rule)
        self._rule_list.addItem(self._rule_label(rule))
        self._sync_remap()
        self._save_current_profile()

    def _remove_custom_rule(self) -> None:
        row = self._rule_list.currentRow()
        if row < 0:
            return
        self._rule_list.takeItem(row)
        del self._rules[row]
        self._sync_remap()
        self._save_current_profile()

    def _recenter_sticks(self) -> None:
        raw = self._pump.latest() if self._pump else None
        if raw is None:
            return
        with self._cal_lock:
            self._cal.left.center_x = raw.lx
            self._cal.left.center_y = raw.ly
            self._cal.right.center_x = raw.rx
            self._cal.right.center_y = raw.ry
        self._status.setText(tr("centers"))
        self._save_current_profile()

    def _current_state(self) -> NormalizedState | None:
        if self._pump is None:
            return None
        return self._filtered(self._pump.latest())

    def _stop_pump(self) -> None:
        if self._pump is not None:
            self._pump.stop()
            self._pump = None

    def _start_diag(self) -> None:
        if self._pump is None:
            self._status.setText(tr("select_pad"))
            return
        self._diag.start()
        self._diag_result_shown = False
        self._diag_out.setPlainText(tr("diag_started"))
        hint = self._diag_hint()
        self._diag_step.setText(hint)
        self._status.setText(hint)

    def _apply_diag_recs(self) -> None:
        result = self._diag.result
        if result is None:
            self._status.setText(tr("run_diag_first"))
            return
        with self._cal_lock:
            for item in result.scores:
                if item.name == "LS" and item.deadzone_hint is not None:
                    self._cal.left.inner = item.deadzone_hint
                    if item.center_x is not None:
                        self._cal.left.center_x = item.center_x
                        self._cal.left.center_y = item.center_y or 0.0
                    self._ls_dz.blockSignals(True)
                    self._ls_dz.setValue(int(round(item.deadzone_hint * 100)))
                    self._ls_dz.blockSignals(False)
                if item.name == "RS" and item.deadzone_hint is not None:
                    self._cal.right.inner = item.deadzone_hint
                    if item.center_x is not None:
                        self._cal.right.center_x = item.center_x
                        self._cal.right.center_y = item.center_y or 0.0
                    self._rs_dz.blockSignals(True)
                    self._rs_dz.setValue(int(round(item.deadzone_hint * 100)))
                    self._rs_dz.blockSignals(False)
        self._status.setText(tr("applied_diag"))
        self._save_current_profile()

    def _tick(self) -> None:
        if self._pump is None:
            return
        raw = self._pump.latest()
        if raw is not None and self._diag.running():
            self._diag.feed(raw)
            hint = self._diag_hint()
            self._diag_step.setText(hint)
            self._status.setText(hint)
        elif self._diag.result is not None and not self._diag_result_shown:
            result = self._diag.result
            self._diag_result_shown = True
            lines = [tr("diag_score", score=result.global_score)]
            lines.extend(f"{item.name}: {item.score}  {item.detail}" for item in result.scores)
            lines.extend(tr(item.key, **item.params) for item in result.recommendations)
            self._diag_out.setPlainText("\n".join(lines))
            self._diag_step.setText(tr("diag_done", score=result.global_score))
            self._apply_diag_recs()
        if self._virtual.error():
            self._status.setText(tr("virtual_err", error=self._virtual.error()))
            self._virtual.stop()
            self._virtual_btn.setChecked(False)
            self._virtual_btn.setText(tr("virtual_on"))
            return
        if self._pump.error():
            self._status.setText(str(self._pump.error()))
            return
        if not self._pump.connected():
            self._status.setText(tr("disconnected"))
            return
        state = self._filtered(self._pump.latest())
        if state is None:
            return
        self._apply(state)

    def _apply(self, state: NormalizedState) -> None:
        self._ls.set_value(state.lx, state.ly)
        self._rs.set_value(state.rx, state.ry)
        self._lt.setValue(max(0, min(100, int(round(max(0.0, state.lt) * 100)))))
        self._rt.setValue(max(0, min(100, int(round(max(0.0, state.rt) * 100)))))
        self._pad.set_state(state)
