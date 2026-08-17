#!/usr/bin/env python3
"""Does awareness-of-position language actually correlate with an
agent's own structural advantage (degree, net payoff)? The pilot-stage
manuscript claims no ("advantaged and disadvantaged agents talk about
reciprocity at similar rates") -- this checks it for real, at full
scale, using h2_per_agent.csv joined against each agent's own degree
and net payoff from the raw exports.

Usage:
    python3 h2_vs_structure.py   # defaults to h2_per_agent.csv next to this script,
                                  # falling back to reports/raw_exports/ if not found
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from analyze_main_study import DEFAULT_ROOT, ENVIRONMENTS, pearson_r, fisher_ci, load


def agent_degree_payoff(root: Path, environment: str, population: str, topology: str,
                        sanctioning: str, rep: str, payoff_table: str) -> dict[str, tuple[int, float]]:
    rep_path = root / environment / f"{population}__{topology}__sanctioning_{sanctioning}" / f"{rep}.json"
    if not rep_path.is_file():
        return {}
    d = load(rep_path)
    payoff_rows = d.get(payoff_table, [])
    agent_ids = sorted(set(r["agent_id"] for r in payoff_rows))
    net_payoff = {a: 0.0 for a in agent_ids}
    for r in payoff_rows:
        net_payoff[r["agent_id"]] += r["net"]
    vis = [r for r in d.get("visibility", []) if r["agent_id"] in agent_ids]
    edges = set(tuple(sorted((r["agent_id"], r["visible_agent_id"]))) for r in vis
                if r["visible_agent_id"] in agent_ids)
    degree = {a: 0 for a in agent_ids}
    for a, b in edges:
        degree[a] += 1
        degree[b] += 1
    return {a: (degree[a], net_payoff[a]) for a in agent_ids}


def main() -> int:
    parser = argparse.ArgumentParser()
    _here = Path(__file__).resolve().parent
    _default_h2_csv = _here / "h2_per_agent.csv"
    if not _default_h2_csv.is_file():
        _default_h2_csv = _here / "reports" / "raw_exports" / "h2_per_agent.csv"
    parser.add_argument("--h2-csv", default=str(_default_h2_csv))
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()

    h2_rows = list(csv.DictReader(open(args.h2_csv)))
    cache: dict[tuple, dict] = {}
    joined = []
    for row in h2_rows:
        key = (row["environment"], row["population"], row["topology"], row["sanctioning"], row["rep"])
        if key not in cache:
            payoff_table = ENVIRONMENTS[row["environment"]]["payoff_table"]
            cache[key] = agent_degree_payoff(args.root, *key, payoff_table)
        dp = cache[key].get(row["agent_id"])
        if dp is None:
            continue
        degree, net_payoff = dp
        joined.append({**row, "degree": degree, "net_payoff": net_payoff})

    print(f"{len(joined)} agent-replicate rows joined with degree/payoff\n")
    for environment in ENVIRONMENTS:
        for population in ["uniform_fair", "mixed"]:
            rows = [r for r in joined if r["environment"] == environment and r["population"] == population]
            if len(rows) < 10:
                continue
            aware = [float(r["judge_aware_rate"]) for r in rows]
            fair = [float(r["judge_fair_rate"]) for r in rows]
            degree = [r["degree"] for r in rows]
            payoff = [r["net_payoff"] for r in rows]
            r_aware_degree = pearson_r(aware, degree)
            r_aware_payoff = pearson_r(aware, payoff)
            r_fair_degree = pearson_r(fair, degree)
            n = len(rows)
            print(f"{environment}/{population} (n={n} agent-replicates):")
            if r_aware_degree is not None:
                lo, hi = fisher_ci(r_aware_degree, n)
                print(f"  aware_rate vs degree:     r={r_aware_degree:+.3f} [{lo:+.3f}, {hi:+.3f}]")
            if r_aware_payoff is not None:
                lo, hi = fisher_ci(r_aware_payoff, n)
                print(f"  aware_rate vs net_payoff: r={r_aware_payoff:+.3f} [{lo:+.3f}, {hi:+.3f}]")
            if r_fair_degree is not None:
                lo, hi = fisher_ci(r_fair_degree, n)
                print(f"  fair_rate vs degree:      r={r_fair_degree:+.3f} [{lo:+.3f}, {hi:+.3f}]")
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
