"""Extract and validate Pokemon Center URLs from Discord message text."""

import re
from urllib.parse import urlparse

ALLOWED_HOST_SUFFIX = "pokemoncenter.com"
DEFAULT_RESTOCK_KEYWORDS = (
    "restock",
    "in stock",
    "instock",
    "live",
    "drop",
    "available",
    "available now",
    "back in stock",
    "back up",
)

_URL_RE = re.compile(r"https?://[^\s<>()\[\]]+", re.IGNORECASE)


def is_pokemoncenter(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return host == ALLOWED_HOST_SUFFIX or host.endswith("." + ALLOWED_HOST_SUFFIX)


def extract_pokecenter_url(text: str) -> str | None:
    """Return the first pokemoncenter.com URL found in text, or None."""
    for match in _URL_RE.finditer(text or ""):
        candidate = match.group(0).rstrip(".,);]")
        if is_pokemoncenter(candidate):
            return candidate
    return None


def has_restock_keyword(text: str, keywords: tuple[str, ...] = DEFAULT_RESTOCK_KEYWORDS) -> bool:
    """Return True when the message/embed text contains a restock signal keyword."""
    haystack = (text or "").lower()
    return any(keyword.lower() in haystack for keyword in keywords)


def guess_product_name(text: str, url: str) -> str:
    """
    Best-effort product name: strip the URL out and take the longest
    remaining line, capped. Purely cosmetic for the DM.
    """
    if not text:
        return ""
    cleaned = text.replace(url, " ")
    lines = [ln.strip(" -*|>") for ln in re.split(r"[\n\r]", cleaned)]
    lines = [ln for ln in lines if ln]
    if not lines:
        return ""
    best = max(lines, key=len)
    return best[:120]
