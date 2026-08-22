from __future__ import annotations

import threading
import time
from collections.abc import Callable

from engine.device.catalog import device_key, enumerate_all
from engine.state import DeviceIdentity

OnChange = Callable[[DeviceIdentity], None]


class HotplugMonitor:
    """Polls enumerate_all() so a UI thread never has to scan HID itself."""

    def __init__(
        self,
        interval: float = 0.5,
        on_add: OnChange | None = None,
        on_remove: OnChange | None = None,
    ):
        self.interval = interval
        self.on_add = on_add
        self.on_remove = on_remove
        self._known: dict[str, DeviceIdentity] = {}
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def snapshot(self) -> list[DeviceIdentity]:
        with self._lock:
            return list(self._known.values())

    def poll(self) -> None:
        current = {device_key(dev): dev for dev in enumerate_all()}
        with self._lock:
            added = [dev for key, dev in current.items() if key not in self._known]
            removed = [dev for key, dev in self._known.items() if key not in current]
            self._known = current
        for dev in removed:
            if self.on_remove:
                self.on_remove(dev)
        for dev in added:
            if self.on_add:
                self.on_add(dev)

    def start(self) -> None:
        if self._thread is not None:
            return
        self.poll()
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="hotplug", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def _run(self) -> None:
        while not self._stop.wait(self.interval):
            self.poll()


if __name__ == "__main__":
    def _added(dev: DeviceIdentity) -> None:
        print(f"+ {dev.backend} {dev.product_name}", flush=True)

    def _removed(dev: DeviceIdentity) -> None:
        print(f"- {dev.backend} {dev.product_name}", flush=True)

    monitor = HotplugMonitor(on_add=_added, on_remove=_removed)
    monitor.start()
    print("Watching connect/disconnect (Ctrl+C to stop)", flush=True)
    try:
        while True:
            time.sleep(0.25)
    except KeyboardInterrupt:
        monitor.stop()
