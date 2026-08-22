from __future__ import annotations

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
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from engine.diagnose import DiagnoseRunner
from engine.pipeline import Calibration, apply_calibration
from engine.remap import BUTTONS, RemapConfig, RemapEngine, RemapRule
from engine.device.catalog import device_key, enumerate_all
from engine.device.hotplug import HotplugMonitor
from engine.device.pump import DevicePump
from engine.device.xinput import enumerate_devices as enumerate_xinput
from engine.state import DeviceIdentity, NormalizedState
from engine.vigem import ViGEmMissingError, download_installer, launch_installer
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
        self.resize(860, 520)
        self._pump: DevicePump | None = None
        self._virtual = VirtualXbox()
        self._ignore_xinput: set[int] = set()
        self._devices: dict[str, DeviceIdentity] = {}

        self._list = QListWidget()
        self._list.currentItemChanged.connect(self._on_pick)
        self._cal = Calibration.default()
        self._cal_lock = threading.Lock()
        self._diag = DiagnoseRunner()
        self._remap = RemapEngine()
        self._remap_lock = threading.Lock()
        self._ls = StickView("Left stick (filtered)")
        self._rs = StickView("Right stick (filtered)")
        self._lt = QProgressBar()
        self._rt = QProgressBar()
        for bar in (self._lt, self._rt):
            bar.setRange(0, 100)
            bar.setTextVisible(True)
        self._pad = ButtonPad()
        self._virtual_btn = QPushButton("Activar mando virtual")
        self._virtual_btn.setCheckable(True)
        self._virtual_btn.clicked.connect(self._toggle_virtual)
        self._status = QLabel("No pad selected")
        self._ls_dz = self._slider(0, 40, 10)
        self._rs_dz = self._slider(0, 40, 10)
        self._curve = self._slider(20, 200, 100)
        self._invert_ly = QCheckBox("Invert LY")
        self._invert_ry = QCheckBox("Invert RY")
        self._recenter = QPushButton("Recenter sticks")
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
        self._hold.addItem("No hold toggle", None)
        for key in BUTTONS:
            label = key.upper().replace("_", " ")
            self._src_list.addItem(label)
            self._src_list.item(self._src_list.count() - 1).setData(
                Qt.ItemDataRole.UserRole, key
            )
            self._dest.addItem(label, key)
            self._hold.addItem(f"Hold {label} toggles", key)
        self._rule_list = QListWidget()
        self._add_rule = QPushButton("Add remap")
        self._del_rule = QPushButton("Remove remap")
        self._diag_btn = QPushButton("Run diagnosis")
        self._apply_diag = QPushButton("Apply recommendations")
        self._diag_out = QPlainTextEdit()
        self._diag_out.setReadOnly(True)
        self._diag_out.setMaximumHeight(120)
        self._diag_btn.clicked.connect(self._start_diag)
        self._apply_diag.clicked.connect(self._apply_diag_recs)
        self._add_rule.clicked.connect(self._add_custom_rule)
        self._del_rule.clicked.connect(self._remove_custom_rule)

        sticks = QHBoxLayout()
        sticks.addWidget(self._ls)
        sticks.addWidget(self._rs)
        triggers = QVBoxLayout()
        triggers.addWidget(QLabel("LT"))
        triggers.addWidget(self._lt)
        triggers.addWidget(QLabel("RT"))
        triggers.addWidget(self._rt)
        triggers.addWidget(QLabel("Buttons"))
        triggers.addWidget(self._pad)
        right_host = QWidget()
        right = QVBoxLayout(right_host)
        right.addLayout(sticks)
        right.addLayout(triggers)
        right.addWidget(QLabel("LS deadzone %"))
        right.addWidget(self._ls_dz)
        right.addWidget(QLabel("RS deadzone %"))
        right.addWidget(self._rs_dz)
        right.addWidget(QLabel("Stick curve (100 = linear)"))
        right.addWidget(self._curve)
        right.addWidget(self._invert_ly)
        right.addWidget(self._invert_ry)
        right.addWidget(self._recenter)
        right.addWidget(self._diag_btn)
        right.addWidget(self._apply_diag)
        right.addWidget(self._diag_out)
        right.addWidget(QLabel("Remap sources (multi-select)"))
        right.addWidget(self._src_list)
        right.addWidget(QLabel("Destination"))
        right.addWidget(self._dest)
        right.addWidget(self._hold)
        right.addWidget(self._add_rule)
        right.addWidget(self._rule_list)
        right.addWidget(self._del_rule)
        right.addWidget(self._virtual_btn)
        right.addWidget(self._status)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(right_host)
        root = QHBoxLayout(self)
        root.addWidget(self._list, 1)
        root.addWidget(scroll, 2)

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

        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def closeEvent(self, event) -> None:
        self._timer.stop()
        self._virtual.stop()
        self._stop_pump()
        self._monitor.stop()
        super().closeEvent(event)

    def _toggle_virtual(self, checked: bool) -> None:
        if not checked:
            self._virtual.stop()
            self._ignore_xinput.clear()
            self._virtual_btn.setText("Activar mando virtual")
            self._status.setText("Virtual pad stopped")
            return
        if self._pump is None:
            self._virtual_btn.setChecked(False)
            self._status.setText("Select a pad first")
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
        self._virtual_btn.setText("Parar mando virtual")
        self._status.setText("Virtual Xbox 360 running (games will see two pads)")

    def _offer_vigem_install(self) -> None:
        answer = QMessageBox.question(
            self,
            "ViGEmBus",
            "ViGEmBus is required for the virtual pad.\n"
            "Download the official setup from Nefarius and install it?\n"
            "Windows will ask for administrator permission.",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self._status.setText("Downloading official ViGEmBus setup...")
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
        self._status.setText("Finish the ViGEmBus installer, then activate the virtual pad again.")

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
            self._status.setText("Disconnected")

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
        self._status.setText(f"Live: {device.product_name}")

    def _slider(self, low: int, high: int, value: int) -> QSlider:
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(low, high)
        slider.setValue(value)
        return slider

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
            self._status.setText("Select at least one source and a destination")
            return
        rule = RemapRule(sources, dest, self._hold.currentData())
        self._rules.append(rule)
        self._rule_list.addItem(self._rule_label(rule))
        self._sync_remap()

    def _remove_custom_rule(self) -> None:
        row = self._rule_list.currentRow()
        if row < 0:
            return
        self._rule_list.takeItem(row)
        del self._rules[row]
        self._sync_remap()

    def _recenter_sticks(self) -> None:
        raw = self._pump.latest() if self._pump else None
        if raw is None:
            return
        with self._cal_lock:
            self._cal.left.center_x = raw.lx
            self._cal.left.center_y = raw.ly
            self._cal.right.center_x = raw.rx
            self._cal.right.center_y = raw.ry
        self._status.setText("Stick centers captured")

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
            self._status.setText("Select a pad first")
            return
        self._diag.start()
        self._diag_out.setPlainText("Diagnosis started...")
        self._status.setText(self._diag.instruction())

    def _apply_diag_recs(self) -> None:
        result = self._diag.result
        if result is None:
            self._status.setText("Run diagnosis first")
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
        self._status.setText("Applied diagnosis recommendations")

    def _tick(self) -> None:
        if self._pump is None:
            return
        raw = self._pump.latest()
        if raw is not None and self._diag.running():
            self._diag.feed(raw)
            self._status.setText(self._diag.instruction())
        elif self._diag.result is not None and self._diag_out.toPlainText().startswith("Diagnosis"):
            result = self._diag.result
            lines = [f"Score {result.global_score}/100"]
            lines.extend(f"{item.name}: {item.score}  {item.detail}" for item in result.scores)
            lines.extend(result.recommendations)
            self._diag_out.setPlainText("\n".join(lines))
        if self._virtual.error():
            self._status.setText(f"Virtual pad: {self._virtual.error()}")
            self._virtual.stop()
            self._virtual_btn.setChecked(False)
            self._virtual_btn.setText("Activar mando virtual")
            return
        if self._pump.error():
            self._status.setText(str(self._pump.error()))
            return
        if not self._pump.connected():
            self._status.setText("Disconnected")
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
