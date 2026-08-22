from __future__ import annotations

from PySide6.QtCore import QObject, QPointF, QTimer, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from engine.device.catalog import device_key, enumerate_all
from engine.device.hotplug import HotplugMonitor
from engine.device.pump import DevicePump
from engine.device.xinput import enumerate_devices as enumerate_xinput
from engine.state import DeviceIdentity, NormalizedState
from engine.virtual import VirtualXbox


class _Bridge(QObject):
    added = Signal(object)
    removed = Signal(object)


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
        self._ls = StickView("Left stick")
        self._rs = StickView("Right stick")
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
        right = QVBoxLayout()
        right.addLayout(sticks)
        right.addLayout(triggers)
        right.addWidget(self._virtual_btn)
        right.addWidget(self._status)

        root = QHBoxLayout(self)
        root.addWidget(self._list, 1)
        root.addLayout(right, 2)

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
        except RuntimeError as exc:
            self._virtual_btn.setChecked(False)
            self._status.setText(str(exc))
            return
        after = {dev.index for dev in enumerate_xinput() if dev.index is not None}
        self._ignore_xinput = after - before
        self._virtual_btn.setText("Parar mando virtual")
        self._status.setText("Virtual Xbox 360 running (games will see two pads)")

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

    def _current_state(self) -> NormalizedState | None:
        if self._pump is None:
            return None
        return self._pump.latest()

    def _stop_pump(self) -> None:
        if self._pump is not None:
            self._pump.stop()
            self._pump = None

    def _tick(self) -> None:
        if self._pump is None:
            return
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
        state = self._pump.latest()
        if state is None:
            return
        self._apply(state)

    def _apply(self, state: NormalizedState) -> None:
        self._ls.set_value(state.lx, state.ly)
        self._rs.set_value(state.rx, state.ry)
        self._lt.setValue(max(0, min(100, int(round(max(0.0, state.lt) * 100)))))
        self._rt.setValue(max(0, min(100, int(round(max(0.0, state.rt) * 100)))))
        self._pad.set_state(state)
