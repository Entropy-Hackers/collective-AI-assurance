#!/usr/bin/env python3
"""Statistical analysis built directly on the main study's raw exports,
pure stdlib (no numpy/scipy/statsmodels -- matches this repo's
established convention, see visualize_topology.py's own note).

Three pieces:

1. Per-replicate long-format table (one row per run: environment,
   population, topology, sanctioning, rep id, within-replicate r
   [n=20], Gini, compliance rate). Building block for the other two.

2. Balanced fixed-effects variance decomposition (closed-form
   sum-of-squares over cell/marginal means -- exact for a balanced
   design, no design matrix or matrix inversion needed since every
   cell has the same replicate count). This is an explicit
   approximation of the manuscript's stated mixed-effects model
   (`outcome ~ alignment * topology * institution + (1|seed)`): the
   `(1|seed)` random effect is not fit as a variance component here,
   it is simply the within-cell residual across replicates. Documented
   as such, not presented as a true REML fit.

3. H3 equivalence test (does sanctioning move Gini by more than a
   pre-specified practical margin): bootstrap over replicates rather
   than parametric TOST (no scipy.stats.t available) -- resample
   replicates within each sanctioning arm with replacement, compute
   delta-Gini per bootstrap draw, take the percentile CI, and check
   whether it sits entirely inside +/-MARGIN. Confirmatory scope is
   pinned to the two cells where H1's degree-payoff signal is
   strongest and sanctioning's degree-targeting is confirmed real
   (uniform_fair x scale_free, both environments); the other ten cells
   are reported descriptively, not part of the confirmatory claim --
   same asymmetric scope H1 itself uses.

4. Baseline-vs-real permutation test: same resampling technique reused
   for a different comparison (real LLM r vs. non-LLM baseline r) --
   shuffle the real/baseline labels across the pooled replicate-level
   values, recompute the difference in means under each shuffle, and
   compare the observed difference to that null distribution.

Usage:
    python3 stats_main_study.py replicates --out replicate_metrics.csv
    python3 stats_main_study.py anova --out variance_decomposition.md
    python3 stats_main_study.py h3 --out h3_equivalence.md
    python3 stats_main_study.py baseline --real-root <dir> --baseline-root <dir> --out baseline_test.md
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import statistics
from pathlib import Path

from analyze_main_study import (
    DEFAULT_ROOT, ENVIRONMENTS, POPULATIONS, TOPOLOGIES, SANCTIONING,
    gini, pearson_r, load,
)

MARGIN = 0.05  # H3 practical-equivalence margin on delta-Gini
N_BOOT = 10000
CI_LEVEL = 0.95  # matches a two-one-sided-test at alpha=0.05 in spirit


# ------------------------------------------------------------- (1) ---

def replicate_row(rep_path: Path, payoff_table: str, compliant_action: str) -> dict | None:
    d = load(rep_path)
    payoff_rows = d.get(payoff_table, [])
    if not payoff_rows:
        return None
    agent_ids = sorted(set(r["agent_id"] for r in payoff_rows))
    net_payoff = {a: 0.0 for a in agent_ids}
    compliance_num = compliance_den = 0
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

    degrees = [degree[a] for a in agent_ids]
    payoffs = [net_payoff[a] for a in agent_ids]
    return {
        "r": pearson_r(degrees, payoffs),
        "gini": gini(payoffs),
        "compliance_rate": compliance_num / compliance_den if compliance_den else None,
        "n_agents": len(agent_ids),
    }


def all_replicate_rows(root: Path) -> list[dict]:
    rows = []
    for environment, cfg in ENVIRONMENTS.items():
        for population in POPULATIONS:
            for topology in TOPOLOGIES:
                for sanctioning in SANCTIONING:
                    cell_dir = root / environment / f"{population}__{topology}__sanctioning_{sanctioning}"
                    if not cell_dir.is_dir():
                        continue
                    for rep_path in sorted(cell_dir.glob("rep*.json")):
                        m = replicate_row(rep_path, cfg["payoff_table"], cfg["compliant_action"])
                        if m is None:
                            continue
                        rows.append({
                            "environment": environment, "population": population,
                            "topology": topology, "sanctioning": sanctioning,
                            "rep": rep_path.stem, **m,
                        })
    return rows


BASELINE_STRATEGIES_BY_ENV = {"commons": ["fixed", "random"], "triage": ["fixed", "random", "reciprocal"]}


def all_baseline_replicate_rows(root: Path) -> list[dict]:
    """Same shape as all_replicate_rows(), but for run_baseline_study.sh's
    output layout: root/environment/{strategy}__{topology}__sanctioning_{s}/
    -- strategy instead of population as the first path component,
    since baseline runs don't have a persona population."""
    rows = []
    for environment, cfg in ENVIRONMENTS.items():
        for strategy in BASELINE_STRATEGIES_BY_ENV[environment]:
            for topology in TOPOLOGIES:
                for sanctioning in SANCTIONING:
                    cell_dir = root / environment / f"{strategy}__{topology}__sanctioning_{sanctioning}"
                    if not cell_dir.is_dir():
                        continue
                    for rep_path in sorted(cell_dir.glob("rep*.json")):
                        m = replicate_row(rep_path, cfg["payoff_table"], cfg["compliant_action"])
                        if m is None:
                            continue
                        rows.append({
                            "environment": environment, "strategy": strategy,
                            "topology": topology, "sanctioning": sanctioning,
                            "rep": rep_path.stem, **m,
                        })
    return rows


