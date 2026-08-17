# H2 calibration: inter-coder reliability, classifier-construct mapping, prevalence

Status: **Complete.** All 5 steps done, including adjudication of the
21 disputed items and the final stratum-reweighted prevalence.
`tools/h2_calibration_analysis.py`, outputs in
`tools/reports/raw_exports/h2_calibration/`.

## Headline: the pre-stated expectation does not hold

The hoped-for story -- "keyword measures specific_reference (mapping
A), judge measures the broader specific_reference-OR-generic
construct (mapping C), so the 36-point gap is two classifiers
calibrated to different constructs, not one being wrong" -- **does
not hold**. Both classifiers' `aware` label best matches mapping A
(specific_reference), on the final adjudicated ground truth (kappa
0.573 judge vs. 0.369 keyword) as well as against each individual
coder pre-adjudication. The real story: judge is simply a
substantially better detector of the *same* construct than keyword
is. This is a real, more complicated finding than either "the
classifiers measure different things" or "one is just wrong" -- worth
its own careful sentence in the paper, not the pre-registered clean
story.

## Inter-coder reliability: real, and pooling would have hidden it (again)

Overall (pooled) kappa: specific_reference=0.668, generic_network_
language=0.950 -- looks fine pooled. Per-cell, it isn't:

| Cell | specific_reference kappa | Note |
|---|---|---|
| commons/uniform_fair | 1.000 | Trivial -- both coders said "no" on all 37 items, zero variance |
| commons/mixed | **0.033** | Essentially no agreement |
| triage/uniform_fair | 0.668 | Substantial |
| triage/mixed | 0.834 | Almost perfect |

`generic_network_language` is far more stable across cells (0.841-1.000
everywhere). Full contingency tables in `h2_calibration.md`.

## Adjudication: 21/148 items resolved, not by majority vote

Disagreement concentrated in two patterns: (1) an unnamed,
undifferentiated "others did X" claim (the "H2-029 family", 9 items)
-- resolved specific_reference=no throughout, matching the precedent
of the already-agreed clear-none item H2-146 with the identical
pattern; (2) 12 individually-argued items (own-contribution-history-
isn't-reciprocity-history, plans vs. factual connectivity claims,
abstraction vs. individuation, an agent's own past ACTION counting as
specific unlike a passive comparison). Full reasoning for each item in
`h2_adjudication_needed.csv` (as found) and the resulting
`h2_adjudicated.csv` (148-item sheet, agreed items unchanged, disputed
items resolved). `ADJUDICATED_OVERRIDES` in
`tools/h2_calibration_analysis.py` is the single source of truth, with
the reasoning inline as a comment.

## Step 4: stratum-reweighted prevalence -- computed on the final adjudicated ground truth

N_z (population stratum sizes, `h2_stratum_sizes.csv`) supplied
2026-08-16, after three attempts to reverse-engineer the
zone-assignment rule from the sample alone were tried and rejected
(keyword-proxy, judge-proxy, keyword-vs-judge-agreement -- best fit
55/146 items, not good enough to build a headline number on). One
data-quality flag not corrected, just recorded: supplied N_cell for
commons/mixed (19,499) is ~6.5% above this repo's own direct corpus
count (18,302); the other three cells match to <0.3%.

The real result, `h2_calibration.md`'s "FINAL (adjudicated ground
truth)" table: triage's strata are well-populated (8,675/5,379/336 and
5,311/3,154/5,940) and that's where the reweighted estimate is
trustworthy. Commons cells are inherently thin regardless of
adjudication -- commons/uniform_fair's dominant stratum (grey, 99.4%
weight) has only 20 sample items, commons/mixed's dominant stratum
(clear-none, 56% weight) has only 7 -- wide CIs by construction, not
something more coding could fix.

## Reproducing this

```
cd tools
python3 h2_calibration_analysis.py
```

Regenerates `h2_judge_by_text.csv`, `h2_adjudicated.csv`,
`h2_calibration.md`, `h2_calibration.csv`, `h2_adjudication_needed.csv`
in `reports/raw_exports/h2_calibration/`. Verified byte-reproducible
across runs (bootstrap seeds are `zlib.crc32`-based, not Python's
per-process-randomized `hash()`).
