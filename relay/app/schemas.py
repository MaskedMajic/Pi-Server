"""
Event schemas for the relay.

Two directions of traffic:
  bot  -> relay -> extension : RestockEvent
  extension -> relay -> bot  : StatusEvent

Every event carries a monotonic-ish `ts` (unix seconds) and an `event_id`
(uuid) so the relay can reject replays and duplicates.
"""

from __future__ import annotations

import time
import uuid
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


ALLOWED_HOST_SUFFIX = "pokemoncenter.com"

RESTOCK = "restock_detected"

STATUS_EVENTS = {
    "event_received",
    "tab_opened",
    "page_loading",
    "queue_detected",
    "captcha_required",
    "product_page_reached",
    "access_denied",
    "timeout",
    "failed",
}


def now() -> float:
    return time.time()


def new_id() -> str:
    return uuid.uuid4().hex


class RestockEvent(BaseModel):
    """Bot -> extension. A validated Pokemon Center restock."""

    type: Literal["restock_detected"] = RESTOCK
    event_id: str = Field(default_factory=new_id)
    ts: float = Field(default_factory=now)
    url: str
    product_name: str = ""

    @field_validator("url")
    @classmethod
    def _must_be_pokemoncenter(cls, v: str) -> str:
        from urllib.parse import urlparse

        host = (urlparse(v).hostname or "").lower()
        if not (host == ALLOWED_HOST_SUFFIX or host.endswith("." + ALLOWED_HOST_SUFFIX)):
            raise ValueError(f"URL host not allowed: {host!r}")
        return v


class StatusEvent(BaseModel):
    """Extension -> bot. A browser-state report tied to a restock event_id."""

    type: str
    event_id: str
    ts: float = Field(default_factory=now)
    url: Optional[str] = None
    detail: str = ""

    @field_validator("type")
    @classmethod
    def _known_status(cls, v: str) -> str:
        if v not in STATUS_EVENTS:
            raise ValueError(f"Unknown status event: {v!r}")
        return v


class AuthMessage(BaseModel):
    """First frame a client sends after connecting."""

    token: str
    role: Literal["bot", "extension"]
