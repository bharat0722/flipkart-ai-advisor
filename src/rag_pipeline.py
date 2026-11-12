"""Grounded answer pipeline: question -> filters -> retrieval -> prompt -> LLM -> answer + sources.

    from src.rag_pipeline import answer_question
    result = answer_question("Suggest a router under 1500", history=[...])
    result.answer, result.cited_product_ids, result.sources

The LLM is only called when retrieval found usable evidence. Otherwise a fixed
insufficient-evidence message is returned without calling it.
"""

from __future__ import annotations

import os
import re
from dataclasses import asdict, dataclass, field

from src import settings
from src.prompts import FALLBACK_MESSAGE, NO_BUDGET_MATCH_MESSAGE, SYSTEM_PROMPT, build_user_message
from src.query_understanding import Constraints, extract_comparison_targets, understand
from src.retrieval import RetrievedChunk, Retriever

_CITATION = re.compile(r"\[([A-Za-z0-9_\-]+)\]")
_WORD = re.compile(r"[a-z0-9]+")


class LLMUnavailableError(RuntimeError):
    """The LLM could not be reached or is not configured. The message is safe to show in the UI."""


@dataclass
class RagResult:
    answer: str
    grounded: bool                      # False when the fixed fallback was returned (LLM not called)
    reason: str                         # "answered", "no_support" (LLM declined or cited nothing), "no_evidence", "weak_evidence", "no_budget_match"
    cited_product_ids: list[str] = field(default_factory=list)   # ids cited in the answer that were retrieved
    invalid_citations: list[str] = field(default_factory=list)   # cited ids NOT in the retrieved evidence
    sources: list[RetrievedChunk] = field(default_factory=list)  # retrieved evidence, in rank order
    constraints: Constraints = field(default_factory=Constraints)
    prompt_version: str = settings.PROMPT_VERSION

    def to_dict(self) -> dict:
        d = asdict(self)
        d["sources"] = [s.to_dict() for s in self.sources]
        d["constraints"] = self.constraints.to_dict()
        return d


def _clean_history(history: list[dict] | None) -> list[dict]:
    """Keep only the last few well-formed user/assistant turns."""
    ok = [{"role": m["role"], "content": str(m["content"])} for m in (history or [])
          if isinstance(m, dict) and m.get("role") in ("user", "assistant") and m.get("content")]
    return ok[-settings.HISTORY_MESSAGES:]


def _words(text: str) -> set[str]:
    return set(_WORD.findall(text.lower()))


def _retrieve_named(targets: list[str], retriever, constraints: Constraints, k: int):
    """One search per named product, keeping the candidates whose names best match the request.

    A single semantic search over "compare A and B" returns look-alikes of either. Searching per name and
    ranking by word overlap with the product name puts the exact model first. Returns (sources, notes).
    """
    sources: list[RetrievedChunk] = []
    notes: list[str] = []
    seen: set[str] = set()
    for target in targets:
        wanted = _words(target)
        hits = retriever.search(target, settings.NAMED_CANDIDATES, max_price=constraints.max_price,
                                min_price=constraints.min_price, categories=constraints.categories or None)
        ranked = sorted(((len(wanted & _words(h.name)) / len(wanted), h.score, h) for h in hits),
                        key=lambda x: x[:2], reverse=True)
        if ranked and ranked[0][0] >= settings.NAMED_MATCH_MIN_OVERLAP:
            chosen = [h for _, _, h in ranked[:2]]   # the named model, plus its closest alternative
        else:
            notes.append(f"No product in the context clearly matches the customer's \"{target}\".")
            chosen = [h for _, _, h in ranked[:1]]
        for hit in chosen:
            if hit.product_id not in seen:
                seen.add(hit.product_id)
                sources.append(hit)
    return sources, notes


def make_client():
    """OpenAI-compatible client configured from the environment. Imported lazily so tests need no key."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:  # pragma: no cover
        pass
    api_key = os.getenv(settings.LLM_API_KEY_ENV)
    if not api_key:
        raise LLMUnavailableError(f"No API key configured. Set {settings.LLM_API_KEY_ENV} in your .env file.")
    from openai import OpenAI
    return OpenAI(api_key=api_key, base_url=os.getenv(settings.LLM_BASE_URL_ENV) or None, max_retries=2, timeout=settings.LLM_TIMEOUT_SECONDS)


def _call_llm(client, messages: list[dict]) -> str:
    model = os.getenv(settings.LLM_MODEL_ENV) or settings.DEFAULT_LLM_MODEL
    try:
        resp = client.chat.completions.create(model=model, messages=messages, temperature=0)
    except Exception as exc:  # the SDK raises several error types; surface one friendly message
        raise LLMUnavailableError(
            f"The language model is unavailable right now ({type(exc).__name__}). Please try again.") from exc
    return (resp.choices[0].message.content or "").strip()


def answer_question(question: str, history: list[dict] | None = None, *, retriever: Retriever | None = None,
                    client=None, k: int = settings.DEFAULT_TOP_K) -> RagResult:
    question = (question or "").strip()
    if not question:
        raise ValueError("Question must not be empty.")
    constraints = understand(question)
    retriever = retriever or Retriever()
    targets = extract_comparison_targets(question)
    notes: list[str] = []
    sources: list[RetrievedChunk] = []
    if targets:
        sources, notes = _retrieve_named(targets, retriever, constraints, k)
    if not sources:
        sources = retriever.search(question, k, max_price=constraints.max_price, min_price=constraints.min_price,
                                   categories=constraints.categories or None)

    if not sources:
        if constraints.has_price_limit:
            return RagResult(NO_BUDGET_MATCH_MESSAGE, False, "no_budget_match", constraints=constraints)
        return RagResult(FALLBACK_MESSAGE, False, "no_evidence", constraints=constraints)
    if max(s.score for s in sources) < settings.MIN_EVIDENCE_SCORE:
        return RagResult(FALLBACK_MESSAGE, False, "weak_evidence", sources=sources, constraints=constraints)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}, *_clean_history(history),
                {"role": "user", "content": build_user_message(question, sources, notes)}]
    text = _call_llm(client or make_client(), messages)

    retrieved_ids = {s.product_id for s in sources}
    cited = list(dict.fromkeys(_CITATION.findall(text)))
    valid = [c for c in cited if c in retrieved_ids]
    # An answer that cites no retrieved product is a refusal or an unsupported reply, not a grounded answer.
    return RagResult(
        answer=text, grounded=bool(valid), reason="answered" if valid else "no_support", sources=sources,
        constraints=constraints, cited_product_ids=valid,
        invalid_citations=[c for c in cited if c not in retrieved_ids],
    )
