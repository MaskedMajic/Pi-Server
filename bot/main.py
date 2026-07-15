"""
Discord bot entry point.

Watches one channel in one guild, only reacts to approved authors, extracts
Pokemon Center links, checks for restock keywords in message/embed text,
dedups via cooldown, forwards to the relay, and DMs the owner on detection
and on every status update the relay sends back.

Run:  python main.py
"""

from __future__ import annotations

import asyncio
import logging

import discord

from config import config
from handlers.cooldown import Cooldown
from handlers.notify import format_status
from handlers.relay_client import RelayClient
from handlers.urls import extract_pokecenter_url, guess_product_name, has_restock_keyword

# ---- logging to logs/bot.log and stdout ----
from pathlib import Path

log_dir = Path(__file__).resolve().parent.parent / "logs"
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [bot] %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "bot.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("bot")

cooldown = Cooldown(config.PRODUCT_COOLDOWN_SECONDS)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


async def dm_owner(text: str):
    try:
        user = await client.fetch_user(config.OWNER_USER_ID)
        await user.send(text)
    except Exception as e:  # noqa: BLE001
        log.error("Failed to DM owner: %s", e)


async def on_status(data: dict):
    """Called by RelayClient for every frame the relay sends the bot."""
    line = format_status(data)
    if line:
        await dm_owner(line)


relay = RelayClient(config.RELAY_WS_URL, config.BOT_RELAY_TOKEN, on_status)


def _is_approved_source(message: discord.Message) -> bool:
    if message.guild is None or message.guild.id != config.WATCH_GUILD_ID:
        return False
    if message.channel.id != config.WATCH_CHANNEL_ID:
        return False
    if message.author.id not in config.APPROVED_AUTHOR_IDS:
        return False
    return True


def _message_text(message: discord.Message) -> str:
    parts = [message.content or ""]
    for e in message.embeds:
        parts.append(e.title or "")
        parts.append(e.description or "")
        for field in getattr(e, "fields", []):
            parts.append(getattr(field, "name", "") or "")
            parts.append(getattr(field, "value", "") or "")
        if e.url:
            parts.append(e.url)
    return "\n".join(p for p in parts if p)


@client.event
async def on_ready():
    log.info("Discord connected as %s", client.user)
    log.info(
        "Watching guild=%s channel=%s approved=%s keywords=%s",
        config.WATCH_GUILD_ID,
        config.WATCH_CHANNEL_ID,
        sorted(config.APPROVED_AUTHOR_IDS),
        config.RESTOCK_KEYWORDS,
    )


@client.event
async def on_message(message: discord.Message):
    if message.author.id == (client.user.id if client.user else 0):
        return
    if not _is_approved_source(message):
        return

    text = _message_text(message)
    url = extract_pokecenter_url(text)
    if not url:
        return

    if not has_restock_keyword(text, config.RESTOCK_KEYWORDS):
        log.info("Ignored matching Pokemon Center link without restock keyword: %s", url)
        return

    if not cooldown.should_fire(url):
        log.info("Cooldown suppressed duplicate: %s", url)
        return

    product = guess_product_name(text, url)
    log.info("Restock detected: %s (%s)", url, product or "unnamed")

    await dm_owner(f"🔔 Restock detected!\n   {product or url}\n   {url}")

    sent = await relay.send_restock(url, product)
    if not sent:
        await dm_owner("⚠️ Relay not connected — couldn't forward to your PC.")


async def main():
    # Run the relay client alongside the discord client.
    asyncio.create_task(relay.run_forever())
    await client.start(config.DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
