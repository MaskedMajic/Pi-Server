"""
Maintains the bot's WebSocket connection to the relay.

- Authenticates with role="bot".
- Exposes send_restock(url, product_name).
- Runs a receive loop that hands status frames to an async callback.
- Auto-reconnects with backoff.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from typing import Awaitable, Callable, Optional

import websockets

log = logging.getLogger("bot.relay")

StatusCallback = Callable[[dict], Awaitable[None]]


class RelayClient:
    def __init__(self, url: str, token: str, on_status: StatusCallback):
        self.url = url
        self.token = token
        self.on_status = on_status
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._connected = asyncio.Event()

    async def _connect_once(self):
        self._ws = await websockets.connect(self.url, ping_interval=20)
        await self._ws.send(json.dumps({"token": self.token, "role": "bot"}))
        self._connected.set()
        log.info("Connected to relay at %s", self.url)

    async def run_forever(self):
        backoff = 1
        while True:
            try:
                await self._connect_once()
                backoff = 1
                async for raw in self._ws:
                    try:
                        data = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    await self.on_status(data)
            except Exception as e:  # noqa: BLE001
                log.warning("Relay connection lost: %s", e)
            finally:
                self._connected.clear()
                self._ws = None
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 30)

    async def send_restock(self, url: str, product_name: str) -> bool:
        if self._ws is None:
            log.warning("Cannot send restock: relay not connected")
            return False
        payload = {
            "type": "restock_detected",
            "event_id": uuid.uuid4().hex,
            "ts": time.time(),
            "url": url,
            "product_name": product_name,
        }
        await self._ws.send(json.dumps(payload))
        return True
