"""Streamlit chat app for the Flipkart AI Electronics Advisor.

    streamlit run app.py

Answers come from ``src.rag_pipeline.answer_question``. Each answer shows its numbered
source records with historical prices. Requires the index (``python scripts/build_index.py``)
and an LLM key in ``.env`` (see ``.env.example``).
"""

from __future__ import annotations

import html
import json
import os
from collections import OrderedDict

import streamlit as st
from dotenv import load_dotenv

from src import settings
from src.hybrid import make_retriever
from src.query_understanding import CATEGORY_KEYWORDS, Constraints
from src.rag_pipeline import LLMUnavailableError, RagResult, answer_question
from src.retrieval import Retriever
from src.ui_helpers import (EXAMPLE_PROMPTS, NO_LIMIT, PRICE_STOPS, REASON_LABELS, cache_key, filter_summary,
                            format_price, icon, number_citations, price_stop_label, product_card_html,
                            source_numbers)
from src.vector_store import IndexNotReadyError

load_dotenv()

DISPLAY_DATA = settings.ROOT / "data" / "processed" / "product_display.json"
STYLESHEET = settings.ROOT / "assets" / "app.css"
ANSWER_CACHE_SIZE = 200
TOP_K_RANGE = (3, 10)
EXAMPLE_ICONS = [":material/battery_charging_full:", ":material/router:", ":material/headphones:",
                 ":material/speaker:", ":material/help:"]
FILTER_DEFAULTS = {"top_k": settings.DEFAULT_TOP_K, "price": (PRICE_STOPS[0], PRICE_STOPS[-1]), "categories": []}

st.set_page_config(page_title="Electronics Advisor · Flipkart catalogue", page_icon=":material/auto_awesome:",
                   layout="centered")
