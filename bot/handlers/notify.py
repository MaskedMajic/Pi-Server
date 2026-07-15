"""Turns relay status frames into friendly DM text for the owner."""

# Maps event type -> (emoji, message template). {detail} filled if present.
STATUS_MESSAGES = {
    "event_received": ("📥", "PC received the alert."),
    "tab_opened": ("🌐", "Pokémon Center opened."),
    "page_loading": ("⏳", "Page is loading..."),
    "queue_detected": ("🚦", "Browser entered a QUEUE. Go take your spot."),
    "captcha_required": ("🧩", "CAPTCHA detected — needs you to solve it manually."),
    "product_page_reached": ("✅", "Product page reached. It's live!"),
    "access_denied": ("⛔", "Access denied by the site."),
    "timeout": ("⌛", "Page timed out."),
    "failed": ("❗", "Something failed while opening the page."),
    "extension_online": ("🟢", "Extension is online and armed."),
    "extension_offline": ("🔴", "Extension is OFFLINE — alerts won't open the browser."),
    "error": ("⚠️", "Relay error."),
}


def format_status(data: dict) -> str | None:
    etype = data.get("type")
    entry = STATUS_MESSAGES.get(etype)
    if not entry:
        return None
    emoji, text = entry
    detail = data.get("detail")
    product = data.get("url")
    line = f"{emoji} {text}"
    if detail:
        line += f"\n   {detail}"
    if product and etype in {"queue_detected", "product_page_reached", "captcha_required"}:
        line += f"\n   {product}"
    return line
