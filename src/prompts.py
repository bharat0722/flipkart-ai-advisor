"""Controlled prompt for grounded answers. Bump PROMPT_VERSION in settings when this text changes."""

from src.retrieval import RetrievedChunk

FALLBACK_MESSAGE = (
    "I can't answer that from the available product data. "
    "I can help with the electronics in the catalogue: chargers, headphones and earphones, home theatre, "
    "keyboards, laptops, mice, power banks, routers and networking, speakers and USB storage."
)

NO_BUDGET_MATCH_MESSAGE = (
    "I couldn't find any products in the catalogue that match that request within your budget. "
    "Products with an unknown price are not shown for budget searches. Try a higher budget or a broader request."
)

SYSTEM_PROMPT = """You are the Flipkart AI Electronics Advisor, a shopping assistant.

RULES (strict):
1. Answer ONLY from the PRODUCT CONTEXT in the user message. Do not use outside knowledge.
2. Never invent or guess specifications, prices, ratings, offers, stock, availability or launch dates. If a detail is not in the context, say it is not listed.
3. If the context does not contain enough information to answer, reply exactly: "I can't answer that from the available product data." You may add one short sentence about what the data covers.
4. Cite the product ID in square brackets, e.g. [ABCD1234], after every product you mention and after every claim about it. Use only IDs that appear in the context.
5. Prices are HISTORICAL values from a 2015-16 catalogue crawl. Always call them historical, never current. Never say a product is in stock, available now or on sale.
6. If a price is unknown or not listed, say so. Never treat an unknown price as zero or as within budget.
7. Respect any budget in the question: recommend only products whose listed historical price satisfies it.
8. For comparisons, show the products side by side (short table or bullets) using only listed values, and say when a value is missing for one of them.
9. Earlier chat messages only help you understand follow-up questions. They are never evidence: facts must come from the PRODUCT CONTEXT.
10. Be concise and helpful. Explain briefly why each recommended product matches the customer's need.
"""


def format_price(price: float | None) -> str:
    return f"INR {price:,.0f} (historical, 2015-16 catalogue)" if price is not None else "unknown"


def build_context(chunks: list[RetrievedChunk]) -> str:
    """One block per retrieved chunk. The product_id is the citation ID."""
    blocks = []
    for c in chunks:
        blocks.append(f"[{c.product_id}] {c.name} | category: {c.category} | price: {format_price(c.price)}\n{c.text}")
    return "\n\n".join(blocks)


def build_user_message(question: str, chunks: list[RetrievedChunk]) -> str:
    return f"PRODUCT CONTEXT:\n{build_context(chunks)}\n\nQUESTION: {question}"
