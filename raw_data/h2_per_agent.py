#!/usr/bin/env python3
"""Per-agent-per-replicate H2 classification (aware/fair rate per
agent per run), not just the cell-level aggregates run_h2_full.py
produces. Needed for the actual H2 hypothesis test the pilot-stage
manuscript text describes -- whether awareness language correlates
with an agent's own structural position (degree) or payoff, which
needs per-agent granularity, not a cell-pooled rate.

All 46,157 unique texts are already classified and cached (by
run_h2_full.py's earlier full run) -- this is pure re-aggregation, no
new judge calls, matches instantly against the on-disk cache.

Usage:
    python3 h2_per_agent.py --out reports/raw_exports/h2_per_agent.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import statistics
from pathlib import Path

from analyze_main_study import DEFAULT_ROOT, ENVIRONMENTS, POPULATIONS, TOPOLOGIES, SANCTIONING, load
from h2_judge import classify_batch, keyword_label, DEFAULT_CACHE_PATH
from run_h2_full import extract_texts, ACTION_TEXT_FIELDS

JOB_NAME = "h2_per_agent"


def _report(cmd: str, *args: str) -> None:
    import subprocess
    subprocess.run(["python3", str(Path(__file__).resolve().parent / "update_progress.py"),
                    JOB_NAME, cmd, *args], check=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--out", default="reports/raw_exports/h2_per_agent.csv")
    parser.add_argument("--cache", default=DEFAULT_CACHE_PATH)
    parser.add_argument("--api-key-env", default="LIGHTWEIGHT_API_KEY")
    args = parser.parse_args()

    api_key = os.environ.get(args.api_key_env, "")  # only needed if cache is incomplete

    rows = []
    all_texts: set[str] = set()
    per_run: list[dict] = []
    for environment, actions in ACTION_TEXT_FIELDS.items():
        for population in POPULATIONS:
            for topology in TOPOLOGIES:
                for sanctioning in SANCTIONING:
                    cell_dir = args.root / environment / f"{population}__{topology}__sanctioning_{sanctioning}"
                    if not cell_dir.is_dir():
                        continue
                    for rep_path in sorted(cell_dir.glob("rep*.json")):
                        pairs = extract_texts(rep_path, actions)
                        all_texts.update(t for _, t in pairs)
                        per_run.append({
                            "environment": environment, "population": population, "topology": topology,
                            "sanctioning": sanctioning, "rep": rep_path.stem, "pairs": pairs,
                        })

    CHUNK = 500
    all_sorted = sorted(all_texts)
    _report("init", str(len(all_sorted)), f"H2 per-agent classification ({len(all_sorted)} unique texts, prompt v2)")
    labels: dict[str, dict] = {}
    for i in range(0, len(all_sorted), CHUNK):
        chunk = all_sorted[i:i + CHUNK]
        labels.update(classify_batch(chunk, api_key, max_parallel=4, cache_path=args.cache))
        done_so_far = min(i + CHUNK, len(all_sorted))
        _report("done_count", str(done_so_far))
        _report("current", f"{done_so_far}/{len(all_sorted)} unique texts classified")
        print(f"  ...{done_so_far}/{len(all_sorted)} classified", flush=True)
    n_missing = len(all_texts) - len(labels)
    if n_missing:
        print(f"warning: {n_missing} texts not in cache and no working api key -- their rows will be skipped", flush=True)

    # keyword_label is deterministic and free -- computed here per unique
    # text too, so the output can compare judge vs. keyword directly at
    # the same per-agent granularity (not just the pilot-scale cell
    # aggregates), for the manuscript's classifier-discrepancy passage.
    kw_labels = {t: keyword_label(t) for t in all_sorted}

    for run in per_run:
        by_agent: dict[str, list[tuple[dict, dict]]] = {}
        for agent_id, text in run["pairs"]:
            if text not in labels:
                continue
            by_agent.setdefault(agent_id, []).append((labels[text], kw_labels[text]))
        for agent_id, classifications in sorted(by_agent.items()):
            n = len(classifications)
            judge_c = [c[0] for c in classifications]
            kw_c = [c[1] for c in classifications]
            aware_rate = statistics.mean(1.0 if c["aware"] else 0.0 for c in judge_c)
            fair_rate = statistics.mean(1.0 if c["fair"] else 0.0 for c in judge_c)
            kw_aware_rate = statistics.mean(1.0 if c["aware"] else 0.0 for c in kw_c)
            kw_fair_rate = statistics.mean(1.0 if c["fair"] else 0.0 for c in kw_c)
            rows.append({
                "environment": run["environment"], "population": run["population"], "topology": run["topology"],
                "sanctioning": run["sanctioning"], "rep": run["rep"], "agent_id": agent_id,
                "n_rounds_classified": n,
                "judge_aware_rate": round(aware_rate, 4), "judge_fair_rate": round(fair_rate, 4),
                "kw_aware_rate": round(kw_aware_rate, 4), "kw_fair_rate": round(kw_fair_rate, 4),
            })

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["environment", "population", "topology", "sanctioning", "rep",
                                          "agent_id", "n_rounds_classified",
                                          "judge_aware_rate", "judge_fair_rate", "kw_aware_rate", "kw_fair_rate"])
        w.writeheader()
        w.writerows(rows)
    print(f"written {args.out} ({len(rows)} agent-replicate rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
