"""




Compatibility shim: ui.utils.thread_manager

Provides a minimal ThreadTracker compatible with historical code:
- ThreadTracker.get_instance()
- cleanup_all_threads()
Optionally allows thread registration.
"""
from __future__ import annotations

import threading
from typing import List, Optional

class ThreadTracker:
    _instance: Optional["ThreadTracker"] = None

    def __init__(self) -> None:
        self._threads: List[threading.Thread] = []

    @classmethod
    def get_instance(cls) -> "ThreadTracker":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, t: threading.Thread) -> None:
        try:
            if isinstance(t, threading.Thread) and t not in self._threads:
                self._threads.append(t)
        except Exception:
            pass

    def cleanup_all_threads(self, timeout: float = 1.0) -> None:
        """Join known threads with a timeout, ignoring current thread."""
        current = threading.current_thread()
        for t in list(self._threads):
            try:
                if t is not current and t.is_alive():
                    t.join(timeout=timeout)
            except Exception:
                pass
        # purge finished
        self._threads = [t for t in self._threads if t.is_alive()]

