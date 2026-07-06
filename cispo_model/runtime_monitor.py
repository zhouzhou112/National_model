"""Low-overhead process-memory monitoring for long model builds and solves."""
from __future__ import annotations

import threading
from time import monotonic

import psutil


class PeakMemoryMonitor:
    """Sample RSS of the current process and its children in a daemon thread."""

    def __init__(self, interval_seconds: float = 0.5) -> None:
        self.interval_seconds = interval_seconds
        self.process = psutil.Process()
        self.started_at = monotonic()
        self.peak_rss_bytes = 0
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _sample(self) -> None:
        processes = [self.process]
        try:
            processes.extend(self.process.children(recursive=True))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        rss = 0
        for process in processes:
            try:
                rss += process.memory_info().rss
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        self.peak_rss_bytes = max(self.peak_rss_bytes, rss)

    def _run(self) -> None:
        while not self._stop.wait(self.interval_seconds):
            self._sample()

    def start(self) -> "PeakMemoryMonitor":
        self._sample()
        self._thread.start()
        return self

    def snapshot(self) -> dict[str, float | int]:
        self._sample()
        return {
            "peak_process_tree_rss_bytes": int(self.peak_rss_bytes),
            "peak_process_tree_rss_gib": round(self.peak_rss_bytes / 1024**3, 3),
            "elapsed_seconds": round(monotonic() - self.started_at, 3),
            "sampling_interval_seconds": self.interval_seconds,
        }

    def stop(self) -> dict[str, float | int]:
        self._stop.set()
        self._thread.join(timeout=max(2.0, self.interval_seconds * 4))
        return self.snapshot()
