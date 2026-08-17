#!/usr/bin/env python3
"""Aggregate the 192-run main study's raw exports into the paper's
core H1 metrics (degree--payoff correlation, Gini, compliance rate)
and the institutional-sanctioning metrics, pooled per cell (population
x topology x sanctioning, per environment).

This computes real numbers from tools/reports/raw_exports/main_study/
-- it does not edit the manuscript. Output is a CSV (one row per cell)
and a markdown summary table, meant to be dropped into results-paper/
so the actual paper text can be written from real numbers in Overleaf.

Scope: H1 (degree-payoff r + CI, Gini + CI, compliance rate) and
institutional sanctioning (sanction count, mean degree of sanctioned
agents vs population mean, Gini with/without sanctioning). NOT
included here: H2 LLM-judge classification (a separate, much larger
batch of judge-model calls over every agent-round's free text) and the
non-LLM baseline comparison (requires separate baseline-strategy runs)
and the mixed-effects variance decomposition (needs a stats package)
-- those remain open, flagged explicitly in the output rather than
silently omitted.

Usage:
    python3 analyze_main_study.py --out results_data.csv --md results_summary.md
    python3 analyze_main_study.py --root /path/to/commons+triage/parent --out ... --md ...

By default looks for `commons/` and `triage/` next to this script
first (the layout used in results-paper/raw_data/'s copy of this
script); if not found there, falls back to this repo's own
tools/reports/raw_exports/main_study/. Pass --root explicitly to
override either way.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if (_HERE / "commons").is_dir() and (_HERE / "triage").is_dir():
    DEFAULT_ROOT = _HERE
else:
    DEFAULT_ROOT = _HERE / "reports" / "raw_exports" / "main_study"

ENVIRONMENTS = {
    "commons": {"payoff_table": "commons_payoffs", "compliant_action": "contribute"},
    "triage": {"payoff_table": "triage_outcomes", "compliant_action": "send"},
}
POPULATIONS = ["uniform_fair", "mixed"]
TOPOLOGIES = ["fully_connected", "clustered", "scale_free"]
SANCTIONING = ["off", "on"]


def gini(values: list[float]) -> float:
    """0 = perfect equality, approaches 1 = maximal inequality. Same
    definition as analyze.py's gini(), reused here for consistency
    with the pilot-stage numbers already reported."""
    if not values:
        return 0.0
    shift = -min(values) if min(values) < 0 else 0
    shifted = sorted(v + shift for v in values)
    n = len(shifted)
    total = sum(shifted)
    if total == 0:
        return 0.0
    cum = sum((i + 1) * v for i, v in enumerate(shifted))
    return (2 * cum) / (n * total) - (n + 1) / n


def pearson_r(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def fisher_ci(r: float, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """95% CI for a Pearson r via the Fisher z-transform."""
    r = max(min(r, 0.999999), -0.999999)
    z = 0.5 * math.log((1 + r) / (1 - r))
    se = 1 / math.sqrt(n - 3) if n > 3 else float("inf")
    zcrit = 1.959963984540054  # z for 95%
    lo_z, hi_z = z - zcrit * se, z + zcrit * se
    lo = (math.exp(2 * lo_z) - 1) / (math.exp(2 * lo_z) + 1)
    hi = (math.exp(2 * hi_z) - 1) / (math.exp(2 * hi_z) + 1)
    return lo, hi


def mean_ci(values: list[float], alpha: float = 0.05) -> tuple[float, float, float]:
    """Mean and a normal-approx 95% CI across replicate-level values
    (e.g. one Gini per replicate). Returns (mean, lo, hi); if fewer
    than 2 values, lo/hi equal the mean (CI undefined)."""
    if not values:
        return 0.0, 0.0, 0.0
    m = statistics.mean(values)
    if len(values) < 2:
        return m, m, m
    sd = statistics.stdev(values)
    se = sd / math.sqrt(len(values))
    zcrit = 1.959963984540054
    return m, m - zcrit * se, m + zcrit * se


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def analyze_cell(reps: list[Path], payoff_table: str, compliant_action: str) -> dict:
    pooled_degree, pooled_payoff = [], []
    gini_per_rep = []
    compliance_num = compliance_den = 0
    sanction_counts = []
    sanctioned_degree_ratios = []  # degree of sanctioned agent / cell population mean degree
    n_reps = 0

    for rep_path in reps:
        d = load(rep_path)
        payoff_rows = d.get(payoff_table, [])
        if not payoff_rows:
            continue
        n_reps += 1
        agent_ids = sorted(set(r["agent_id"] for r in payoff_rows))
        net_payoff = {a: 0.0 for a in agent_ids}
        for r in payoff_rows:
            net_payoff[r["agent_id"]] += r["net"]
            compliance_den += 1
            if r["action"] == compliant_action:
                compliance_num += 1

        vis = [r for r in d.get("visibility", []) if r["agent_id"] in agent_ids]
        edges = set(tuple(sorted((r["agent_id"], r["visible_agent_id"]))) for r in vis
                    if r["visible_agent_id"] in agent_ids)
        degree = {a: 0 for a in agent_ids}
        for a, b in edges:
            degree[a] += 1
            degree[b] += 1

        for a in agent_ids:
            pooled_degree.append(degree[a])
            pooled_payoff.append(net_payoff[a])
        gini_per_rep.append(gini(list(net_payoff.values())))

        sanctions = [s for s in d.get("sanctions", []) if s["target_agent_id"] in agent_ids]
        sanction_counts.append(len(sanctions))
        pop_mean_degree = statistics.mean(degree.values()) if degree else 0
        if pop_mean_degree > 0:
            for s in sanctions:
                deg = degree.get(s["target_agent_id"])
                if deg is not None:
                    sanctioned_degree_ratios.append(deg / pop_mean_degree)

    if n_reps == 0:
        return {"n_reps": 0}

    r = pearson_r(pooled_degree, pooled_payoff)
    n_pooled = len(pooled_degree)
    if r is not None:
        r_lo, r_hi = fisher_ci(r, n_pooled)
    else:
        r_lo = r_hi = None
    gini_mean, gini_lo, gini_hi = mean_ci(gini_per_rep)
    compliance_rate = compliance_num / compliance_den if compliance_den else None
    mean_sanctions = statistics.mean(sanction_counts) if sanction_counts else 0.0
    mean_sanctioned_ratio = statistics.mean(sanctioned_degree_ratios) if sanctioned_degree_ratios else None

    return {
        "n_reps": n_reps,
        "n_pooled_agents": n_pooled,
        "r": r, "r_lo": r_lo, "r_hi": r_hi,
        "gini_mean": gini_mean, "gini_lo": gini_lo, "gini_hi": gini_hi,
        "compliance_rate": compliance_rate,
        "mean_sanctions_per_run": mean_sanctions,
        "sanctioned_degree_ratio": mean_sanctioned_ratio,  # >1 means sanctioned agents skew higher-degree than population mean
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT,
                        help="directory containing commons/ and triage/ subfolders")
    parser.add_argument("--out", default="results_data.csv")
    parser.add_argument("--md", default="results_summary.md")
    args = parser.parse_args()

    rows = []
    for environment, cfg in ENVIRONMENTS.items():
        for population in POPULATIONS:
            for topology in TOPOLOGIES:
                for sanctioning in SANCTIONING:
                    cell_dir = args.root / environment / f"{population}__{topology}__sanctioning_{sanctioning}"
                    reps = sorted(cell_dir.glob("rep*.json")) if cell_dir.is_dir() else []
                    result = analyze_cell(reps, cfg["payoff_table"], cfg["compliant_action"])
                    rows.append({
                        "environment": environment,
                        "population": population,
                        "topology": topology,
                        "sanctioning": sanctioning,
                        "n_replicates_found": len(reps),
                        **result,
                    })

    fieldnames = ["environment", "population", "topology", "sanctioning", "n_replicates_found",
                  "n_reps", "n_pooled_agents", "r", "r_lo", "r_hi",
                  "gini_mean", "gini_lo", "gini_hi", "compliance_rate",
                  "mean_sanctions_per_run", "sanctioned_degree_ratio"]
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow(row)
    print(f"written {args.out} ({len(rows)} cells)")

    lines = ["# Main study -- real computed results (H1 + sanctioning)", "",
             "Computed directly from `tools/reports/raw_exports/main_study/` -- pooled",
             "degree-payoff Pearson r (95% CI via Fisher z, n = pooled agent-runs across",
             "all found replicates in the cell), mean Gini of final net payoff (95% CI",
             "across replicates), and compliance rate (fraction of persona-consistent",
             "actions, pooled across all agents/rounds in the cell).",
             "",
             "**Not included here** (real numbers, but need a separate pass): H2",
             "LLM-judge self-report classification; non-LLM baseline comparison;",
             "mixed-effects variance decomposition.",
             "", "| Env | Population | Topology | Sanctioning | n reps | r [95% CI] | Gini [95% CI] | Compliance | Mean sanctions/run | Sanctioned/mean degree |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for row in rows:
        if row.get("n_reps", 0) == 0:
            lines.append(f"| {row['environment']} | {row['population']} | {row['topology']} | "
                         f"{row['sanctioning']} | 0/{row['n_replicates_found']} | -- | -- | -- | -- | -- |")
            continue
        r_str = f"{row['r']:.3f} [{row['r_lo']:.3f}, {row['r_hi']:.3f}]" if row["r"] is not None else "n/a"
        gini_str = f"{row['gini_mean']:.3f} [{row['gini_lo']:.3f}, {row['gini_hi']:.3f}]"
        comp_str = f"{100*row['compliance_rate']:.1f}%" if row["compliance_rate"] is not None else "n/a"
        sanc_str = f"{row['mean_sanctions_per_run']:.1f}" if row["sanctioning"] == "on" else "--"
        sratio_str = (f"{row['sanctioned_degree_ratio']:.2f}x"
                     if row["sanctioning"] == "on" and row["sanctioned_degree_ratio"] is not None else "--")
        lines.append(f"| {row['environment']} | {row['population']} | {row['topology']} | "
                     f"{row['sanctioning']} | {row['n_reps']}/{row['n_replicates_found']} | {r_str} | "
                     f"{gini_str} | {comp_str} | {sanc_str} | {sratio_str} |")
    Path(args.md).write_text("\n".join(lines) + "\n")
    print(f"written {args.md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
