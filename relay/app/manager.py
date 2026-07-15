"""
Tracks the single bot connection and single extension connection, plus a
short-term memory of seen event_ids for replay/dup rejection.
"""

from __future__ import annotations

import asyncio
from typing import Optional

from fastapi import WebSocket

from .seen_cache import SeenCache


class ConnectionManager:
    def __init__(self):
        self.bot: Optional[WebSocket] = None
        self.extension: Optional[WebSocket] = None
        self.seen = SeenCache()
        self._lock = asyncio.Lock()

    @property
    def extension_online(self) -> bool:
        return self.extension is not None

    async def set_bot(self, ws: Optional[WebSocket]):
        async with self._lock:
            self.bot = ws

    async def set_extension(self, ws: Optional[WebSocket]):
        async with self._lock:
            self.extension = ws

    async def to_extension(self, payload: dict) -> bool:
        if self.extension is None:
            return False
        await self.extension.send_json(payload)
        return True

    async def to_bot(self, payload: dict) -> bool:
        if self.bot is None:
            return False
        await self.bot.send_json(payload)
        return True


manager = ConnectionManager()
