#!/usr/bin/env python3
"""H2 calibration analysis: inter-coder reliability, adjudication,
classifier-construct mapping, stratum-reweighted prevalence.

Answers: (a) do the two human coders agree with each other, (b) which
automated classifier (keyword, judge) corresponds to which human
construct (specific_reference / generic_network_language / their OR),
and (c) what the stratum-reweighted prevalence estimates should be.

Pure stdlib (no numpy/scipy/pandas), matching stats_main_study.py's
convention. Bootstrap CIs throughout instead of parametric tests.

Usage:
    python3 h2_calibration_analysis.py
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import statistics
import zlib
from pathlib import Path

from h2_judge import keyword_label, DEFAULT_CACHE_PATH

HERE = Path(__file__).resolve().parent
if (HERE / "h2_calibration").is_dir():
    CALIB_DIR = HERE / "h2_calibration"  # results-paper/raw_data/'s flat layout
else:
    CALIB_DIR = HERE / "reports" / "raw_exports" / "h2_calibration"  # main repo's tools/ layout
N_BOOT = 10000
CI_LEVEL = 0.95


# ---------------------------------------------------------------- text --

def normalize_text(t: str) -> str:
    """strip, collapse internal whitespace, casefold -- plus one
    documented, deterministic correction: a subset of the coding
    sheet's texts have a single 'a with circumflex' (U+00E2) character
    where the real corpus has an em-dash (U+2014). Verified against
    the real judge cache before applying: of 148 items, 116 already
    match the real corpus verbatim; this correction raises that to
    146/148 (the remaining 2 are examined separately -- see
    diagnose_unmatched()). This is a correction for a known,
    single-character, deterministic encoding artifact, not fuzzy/
    approximate matching -- the join itself stays an exact hash match
    on the normalized string."""
    t = t.replace("â", "—")
    return " ".join(t.strip().split()).casefold()


def text_hash(t: str) -> str:
    return hashlib.sha256(normalize_text(t).encode("utf-8")).hexdigest()[:16]


# ------------------------------------------------------- step 0: join --

def build_judge_by_text(cache_path: str, out_path: Path) -> dict[str, dict]:
    cache = json.loads(Path(cache_path).read_text())
    rows = []
    index: dict[str, dict] = {}
    for text, label in cache.items():
        h = text_hash(text)
        row = {"text_hash": h, "text": text, "aware": label["aware"], "fair": label["fair"]}
        rows.append(row)
        index[h] = row
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["text_hash", "text", "aware", "fair"])
        w.writeheader()
        w.writerows(rows)
    print(f"written {out_path} ({len(rows)} unique judge-classified texts)")
    return index


def load_coding_sheet(path: Path) -> list[dict]:
    return list(csv.DictReader(open(path)))


def join_sheet_to_judge(sheet: list[dict], judge_index: dict[str, dict]) -> tuple[list[dict], list[dict]]:
    joined, failed = [], []
    for row in sheet:
        h = text_hash(row["text"])
        if h in judge_index:
            joined.append({**row, "judge_aware": judge_index[h]["aware"], "judge_fair": judge_index[h]["fair"]})
        else:
            failed.append(row)
    return joined, failed


# ------------------------------------------------------ kappa + boot --

def cohens_kappa(a: list[bool], b: list[bool]) -> float | None:
    n = len(a)
    if n == 0:
        return None
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pa_true = sum(a) / n
    pb_true = sum(b) / n
    pe = pa_true * pb_true + (1 - pa_true) * (1 - pb_true)
    if pe >= 1:
        return 1.0
    return (po - pe) / (1 - pe)


def contingency(a: list[bool], b: list[bool]) -> dict:
    tt = sum(1 for x, y in zip(a, b) if x and y)
    tf = sum(1 for x, y in zip(a, b) if x and not y)
    ft = sum(1 for x, y in zip(a, b) if not x and y)
    ff = sum(1 for x, y in zip(a, b) if not x and not y)
    return {"a_yes_b_yes": tt, "a_yes_b_no": tf, "a_no_b_yes": ft, "a_no_b_no": ff}


def bootstrap_kappa_ci(a: list[bool], b: list[bool], n_boot: int = N_BOOT, seed: int = 1) -> tuple[float, float]:
    n = len(a)
    if n < 2:
        return (float("nan"), float("nan"))
    rng = random.Random(seed)
    idx = list(range(n))
    vals = []
    for _ in range(n_boot):
        sample = [rng.choice(idx) for _ in idx]
        k = cohens_kappa([a[i] for i in sample], [b[i] for i in sample])
        if k is not None:
            vals.append(k)
    vals.sort()
    alpha = 1 - CI_LEVEL
    lo = vals[int((alpha / 2) * len(vals))]
    hi = vals[int((1 - alpha / 2) * len(vals)) - 1]
    return lo, hi


def sensitivity_specificity(pred: list[bool], truth: list[bool]) -> tuple[float | None, float | None]:
    tp = sum(1 for p, t in zip(pred, truth) if p and t)
    fn = sum(1 for p, t in zip(pred, truth) if not p and t)
    tn = sum(1 for p, t in zip(pred, truth) if not p and not t)
    fp = sum(1 for p, t in zip(pred, truth) if p and not t)
    sens = tp / (tp + fn) if (tp + fn) else None
    spec = tn / (tn + fp) if (tn + fp) else None
    return sens, spec


# -------------------------------------------------------- step outputs --

CELLS = [("commons", "uniform_fair"), ("commons", "mixed"), ("triage", "uniform_fair"), ("triage", "mixed")]


def step1_intercoder(c1: list[dict], c2: list[dict]) -> list[dict]:
    assert [r["item_id"] for r in c1] == [r["item_id"] for r in c2], "item order/id mismatch between coders"
    results = []
    for dim in ["specific_reference", "generic_network_language"]:
        a_all = [r[dim] == "yes" for r in c1]
        b_all = [r[dim] == "yes" for r in c2]
        k = cohens_kappa(a_all, b_all)
        lo, hi = bootstrap_kappa_ci(a_all, b_all)
        results.append({
            "dimension": dim, "scope": "overall", "n": len(a_all),
            "kappa": k, "ci_lo": lo, "ci_hi": hi, **contingency(a_all, b_all),
        })
        for env, pop in CELLS:
            idx = [i for i, r in enumerate(c1) if r["_environment"] == env and r["_population"] == pop]
            a = [a_all[i] for i in idx]
            b = [b_all[i] for i in idx]
            k = cohens_kappa(a, b)
            lo, hi = bootstrap_kappa_ci(a, b) if len(a) >= 2 else (float("nan"), float("nan"))
            results.append({
                "dimension": dim, "scope": f"{env}/{pop}", "n": len(a),
                "kappa": k, "ci_lo": lo, "ci_hi": hi, **contingency(a, b),
            })
    return results


def step2_adjudication(c1: list[dict], c2: list[dict], out_path: Path) -> list[dict]:
    needed = []
    for r1, r2 in zip(c1, c2):
        disagree_spec = r1["specific_reference"] != r2["specific_reference"]
        disagree_gen = r1["generic_network_language"] != r2["generic_network_language"]
        if disagree_spec or disagree_gen:
            needed.append({
                "item_id": r1["item_id"], "text": r1["text"],
                "coder1_specific_reference": r1["specific_reference"], "coder2_specific_reference": r2["specific_reference"],
                "coder1_generic_network_language": r1["generic_network_language"], "coder2_generic_network_language": r2["generic_network_language"],
                "coder1_notes": r1["notes"], "coder2_notes": r2["notes"],
                "_zone": r1["_zone"], "_environment": r1["_environment"], "_population": r1["_population"], "_cell": r1["_cell"],
            })
    with open(out_path, "w", newline="") as f:
        fieldnames = list(needed[0].keys()) if needed else [
            "item_id", "text", "coder1_specific_reference", "coder2_specific_reference",
            "coder1_generic_network_language", "coder2_generic_network_language",
            "coder1_notes", "coder2_notes", "_zone", "_environment", "_population", "_cell",
        ]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(needed)
    print(f"written {out_path} ({len(needed)}/{len(c1)} items need adjudication)")
    return needed


MAPPINGS = {
    "A": ("specific_reference", lambda r: r["specific_reference"] == "yes"),
    "B": ("generic_network_language", lambda r: r["generic_network_language"] == "yes"),
    "C": ("specific_reference OR generic_network_language",
          lambda r: r["specific_reference"] == "yes" or r["generic_network_language"] == "yes"),
}


def step3_mapping(joined: list[dict], coder_label: str) -> list[dict]:
    """joined: rows with judge_aware/judge_fair already attached, plus
    keyword_label computed fresh (not re-tuned) per text."""
    results = []
    for classifier_name in ["keyword", "judge"]:
        for mapping_name, (mapping_desc, human_fn) in MAPPINGS.items():
            for scope, idx_fn in [("overall", lambda r: True)] + [
                (f"{env}/{pop}", (lambda r, env=env, pop=pop: r["_environment"] == env and r["_population"] == pop))
                for env, pop in CELLS
            ]:
                rows = [r for r in joined if idx_fn(r)]
                if len(rows) < 2:
                    continue
                human = [human_fn(r) for r in rows]
                if classifier_name == "keyword":
                    pred = [keyword_label(r["text"])["aware"] for r in rows]
                else:
                    pred = [r["judge_aware"] for r in rows]
                k = cohens_kappa(human, pred)
                # zlib.crc32, not builtin hash() -- hash() is randomized per-process
                # (PYTHONHASHSEED) for str/tuple, which made bootstrap CIs vary slightly
                # run-to-run despite identical inputs; crc32 is stable.
                seed_key = "|".join([classifier_name, mapping_name, scope]).encode()
                lo, hi = bootstrap_kappa_ci(human, pred, seed=zlib.crc32(seed_key))
                sens, spec = sensitivity_specificity(pred, human)
                results.append({
                    "coder": coder_label, "classifier": classifier_name, "mapping": mapping_name,
                    "mapping_desc": mapping_desc, "scope": scope, "n": len(rows),
                    "kappa": k, "ci_lo": lo, "ci_hi": hi, "sensitivity": sens, "specificity": spec,
                })
    return results


def step4_raw_prevalence(joined: list[dict], coder_label: str) -> list[dict]:
    """Raw (unweighted) sample prevalence per cell x stratum, for
    'specific_reference' and 'generic_network_language'. NOT the
    required population estimate (see the blocker note in the
    markdown output) -- this is the sample-side half of the
    reweighting formula (p_z), reported explicitly as such, with a
    bootstrap CI on the raw estimate for reference only."""
    results = []
    for env, pop in CELLS:
        for dim in ["specific_reference", "generic_network_language"]:
            cell_rows = [r for r in joined if r["_environment"] == env and r["_population"] == pop]
            if not cell_rows:
                continue
            by_zone: dict[str, list[bool]] = {}
            for r in cell_rows:
                by_zone.setdefault(r["_zone"], []).append(r[dim] == "yes")
            zone_stats = {}
            for zone, vals in by_zone.items():
                p = statistics.mean(vals) if vals else None
                zone_stats[zone] = {"n": len(vals), "p_z": p}
            all_vals = [r[dim] == "yes" for r in cell_rows]
            raw_p = statistics.mean(all_vals)
            results.append({
                "coder": coder_label, "environment": env, "population": pop, "dimension": dim,
                "n_sample": len(cell_rows), "raw_sample_prevalence": raw_p, "by_zone": zone_stats,
            })
    return results


def load_stratum_sizes(path: Path) -> dict[tuple, dict]:
    """{(env, pop): {zone: {'N_z':.., 'N_cell':..}}}"""
    out: dict[tuple, dict] = {}
    for row in csv.DictReader(open(path)):
        key = (row["environment"], row["population"])
        out.setdefault(key, {})[row["zone"]] = {
            "N_z": int(row["N_z"]), "N_cell": int(row["N_cell"]),
        }
    return out


def step4_reweighted_prevalence(joined: list[dict], coder_label: str, stratum_sizes: dict,
                                n_boot: int = N_BOOT, seed: int = 1) -> list[dict]:
    """p_hat = sum_z (N_z/N) * p_z, bootstrap CI by resampling sample
    items within stratum (not the population -- we only have sample-
    level labels) and recomputing the weighted estimate each draw."""
    results = []
    rng = random.Random(seed)
    for env, pop in CELLS:
        key = (env, pop)
        if key not in stratum_sizes:
            continue
        sizes = stratum_sizes[key]
        n_cell = next(iter(sizes.values()))["N_cell"]
        for dim in ["specific_reference", "generic_network_language"]:
            cell_rows = [r for r in joined if r["_environment"] == env and r["_population"] == pop]
            if not cell_rows:
                continue
            by_zone: dict[str, list[bool]] = {}
            for r in cell_rows:
                by_zone.setdefault(r["_zone"], []).append(r[dim] == "yes")

            missing_zones = set(by_zone) - set(sizes)
            if missing_zones:
                raise ValueError(f"zone(s) {missing_zones} in sample but not in stratum-size table for {key}")

            def weighted_estimate(zone_vals: dict[str, list[bool]]) -> float | None:
                total = 0.0
                for zone, vals in zone_vals.items():
                    if not vals:
                        return None  # can't estimate a stratum with zero sample items
                    w = sizes[zone]["N_z"] / n_cell
                    total += w * statistics.mean(vals)
                return total

            p_hat = weighted_estimate(by_zone)
            boot_vals = []
            zones = list(by_zone.keys())
            for _ in range(n_boot):
                resampled = {z: [rng.choice(by_zone[z]) for _ in by_zone[z]] for z in zones}
                est = weighted_estimate(resampled)
                if est is not None:
                    boot_vals.append(est)
            boot_vals.sort()
            alpha = 1 - CI_LEVEL
            lo = boot_vals[int((alpha / 2) * len(boot_vals))] if boot_vals else None
            hi = boot_vals[int((1 - alpha / 2) * len(boot_vals)) - 1] if boot_vals else None

            zone_weights = {z: sizes[z]["N_z"] / n_cell for z in zones}
            dominant_zone = max(zones, key=lambda z: zone_weights[z])
            results.append({
                "coder": coder_label, "environment": env, "population": pop, "dimension": dim,
                "n_sample": len(cell_rows), "p_hat_reweighted": p_hat, "ci_lo": lo, "ci_hi": hi,
                "zone_weights": zone_weights,
                "dominant_zone": dominant_zone, "dominant_zone_weight": zone_weights[dominant_zone],
                "dominant_zone_n": len(by_zone[dominant_zone]),
            })
    return results


# Adjudication decisions for the 21 items where coder1 and coder2
# disagreed (h2_adjudication_needed.csv), 2026-08-16. Reasoning for
# each is in tools/reports/h2_calibration_analysis.md's adjudication
# section -- not a majority vote or a default to either coder, a
# reasoned call against the same operational definition the judge
# prompt and human-coding anchor examples use. Two recurring
# principles: (1) an unnamed, undifferentiated "others did X" claim
# (the "H2-029 family") does not individuate a counterpart, so
# specific_reference=no, matching the already-agreed clear-none
# precedent H2-146 ("those who never contributed"); (2) the agent's
# own past ACTION (e.g. sanctioning) is a checkable event and counts
# as specific, unlike a passive comparison to others' behavior.
ADJUDICATED_OVERRIDES: dict[str, dict[str, str]] = {
    "H2-004": {"specific_reference": "no"},
    "H2-006": {"specific_reference": "no"},
    "H2-029": {"specific_reference": "no"},
    "H2-032": {"generic_network_language": "no"},
    "H2-039": {"specific_reference": "no"},
    "H2-045": {"specific_reference": "no"},
    "H2-055": {"specific_reference": "no"},
    "H2-057": {"specific_reference": "no"},
    "H2-069": {"specific_reference": "no"},
    "H2-070": {"specific_reference": "no"},
    "H2-076": {"specific_reference": "yes"},
    "H2-079": {"specific_reference": "no"},
    "H2-080": {"specific_reference": "no"},
    "H2-089": {"specific_reference": "no"},
    "H2-090": {"specific_reference": "no"},
    "H2-099": {"specific_reference": "no"},
    "H2-100": {"specific_reference": "no"},
    "H2-108": {"generic_network_language": "no"},
    "H2-127": {"specific_reference": "no"},
    "H2-133": {"specific_reference": "no"},
    "H2-140": {"specific_reference": "no"},
}


def build_adjudicated_sheet(c1: list[dict], c2: list[dict], overrides: dict[str, dict[str, str]],
                            out_path: Path) -> list[dict]:
    """148-item sheet: agreed items keep coder1's label (==coder2's by
    definition), disputed items take the adjudicated override. Errors
    loudly if an override is missing for a disputed item or present
    for an item that wasn't actually disputed, so this can't silently
    drift out of sync with h2_adjudication_needed.csv."""
    adjudicated = []
    disputed_seen = set()
    for r1, r2 in zip(c1, c2):
        row = dict(r1)
        disputed = r1["specific_reference"] != r2["specific_reference"] or \
            r1["generic_network_language"] != r2["generic_network_language"]
        if disputed:
            disputed_seen.add(r1["item_id"])
            if r1["item_id"] not in overrides:
                raise ValueError(f"{r1['item_id']} is disputed but has no adjudication override")
            row.update(overrides[r1["item_id"]])
        elif r1["item_id"] in overrides:
            raise ValueError(f"{r1['item_id']} has an override but coders actually agreed -- stale entry?")
        adjudicated.append(row)
    missing = set(overrides) - disputed_seen
    if missing:
        raise ValueError(f"overrides given for non-disputed or unknown items: {missing}")
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(adjudicated[0].keys()))
        w.writeheader()
        w.writerows(adjudicated)
    print(f"written {out_path} ({len(disputed_seen)} adjudicated, {len(adjudicated) - len(disputed_seen)} were already agreed)")
    return adjudicated


def diagnose_unmatched(failed: list[dict]) -> list[dict]:
    return [{"item_id": r["item_id"], "text": r["text"]} for r in failed]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--calib-dir", type=Path, default=CALIB_DIR)
    parser.add_argument("--cache", default=DEFAULT_CACHE_PATH)
    parser.add_argument("--md-out", default=None)
    parser.add_argument("--csv-out", default=None)
    parser.add_argument("--stratum-sizes", default=None,
                        help="CSV with environment,population,zone,N_z,N_cell -- supplies the "
                             "population-level stratum sizes needed for step 4's reweighted "
                             "prevalence. Without it, only raw (unweighted) sample prevalence is reported.")
    args = parser.parse_args()
    calib_dir = args.calib_dir
    md_out = Path(args.md_out) if args.md_out else calib_dir / "h2_calibration.md"
    csv_out = Path(args.csv_out) if args.csv_out else calib_dir / "h2_calibration.csv"
    stratum_sizes_path = Path(args.stratum_sizes) if args.stratum_sizes else calib_dir / "h2_stratum_sizes.csv"
    stratum_sizes = load_stratum_sizes(stratum_sizes_path) if stratum_sizes_path.is_file() else None

    judge_by_text_path = calib_dir / "h2_judge_by_text.csv"
    judge_index = build_judge_by_text(args.cache, judge_by_text_path)

    c1_raw = load_coding_sheet(calib_dir / "h2_coding_sheet_coder1.csv")
    c2_raw = load_coding_sheet(calib_dir / "h2_coding_sheet_coder2.csv")

    c1_joined, c1_failed = join_sheet_to_judge(c1_raw, judge_index)
    c2_joined, c2_failed = join_sheet_to_judge(c2_raw, judge_index)
    print(f"coder1: {len(c1_joined)}/{len(c1_raw)} joined to judge labels, {len(c1_failed)} failed")
    print(f"coder2: {len(c2_joined)}/{len(c2_raw)} joined to judge labels, {len(c2_failed)} failed")

    intercoder = step1_intercoder(c1_raw, c2_raw)

    adjudication_needed = step2_adjudication(c1_raw, c2_raw, calib_dir / "h2_adjudication_needed.csv")

    adjudicated_raw = build_adjudicated_sheet(c1_raw, c2_raw, ADJUDICATED_OVERRIDES,
                                              calib_dir / "h2_adjudicated.csv")
    adjudicated_joined, adjudicated_failed = join_sheet_to_judge(adjudicated_raw, judge_index)

    mapping_c1 = step3_mapping(c1_joined, "coder1")
    mapping_c2 = step3_mapping(c2_joined, "coder2")
    mapping_final = step3_mapping(adjudicated_joined, "adjudicated")

    prevalence_c1 = step4_raw_prevalence(c1_joined, "coder1")
    prevalence_c2 = step4_raw_prevalence(c2_joined, "coder2")

    reweighted_c1 = reweighted_c2 = reweighted_final = None
    if stratum_sizes is not None:
        reweighted_c1 = step4_reweighted_prevalence(c1_joined, "coder1", stratum_sizes, seed=1)
        reweighted_c2 = step4_reweighted_prevalence(c2_joined, "coder2", stratum_sizes, seed=2)
        reweighted_final = step4_reweighted_prevalence(adjudicated_joined, "adjudicated", stratum_sizes, seed=3)
        print(f"stratum sizes loaded from {stratum_sizes_path}: reweighted prevalence computed")
    else:
        print(f"no stratum-sizes file at {stratum_sizes_path}: step 4 stays raw-sample-only")

    unmatched = diagnose_unmatched(c1_failed)

    write_outputs(md_out, csv_out, intercoder, adjudication_needed, mapping_c1, mapping_c2,
                 prevalence_c1, prevalence_c2, unmatched, len(c1_raw),
                 reweighted_c1=reweighted_c1, reweighted_c2=reweighted_c2,
                 mapping_final=mapping_final, reweighted_final=reweighted_final)
    return 0


def write_outputs(md_out, csv_out, intercoder, adjudication_needed, mapping_c1, mapping_c2,
                  prevalence_c1, prevalence_c2, unmatched, n_total,
                  reweighted_c1=None, reweighted_c2=None, mapping_final=None, reweighted_final=None):
    def best_mapping(rows, classifier, coder):
        cand = [r for r in rows if r["classifier"] == classifier and r["coder"] == coder and r["scope"] == "overall"]
        cand = [r for r in cand if r["kappa"] is not None]
        return max(cand, key=lambda r: r["kappa"]) if cand else None

    kw_best_c1 = best_mapping(mapping_c1, "keyword", "coder1")
    judge_best_c1 = best_mapping(mapping_c1, "judge", "coder1")
    kw_best_c2 = best_mapping(mapping_c2, "keyword", "coder2")
    judge_best_c2 = best_mapping(mapping_c2, "judge", "coder2")

    expectation_note = []
    for label, kw_best, judge_best in [("coder1", kw_best_c1, judge_best_c1), ("coder2", kw_best_c2, judge_best_c2)]:
        kw_ok = kw_best and kw_best["mapping"] == "A"
        judge_ok = judge_best and judge_best["mapping"] == "C"
        expectation_note.append((label, kw_ok, judge_ok, kw_best, judge_best))

    lines = ["# H2 calibration: inter-coder reliability, classifier-construct mapping, prevalence", ""]

    lines.append("## Verdict")
    lines.append("")
    if mapping_final is not None:
        kw_best_f = best_mapping(mapping_final, "keyword", "adjudicated")
        judge_best_f = best_mapping(mapping_final, "judge", "adjudicated")
        kw_ok_f = kw_best_f and kw_best_f["mapping"] == "A"
        judge_ok_f = judge_best_f and judge_best_f["mapping"] == "C"
        kw_desc_f = f"mapping {kw_best_f['mapping']} ({kw_best_f['mapping_desc']}), kappa={kw_best_f['kappa']:.3f}" if kw_best_f else "n/a"
        judge_desc_f = f"mapping {judge_best_f['mapping']} ({judge_best_f['mapping_desc']}), kappa={judge_best_f['kappa']:.3f}" if judge_best_f else "n/a"
        verdict_f = "HOLDS" if (kw_ok_f and judge_ok_f) else "DOES NOT FULLY HOLD"
        lines.append(f"**FINAL, adjudicated ground truth** (21 disputed items resolved 2026-08-16, "
                    f"see `h2_adjudicated.csv` and the reasoning notes there -- not a majority vote, "
                    f"a reasoned call against the same operational definition the anchor examples "
                    f"use): keyword's best-fitting mapping is {kw_desc_f}; judge's best-fitting "
                    f"mapping is {judge_desc_f}. Pre-stated expectation (keyword~A, judge~C) "
                    f"**{verdict_f}**. This is the number to cite -- the per-coder breakdown below is "
                    f"a robustness check, not a second answer.")
        lines.append("")
    for label, kw_ok, judge_ok, kw_best, judge_best in expectation_note:
        kw_desc = f"mapping {kw_best['mapping']} ({kw_best['mapping_desc']}), kappa={kw_best['kappa']:.3f}" if kw_best else "n/a"
        judge_desc = f"mapping {judge_best['mapping']} ({judge_best['mapping_desc']}), kappa={judge_best['kappa']:.3f}" if judge_best else "n/a"
        verdict = "HOLDS" if (kw_ok and judge_ok) else "DOES NOT FULLY HOLD"
        lines.append(f"- Against **{label}**: keyword's best-fitting mapping is {kw_desc}; "
                     f"judge's best-fitting mapping is {judge_desc}. Pre-stated expectation "
                     f"(keyword~A, judge~C) **{verdict}**.")
    lines.append("")
    if reweighted_c1 is not None:
        lines.append("**Stratum-reweighted prevalence (step 4) is now computed, on the final "
                    "adjudicated ground truth** -- N_z supplied 2026-08-16 (`h2_stratum_sizes.csv`), "
                    "21 disputed items resolved the same day (`h2_adjudicated.csv`). One data-quality "
                    "note before trusting it: N_cell for commons/mixed (19,499) is ~6.5% higher than "
                    "this repo's own direct count from the real corpus (18,302; the other three cells "
                    "match to within <0.3%). Not corrected here -- using the supplied N_z as given, "
                    "flagged so it's on record. See the Step 4 section below for the numbers and, "
                    "importantly, *why* commons is close to uninformative regardless of adjudication: "
                    "commons/uniform_fair is 99.4% grey (the fair persona makes nearly every agent use "
                    "collective language without naming a specific position, so the stratification "
                    "barely separates anything), so that cell's reweighted estimate rests on only the "
                    "~20 grey sample items drawn -- wide CI by construction, not fixable by "
                    "adjudication. commons/mixed's dominant stratum (`clear-none`) has only 7 sample "
                    "items for the same reason. Triage is where the strata are genuinely informative "
                    "(8,675 / 5,379 / 336) and where the original 51%-vs-87% disagreement actually "
                    "lives -- that's the number worth leaning on, and adjudication has now settled it "
                    "rather than leaving it as a per-coder range.")
    else:
        lines.append("**Stratum-reweighted prevalence (step 4) could NOT be computed.** The reweighting "
                    "formula needs N_z (population stratum sizes) from re-running the exact zone-assignment "
                    "rule used to build this 148-item sample over the full ~59k-text corpus. That rule's "
                    "code was not provided, and it could not be reliably reverse-engineered from the sample "
                    "(tried: keyword-classifier aware/fair proxies, judge-label proxies, and a "
                    "keyword-vs-judge-agreement proxy for the 3-way zone split -- none matched the actual "
                    "_zone column at better than ~55/146 items, no better than a weak partial fit, not "
                    "something to build a headline number on). Reported below instead: raw (unweighted) "
                    "sample prevalence per cell/stratum (p_z) and per-stratum sample sizes (n_z) -- "
                    "everything needed to complete the reweighting immediately once N_z is supplied, "
                    "**not to be quoted as the population estimate itself.**")
    lines.append("")

    lines.append("## Step 0: judge/text join")
    lines.append("")
    lines.append(f"{n_total - len(unmatched)}/{n_total} items joined to a per-text judge label "
                f"(exact match on normalized text, with one documented, verified correction: a "
                f"single-character encoding artifact, U+00E2 for em-dash, present in a subset of "
                f"the coding-sheet texts but not the real corpus -- raised the join from 116/148 to "
                f"{n_total - len(unmatched)}/{n_total}).")
    if unmatched:
        lines.append("")
        lines.append(f"**{len(unmatched)} items failed to join** (not dropped -- reported here; these "
                     f"texts do not appear in the real 264-run corpus even after normalization, most "
                     f"likely paraphrased/condensed versions rather than verbatim samples):")
        for u in unmatched:
            lines.append(f"- `{u['item_id']}`: {u['text']}")
    lines.append("")

    lines.append("## Step 1: inter-coder reliability")
    lines.append("")
    lines.append("Kappa computed separately per cell (not pooled -- pooling masked the original "
                "30-item validation's real disagreement). 2x2 contingency table alongside each kappa.")
    lines.append("")
    lines.append("| Dimension | Scope | n | kappa | 95% CI | yes/yes | yes/no | no/yes | no/no |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for r in intercoder:
        k = f"{r['kappa']:.3f}" if r["kappa"] is not None else "n/a"
        ci = f"[{r['ci_lo']:.3f}, {r['ci_hi']:.3f}]" if r["ci_lo"] == r["ci_lo"] else "n/a"
        lines.append(f"| {r['dimension']} | {r['scope']} | {r['n']} | {k} | {ci} | "
                    f"{r['a_yes_b_yes']} | {r['a_yes_b_no']} | {r['a_no_b_yes']} | {r['a_no_b_no']} |")
    lines.append("")

    lines.append("## Step 2: adjudication")
    lines.append("")
    lines.append(f"{len(adjudication_needed)}/{n_total} items need a third-party decision "
                f"(coders disagreed on `specific_reference` and/or `generic_network_language`). "
                f"Full list with both coders' labels and notes: `h2_adjudication_needed.csv`. "
                f"Not auto-resolved by majority or default.")
    lines.append("")

    lines.append("## Step 3: which classifier matches which construct")
    lines.append("")
    lines.append("Classifier = keyword or judge's own `aware` label (the dimension the original "
                "36-point discrepancy was about). Human construct = one of three candidate mappings. "
                "Run once per coder (adjudication pending).")
    lines.append("")
    for coder_label, rows in [("coder1", mapping_c1), ("coder2", mapping_c2)]:
        lines.append(f"### Against {coder_label}")
        lines.append("")
        lines.append("| Classifier | Mapping | Scope | n | kappa | 95% CI | sensitivity | specificity |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for r in rows:
            if r["scope"] != "overall":
                continue
            k = f"{r['kappa']:.3f}" if r["kappa"] is not None else "n/a"
            ci = f"[{r['ci_lo']:.3f}, {r['ci_hi']:.3f}]" if r["ci_lo"] == r["ci_lo"] else "n/a"
            sens = f"{r['sensitivity']:.3f}" if r["sensitivity"] is not None else "n/a"
            spec = f"{r['specificity']:.3f}" if r["specificity"] is not None else "n/a"
            lines.append(f"| {r['classifier']} | {r['mapping']} ({r['mapping_desc']}) | {r['scope']} | "
                        f"{r['n']} | {k} | {ci} | {sens} | {spec} |")
        lines.append("")
        lines.append("Per-cell breakdown (all scopes) in `h2_calibration.csv`.")
        lines.append("")

    if reweighted_c1 is not None:
        lines.append("## Step 4: stratum-reweighted prevalence (the population estimate)")
        lines.append("")
        lines.append("`p_hat = sum_z (N_z/N_cell) * p_z`, bootstrap 95% CI (10,000 draws, resampling "
                    "sample items within stratum). **The FINAL (adjudicated) table is the number to "
                    "cite in the paper**; the per-coder tables below it are a robustness check, not a "
                    "second answer -- raw sample prevalence (further below still) is not the population "
                    "estimate at all.")
        lines.append("")
        if reweighted_final is not None:
            lines.append("### FINAL (adjudicated ground truth)")
            lines.append("")
            lines.append("| Env | Population | Dimension | n sample | dominant stratum (weight, n) | reweighted p_hat | 95% CI |")
            lines.append("|---|---|---|---|---|---|---|")
            for r in reweighted_final:
                ci = f"[{r['ci_lo']:.3f}, {r['ci_hi']:.3f}]" if r["ci_lo"] is not None else "n/a"
                p = f"{r['p_hat_reweighted']:.3f}" if r["p_hat_reweighted"] is not None else "n/a"
                dom = f"{r['dominant_zone']} ({r['dominant_zone_weight']:.1%}, n={r['dominant_zone_n']})"
                lines.append(f"| {r['environment']} | {r['population']} | {r['dimension']} | {r['n_sample']} | "
                            f"{dom} | {p} | {ci} |")
            lines.append("")
        lines.append("### Per-coder (robustness check, pre-adjudication)")
        lines.append("")
        for coder_label, rows in [("coder1", reweighted_c1), ("coder2", reweighted_c2)]:
            lines.append(f"### {coder_label}")
            lines.append("")
            lines.append("| Env | Population | Dimension | n sample | dominant stratum (weight, n) | reweighted p_hat | 95% CI |")
            lines.append("|---|---|---|---|---|---|---|")
            for r in rows:
                ci = f"[{r['ci_lo']:.3f}, {r['ci_hi']:.3f}]" if r["ci_lo"] is not None else "n/a"
                p = f"{r['p_hat_reweighted']:.3f}" if r["p_hat_reweighted"] is not None else "n/a"
                dom = f"{r['dominant_zone']} ({r['dominant_zone_weight']:.1%}, n={r['dominant_zone_n']})"
                lines.append(f"| {r['environment']} | {r['population']} | {r['dimension']} | {r['n_sample']} | "
                            f"{dom} | {p} | {ci} |")
            lines.append("")
        lines.append("`dominant stratum` = the zone that carries the most population weight for that "
                    "cell -- its sample size is what actually limits precision, not the numerically "
                    "smallest stratum. In every commons cell that's `grey` (>99% weight in "
                    "uniform_fair, ~43% in mixed) at only ~20 sample items -- that's why those CIs are "
                    "wide despite n_sample=36-37.")
        lines.append("")
        lines.append("**Adjudication impact check** -- cells where the FINAL adjudicated p_hat sits "
                    "meaningfully outside where either individual coder alone would have put it (i.e. "
                    "adjudication actually mattered for the headline number, not just for kappa):")
        lines.append("")
        lines.append("| Env | Population | Dimension | coder1 p_hat | coder2 p_hat | FINAL p_hat | max abs diff from FINAL |")
        lines.append("|---|---|---|---|---|---|---|")
        rows3 = zip(reweighted_c1, reweighted_c2, reweighted_final) if reweighted_final is not None else []
        for r1, r2, rf in rows3:
            if r1["p_hat_reweighted"] is None or r2["p_hat_reweighted"] is None or rf["p_hat_reweighted"] is None:
                continue
            diff = max(abs(r1["p_hat_reweighted"] - rf["p_hat_reweighted"]),
                      abs(r2["p_hat_reweighted"] - rf["p_hat_reweighted"]))
            if diff < 0.03:
                continue
            lines.append(f"| {r1['environment']} | {r1['population']} | {r1['dimension']} | "
                        f"{r1['p_hat_reweighted']:.3f} | {r2['p_hat_reweighted']:.3f} | "
                        f"{rf['p_hat_reweighted']:.3f} | {diff:.3f} |")
        lines.append("")
        lines.append("commons/mixed/specific_reference remains the cell where the individual coders "
                    "differed most (0.202 vs. 0.002, tracking that cell's near-zero inter-coder kappa "
                    "of 0.033) -- the adjudicated FINAL value resolves it to a single number, but given "
                    "how thin that cell's dominant stratum is (`clear-none`, n=7 sample items), treat "
                    "its precision as limited regardless of which label is \"correct\".")
        lines.append("")

    lines.append("## Step 4b: raw sample prevalence (NOT the population estimate -- reference only)")
    lines.append("")
    for coder_label, rows in [("coder1", prevalence_c1), ("coder2", prevalence_c2)]:
        lines.append(f"### {coder_label}")
        lines.append("")
        lines.append("| Env | Population | Dimension | n sample | raw sample prevalence | per-stratum (n, p_z) |")
        lines.append("|---|---|---|---|---|---|")
        for r in rows:
            zone_str = "; ".join(f"{z}: n={s['n']}, p={s['p_z']:.3f}" if s["p_z"] is not None else f"{z}: n=0"
                                 for z, s in r["by_zone"].items())
            lines.append(f"| {r['environment']} | {r['population']} | {r['dimension']} | {r['n_sample']} | "
                        f"{r['raw_sample_prevalence']:.3f} | {zone_str} |")
        lines.append("")

    lines.append("## What this does not resolve")
    lines.append("")
    lines.append("This does not establish whether self-reports reflect the computation that actually "
                "produced the action. That limitation is unaffected by anything above and stays in the "
                "paper.")

    Path(md_out).write_text("\n".join(lines) + "\n")
    print(f"written {md_out}")

    csv_rows = []
    for r in intercoder:
        csv_rows.append({"section": "intercoder", **{k: v for k, v in r.items()}})
    for r in mapping_c1 + mapping_c2 + (mapping_final or []):
        csv_rows.append({"section": "mapping", **{k: v for k, v in r.items()}})
    for r in prevalence_c1 + prevalence_c2:
        row = {k: v for k, v in r.items() if k != "by_zone"}
        for zone, stats in r["by_zone"].items():
            row[f"zone_{zone}_n"] = stats["n"]
            row[f"zone_{zone}_p"] = stats["p_z"]
        csv_rows.append({"section": "prevalence_raw", **row})
    if reweighted_c1 is not None:
        for r in reweighted_c1 + reweighted_c2 + (reweighted_final or []):
            row = {k: v for k, v in r.items() if k != "zone_weights"}
            for zone, w in r["zone_weights"].items():
                row[f"weight_{zone}"] = w
            csv_rows.append({"section": "prevalence_reweighted", **row})
    all_fields = sorted(set().union(*(r.keys() for r in csv_rows))) if csv_rows else []
    all_fields = ["section"] + [f for f in all_fields if f != "section"]
    with open(csv_out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=all_fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(csv_rows)
    print(f"written {csv_out}")


if __name__ == "__main__":
    raise SystemExit(main())
