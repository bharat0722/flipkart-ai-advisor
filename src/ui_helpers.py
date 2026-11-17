"""Display helpers for the Streamlit app, kept free of Streamlit so they can be unit tested.

The pipeline cites products as ``[product_id]``. The app numbers the sources in rank
order and shows ``[1]``, ``[2]`` ... in the answer, matching the numbered source cards.
"""

from __future__ import annotations

import html
import re

from src.query_understanding import is_follow_up
from src.retrieval import RetrievedChunk

_CITATION = re.compile(r"\[([A-Za-z0-9_\-]+)\]")
_NON_WORD = re.compile(r"[^\w\s]")

# Short, user-facing explanations for each RagResult.reason.
REASON_LABELS = {
    "answered": "Grounded answer from catalogue records",
    "no_support": "The catalogue evidence does not support an answer",
    "no_evidence": "No matching products in the catalogue",
    "weak_evidence": "Nothing in the catalogue is close enough to this question",
    "no_budget_match": "No products with a known price match this budget",
}

EXAMPLE_PROMPTS = [
    "Suggest a power bank under 1500",
    "Compare the TP-LINK TL-WR841N and the iBall 150M router",
    "Good wireless headphones under 2000?",
    "Which portable bluetooth speaker should I buy?",
    "What can you help me with?",
]


# Thin-line icons (Lucide, MIT licence), drawn with currentColor so CSS sets their colour.
ICONS = {
    "sparkles": '<path d="M9.94 15.5A2 2 0 0 0 8.5 14.06l-6.14-1.58a.5.5 0 0 1 0-.96L8.5 9.94A2 2 0 0 0 9.94 8.5'
                'l1.58-6.14a.5.5 0 0 1 .96 0L14.06 8.5A2 2 0 0 0 15.5 9.94l6.14 1.58a.5.5 0 0 1 0 .96L15.5 14.06'
                'a2 2 0 0 0-1.44 1.44l-1.58 6.14a.5.5 0 0 1-.96 0z"/><path d="M20 3v4M22 5h-4M4 17v2M5 18H3"/>',
    "grid": '<rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/>'
            '<rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/>',
    "sliders": '<path d="M21 4h-7M10 4H3M21 12h-9M8 12H3M21 20h-5M12 20H3M14 2v4M8 10v4M16 18v4"/>',
    "history": '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5M12 7v5l4 2"/>',
    "cpu": '<rect width="16" height="16" x="4" y="4" rx="2"/><rect width="6" height="6" x="9" y="9" rx="1"/>'
           '<path d="M15 2v2M15 20v2M2 15h2M2 9h2M20 15h2M20 9h2M9 2v2M9 20v2"/>',
    "zap": '<path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 '
           '.78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z"/>',
    "filter": '<path d="M22 3H2l8 9.46V19l4 2v-8.54z"/>',
}


def icon(name: str, size: int = 16) -> str:
    return (f'<svg class="ico" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>')


# Price filter stops in rupees. NO_LIMIT at the top end means no maximum.
NO_LIMIT = 1_000_000
PRICE_STOPS = [0, 250, 500, 1_000, 2_000, 5_000, 10_000, 25_000, 50_000, NO_LIMIT]


def price_stop_label(value: int) -> str:
    return "No limit" if value >= NO_LIMIT else f"₹{value:,}"


def filter_summary(min_price: float | None, max_price: float | None, categories: list[str]) -> str:
    """Short text for the active sidebar filters, empty when none are set."""
    parts = []
    if min_price is not None and max_price is not None:
        parts.append(f"₹{min_price:,.0f} – ₹{max_price:,.0f}")
    elif max_price is not None:
        parts.append(f"Under ₹{max_price:,.0f}")
    elif min_price is not None:
        parts.append(f"Above ₹{min_price:,.0f}")
    parts.extend(categories)
    return " · ".join(parts)


def source_numbers(sources: list[RetrievedChunk]) -> dict[str, int]:
    """Map each product ID to its 1-based position in the source list."""
    numbers: dict[str, int] = {}
    for s in sources:
        numbers.setdefault(s.product_id, len(numbers) + 1)
    return numbers


def number_citations(answer: str, sources: list[RetrievedChunk]) -> str:
    """Replace ``[product_id]`` with ``[n]`` for retrieved products; drop citations to unknown IDs."""
    numbers = source_numbers(sources)

    def repl(m: re.Match) -> str:
        n = numbers.get(m.group(1))
        if n is not None:
            return f"[{n}]"
        # Not a retrieved product: an invented ID is removed, other bracketed text is kept.
        return "" if m.group(1).startswith("P-") else m.group(0)

    text = _CITATION.sub(repl, answer)
    return re.sub(r"(\[\d+\])(?:\s*\1)+", r"\1", text)  # collapse "[1] [1]" left by repeated citations


def _normalise(text: str) -> str:
    return " ".join(_NON_WORD.sub(" ", text.lower()).split())


def cache_key(question: str, history: list[dict]) -> tuple[str, ...]:
    """Key for reusing an answer. A new-topic question is keyed on its text alone. A follow-up
    depends on the conversation, so the last three earlier user questions are part of its key."""
    if not history or not is_follow_up(question):
        return (_normalise(question),)
    earlier = [_normalise(m["content"]) for m in history if m.get("role") == "user"][-3:]
    return (_normalise(question), *earlier)


def format_price(price: float | None) -> str:
    """Historical catalogue price. ``None`` means unknown and is never shown as zero."""
    if price is None:
        return "Price unknown"
    return f"INR {price:,.0f} (2015-16 price)"


def format_rating(rating: float | None) -> str:
    """Average catalogue rating out of 5. Most records have none."""
    if rating is None:
        return "No rating"
    return f"★ {rating:g} / 5"


def format_rupees(price: float | None) -> str:
    """Compact card price. The card labels it as a 2015-16 price separately."""
    if price is None:
        return "Price unknown"
    return f"₹{price:,.0f}"


def product_card_html(number: int, chunk: RetrievedChunk, image_url: str | None, rating: float | None) -> str:
    """One product tile for the card grid. Every catalogue value is escaped."""
    def esc(value) -> str:
        return html.escape(str(value), quote=True)

    def link(inner: str, cls: str) -> str:
        if not chunk.source_url:
            return f'<div class="{cls}">{inner}</div>'
        return f'<a class="{cls}" href="{esc(chunk.source_url)}" target="_blank" rel="noopener">{inner}</a>'

    image = f'<img src="{esc(image_url)}" alt="" loading="lazy">' if image_url else '<span class="pcard-noimg">No image</span>'
    badge = (f'<span class="pcard-rating">{rating:g} ★</span>' if rating is not None
             else '<span class="pcard-norating">No ratings</span>')
    price_class = "pcard-price" if chunk.price is not None else "pcard-price pcard-unknown"
    return (f'<div class="pcard">{link(image, "pcard-img")}<div class="pcard-body">'
            f'<div class="pcard-meta"><span class="pcard-num">{number}</span>'
            f'{esc(chunk.category)} · {esc(chunk.brand or "Unknown brand")}</div>'
            f'{link(esc(chunk.name), "pcard-name")}'
            f'<div class="pcard-row"><span class="{price_class}">{esc(format_rupees(chunk.price))}</span>{badge}</div>'
            f'<div class="pcard-note">2015-16 catalogue price</div></div></div>')