# ------------------------------------------------------------- (2) ---

def _mean(vals: list[float]) -> float:
    return statistics.mean(vals) if vals else 0.0


def balanced_anova(rows: list[dict], environment: str, metric: str) -> dict:
    """Closed-form 3-way balanced fixed-effects sum-of-squares
    decomposition (population x topology x sanctioning) for one
    environment. Requires every cell to have the same replicate count
    (checked; raises if not balanced).

    Factor levels are derived from the data actually present for this
    metric, not assumed from the global constants -- `r` is
    structurally undefined for fully_connected topology (zero degree
    variance by construction), so that level drops out of the
    topology factor entirely for metric="r" (a 2x2x2 design), while
    metric="gini" keeps all 3 topology levels (2x3x2)."""
    data = [r for r in rows if r["environment"] == environment and r[metric] is not None]
    by_cell: dict[tuple, list[float]] = {}
    for r in data:
        key = (r["population"], r["topology"], r["sanctioning"])
        by_cell.setdefault(key, []).append(r[metric])

    counts = {len(v) for v in by_cell.values()}
    if len(counts) != 1:
        raise ValueError(f"unbalanced design for {environment}/{metric}: cell sizes {sorted(counts)}")
    n = counts.pop()

    all_vals = [v for vals in by_cell.values() for v in vals]
    grand_mean = _mean(all_vals)
    ss_total = sum((v - grand_mean) ** 2 for v in all_vals)

    def marginal_mean(factor_idx: int, level) -> float:
        vals = [v for key, vals in by_cell.items() for v in vals if key[factor_idx] == level]
        return _mean(vals)

    def cell_mean(key: tuple) -> float:
        return _mean(by_cell[key])

    pops = sorted({k[0] for k in by_cell})
    topos = sorted({k[1] for k in by_cell})
    sancs = sorted({k[2] for k in by_cell})
    expected_cells = len(pops) * len(topos) * len(sancs)
    if len(by_cell) != expected_cells:
        raise ValueError(f"incomplete factorial for {environment}/{metric}: "
                         f"{len(by_cell)} cells present, {expected_cells} expected "
                         f"from levels pop={pops} topo={topos} sanc={sancs}")
    n_pop, n_topo, n_sanc = len(pops), len(topos), len(sancs)

    ss_pop = n_topo * n_sanc * n * sum((marginal_mean(0, p) - grand_mean) ** 2 for p in pops)
    ss_topo = n_pop * n_sanc * n * sum((marginal_mean(1, t) - grand_mean) ** 2 for t in topos)
    ss_sanc = n_pop * n_topo * n * sum((marginal_mean(2, s) - grand_mean) ** 2 for s in sancs)

    def two_way_mean(i, li, j, lj):
        vals = [v for key, vals in by_cell.items() for v in vals if key[i] == li and key[j] == lj]
        return _mean(vals)

    ss_pop_topo = n_sanc * n * sum(
        (two_way_mean(0, p, 1, t) - marginal_mean(0, p) - marginal_mean(1, t) + grand_mean) ** 2
        for p in pops for t in topos)
    ss_pop_sanc = n_topo * n * sum(
        (two_way_mean(0, p, 2, s) - marginal_mean(0, p) - marginal_mean(2, s) + grand_mean) ** 2
        for p in pops for s in sancs)
    ss_topo_sanc = n_pop * n * sum(
        (two_way_mean(1, t, 2, s) - marginal_mean(1, t) - marginal_mean(2, s) + grand_mean) ** 2
        for t in topos for s in sancs)

    ss_three_way = n * sum(
        (cell_mean((p, t, s)) - two_way_mean(0, p, 1, t) - two_way_mean(0, p, 2, s) - two_way_mean(1, t, 2, s)
         + marginal_mean(0, p) + marginal_mean(1, t) + marginal_mean(2, s) - grand_mean) ** 2
        for p in pops for t in topos for s in sancs)

    ss_residual = sum(sum((v - cell_mean(key)) ** 2 for v in vals) for key, vals in by_cell.items())

    ss_explained = ss_pop + ss_topo + ss_sanc + ss_pop_topo + ss_pop_sanc + ss_topo_sanc + ss_three_way
    ss_check = ss_explained + ss_residual
    assert abs(ss_check - ss_total) < 1e-6 * max(ss_total, 1.0), \
        f"SS decomposition doesn't sum to total: {ss_check} vs {ss_total}"

    def pct(ss):
        return 100 * ss / ss_total if ss_total > 0 else 0.0

    return {
        "environment": environment, "metric": metric, "n_per_cell": n, "grand_mean": grand_mean,
        "ss_total": ss_total,
        "population_pct": pct(ss_pop), "topology_pct": pct(ss_topo), "sanctioning_pct": pct(ss_sanc),
        "population_x_topology_pct": pct(ss_pop_topo), "population_x_sanctioning_pct": pct(ss_pop_sanc),
        "topology_x_sanctioning_pct": pct(ss_topo_sanc), "three_way_pct": pct(ss_three_way),
        "residual_pct": pct(ss_residual),
    }


