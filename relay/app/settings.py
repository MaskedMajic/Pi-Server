"""Relay configuration, loaded from environment variables."""

import os


def _require(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return val


class Settings:
    HOST: str = os.environ.get("RELAY_HOST", "0.0.0.0")
    PORT: int = int(os.environ.get("RELAY_PORT", "8000"))
    BOT_TOKEN: str = _require("RELAY_BOT_TOKEN")
    EXTENSION_TOKEN: str = _require("RELAY_EXTENSION_TOKEN")
    EVENT_MAX_AGE_SECONDS: int = int(os.environ.get("EVENT_MAX_AGE_SECONDS", "30"))


settings = Settings()
