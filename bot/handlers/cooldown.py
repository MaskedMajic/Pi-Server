"""Short-term cooldown so the same product doesn't fire repeatedly."""

import time


class Cooldown:
    def __init__(self, seconds: int):
        self.seconds = seconds
        self._last: dict[str, float] = {}

    def should_fire(self, key: str) -> bool:
        """True if this key hasn't fired within the cooldown window."""
        now = time.time()
        last = self._last.get(key)
        # purge old entries occasionally
        if len(self._last) > 256:
            self._last = {k: t for k, t in self._last.items() if now - t < self.seconds}
        if last is not None and (now - last) < self.seconds:
            return False
        self._last[key] = now
        return True