# ------------------------------------------------------------- (3) ---

def bootstrap_delta_ci(off_vals: list[float], on_vals: list[float], n_boot: int = N_BOOT,
                       ci_level: float = CI_LEVEL, seed: int = 1) -> tuple[float, float, float]:
    """Bootstrap CI on mean(on) - mean(off), resampling each arm
    independently with replacement. Returns (observed_delta, lo, hi)."""
    rng = random.Random(seed)
    observed = _mean(on_vals) - _mean(off_vals)
    deltas = []
    for _ in range(n_boot):
        off_s = [rng.choice(off_vals) for _ in off_vals]
        on_s = [rng.choice(on_vals) for _ in on_vals]
        deltas.append(_mean(on_s) - _mean(off_s))
    deltas.sort()
    alpha = 1 - ci_level
    lo_idx = int((alpha / 2) * n_boot)
    hi_idx = int((1 - alpha / 2) * n_boot) - 1
    return observed, deltas[lo_idx], deltas[hi_idx]


def h3_equivalence(rows: list[dict]) -> list[dict]:
    """Confirmatory: uniform_fair x scale_free, both environments.
    Descriptive: the other 10 cells per environment (reported, not
    part of the confirmatory equivalence claim)."""
    results = []
    for environment in ENVIRONMENTS:
        for population in POPULATIONS:
            for topology in TOPOLOGIES:
                off_vals = [r["gini"] for r in rows if r["environment"] == environment
                           and r["population"] == population and r["topology"] == topology
                           and r["sanctioning"] == "off" and r["gini"] is not None]
                on_vals = [r["gini"] for r in rows if r["environment"] == environment
                          and r["population"] == population and r["topology"] == topology
                          and r["sanctioning"] == "on" and r["gini"] is not None]
                if not off_vals or not on_vals:
                    continue
                observed, lo, hi = bootstrap_delta_ci(off_vals, on_vals)
                confirmatory = (population == "uniform_fair" and topology == "scale_free")
                equivalent = (lo > -MARGIN) and (hi < MARGIN)
                results.append({
                    "environment": environment, "population": population, "topology": topology,
                    "confirmatory": confirmatory, "n_off": len(off_vals), "n_on": len(on_vals),
                    "delta_gini": observed, "ci_lo": lo, "ci_hi": hi,
                    "equivalent_within_margin": equivalent,
                })
    return results


# ------------------------------------------------------------- (4) ---

