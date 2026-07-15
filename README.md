# Pi-Server

The Raspberry Pi half of a notify-only Pokémon Center restock watcher: a
Discord bot + relay that run 24/7 on the Pi, watch for restock pings, and
tell a Chrome extension on your PC when to open the page — without touching
the queue, CAPTCHA, cart, or checkout.

```
Discord restock ping
      │
      ▼
┌───────────┐   restock_detected    ┌───────────┐   restock_detected
│  bot/     │ ────────────────────► │  relay/   │ ─────────────────►  (Chrome extension,
│ (Discord) │                       │ (FastAPI) │                      runs on your PC —
│           │ ◄──────────────────── │           │ ◄─────────────────   separate repo)
└───────────┘   status events       └───────────┘   status events
      │
      ▼
   DMs you: detected / received / opened / queue / captcha / product / offline / error
```

## Components (both run on the Pi, 24/7, colocated)

- **bot/** — Discord bot. Watches one channel, reacts only to approved
  author IDs, extracts pokemoncenter.com links, dedups with a cooldown,
  forwards to the relay, and DMs you on detection and on every status update.
- **relay/** — FastAPI + WebSockets. Authenticates the bot and the extension
  with *separate* tokens, routes restock events one way and status events
  the other, tracks whether the extension is online, and rejects
  expired/duplicate/unauthorized events.

The Chrome extension that actually opens tabs lives in its own repo,
[PKC-Chrome](https://github.com/MaskedMajic/PKC-Chrome), and runs on each
user's own PC — it is **not** part of this repo, since it never runs on the
Pi.

## What this system will NOT do (by design)

- It does **not** solve or bypass CAPTCHAs — it only *detects and reports* them.
- It does **not** bypass or skip the queue — it *detects* the queue and hands you
  control.
- It does **not** add to cart or automate checkout.
- It does **not** refresh/hammer the site.

These aren't optional add-ons; they're the whole posture. The system is a fast
doorbell, not a bot.

## Setup

### 0. Config
```bash
cp config/.env.example config/.env
# edit config/.env — fill in the Discord token, IDs, and generate two random
# relay tokens (one for the bot, one for the extension).
```
Generate tokens with: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`

### 1. Relay (run first — the bot connects to it)
```bash
cd relay
pip install -r requirements.txt
python run.py
# health check: curl http://127.0.0.1:8000/health
```

### 2. Discord bot
Create the app + bot at https://discord.com/developers/applications, enable
**Message Content Intent**, invite it with "Read Messages/View Channels", then:
```bash
cd bot
pip install -r requirements.txt
python main.py
```

### 3. Chrome extension
Set up separately from [PKC-Chrome](https://github.com/MaskedMajic/PKC-Chrome),
on each user's own machine. Point it at the Pi's Tailscale IP/port and the
**extension** relay token.

## Testing without a real drop

- **Logic tests:** `python3 tests/test_logic.py` (URL validation, cooldown, dedup).
- **End-to-end dry run:** post a message containing a pokemoncenter.com product
  link in the watched channel from an approved author ID. Watch `logs/bot.log`
  and your DMs.

## Build phases (as implemented)

1. Bot detects & logs pokemoncenter.com links. ✓
2. FastAPI relay + event schemas. ✓
3. Auth, reconnect, dedup, cooldowns, logging, config, error handling. ✓

## Security notes

- The Discord token lives only in `config/.env`, loaded by the bot. It is
  **never** shipped to the extension.
- Bot and extension use different relay tokens, checked on the first WS frame.
- Event freshness (`EVENT_MAX_AGE_SECONDS`) + a seen-cache reject replays/dupes.
- URL host validation happens in **two** places here (bot, relay schema) —
  the extension repo validates independently too — so a bad link can't slip
  through one layer.
- `config/.env` and `logs/` are gitignored.
- The Discord token sits on the same Pi you may later expose more broadly
  (Tailscale Funnel, etc.) — worth keeping in mind.
