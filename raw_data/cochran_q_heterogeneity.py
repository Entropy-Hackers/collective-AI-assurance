#!/usr/bin/env python3
"""Cochran's Q / I^2 heterogeneity test across the cross-model
degree-payoff correlations (uniform_fair x scale_free, both
environments) -- are the differences between DeepSeek/Qwen/GLM-5.2/
Mistral-medium-3.5's r values real between-provider variance, or just
noise around one shared value? Only meaningful with 3+ models at real
replicate scale, which is why this wasn't run at 2 (DeepSeek + Qwen).

Method: standard meta-analytic heterogeneity test on Fisher-z
transformed correlations. Pure stdlib -- the chi-square survival
function (for Q's p-value) is implemented directly via the regularized
incomplete gamma function (series expansion for the lower part,
continued fraction for the upper -- the standard Numerical-Recipes
`gammp`/`gammq` approach), since no scipy.stats.chi2 is available.

    z_i = arctanh(r_i) = 0.5 * ln((1+r_i)/(1-r_i)),  v_i = 1/(n_i - 3)
    w_i = 1/v_i
    z_bar = sum(w_i * z_i) / sum(w_i)                (fixed-effect pooled estimate)
    Q = sum(w_i * (z_i - z_bar)^2),  df = k - 1
    I^2 = max(0, (Q - df) / Q) * 100%

Usage:
    python3 cochran_q_heterogeneity.py
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

from analyze_main_study import analyze_cell, ENVIRONMENTS

# Two possible layouts: this repo's tools/reports/raw_exports/ (model
# folders named glm/, mmed/) or results-paper/raw_data/'s flat layout
# (model folders named glm_crossmodel/, mistral_medium_crossmodel/,
# copied in with fuller names for clarity in the Overleaf handoff).
# Auto-detected the same way analyze_main_study.py's DEFAULT_ROOT is.
_HERE = Path(__file__).resolve().parent
if (_HERE / "commons").is_dir() and (_HERE / "triage").is_dir():
    _MAIN_STUDY_ROOT = _HERE
    MODELS = {
        "DeepSeek-v4-flash": _MAIN_STUDY_ROOT,
        "Qwen3.5-122b": _HERE / "qwen_crossmodel",
        "GLM-5.2": _HERE / "glm_crossmodel",
        "Mistral-medium-3.5": _HERE / "mistral_medium_crossmodel",
    }
else:
    _ROOT = _HERE / "reports" / "raw_exports"
    _MAIN_STUDY_ROOT = _ROOT / "main_study"
    MODELS = {
        "DeepSeek-v4-flash": _MAIN_STUDY_ROOT,
        "Qwen3.5-122b": _ROOT / "qwen_crossmodel",
        "GLM-5.2": _ROOT / "glm",
        "Mistral-medium-3.5": _ROOT / "mmed",
    }


def _log_gamma(x: float) -> float:
    # Lanczos approximation, standard coefficients.
    g = 7
    c = [0.99999999999980993, 676.5203681218851, -1259.1392167224028,
         771.32342877765313, -176.61502916214059, 12.507343278686905,
         -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7]
    if x < 0.5:
        return math.log(math.pi / math.sin(math.pi * x)) - _log_gamma(1 - x)
    x -= 1
    a = c[0]
    t = x + g + 0.5
    for i in range(1, g + 2):
        a += c[i] / (x + i)
    return 0.5 * math.log(2 * math.pi) + (x + 0.5) * math.log(t) - t + math.log(a)


def _gammp(a: float, x: float) -> float:
    """Regularized lower incomplete gamma P(a, x), series expansion."""
    if x < a + 1:
        term = 1.0 / a
        total = term
        n = a
        for _ in range(200):
            n += 1
            term *= x / n
            total += term
            if abs(term) < abs(total) * 1e-14:
                break
        return total * math.exp(-x + a * math.log(x) - _log_gamma(a))
    return 1 - _gammq_cf(a, x)


def _gammq_cf(a: float, x: float) -> float:
    """Regularized upper incomplete gamma Q(a, x), continued fraction."""
    tiny = 1e-300
    b = x + 1 - a
    c = 1 / tiny
    d = 1 / b
    h = d
    for i in range(1, 200):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        if abs(d) < tiny:
            d = tiny
        c = b + an / c
        if abs(c) < tiny:
            c = tiny
        d = 1 / d
        delta = d * c
        h *= delta
        if abs(delta - 1) < 1e-14:
            break
    return math.exp(-x + a * math.log(x) - _log_gamma(a)) * h


def chi2_sf(x: float, df: int) -> float:
    """Survival function (1 - CDF) of the chi-square distribution -- the p-value for Q."""
    if x <= 0:
        return 1.0
    a = df / 2.0
    xx = x / 2.0
    p = _gammp(a, xx) if xx < a + 1 else 1 - _gammq_cf(a, xx)
    return max(0.0, min(1.0, 1 - p))


def fisher_z(r: float) -> float:
    r = max(min(r, 0.999999), -0.999999)
    return 0.5 * math.log((1 + r) / (1 - r))


def cochran_q(studies: list[tuple[str, float, int]]) -> dict:
    """studies: [(label, r, n), ...]"""
    zs = [fisher_z(r) for _, r, _ in studies]
    ws = [n - 3 for _, _, n in studies]
    z_bar = sum(w * z for w, z in zip(ws, zs)) / sum(ws)
    q = sum(w * (z - z_bar) ** 2 for w, z in zip(ws, zs))
    df = len(studies) - 1
    i2 = max(0.0, (q - df) / q) * 100 if q > 0 else 0.0
    p = chi2_sf(q, df) if df > 0 else 1.0
    r_bar = math.tanh(z_bar)
    return {"q": q, "df": df, "p": p, "i2": i2, "pooled_r": r_bar}


def main() -> int:
    for environment in ENVIRONMENTS:
        cfg = ENVIRONMENTS[environment]
        studies = []
        for model, root in MODELS.items():
            if model == "DeepSeek-v4-flash":
                cell_dir = root / environment / f"uniform_fair__scale_free__sanctioning_off"
                reps = sorted(cell_dir.glob("rep[1-8].json"))
            else:
                cell_dir = root / environment
                reps = sorted(cell_dir.glob("rep*.json"))
            res = analyze_cell(reps, cfg["payoff_table"], cfg["compliant_action"])
            if res.get("r") is None:
                print(f"  skipping {model}/{environment}: no data", file=sys.stderr)
                continue
            studies.append((model, res["r"], res["n_pooled_agents"]))

        print(f"\n=== {environment} (uniform_fair x scale_free) ===")
        for label, r, n in studies:
            print(f"  {label}: r={r:.4f}, n={n}")
        result = cochran_q(studies)
        print(f"  Cochran's Q = {result['q']:.3f}, df={result['df']}, p={result['p']:.4f}")
        print(f"  I^2 = {result['i2']:.1f}%  (0%=all variation is noise, 100%=all variation is real heterogeneity)")
        print(f"  Fixed-effect pooled r = {result['pooled_r']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
