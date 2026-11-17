"""LLM-as-judge scoring of the pipeline on the questions in docs/sample_questions.md.

    python scripts/judge_answers.py [--questions docs/sample_questions.md] [--limit N]

For every question it runs the real pipeline, then asks the configured LLM to grade the answer against the
retrieved evidence. Metrics (RAGAS-style, but with no extra dependency):

  faithfulness       share of the answer's factual claims that the retrieved text supports (1.0 = none invented)
  relevancy          1-5, does the answer address every part of the question
  context_precision  share of retrieved chunks that are useful for the question
  answerable         could the question be answered from the retrieved text (a refusal while answerable is a miss)

Writes docs/judge_report.md and data/evaluation/judge_results.csv. The judge is the same LLM that writes
the answers, so scores lean generous; treat them as a regression signal and read the flagged rows by hand.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from dotenv import load_dotenv  # noqa: E402

from run_questions import parse  # noqa: E402
from src.hybrid import make_retriever  # noqa: E402
from src.prompts import CATALOGUE_SCOPE, build_context  # noqa: E402
from src.rag_pipeline import _call_llm, answer_question, make_client  # noqa: E402

JUDGE_PROMPT = """You are a strict evaluator of a retrieval-augmented shopping assistant.
You get the QUESTION, the retrieved CONTEXT (the only allowed evidence) and the assistant's ANSWER.
Judge using ONLY the context. Product IDs in square brackets are citations, not claims.
Prices in the answer are meant to be historical (2015-16); that framing is not a claim to check.

Reply with one JSON object and nothing else:
{
  "claims": [{"text": "<one factual claim from the answer>", "supported": true|false}],
  "relevancy": <integer 1-5: does the answer address every part of the question; a correct refusal of an unanswerable question scores 5>,
  "chunks": [{"id": "<product id>", "useful": true|false}],
  "answerable": true|false,
  "notes": "<one short sentence on the main weakness, or 'none'>"
}
"chunks" lists every product id in the context. "useful" means that chunk helps answer the question.
"answerable" is true if the context holds enough to answer the question (or a reasonable part of it)."""


def judge(client, question: str, answer: str, sources) -> dict:
    user = f"QUESTION: {question}\n\nCONTEXT:\n{build_context(sources)}\n\nANSWER:\n{answer}"
    text = _call_llm(client, [{"role": "system", "content": JUDGE_PROMPT}, {"role": "user", "content": user}])
    match = re.search(r"\{.*\}", text, re.S)
    return json.loads(match.group(0))


def score(verdict: dict, n_sources: int) -> dict:
    claims = verdict.get("claims") or []
    supported = sum(1 for c in claims if c.get("supported"))
    chunks = verdict.get("chunks") or []
    useful = sum(1 for c in chunks if c.get("useful"))
    return {
        "faithfulness": round(supported / len(claims), 2) if claims else 1.0,
        "unsupported": [c.get("text", "") for c in claims if not c.get("supported")],
        "relevancy": int(verdict.get("relevancy", 0)),
        "context_precision": round(useful / len(chunks), 2) if chunks else 0.0,
        "answerable": bool(verdict.get("answerable")),
        "notes": str(verdict.get("notes", "")),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--questions", default=str(ROOT / "docs" / "sample_questions.md"))
    ap.add_argument("--limit", type=int, default=0, help="judge only the first N questions")
    args = ap.parse_args()
    load_dotenv(ROOT / ".env")
    retriever, client = make_retriever(), make_client()

    rows = []
    for section, questions in parse(Path(args.questions)):
        history: list[dict] = []
        follow_up = section.lower().startswith("follow-up")
        for q in questions:
            if args.limit and len(rows) >= args.limit:
                break
            print(f"[{section}] {q}", flush=True)
            row = {"section": section, "question": q}
            try:
                r = answer_question(q, history if follow_up else None, retriever=retriever, client=client)
                if follow_up:
                    history += [{"role": "user", "content": q}, {"role": "assistant", "content": r.answer}]
                row.update(reason=r.reason, grounded=r.grounded)
                if r.sources:
                    row.update(score(judge(client, q, r.answer.replace(CATALOGUE_SCOPE, "").strip(), r.sources), len(r.sources)))
                else:  # nothing retrieved (e.g. budget miss): a refusal is the only possible answer
                    row.update(faithfulness=1.0, unsupported=[], relevancy=5, context_precision=None,
                               answerable=False, notes="no evidence retrieved; fixed refusal")
            except Exception as e:  # keep going so one failure doesn't lose the run
                row.update(error=f"{type(e).__name__}: {e}")
            rows.append(row)

    ok = [r for r in rows if "error" not in r]

    def mean(key, subset=ok):
        vals = [r[key] for r in subset if r.get(key) is not None]
        return round(sum(vals) / len(vals), 2) if vals else None

    answered = [r for r in ok if r["reason"] == "answered"]
    refused = [r for r in ok if r["reason"] != "answered"]
    false_refusals = [r for r in refused if r["answerable"]]
    flagged = [r for r in ok if r["faithfulness"] < 1 or r["relevancy"] <= 3 or r in false_refusals]

    out_csv = ROOT / "data" / "evaluation" / "judge_results.csv"
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fields = ["section", "question", "reason", "grounded", "faithfulness", "relevancy", "context_precision",
              "answerable", "unsupported", "notes", "error"]
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({**r, "unsupported": " | ".join(r.get("unsupported", []))})

    md = ["# Judge report", "", "Generated by `scripts/judge_answers.py`. The judge is the same LLM that writes the answers, "
          "so scores lean generous. Use them to spot regressions and read the flagged rows by hand.", "",
          f"Questions judged: {len(ok)} of {len(rows)} ({len(rows) - len(ok)} errors)", "",
          "| Metric | Mean |", "|---|---|",
          f"| Faithfulness (answered questions) | {mean('faithfulness', answered)} |",
          f"| Relevancy, 1-5 (all) | {mean('relevancy')} |",
          f"| Context precision | {mean('context_precision')} |",
          f"| Refusals that were answerable from the evidence | {len(false_refusals)} of {len(refused)} |", "",
          "## Per question", "", "| Section | Question | Reason | Faith. | Rel. | Ctx prec. | Notes |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        if "error" in r:
            md.append(f"| {r['section']} | {r['question']} | error | | | | {r['error']} |")
        else:
            md.append(f"| {r['section']} | {r['question']} | {r['reason']} | {r['faithfulness']} | {r['relevancy']} | "
                      f"{r['context_precision']} | {r['notes'].replace('|', '/')} |")
    md += ["", "## Flagged for manual review", ""]
    for r in flagged:
        why = []
        if r["faithfulness"] < 1:
            why.append("unsupported claims: " + "; ".join(r["unsupported"]))
        if r["relevancy"] <= 3:
            why.append(f"relevancy {r['relevancy']}")
        if r in false_refusals:
            why.append("refused although the evidence could answer it")
        md.append(f"- **{r['question']}** ({r['reason']}): {' / '.join(why)}")
    if not flagged:
        md.append("None.")
    (ROOT / "docs" / "judge_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"Wrote docs/judge_report.md and {out_csv.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
