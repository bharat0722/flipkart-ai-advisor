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
from src.rag_pipeline import LLMUnavailableError, RagResult, answer_question
from src.hybrid import make_retriever
from src.retrieval import Retriever
from src.ui_helpers import (EXAMPLE_PROMPTS, REASON_LABELS, cache_key, format_price, format_rating,
                            number_citations, source_numbers)
from src.vector_store import IndexNotReadyError

load_dotenv()

DISPLAY_DATA = settings.ROOT / "data" / "processed" / "product_display.json"
ANSWER_CACHE_SIZE = 200

st.set_page_config(page_title="Flipkart AI Electronics Advisor", page_icon="🛒", layout="centered")


@st.cache_resource(show_spinner="Loading the product index and embedding model...")
def get_retriever() -> Retriever:
    """Load the embedding model and ChromaDB collection once per server process."""
    return make_retriever()


@st.cache_resource
def answer_cache() -> OrderedDict:
    """Answers shared by all sessions of this server process, most recently used last."""
    return OrderedDict()


def cached_answer(question: str, history: list[dict], retriever: Retriever) -> tuple[RagResult, bool]:
    """Return (result, from_cache). LLM errors raise and are never cached."""
    cache, key = answer_cache(), cache_key(question, history)
    if key in cache:
        cache.move_to_end(key)
        return cache[key], True
    result = answer_question(question, history, retriever=retriever)
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


def render_product_cards(result: dict) -> None:
    """A card for each product cited in the answer, numbered like the answer's [n] citations."""
    numbers = source_numbers(result["sources"])
    by_id = {s.product_id: s for s in result["sources"]}
    display = get_display_data()
    for pid in sorted(result["cited_product_ids"], key=numbers.get):
        s, extra = by_id[pid], display.get(pid, {})
        url = html.escape(s.source_url or "", quote=True)
        image, text = st.columns([1, 3], vertical_alignment="center")
        with image:
            if extra.get("image_url"):
                img = f'<img src="{html.escape(extra["image_url"], quote=True)}" alt="" style="max-width:100%;max-height:110px">'
                st.markdown(f'<a href="{url}" target="_blank">{img}</a>' if url else img, unsafe_allow_html=True)
        with text:
            name = html.escape(s.name)
            st.markdown(f'**[{numbers[pid]}]** <a href="{url}" target="_blank">{name}</a>' if url else
                        f"**[{numbers[pid]}]** {name}", unsafe_allow_html=True)
            st.markdown(f"**{format_price(s.price)}** · {format_rating(extra.get('rating'))}")
            st.caption(f"{s.category} · {s.brand or 'Unknown brand'}"
                       + (" · 🧪 synthetic demo record" if s.source_ref == "SYNTHETIC" else ""))


def render_sources(result: dict) -> None:
    sources = result["sources"]
    if not sources:
        return
    numbers = source_numbers(sources)
    with st.expander(f"All retrieved records ({len(numbers)})"):
        for s in sources:
            st.markdown(f"**[{numbers[s.product_id]}] {s.name}**")
            st.caption(f"{s.category} · {s.brand or 'Unknown brand'} · **{format_price(s.price)}** · "
                       f"relevance {s.score:.2f}")
            st.text(s.text[:600] + ("..." if len(s.text) > 600 else ""))
            st.caption(f"Source: `{s.source_ref}`" + (" (invented demo record)" if s.source_ref == "SYNTHETIC" else ""))


def render_assistant(msg: dict) -> None:
    if msg.get("error"):
        st.error(msg["error"])
        return
    result = msg["result"]
    st.markdown(number_citations(result["answer"], result["sources"]))
    if not result["grounded"]:
        st.info(REASON_LABELS.get(result["reason"], result["reason"]))
    render_product_cards(result)
    if result["reason"] != "weak_evidence":  # weak matches are unrelated records, not evidence
        render_sources(result)
    if msg.get("cached"):
        st.caption("⚡ Answered from cache")


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
    st.header("About")
    st.write("Ask about electronics in a historical Flipkart catalogue: chargers, headphones, "
             "home theatre, keyboards, mice, power banks, routers, speakers and USB storage.")
    st.warning("Prices and details come from a 2015-16 catalogue. They are not current prices "
               "or availability.")
    st.caption("The catalogue has only 2 laptops and no phones, so the advisor will say when it "
               "cannot answer.")
    if st.button("Clear chat", use_container_width=True, disabled=not st.session_state.messages):
        st.session_state.messages = []
        st.rerun()
    st.divider()
    st.caption(f"Model: `{os.getenv(settings.LLM_MODEL_ENV) or settings.DEFAULT_LLM_MODEL}` · "
               f"prompt {settings.PROMPT_VERSION} · {settings.retrieval_mode()} retrieval · "
               f"top {settings.DEFAULT_TOP_K} sources")

st.title("🛒 Flipkart AI Electronics Advisor")
st.caption("Recommendations and comparisons grounded in catalogue records, with sources.")

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
            st.markdown(msg["content"])
        else:
            render_assistant(msg)

question = st.chat_input("Ask about a product, a budget or a comparison")

if not st.session_state.messages and not question:
    st.write("Try one of these:")
    for i, prompt in enumerate(EXAMPLE_PROMPTS):
        if st.button(prompt, key=f"example-{i}"):
            question = prompt

if question:
    history = llm_history()
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.spinner("Searching the catalogue and writing an answer..."):
            try:
                r, from_cache = cached_answer(question, history, retriever)
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
