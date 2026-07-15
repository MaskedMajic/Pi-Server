"""Bot configuration, loaded from environment variables."""

import os
from pathlib import Path


def _load_env_file():
    env_path = Path(__file__).resolve().parent.parent / "config" / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


_load_env_file()


def _require(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return val


class Config:
    DISCORD_TOKEN = _require("DISCORD_TOKEN")
    WATCH_GUILD_ID = int(_require("WATCH_GUILD_ID"))
    WATCH_CHANNEL_ID = int(_require("WATCH_CHANNEL_ID"))
    OWNER_USER_ID = int(_require("OWNER_USER_ID"))
    RELAY_WS_URL = os.environ.get("RELAY_WS_URL", "ws://127.0.0.1:8000/ws/bot")
    BOT_RELAY_TOKEN = _require("RELAY_BOT_TOKEN")
    PRODUCT_COOLDOWN_SECONDS = int(os.environ.get("PRODUCT_COOLDOWN_SECONDS", "90"))


config = Config()
