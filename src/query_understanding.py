"""Turn a question into retrieval filters: a price range and product categories.

Rule-based on purpose (simple to explain, no extra LLM call). Category names are the
controlled labels used by the index (see docs/phase2_build_log.md section 8).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# category -> phrases that signal it (matched as whole words / phrases)
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Chargers & Adapters": ["charger", "chargers", "adapter", "adapters", "adaptor", "adaptors"],
    "Headphones & Earphones": ["headphone", "headphones", "earphone", "earphones", "earbuds", "earbud",
                               "neckband", "headset", "headsets"],
    "Home Theater": ["home theater", "home theatre", "home theaters", "home theatres"],
    "Keyboards": ["keyboard", "keyboards"],
    "Laptops": ["laptop", "laptops", "notebook", "notebooks", "macbook", "chromebook"],
    "Mice": ["mouse", "mice"],
    "Power Banks": ["power bank", "power banks", "powerbank", "powerbanks"],
    "Routers & Networking": ["router", "routers", "wifi", "wi-fi", "modem", "modems", "range extender",
                             "networking", "dongle"],
    "Speakers": ["speaker", "speakers", "soundbar"],
    "USB Storage": ["pendrive", "pendrives", "pen drive", "pen drives", "flash drive", "usb drive",
                    "usb storage", "thumb drive"],
}

_UNITS = {"k": 1_000, "thousand": 1_000, "lakh": 100_000, "lac": 100_000}
# An amount like "50,000", "Rs 2000", "₹1.5k". Not followed by a spec unit (16GB, 5000 mAh, 10 hours ...).
_AMOUNT = (r"(?:rs\.?|inr|₹)?\s*(\d[\d,]*(?:\.\d+)?)\s*(k|thousand|lakh|lac)?\b"
           r"(?!\s*(?:gb|tb|mb|mah|w|watt|watts|hours?|hrs?|mm|inch|inches|%|x|mp))")
_MAX_WORDS = r"(?:under|below|less than|lesser than|within|upto|up to|budget of|budget is|budget|max(?:imum)?|not more than|cheaper than)"
_MIN_WORDS = r"(?:above|over|more than|at least|minimum|min|costlier than|starting from)"


@dataclass(frozen=True)
class Constraints:
    max_price: float | None = None
    min_price: float | None = None
    categories: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"max_price": self.max_price, "min_price": self.min_price, "categories": list(self.categories)}

    @property
    def has_price_limit(self) -> bool:
        return self.max_price is not None or self.min_price is not None


def _amount(number: str, unit: str | None) -> float:
    return float(number.replace(",", "")) * _UNITS.get((unit or "").lower(), 1)


def extract_budget(text: str) -> tuple[float | None, float | None]:
    """Return (min_price, max_price). Handles 'under 50,000', 'below Rs 2000', 'under 2k', 'between 1k and 3k'."""
    q = text.lower()
    between = re.search(r"between\s*" + _AMOUNT + r"\s*(?:and|to|-)\s*" + _AMOUNT, q)
    if between:
        lo = _amount(between.group(1), between.group(2))
        hi = _amount(between.group(3), between.group(4))
        return (min(lo, hi), max(lo, hi))
    max_price = min_price = None
    m = re.search(_MAX_WORDS + r"\s*(?:of\s*)?" + _AMOUNT, q)
    if m:
        max_price = _amount(m.group(1), m.group(2))
    else:  # "5000 or less", "2k or below"
        m = re.search(_AMOUNT + r"\s*(?:or less|or below|or under|and below)", q)
        if m:
            max_price = _amount(m.group(1), m.group(2))
    m = re.search(_MIN_WORDS + r"\s*" + _AMOUNT, q)
    if m:
        min_price = _amount(m.group(1), m.group(2))
    return min_price, max_price


def extract_categories(text: str) -> list[str]:
    q = " " + re.sub(r"[^a-z0-9\- ]+", " ", text.lower()) + " "
    return [category for category, words in CATEGORY_KEYWORDS.items() if any(f" {w} " in q for w in words)]


def understand(question: str) -> Constraints:
    lo, hi = extract_budget(question)
    return Constraints(max_price=hi, min_price=lo, categories=extract_categories(question))


_COMPARE_LEAD = re.compile(
    r"\b(?:compare|comparison\s+of|comparing|difference(?:s)?\s+between|diff\s+between)\s+(.+)$", re.I)
_SEPARATOR = re.compile(r"\s+(?:vs\.?|versus|and|with|or|to)\s+", re.I)
_VS = re.compile(r"\s+(?:vs\.?|versus)\s+", re.I)
_TAIL = re.compile(r"\s+(?:in terms of|based on|for|on|regarding|which|what)\b.*$|[,;?.!]+.*$", re.I)
_BUDGET_TAIL = re.compile(r"\b(?:" + _MAX_WORDS[3:-1] + "|" + _MIN_WORDS[3:-1] + r")\b.*$", re.I)
_GENERIC_PHRASES = sorted(
    {tuple(w.split()) for words in CATEGORY_KEYWORDS.values() for w in words} | {(w,) for w in ("model", "models", "product", "products", "one")},
    key=len, reverse=True)


def _clean_target(text: str) -> str:
    text = _BUDGET_TAIL.sub("", _TAIL.sub("", text)).strip()
    text = re.sub(r"^(?:the|a|an)\s+", "", text, flags=re.I)
    words = text.split()
    changed = True
    while words and changed:  # "iBall 150M router" -> "iBall 150M"; "mw5b power bank" -> "mw5b"
        changed = False
        for phrase in _GENERIC_PHRASES:
            n = len(phrase)
            if len(words) > n and [w.lower().strip("-") for w in words[-n:]] == list(phrase):
                del words[-n:]
                changed = True
                break
    return " ".join(words)


def extract_comparison_targets(question: str) -> list[str]:
    """Product names a customer wants compared, e.g. 'Compare the A and the B' -> ['A', 'B']; [] otherwise."""
    q = question.strip()
    m = _COMPARE_LEAD.search(q)
    if m:
        parts = _SEPARATOR.split(m.group(1))
    elif _VS.search(q):
        parts = _VS.split(q)
    else:
        return []
    targets = [_clean_target(p) for p in parts]
    targets = [t for t in targets if t]
    return targets[:3] if len(targets) >= 2 else []
