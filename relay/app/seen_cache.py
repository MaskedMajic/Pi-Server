"""Dependency-free dedup cache. Imported by manager.py and testable alone."""

from __future__ import annotations

import time
from collections import OrderedDict


class SeenCache:
    """Fixed-size set of event keys with TTL, for replay/duplicate rejection."""

    def __init__(self, maxsize: int = 512, ttl: float = 300.0):
        self.maxsize = maxsize
        self.ttl = ttl
        self._d: "OrderedDict[str, float]" = OrderedDict()

    def seen(self, key: str) -> bool:
        now = time.time()
        expired = [k for k, t in self._d.items() if now - t > self.ttl]
        for k in expired:
            self._d.pop(k, None)
        if key in self._d:
            return True
        self._d[key] = now
        self._d.move_to_end(key)
        while len(self._d) > self.maxsize:
            self._d.popitem(last=False)
        return False
