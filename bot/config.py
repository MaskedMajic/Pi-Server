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


def _id_set(name: str) -> set[int]:
    raw = os.environ.get(name, "")
    return {int(x) for x in raw.replace(" ", "").split(",") if x}


def _keyword_tuple(name: str, default: str) -> tuple[str, ...]:
    raw = os.environ.get(name, default)
    return tuple(part.strip().lower() for part in raw.split(",") if part.strip())


class Config:
    DISCORD_TOKEN = _require("DISCORD_TOKEN")
    WATCH_GUILD_ID = int(_require("WATCH_GUILD_ID"))
    WATCH_CHANNEL_ID = int(_require("WATCH_CHANNEL_ID"))
    OWNER_USER_ID = int(_require("OWNER_USER_ID"))
    APPROVED_AUTHOR_IDS = _id_set("APPROVED_AUTHOR_IDS")
    RELAY_WS_URL = os.environ.get("RELAY_WS_URL", "ws://127.0.0.1:8000/ws/bot")
    BOT_RELAY_TOKEN = _require("RELAY_BOT_TOKEN")
    PRODUCT_COOLDOWN_SECONDS = int(os.environ.get("PRODUCT_COOLDOWN_SECONDS", "90"))
    RESTOCK_KEYWORDS = _keyword_tuple(
        "RESTOCK_KEYWORDS",
        "restock,in stock,instock,live,drop,available,available now,back in stock,back up",
    )


config = Config()
