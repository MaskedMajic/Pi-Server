"""
Relay server.

Endpoints:
  GET /health           - liveness + whether extension is online
  WS  /ws/bot           - the Discord bot connects here
  WS  /ws/extension     - the Chrome extension connects here

Auth: first frame after connect must be {"token": "...", "role": "..."}.
Wrong token or role -> close 4401.

Routing:
  bot frame (RestockEvent)      -> validate, dedup, replay-check -> extension
                                   also echo EXTENSION_OFFLINE back to bot if
                                   no extension is connected.
  extension frame (StatusEvent) -> validate, dedup -> bot
"""

from __future__ import annotations

import logging
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from .manager import manager
from .schemas import AuthMessage, RestockEvent, StatusEvent
from .settings import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [relay] %(levelname)s %(message)s",
)
log = logging.getLogger("relay")

app = FastAPI(title="PokeCenter Relay")


@app.get("/health")
async def health():
    return {"ok": True, "extension_online": manager.extension_online}


async def _authenticate(ws: WebSocket, expected_role: str, expected_token: str) -> bool:
    await ws.accept()
    try:
        raw = await ws.receive_json()
        auth = AuthMessage(**raw)
    except (ValidationError, Exception):
        await ws.close(code=4400)
        return False
    if auth.role != expected_role or auth.token != expected_token:
        log.warning("Auth failed for role=%s", expected_role)
        await ws.close(code=4401)
        return False
    return True


def _fresh(ts: float) -> bool:
    return (time.time() - ts) <= settings.EVENT_MAX_AGE_SECONDS


@app.websocket("/ws/bot")
async def ws_bot(ws: WebSocket):
    if not await _authenticate(ws, "bot", settings.BOT_TOKEN):
        return
    await manager.set_bot(ws)
    log.info("Bot connected")
    # Tell the bot the current extension state on connect.
    await manager.to_bot(
        {"type": "extension_online" if manager.extension_online else "extension_offline"}
    )
    try:
        while True:
            raw = await ws.receive_json()
            try:
                event = RestockEvent(**raw)
            except ValidationError as e:
                await manager.to_bot({"type": "error", "detail": f"bad restock event: {e}"})
                continue
            if not _fresh(event.ts):
                await manager.to_bot(
                    {"type": "error", "event_id": event.event_id, "detail": "stale event"}
                )
                continue
            if manager.seen.seen(event.event_id):
                continue  # duplicate, silently drop
            delivered = await manager.to_extension(event.model_dump())
            if not delivered:
                await manager.to_bot({"type": "extension_offline", "event_id": event.event_id})
            else:
                log.info("Restock -> extension: %s", event.url)
    except WebSocketDisconnect:
        log.info("Bot disconnected")
    finally:
        await manager.set_bot(None)


@app.websocket("/ws/extension")
async def ws_extension(ws: WebSocket):
    if not await _authenticate(ws, "extension", settings.EXTENSION_TOKEN):
        return
    await manager.set_extension(ws)
    log.info("Extension connected")
    # Notify the bot that the extension just came online.
    await manager.to_bot({"type": "extension_online"})
    try:
        while True:
            raw = await ws.receive_json()
            try:
                event = StatusEvent(**raw)
            except ValidationError as e:
                log.warning("Bad status event: %s", e)
                continue
            if manager.seen.seen(event.event_id + ":" + event.type):
                continue
            await manager.to_bot(event.model_dump())
            log.info("Status -> bot: %s (%s)", event.type, event.event_id[:8])
    except WebSocketDisconnect:
        log.info("Extension disconnected")
    finally:
        await manager.set_extension(None)
        # Let the bot know the extension went offline.
        await manager.to_bot({"type": "extension_offline"})