def permutation_test(real_vals: list[float], baseline_vals: list[float], n_perm: int = N_BOOT,
                     seed: int = 1) -> dict:
    """Two-sided permutation test on mean(real) - mean(baseline):
    shuffle the pooled real+baseline values into two groups of the
    original sizes, many times, and see how extreme the observed
    difference is relative to that null distribution."""
    rng = random.Random(seed)
    observed = _mean(real_vals) - _mean(baseline_vals)
    pooled = real_vals + baseline_vals
    n_real = len(real_vals)
    count_extreme = 0
    for _ in range(n_perm):
        shuffled = pooled[:]
        rng.shuffle(shuffled)
        diff = _mean(shuffled[:n_real]) - _mean(shuffled[n_real:])
        if abs(diff) >= abs(observed):
            count_extreme += 1
    p_value = count_extreme / n_perm
    return {"observed_diff": observed, "p_value": p_value, "n_real": n_real, "n_baseline": len(baseline_vals)}


# --------------------------------------------------------------- CLI --

def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("replicates")
    p1.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    p1.add_argument("--out", default="replicate_metrics.csv")

    p2 = sub.add_parser("anova")
    p2.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    p2.add_argument("--metric", choices=["r", "gini"], default="r")
    p2.add_argument("--out", default="variance_decomposition.md")

    p3 = sub.add_parser("h3")
    p3.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    p3.add_argument("--out", default="h3_equivalence.md")

    p4 = sub.add_parser("baseline")
    p4.add_argument("--real-root", type=Path, default=DEFAULT_ROOT)
    p4.add_argument("--baseline-root", type=Path, required=True)
    p4.add_argument("--out", default="baseline_test.md")

    args = parser.parse_args()

    if args.cmd == "replicates":
        rows = all_replicate_rows(args.root)
        fieldnames = ["environment", "population", "topology", "sanctioning", "rep", "r", "gini",
                     "compliance_rate", "n_agents"]
        with open(args.out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(rows)
        print(f"written {args.out} ({len(rows)} replicate rows)")

    elif args.cmd == "anova":
        rows = all_replicate_rows(args.root)
        # Cap every cell to its first 8 replicates -- 3 cells now have
        # 20 (see variance_and_h3_results.md for why), which breaks the
        # balanced-design requirement. The extra replicates were run to
        # resolve specific ambiguous cells (H1/H3), not to grow the
        # overall factorial design, so ANOVA stays on the original
        # 8-reps-per-cell standard.
        by_cell: dict[tuple, list[dict]] = {}
        for r in rows:
            key = (r["environment"], r["population"], r["topology"], r["sanctioning"])
            by_cell.setdefault(key, []).append(r)
        rows = [r for reps in by_cell.values()
                for r in sorted(reps, key=lambda x: int(x["rep"].removeprefix("rep")))[:8]]
        lines = [f"# Variance decomposition ({args.metric}), balanced fixed-effects ANOVA", "",
                "Closed-form sum-of-squares over cell/marginal means (balanced design,",
                "8 replicates/cell -- capped there even for the 3 cells with 20, to keep",
                "this specific analysis balanced) -- an explicit approximation of the",
                "manuscript's `outcome ~ alignment * topology * institution + (1|seed)`",
                "mixed-effects model: the `(1|seed)` random effect is the within-cell",
                "residual here, not a fitted variance component. Fit separately per",
                "environment, matching the manuscript's stated analysis model.", ""]
        for environment in ENVIRONMENTS:
            res = balanced_anova(rows, environment, args.metric)
            lines.append(f"## {environment}")
            lines.append("")
            lines.append(f"n = {res['n_per_cell']}/cell, grand mean = {res['grand_mean']:.4f}, "
                         f"SS total = {res['ss_total']:.4f}")
            lines.append("")
            lines.append("| Source | % variance |")
            lines.append("|---|---|")
            lines.append(f"| population (alignment) | {res['population_pct']:.1f}% |")
            lines.append(f"| topology | {res['topology_pct']:.1f}% |")
            lines.append(f"| sanctioning (institution) | {res['sanctioning_pct']:.1f}% |")
            lines.append(f"| population x topology | {res['population_x_topology_pct']:.1f}% |")
            lines.append(f"| population x sanctioning | {res['population_x_sanctioning_pct']:.1f}% |")
            lines.append(f"| topology x sanctioning | {res['topology_x_sanctioning_pct']:.1f}% |")
            lines.append(f"| three-way interaction | {res['three_way_pct']:.1f}% |")
            lines.append(f"| residual (within-cell, ~ (1\\|seed)) | {res['residual_pct']:.1f}% |")
            lines.append("")
        Path(args.out).write_text("\n".join(lines) + "\n")
        print(f"written {args.out}")

    elif args.cmd == "h3":
        rows = all_replicate_rows(args.root)
        results = h3_equivalence(rows)
        lines = ["# H3: institutional sanctioning does not reduce Gini inequality", "",
                "**H3 (confirmatory, uniform_fair x scale_free, both environments):**",
                "institutional peer sanctioning does not reduce the Gini inequality of",
                "final payoffs -- even in the condition where sanctioning demonstrably",
                f"targets high-degree agents disproportionately -- i.e. the effect of",
                f"sanctioning on/off on Gini is, within a pre-specified practical",
                f"equivalence margin (+/-{MARGIN}), statistically indistinguishable from",
                "zero, not merely \"not significant\". The other ten cells (per",
                "environment) are reported descriptively, not part of the confirmatory",
                "claim -- the same asymmetric scope H1 itself uses.", "",
                f"Bootstrap CI ({int(CI_LEVEL*100)}%, {N_BOOT} resamples) on "
                "mean(Gini | sanctioning=on) - mean(Gini | sanctioning=off).", "",
                "| Env | Population | Topology | Confirmatory | n off/on | delta Gini | CI | Equivalent (within margin)? |",
                "|---|---|---|---|---|---|---|---|"]
        for r in results:
            conf = "**yes**" if r["confirmatory"] else "descriptive"
            equiv = "**yes**" if r["equivalent_within_margin"] else "no"
            lines.append(f"| {r['environment']} | {r['population']} | {r['topology']} | {conf} | "
                        f"{r['n_off']}/{r['n_on']} | {r['delta_gini']:+.4f} | "
                        f"[{r['ci_lo']:+.4f}, {r['ci_hi']:+.4f}] | {equiv} |")
        Path(args.out).write_text("\n".join(lines) + "\n")
        print(f"written {args.out}")

    elif args.cmd == "baseline":
        real_rows = all_replicate_rows(args.real_root)
        baseline_rows = all_baseline_replicate_rows(args.baseline_root)
        print(f"real rows: {len(real_rows)}, baseline rows: {len(baseline_rows)}")
        lines = ["# Real LLM (uniform_fair) vs. non-LLM baseline: permutation test", "",
                "Is H1's degree-payoff correlation close to mechanically guaranteed by ",
                "the payoff structure once behaviour is uniform, or specific to real LLM ",
                "agent behaviour? Two-sided permutation test (10,000 shuffles) on the ",
                "difference in mean within-replicate r between the real uniform_fair LLM ",
                "runs and each non-LLM strategy, matched by environment/topology/",
                "sanctioning (8 replicates each side).", "",
                "| Env | Topology | Sanctioning | Strategy | real r (mean) | baseline r (mean) | diff | p |",
                "|---|---|---|---|---|---|---|---|"]
        for environment in ENVIRONMENTS:
            for topology in TOPOLOGIES:
                for sanctioning in SANCTIONING:
                    real_vals = [r["r"] for r in real_rows if r["environment"] == environment
                                and r["population"] == "uniform_fair" and r["topology"] == topology
                                and r["sanctioning"] == sanctioning and r["r"] is not None]
                    if not real_vals:
                        continue
                    for strategy in BASELINE_STRATEGIES_BY_ENV[environment]:
                        baseline_vals = [r["r"] for r in baseline_rows if r["environment"] == environment
                                         and r["strategy"] == strategy and r["topology"] == topology
                                         and r["sanctioning"] == sanctioning and r["r"] is not None]
                        if not baseline_vals:
                            continue
                        res = permutation_test(real_vals, baseline_vals)
                        lines.append(f"| {environment} | {topology} | {sanctioning} | {strategy} | "
                                    f"{_mean(real_vals):.3f} | {_mean(baseline_vals):.3f} | "
                                    f"{res['observed_diff']:+.4f} | {res['p_value']:.4f} |")
        Path(args.out).write_text("\n".join(lines) + "\n")
        print(f"written {args.out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
