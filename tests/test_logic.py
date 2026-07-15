"""
Dependency-free tests for the logic we CAN test without network/pydantic:
  - bot URL extraction + pokemoncenter validation
  - bot restock keyword detection
  - bot cooldown dedup
  - relay SeenCache dedup + TTL

Run: python3 tests/test_logic.py
"""

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bot"))
sys.path.insert(0, str(ROOT / "relay"))

# --- bot URL logic ---
from handlers.urls import extract_pokecenter_url, is_pokemoncenter, guess_product_name, has_restock_keyword

assert is_pokemoncenter("https://www.pokemoncenter.com/product/123")
assert is_pokemoncenter("https://pokemoncenter.com/x")
assert not is_pokemoncenter("https://evil-pokemoncenter.com.attacker.net/x")
assert not is_pokemoncenter("https://pokemoncenter.com.evil.com/x")
assert not is_pokemoncenter("https://amazon.com/pokemoncenter")

msg = "RESTOCK! Charizard UPC now live https://www.pokemoncenter.com/product/999 grab it"
url = extract_pokecenter_url(msg)
assert url == "https://www.pokemoncenter.com/product/999", url
assert "Charizard" in guess_product_name(msg, url)
assert has_restock_keyword(msg) is True
assert has_restock_keyword("Heads up, product page only https://www.pokemoncenter.com/product/999") is False
assert has_restock_keyword("BACK IN STOCK now") is True

# trailing punctuation stripped
assert extract_pokecenter_url("see (https://pokemoncenter.com/p/1).") == "https://pokemoncenter.com/p/1"

# non-PC links ignored
assert extract_pokecenter_url("https://twitter.com/foo https://target.com/bar") is None
print("bot URL logic: OK")

# --- bot cooldown ---
from handlers.cooldown import Cooldown

cd = Cooldown(seconds=2)
assert cd.should_fire("url-A") is True
assert cd.should_fire("url-A") is False   # within window
assert cd.should_fire("url-B") is True    # different key
time.sleep(2.1)
assert cd.should_fire("url-A") is True     # window elapsed
print("bot cooldown: OK")

# --- relay SeenCache ---
from app.seen_cache import SeenCache

sc = SeenCache(maxsize=3, ttl=1.0)
assert sc.seen("e1") is False
assert sc.seen("e1") is True              # duplicate
assert sc.seen("e2") is False
time.sleep(1.1)
assert sc.seen("e1") is False             # expired, treated as new
# eviction beyond maxsize
sc2 = SeenCache(maxsize=2, ttl=100)
sc2.seen("a"); sc2.seen("b"); sc2.seen("c")  # 'a' evicted
assert sc2.seen("a") is False             # 'a' was evicted so looks new
assert sc2.seen("c") is True              # 'c' still present
print("relay SeenCache: OK")

print("\nALL LOGIC TESTS PASSED")
