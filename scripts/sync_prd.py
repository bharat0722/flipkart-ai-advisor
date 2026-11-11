"""Render the live PRD's phase table from reviewed status records."""

import argparse
import json
import sys
from pathlib import Path


DOCS = Path(__file__).resolve().parents[1] / "docs"
START = "<!-- BEGIN PHASE STATUS -->"
END = "<!-- END PHASE STATUS -->"
STATES = {
    "planned": "Planned",
    "in_progress": "In progress",
    "blocked": "Blocked",
    "ready_for_review": "Ready for review",
    "accepted": "Accepted",
}


def cell(value):
    return value.replace("|", r"\|").replace("\n", " ")


def render(records, docs):
    if not isinstance(records, list) or [r.get("phase") for r in records] != list(range(1, 6)):
        raise ValueError("phase_status.json must contain phases 1 through 5 in order")

    lines = [
        "| Phase | Lead | Status | Handoff | Evidence and next decision |",
        "| --- | --- | --- | --- | --- |",
    ]
    for record in records:
        phase = record["phase"]
        title = cell(record["title"])
        owner = cell(record["owner"])
        status = record["status"]
        evidence = cell(record["evidence"])
        handoff = record.get("handoff")
        if status not in STATES:
            raise ValueError(f"Phase {phase} has an unknown status: {status}")
        if handoff is not None:
            expected = f"handoffs/phase-{phase:02d}.md"
            if handoff != expected or not (docs / expected).is_file():
                raise ValueError(f"Phase {phase} handoff must point to an existing {expected}")
        if status in {"ready_for_review", "accepted"} and (not handoff or not evidence.strip()):
            raise ValueError(f"Phase {phase} requires a handoff and evidence before review")
        if status == "accepted":
            reviewer = record.get("accepted_by", "").strip()
            if not reviewer:
                raise ValueError(f"Phase {phase} needs its receiving lead's acceptance record")
            evidence = f"{evidence} Accepted by {cell(reviewer)}."
        link = f"[Handoff]({handoff})" if handoff else "Pending"
        lines.append(f"| {phase}. {title} | {owner} | {STATES[status]} | {link} | {evidence} |")
    return "\n".join(lines)


def sync(docs, check):
    prd = docs / "PRD.md"
    original = prd.read_text(encoding="utf-8")
    if original.count(START) != 1 or original.count(END) != 1 or original.index(START) > original.index(END):
        raise ValueError("PRD.md must contain one ordered pair of status markers")
    records = json.loads((docs / "phase_status.json").read_text(encoding="utf-8"))
    before = original[: original.index(START) + len(START)]
    after = original[original.index(END) :]
    updated = f"{before}\n{render(records, docs)}\n{after}"
    if updated == original:
        print("PRD phase status is current.")
        return 0
    if check:
        print("PRD phase status is stale. Run python scripts/sync_prd.py.", file=sys.stderr)
        return 1
    prd.write_text(updated, encoding="utf-8")
    print("Updated docs/PRD.md from phase_status.json.")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if the generated table is stale.")
    args = parser.parse_args()
    try:
        return sync(DOCS, args.check)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        print(f"Cannot sync PRD: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
