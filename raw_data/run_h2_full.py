#!/usr/bin/env python3
"""H2 self-report classification over the FULL main-study dataset (192
runs), not just the pilot spot-check. Extracts every agent-round's
free-text "reason" from the `events` table's params_json (the same
field the pilot-scale classifier used), runs it through h2_judge's
LLM-judge classifier (deepseek-v4-flash via e-INFRA CZ, same model as
the agents themselves), and writes per-cell H2 rates (aware %, fair %)
alongside a full per-text classification table.

Text is deduplicated before hitting the judge (h2_judge's on-disk
cache keyed by exact text) -- agents frequently repeat near-identical
reasoning, so this is much cheaper than 192 x up to 20 agents x 15
rounds of raw calls would suggest.

Usage:
    python3 run_h2_full.py --out reports/h2_full_results.md --csv reports/raw_exports/h2_full_by_cell.csv
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from analyze_main_study import DEFAULT_ROOT, ENVIRONMENTS, POPULATIONS, TOPOLOGIES, SANCTIONING
from h2_judge import classify_batch, DEFAULT_CACHE_PATH

JOB_NAME = "h2_full_classification"


def _report(cmd: str, *args: str) -> None:
    import subprocess
    subprocess.run(["python3", str(Path(__file__).resolve().parent / "update_progress.py"),
                    JOB_NAME, cmd, *args], check=False)

ACTION_TEXT_FIELDS = {
    "commons": ("commons_contribute", "commons_extract"),
    "triage": ("triage_send", "triage_keep"),
}


def extract_texts(export_path: Path, actions: tuple[str, ...]) -> list[tuple[str, str]]:
    """Returns [(agent_id, reason_text), ...] for every matching event."""
    d = json.loads(export_path.read_text())
    out = []
    for e in d.get("events", []):
        if e["action"] not in actions:
            continue
        try:
            params = json.loads(e["params_json"])
        except (json.JSONDecodeError, TypeError):
            continue
        reason = params.get("reason", "").strip()
        if reason:
            out.append((e["agent_id"], reason))
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--out", default="reports/h2_full_results.md")
    parser.add_argument("--csv", default="reports/raw_exports/h2_full_by_cell.csv")
    parser.add_argument("--cache", default=DEFAULT_CACHE_PATH)
    parser.add_argument("--max-parallel", type=int, default=4,
                        help="e-INFRA CZ's known constraint: max_parallel_requests=4 per key")
    parser.add_argument("--api-key-env", default="LIGHTWEIGHT_API_KEY",
                        help="h2_judge.py is routed through e-INFRA CZ (free) by default -- "
                             "source ~/.e_infra_env and export LIGHTWEIGHT_API_KEY=$OPENAI_API_KEY first")
    args = parser.parse_args()

    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        print(f"set {args.api_key_env} in the environment (source ~/.e_infra_env)", file=sys.stderr)
        return 1

    # Pass 1: collect every (cell, text) pair across all 192 exports.
    cell_texts: dict[tuple, list[tuple[str, str]]] = {}
    all_texts: set[str] = set()
    n_files = 0
    for environment, actions in ACTION_TEXT_FIELDS.items():
        for population in POPULATIONS:
            for topology in TOPOLOGIES:
                for sanctioning in SANCTIONING:
                    cell_dir = args.root / environment / f"{population}__{topology}__sanctioning_{sanctioning}"
                    if not cell_dir.is_dir():
                        continue
                    key = (environment, population, topology, sanctioning)
                    for rep_path in sorted(cell_dir.glob("rep*.json")):
                        n_files += 1
                        pairs = extract_texts(rep_path, actions)
                        cell_texts.setdefault(key, []).extend(pairs)
                        all_texts.update(t for _, t in pairs)

    n_total_texts = sum(len(v) for v in cell_texts.values())
    print(f"scanned {n_files} run exports, {n_total_texts} agent-round texts, "
         f"{len(all_texts)} unique strings to classify", file=sys.stderr)

    # Pass 2: classify every unique text once (cached), chunked so the
    # dashboard gets progress updates -- a single classify_batch call
    # over all ~46k texts would otherwise report nothing until it's
    # entirely done, hours later.
    CHUNK = 500
    all_sorted = sorted(all_texts)
    _report("init", str(len(all_sorted)), "H2 full-dataset classification (46k unique texts)")
    labels: dict[str, dict] = {}
    for i in range(0, len(all_sorted), CHUNK):
        chunk = all_sorted[i:i + CHUNK]
        chunk_labels = classify_batch(chunk, api_key, max_parallel=args.max_parallel, cache_path=args.cache)
        labels.update(chunk_labels)
        done_so_far = min(i + CHUNK, len(all_sorted))
        _report("done_count", str(done_so_far))
        _report("current", f"{done_so_far}/{len(all_sorted)} unique texts classified")
        print(f"  ...{done_so_far}/{len(all_sorted)} classified", file=sys.stderr)
    print(f"classified {len(labels)}/{len(all_texts)} unique texts (rest failed after retries)", file=sys.stderr)

    # Pass 3: aggregate per cell.
    import csv
    import statistics

    rows = []
    for (environment, population, topology, sanctioning), pairs in sorted(cell_texts.items()):
        classified = [labels[t] for _, t in pairs if t in labels]
        n = len(classified)
        aware_rate = statistics.mean(1.0 if c["aware"] else 0.0 for c in classified) if n else None
        fair_rate = statistics.mean(1.0 if c["fair"] else 0.0 for c in classified) if n else None
        rows.append({
            "environment": environment, "population": population, "topology": topology,
            "sanctioning": sanctioning, "n_texts": n, "n_classified": len(classified),
            "aware_rate": aware_rate, "fair_rate": fair_rate,
        })

    Path(args.csv).parent.mkdir(parents=True, exist_ok=True)
    with open(args.csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["environment", "population", "topology", "sanctioning",
                                          "n_texts", "n_classified", "aware_rate", "fair_rate"])
        w.writeheader()
        w.writerows(rows)
    print(f"written {args.csv} ({len(rows)} cells)", file=sys.stderr)

    lines = ["# H2 self-report classification, full 192-run dataset", "",
            f"LLM-judge (deepseek-v4-flash, same model as the agents) over every ",
            f"agent-round's free-text reason. {len(all_texts)} unique texts classified ",
            f"(deduplicated from {sum(len(v) for v in cell_texts.values())} total agent-round texts).",
            "", "| Env | Population | Topology | Sanctioning | n | Aware % | Fair % |",
            "|---|---|---|---|---|---|---|"]
    for row in rows:
        aware_str = f"{100*row['aware_rate']:.1f}%" if row["aware_rate"] is not None else "n/a"
        fair_str = f"{100*row['fair_rate']:.1f}%" if row["fair_rate"] is not None else "n/a"
        lines.append(f"| {row['environment']} | {row['population']} | {row['topology']} | "
                    f"{row['sanctioning']} | {row['n_classified']}/{row['n_texts']} | {aware_str} | {fair_str} |")
    Path(args.out).write_text("\n".join(lines) + "\n")
    print(f"written {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
