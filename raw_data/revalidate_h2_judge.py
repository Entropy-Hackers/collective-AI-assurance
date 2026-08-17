#!/usr/bin/env python3
"""Re-validates the CURRENT h2_judge.py configuration (deepseek-v4-flash
via e-INFRA CZ, pinned model) against the same blind human-coded
30-item spot-check used for the original validation
(h2_classifier_validation.md) -- which was run against a DIFFERENT
configuration (validate_h2_classifier.py's own "deepseek-chat" via
DeepSeek's commercial API, before the model-pinning fix and before
this project standardized on e-INFRA CZ). Confirms the switch in
serving infrastructure didn't silently change classifier behaviour
before trusting the full 192-run classification that used it.

`fair` labels come from h2_human_coding_sheet.md (solid on first pass,
never redone). `aware` labels come from
h2_human_coding_sheet_aware_redo.md (the corrected pass, after the
documented definition-drift false start on the original aware pass).

Usage:
    python3 revalidate_h2_judge.py
"""
from __future__ import annotations

import os
import re
import sys

from h2_judge import classify_batch, keyword_label

SHEET = "reports/raw_exports/h2_human_coding_sheet.md"
AWARE_REDO_SHEET = "reports/raw_exports/h2_human_coding_sheet_aware_redo.md"


def cohens_kappa(a: list[bool], b: list[bool]) -> float | None:
    n = len(a)
    if n == 0:
        return None
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pa_true = sum(a) / n
    pb_true = sum(b) / n
    pe = pa_true * pb_true + (1 - pa_true) * (1 - pb_true)
    if pe == 1:
        return 1.0
    return (po - pe) / (1 - pe)


def parse_sheet(path: str, want_fields: tuple[str, ...]) -> list[dict]:
    text = open(path).read()
    items = re.split(r"\n## \d+\n", text)[1:]
    rows = []
    for item in items:
        m = re.search(r"^> (.+)$", item, re.MULTILINE)
        quote = m.group(1).strip() if m else None
        row = {"text": quote}
        for field in want_fields:
            fm = re.search(rf"^{field}:\s*(y|n)\s*$", item, re.MULTILINE)
            row[field] = fm.group(1) if fm else None
        rows.append(row)
    return rows


def main() -> int:
    fair_rows = parse_sheet(SHEET, ("fair",))
    aware_rows = parse_sheet(AWARE_REDO_SHEET, ("aware",))
    if len(fair_rows) != len(aware_rows):
        print(f"length mismatch: fair sheet {len(fair_rows)}, aware sheet {len(aware_rows)}", file=sys.stderr)
        return 1

    items = []
    for f, a in zip(fair_rows, aware_rows):
        if f["text"] != a["text"]:
            print(f"text mismatch:\n  fair sheet: {f['text']}\n  aware sheet: {a['text']}", file=sys.stderr)
            return 1
        items.append({"text": f["text"], "fair": f["fair"], "aware": a["aware"]})

    unfilled = [i + 1 for i, it in enumerate(items) if it["fair"] not in ("y", "n") or it["aware"] not in ("y", "n")]
    if unfilled:
        print(f"unfilled items: {unfilled}", file=sys.stderr)
        return 1

    api_key = os.environ.get("LIGHTWEIGHT_API_KEY")
    if not api_key:
        print("set LIGHTWEIGHT_API_KEY (source ~/.e_infra_env; export LIGHTWEIGHT_API_KEY=$OPENAI_API_KEY)", file=sys.stderr)
        return 1

    texts = [it["text"] for it in items]
    # Bypass the cache -- these exact human-coding-sheet texts are
    # short illustrative examples, unlikely to already be cached from
    # the real run, but force a fresh call either way for a clean
    # re-validation, not an accidental cache hit from the original
    # (different-config) validation run.
    judge_labels = classify_batch(texts, api_key, max_parallel=4,
                                   cache_path="/tmp/h2_revalidation_cache.json")

    human_fair = [it["fair"] == "y" for it in items]
    human_aware = [it["aware"] == "y" for it in items]
    judge_fair = [judge_labels.get(t, {}).get("fair", False) for t in texts]
    judge_aware = [judge_labels.get(t, {}).get("aware", False) for t in texts]
    kw_fair = [keyword_label(t)["fair"] for t in texts]
    kw_aware = [keyword_label(t)["aware"] for t in texts]

    n = len(items)
    print(f"n={n} items, judge classified {sum(1 for t in texts if t in judge_labels)}/{n}")
    print()
    for dim, human, judge, kw in [("fair", human_fair, judge_fair, kw_fair), ("aware", human_aware, judge_aware, kw_aware)]:
        agree = sum(1 for x, y in zip(human, judge) if x == y) / n
        kappa = cohens_kappa(human, judge)
        agree_kw = sum(1 for x, y in zip(human, kw) if x == y) / n
        kappa_kw = cohens_kappa(human, kw)
        print(f"{dim}: human positive={sum(human)}, judge positive={sum(judge)}, keyword positive={sum(kw)}")
        print(f"  human vs judge (e-INFRA CZ, current config):   agreement={agree:.1%}, kappa={kappa:.3f}")
        print(f"  human vs keyword:                               agreement={agree_kw:.1%}, kappa={kappa_kw:.3f}")
        disagreements = [(t, h, j) for t, h, j in zip(texts, human, judge) if h != j]
        print(f"  disagreements ({len(disagreements)}):")
        for t, h, j in disagreements:
            print(f"    human={h}, judge={j}: {t}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
