from __future__ import annotations

import threading
import time

from engine.device.catalog import enumerate_all, reader_for
from engine.device.hotplug import HotplugMonitor
from engine.state import DeviceIdentity, NormalizedState


class DevicePump:
    """Background read loop. latest() is safe to call from a UI thread."""

    def __init__(self, identity: DeviceIdentity):
        self.identity = identity
        self._lock = threading.Lock()
        self._state: NormalizedState | None = None
        self._error: BaseException | None = None
        self._connected = True
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="device-pump", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def latest(self) -> NormalizedState | None:
        with self._lock:
            return self._state

    def error(self) -> BaseException | None:
        with self._lock:
            return self._error

    def connected(self) -> bool:
        with self._lock:
            return self._connected

    def _run(self) -> None:
        try:
            reader = reader_for(self.identity)
            reader.open()
        except BaseException as exc:
            with self._lock:
                self._error = exc
                self._connected = False
            return
        try:
            while not self._stop.is_set():
                state = reader.read()
                if state is None:
                    if self.identity.backend == "xinput":
                        with self._lock:
                            self._connected = False
                        return
                    time.sleep(0.004)
                    continue
                with self._lock:
                    self._state = state
        except BaseException as exc:
            with self._lock:
                self._error = exc
                self._connected = False
        finally:
            try:
                reader.close()
            except Exception:
                pass


if __name__ == "__main__":
    monitor = HotplugMonitor(
        on_add=lambda dev: print(f"+ {dev.backend} {dev.product_name}", flush=True),
        on_remove=lambda dev: print(f"- {dev.backend} {dev.product_name}", flush=True),
    )
    monitor.start()
    devices = enumerate_all()
    if not devices:
        print("No pads. Plug one in; hotplug is watching (Ctrl+C to stop).")
        try:
            while True:
                time.sleep(0.25)
        except KeyboardInterrupt:
            monitor.stop()
        raise SystemExit(0)

    for i, identity in enumerate(devices):
        print(f"[{i}] {identity.backend} {identity.product_name}")
    chosen = devices[0]
    pump = DevicePump(chosen)
    pump.start()
    print(f"Pumping {chosen.product_name} on a background thread", flush=True)
    last = None
    try:
        while pump.connected():
            state = pump.latest()
            line = state.format_line() if state else None
            if line and line != last:
                print(line, flush=True)
                last = line
            time.sleep(0.008)
        if pump.error():
            print(pump.error())
        else:
            print("disconnected")
    except KeyboardInterrupt:
        pass
    finally:
        pump.stop()
        monitor.stop()