st.markdown(f"<style>{STYLESHEET.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


@st.cache_resource(show_spinner="Loading the product index and embedding model (the first start builds the index, "
                                "about 2 minutes)...")
def get_retriever() -> Retriever:
    """Load the embedding model and ChromaDB collection once per server process.

    The deploy branch ships the cleaned CSV but not the index, so a fresh host builds it once here."""
    try:
        return make_retriever()
    except IndexNotReadyError:
        if not settings.PROCESSED_CSV.exists():
            raise
        from scripts.build_index import build_index
        build_index(settings.PROCESSED_CSV, settings.INDEX_DIR, settings.COLLECTION_NAME)
        return make_retriever()


@st.cache_resource
def answer_cache() -> OrderedDict:
    """Answers shared by all sessions of this server process, most recently used last."""
    return OrderedDict()


def cached_answer(question: str, history: list[dict], retriever: Retriever, k: int,
                  filters: Constraints | None) -> tuple[RagResult, bool]:
    """Return (result, from_cache). LLM errors raise and are never cached. The filters are part of the key."""
    filter_key = (k, *(() if filters is None else (filters.min_price, filters.max_price, tuple(filters.categories))))
    cache, key = answer_cache(), (cache_key(question, history), filter_key)
    if key in cache:
        cache.move_to_end(key)
        return cache[key], True
    result = answer_question(question, history, retriever=retriever, k=k, filters=filters)
    cache[key] = result
    if len(cache) > ANSWER_CACHE_SIZE:
        cache.popitem(last=False)
    return result, False


@st.cache_data
def get_display_data() -> dict:
    """Images and ratings from ``scripts/build_display_data.py``; cards still render without them."""
    try:
        return json.loads(DISPLAY_DATA.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def section_label(icon_name: str, text: str) -> None:
    st.markdown(f'<div class="section-label">{icon(icon_name)}<span>{text}</span></div>', unsafe_allow_html=True)


def current_filters() -> Constraints | None:
    """The sidebar's price and category limits, or None when they are left at 'everything'."""
    low, high = st.session_state.price
    min_price = float(low) if low > PRICE_STOPS[0] else None
    max_price = float(high) if high < NO_LIMIT else None
    categories = list(st.session_state.categories)
    if min_price is None and max_price is None and not categories:
        return None
    return Constraints(max_price=max_price, min_price=min_price, categories=categories)


def reset_filters() -> None:
    for key, value in FILTER_DEFAULTS.items():
        st.session_state[key] = value


def render_product_cards(result: dict) -> None:
    """A card for each product cited in the answer, numbered like the answer's [n] citations."""
    numbers = source_numbers(result["sources"])
    by_id = {s.product_id: s for s in result["sources"]}
    display = get_display_data()
    cards = []
    for pid in sorted(result["cited_product_ids"], key=numbers.get):
        extra = display.get(pid, {})
        cards.append(product_card_html(numbers[pid], by_id[pid], extra.get("image_url"), extra.get("rating")))
    if cards:
        section_label("grid", "Products")
        st.markdown(f'<div class="pgrid">{"".join(cards)}</div>', unsafe_allow_html=True)


def render_sources(result: dict) -> None:
    sources = result["sources"]
    if not sources:
        return
    numbers = source_numbers(sources)
    rows = []
    for s in sources:
        snippet = s.text[:600] + ("..." if len(s.text) > 600 else "")
        meta = f"{s.category} · {s.brand or 'Unknown brand'} · {format_price(s.price)} · relevance {s.score:.2f}"
        rows.append(f'<div class="src"><div class="src-name">[{numbers[s.product_id]}] {html.escape(s.name)}</div>'
                    f'<div class="src-meta">{html.escape(meta)}</div>'
                    f'<div class="src-text">{html.escape(snippet)}</div>'
                    f'<div class="src-ref">{html.escape(s.source_ref)}</div></div>')
    with st.expander(f"Sources · {len(numbers)} catalogue records", icon=":material/menu_book:"):
        st.markdown("".join(rows), unsafe_allow_html=True)


def render_question(msg: dict) -> None:
    """The question as a heading, with the filters it was asked under."""
    tags = f'<div class="q-filters">{icon("filter", 13)}{html.escape(msg["filters"])}</div>' if msg.get("filters") else ""
    st.markdown(f'<div class="q">{html.escape(msg["content"])}</div>{tags}', unsafe_allow_html=True)


def render_assistant(msg: dict) -> None:
    if msg.get("error"):
        st.error(msg["error"], icon=":material/error:")
        return
    result = msg["result"]
    section_label("sparkles", "Answer")
    st.markdown(number_citations(result["answer"], result["sources"]))
    if not result["grounded"]:
        st.info(REASON_LABELS.get(result["reason"], result["reason"]), icon=":material/info:")
    render_product_cards(result)
    if result["reason"] != "weak_evidence":  # weak matches are unrelated records, not evidence
        render_sources(result)
    if msg.get("cached"):
        st.markdown(f'<span class="cache-badge">{icon("zap", 12)}Answered from cache</span>', unsafe_allow_html=True)


def llm_history() -> list[dict]:
    """Previous turns for the LLM: raw answers with product IDs, errors left out."""
    out = []
    for m in st.session_state.messages:
        if m["role"] == "user":
            out.append({"role": "user", "content": m["content"]})
        elif m.get("result"):
            out.append({"role": "assistant", "content": m["result"]["answer"]})
    return out


if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    if st.button("New chat", icon=":material/add:", use_container_width=True,
                 disabled=not st.session_state.messages):
        st.session_state.messages = []
        st.rerun()

    section_label("sliders", "Filters")
    st.slider("Products to consider", *TOP_K_RANGE, value=FILTER_DEFAULTS["top_k"], key="top_k",
              help="How many catalogue records the advisor reads before answering.")
    st.select_slider("Price range (2015-16)", options=PRICE_STOPS, value=FILTER_DEFAULTS["price"], key="price",
                     format_func=price_stop_label)
    st.multiselect("Categories", list(CATEGORY_KEYWORDS), default=FILTER_DEFAULTS["categories"], key="categories",
                   placeholder="All categories")
    is_default = all(st.session_state[k] == v for k, v in FILTER_DEFAULTS.items())
    st.button("Reset filters", icon=":material/restart_alt:", on_click=reset_filters, disabled=is_default,
              use_container_width=True, type="tertiary")

    st.markdown(f'<div class="notice"><div class="notice-head">{icon("history", 14)}Historical catalogue</div>'
                "Prices and details come from 2015-16 Flipkart listings, not current prices or availability. "
                "There are only 2 laptops and no phones, so the advisor will say when it cannot answer.</div>",
                unsafe_allow_html=True)
    model = html.escape(os.getenv(settings.LLM_MODEL_ENV) or settings.DEFAULT_LLM_MODEL)
    section_label("cpu", "System")
    st.markdown(f'<div class="side-meta">Model <code>{model}</code><br>Prompt {settings.PROMPT_VERSION} · '
                f"{settings.retrieval_mode()} retrieval</div>", unsafe_allow_html=True)

st.markdown(f'<div class="app-hero"><div class="app-mark">{icon("sparkles", 22)}</div><div>'
            '<div class="app-title">Electronics Advisor<span class="app-tag">2015-16 catalogue</span></div>'
            '<div class="app-sub">Recommendations and comparisons grounded in Flipkart catalogue records, '
            "with sources.</div></div></div>", unsafe_allow_html=True)

try:
    retriever = get_retriever()
except IndexNotReadyError as exc:
    st.error(f"The product index is not ready. {exc}")
    st.stop()

if not os.getenv(settings.LLM_API_KEY_ENV):
    st.error(f"No LLM API key found. Copy `.env.example` to `.env`, set `{settings.LLM_API_KEY_ENV}`, "
             "and restart the app.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            render_question(msg)
        else:
            render_assistant(msg)

question = st.chat_input("Ask about a product, a budget or a comparison")

if not st.session_state.messages and not question:
    st.markdown('<div class="empty-title">What are you shopping for?</div>'
                '<div class="empty-sub">Ask for a recommendation, set a budget or compare two products. '
                "Try one of these:</div>", unsafe_allow_html=True)
    columns = st.columns(2)
    for i, (prompt, prompt_icon) in enumerate(zip(EXAMPLE_PROMPTS, EXAMPLE_ICONS, strict=True)):
        if columns[i % 2].button(prompt, key=f"example-{i}", icon=prompt_icon, use_container_width=True):
            question = prompt

if question:
    history = llm_history()
    filters = current_filters()
    user_msg = {"role": "user", "content": question,
                "filters": filter_summary(filters.min_price, filters.max_price, filters.categories) if filters else ""}
    st.session_state.messages.append(user_msg)
    with st.chat_message("user"):
        render_question(user_msg)
    with st.chat_message("assistant"):
        with st.spinner("Searching the catalogue and writing an answer..."):
            try:
                r, from_cache = cached_answer(question, history, retriever, st.session_state.top_k, filters)
                msg = {"role": "assistant", "cached": from_cache, "result": {
                    "answer": r.answer, "grounded": r.grounded, "reason": r.reason,
                    "cited_product_ids": r.cited_product_ids, "sources": r.sources}}
            except LLMUnavailableError as exc:
                msg = {"role": "assistant", "error": str(exc)}
            except Exception as exc:  # keep the chat usable on unexpected failures
                msg = {"role": "assistant", "error": f"Something went wrong ({type(exc).__name__}). "
                                                     "Please try again."}
        render_assistant(msg)
    st.session_state.messages.append(msg)
    st.rerun()
