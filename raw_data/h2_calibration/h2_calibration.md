# H2 calibration: inter-coder reliability, classifier-construct mapping, prevalence

## Verdict

**FINAL, adjudicated ground truth** (21 disputed items resolved 2026-08-16, see `h2_adjudicated.csv` and the reasoning notes there -- not a majority vote, a reasoned call against the same operational definition the anchor examples use): keyword's best-fitting mapping is mapping A (specific_reference), kappa=0.369; judge's best-fitting mapping is mapping A (specific_reference), kappa=0.573. Pre-stated expectation (keyword~A, judge~C) **DOES NOT FULLY HOLD**. This is the number to cite -- the per-coder breakdown below is a robustness check, not a second answer.

- Against **coder1**: keyword's best-fitting mapping is mapping A (specific_reference), kappa=0.320; judge's best-fitting mapping is mapping A (specific_reference), kappa=0.519. Pre-stated expectation (keyword~A, judge~C) **DOES NOT FULLY HOLD**.
- Against **coder2**: keyword's best-fitting mapping is mapping A (specific_reference), kappa=0.391; judge's best-fitting mapping is mapping A (specific_reference), kappa=0.628. Pre-stated expectation (keyword~A, judge~C) **DOES NOT FULLY HOLD**.

**Stratum-reweighted prevalence (step 4) is now computed, on the final adjudicated ground truth** -- N_z supplied 2026-08-16 (`h2_stratum_sizes.csv`), 21 disputed items resolved the same day (`h2_adjudicated.csv`). One data-quality note before trusting it: N_cell for commons/mixed (19,499) is ~6.5% higher than this repo's own direct count from the real corpus (18,302; the other three cells match to within <0.3%). Not corrected here -- using the supplied N_z as given, flagged so it's on record. See the Step 4 section below for the numbers and, importantly, *why* commons is close to uninformative regardless of adjudication: commons/uniform_fair is 99.4% grey (the fair persona makes nearly every agent use collective language without naming a specific position, so the stratification barely separates anything), so that cell's reweighted estimate rests on only the ~20 grey sample items drawn -- wide CI by construction, not fixable by adjudication. commons/mixed's dominant stratum (`clear-none`) has only 7 sample items for the same reason. Triage is where the strata are genuinely informative (8,675 / 5,379 / 336) and where the original 51%-vs-87% disagreement actually lives -- that's the number worth leaning on, and adjudication has now settled it rather than leaving it as a per-coder range.

## Step 0: judge/text join

146/148 items joined to a per-text judge label (exact match on normalized text, with one documented, verified correction: a single-character encoding artifact, U+00E2 for em-dash, present in a subset of the coding-sheet texts but not the real corpus -- raised the join from 116/148 to 146/148).

**2 items failed to join** (not dropped -- reported here; these texts do not appear in the real 264-run corpus even after normalization, most likely paraphrased/condensed versions rather than verbatim samples):
- `H2-068`: Received 30 units from me over three rounds with zero reciprocation; repeatedly failed to return trust extended to them.
- `H2-099`: Repeatedly extracting far more than a fair share with no contributions, continuing to devastate the nearly-depleted commons.

## Step 1: inter-coder reliability

Kappa computed separately per cell (not pooled -- pooling masked the original 30-item validation's real disagreement). 2x2 contingency table alongside each kappa.

| Dimension | Scope | n | kappa | 95% CI | yes/yes | yes/no | no/yes | no/no |
|---|---|---|---|---|---|---|---|---|
| specific_reference | overall | 148 | 0.668 | [0.519, 0.796] | 29 | 14 | 5 | 100 |
| specific_reference | commons/uniform_fair | 37 | 1.000 | [1.000, 1.000] | 0 | 0 | 0 | 37 |
| specific_reference | commons/mixed | 37 | 0.033 | [-0.183, 0.324] | 1 | 9 | 2 | 25 |
| specific_reference | triage/uniform_fair | 37 | 0.668 | [0.362, 0.924] | 8 | 3 | 2 | 24 |
| specific_reference | triage/mixed | 37 | 0.834 | [0.621, 1.000] | 20 | 2 | 1 | 14 |
| generic_network_language | overall | 148 | 0.950 | [0.867, 1.000] | 123 | 0 | 2 | 23 |
| generic_network_language | commons/uniform_fair | 37 | 1.000 | [1.000, 1.000] | 37 | 0 | 0 | 0 |
| generic_network_language | commons/mixed | 37 | 1.000 | [1.000, 1.000] | 25 | 0 | 0 | 12 |
| generic_network_language | triage/uniform_fair | 37 | 1.000 | [1.000, 1.000] | 33 | 0 | 0 | 4 |
| generic_network_language | triage/mixed | 37 | 0.841 | [0.549, 1.000] | 28 | 0 | 2 | 7 |

## Step 2: adjudication

21/148 items need a third-party decision (coders disagreed on `specific_reference` and/or `generic_network_language`). Full list with both coders' labels and notes: `h2_adjudication_needed.csv`. Not auto-resolved by majority or default.

## Step 3: which classifier matches which construct

Classifier = keyword or judge's own `aware` label (the dimension the original 36-point discrepancy was about). Human construct = one of three candidate mappings. Run once per coder (adjudication pending).

### Against coder1

| Classifier | Mapping | Scope | n | kappa | 95% CI | sensitivity | specificity |
|---|---|---|---|---|---|---|---|
| keyword | A (specific_reference) | overall | 146 | 0.320 | [0.160, 0.478] | 0.643 | 0.712 |
| keyword | B (generic_network_language) | overall | 146 | 0.186 | [0.096, 0.284] | 0.455 | 0.920 |
| keyword | C (specific_reference OR generic_network_language) | overall | 146 | 0.194 | [0.117, 0.284] | 0.456 | 1.000 |
| judge | A (specific_reference) | overall | 146 | 0.519 | [0.367, 0.658] | 0.762 | 0.798 |
| judge | B (generic_network_language) | overall | 146 | 0.095 | [0.002, 0.188] | 0.397 | 0.800 |
| judge | C (specific_reference OR generic_network_language) | overall | 146 | 0.152 | [0.078, 0.237] | 0.416 | 0.952 |

Per-cell breakdown (all scopes) in `h2_calibration.csv`.

### Against coder2

| Classifier | Mapping | Scope | n | kappa | 95% CI | sensitivity | specificity |
|---|---|---|---|---|---|---|---|
| keyword | A (specific_reference) | overall | 146 | 0.391 | [0.238, 0.537] | 0.781 | 0.719 |
| keyword | B (generic_network_language) | overall | 146 | 0.214 | [0.135, 0.308] | 0.463 | 1.000 |
| keyword | C (specific_reference OR generic_network_language) | overall | 146 | 0.194 | [0.117, 0.284] | 0.456 | 1.000 |
| judge | A (specific_reference) | overall | 146 | 0.628 | [0.493, 0.754] | 0.969 | 0.807 |
| judge | B (generic_network_language) | overall | 146 | 0.123 | [0.041, 0.212] | 0.407 | 0.870 |
| judge | C (specific_reference OR generic_network_language) | overall | 146 | 0.152 | [0.078, 0.237] | 0.416 | 0.952 |

Per-cell breakdown (all scopes) in `h2_calibration.csv`.

## Step 4: stratum-reweighted prevalence (the population estimate)

`p_hat = sum_z (N_z/N_cell) * p_z`, bootstrap 95% CI (10,000 draws, resampling sample items within stratum). **The FINAL (adjudicated) table is the number to cite in the paper**; the per-coder tables below it are a robustness check, not a second answer -- raw sample prevalence (further below still) is not the population estimate at all.

### FINAL (adjudicated ground truth)

| Env | Population | Dimension | n sample | dominant stratum (weight, n) | reweighted p_hat | 95% CI |
|---|---|---|---|---|---|---|
| commons | uniform_fair | specific_reference | 37 | grey (99.4%, n=20) | 0.000 | [0.000, 0.000] |
| commons | uniform_fair | generic_network_language | 37 | grey (99.4%, n=20) | 1.000 | [1.000, 1.000] |
| commons | mixed | specific_reference | 36 | clear-none (56.4%, n=7) | 0.002 | [0.000, 0.006] |
| commons | mixed | generic_network_language | 36 | clear-none (56.4%, n=7) | 0.510 | [0.427, 0.672] |
| triage | uniform_fair | specific_reference | 37 | clear-specific (60.3%, n=10) | 0.384 | [0.188, 0.565] |
| triage | uniform_fair | generic_network_language | 37 | clear-specific (60.3%, n=10) | 0.987 | [0.980, 0.997] |
| triage | mixed | specific_reference | 36 | clear-none (41.2%, n=7) | 0.466 | [0.314, 0.629] |
| triage | mixed | generic_network_language | 36 | clear-none (41.2%, n=7) | 0.506 | [0.383, 0.588] |

### Per-coder (robustness check, pre-adjudication)

### coder1

| Env | Population | Dimension | n sample | dominant stratum (weight, n) | reweighted p_hat | 95% CI |
|---|---|---|---|---|---|---|
| commons | uniform_fair | specific_reference | 37 | grey (99.4%, n=20) | 0.000 | [0.000, 0.000] |
| commons | uniform_fair | generic_network_language | 37 | grey (99.4%, n=20) | 1.000 | [1.000, 1.000] |
| commons | mixed | specific_reference | 36 | clear-none (56.4%, n=7) | 0.202 | [0.112, 0.293] |
| commons | mixed | generic_network_language | 36 | clear-none (56.4%, n=7) | 0.510 | [0.427, 0.672] |
| triage | uniform_fair | specific_reference | 37 | clear-specific (60.3%, n=10) | 0.508 | [0.333, 0.644] |
| triage | uniform_fair | generic_network_language | 37 | clear-specific (60.3%, n=10) | 0.987 | [0.980, 0.997] |
| triage | mixed | specific_reference | 36 | clear-none (41.2%, n=7) | 0.548 | [0.456, 0.677] |
| triage | mixed | generic_network_language | 36 | clear-none (41.2%, n=7) | 0.506 | [0.383, 0.588] |

### coder2

| Env | Population | Dimension | n sample | dominant stratum (weight, n) | reweighted p_hat | 95% CI |
|---|---|---|---|---|---|---|
| commons | uniform_fair | specific_reference | 37 | grey (99.4%, n=20) | 0.000 | [0.000, 0.000] |
| commons | uniform_fair | generic_network_language | 37 | grey (99.4%, n=20) | 1.000 | [1.000, 1.000] |
| commons | mixed | specific_reference | 36 | clear-none (56.4%, n=7) | 0.002 | [0.000, 0.006] |
| commons | mixed | generic_network_language | 36 | clear-none (56.4%, n=7) | 0.510 | [0.427, 0.672] |
| triage | uniform_fair | specific_reference | 37 | clear-specific (60.3%, n=10) | 0.406 | [0.206, 0.587] |
| triage | uniform_fair | generic_network_language | 37 | clear-specific (60.3%, n=10) | 0.987 | [0.980, 0.997] |
| triage | mixed | specific_reference | 36 | clear-none (41.2%, n=7) | 0.477 | [0.328, 0.633] |
| triage | mixed | generic_network_language | 36 | clear-none (41.2%, n=7) | 0.588 | [0.588, 0.588] |

`dominant stratum` = the zone that carries the most population weight for that cell -- its sample size is what actually limits precision, not the numerically smallest stratum. In every commons cell that's `grey` (>99% weight in uniform_fair, ~43% in mixed) at only ~20 sample items -- that's why those CIs are wide despite n_sample=36-37.

**Adjudication impact check** -- cells where the FINAL adjudicated p_hat sits meaningfully outside where either individual coder alone would have put it (i.e. adjudication actually mattered for the headline number, not just for kappa):

| Env | Population | Dimension | coder1 p_hat | coder2 p_hat | FINAL p_hat | max abs diff from FINAL |
|---|---|---|---|---|---|---|
| commons | mixed | specific_reference | 0.202 | 0.002 | 0.002 | 0.200 |
| triage | uniform_fair | specific_reference | 0.508 | 0.406 | 0.384 | 0.124 |
| triage | mixed | specific_reference | 0.548 | 0.477 | 0.466 | 0.082 |
| triage | mixed | generic_network_language | 0.506 | 0.588 | 0.506 | 0.082 |

commons/mixed/specific_reference remains the cell where the individual coders differed most (0.202 vs. 0.002, tracking that cell's near-zero inter-coder kappa of 0.033) -- the adjudicated FINAL value resolves it to a single number, but given how thin that cell's dominant stratum is (`clear-none`, n=7 sample items), treat its precision as limited regardless of which label is "correct".

## Step 4b: raw sample prevalence (NOT the population estimate -- reference only)

### coder1

| Env | Population | Dimension | n sample | raw sample prevalence | per-stratum (n, p_z) |
|---|---|---|---|---|---|
| commons | uniform_fair | specific_reference | 37 | 0.000 | grey: n=20, p=0.000; clear-specific: n=10, p=0.000; clear-none: n=7, p=0.000 |
| commons | uniform_fair | generic_network_language | 37 | 1.000 | grey: n=20, p=1.000; clear-specific: n=10, p=1.000; clear-none: n=7, p=1.000 |
| commons | mixed | specific_reference | 36 | 0.278 | clear-specific: n=10, p=0.100; clear-none: n=7, p=0.000; grey: n=19, p=0.474 |
| commons | mixed | generic_network_language | 36 | 0.667 | clear-specific: n=10, p=0.400; clear-none: n=7, p=0.143; grey: n=19, p=1.000 |
| triage | uniform_fair | specific_reference | 37 | 0.297 | clear-specific: n=10, p=0.800; grey: n=20, p=0.050; clear-none: n=7, p=0.286 |
| triage | uniform_fair | generic_network_language | 37 | 0.892 | clear-specific: n=10, p=1.000; grey: n=20, p=1.000; clear-none: n=7, p=0.429 |
| triage | mixed | specific_reference | 36 | 0.583 | grey: n=20, p=0.550; clear-specific: n=9, p=1.000; clear-none: n=7, p=0.143 |
| triage | mixed | generic_network_language | 36 | 0.750 | grey: n=20, p=1.000; clear-specific: n=9, p=0.778; clear-none: n=7, p=0.000 |

### coder2

| Env | Population | Dimension | n sample | raw sample prevalence | per-stratum (n, p_z) |
|---|---|---|---|---|---|
| commons | uniform_fair | specific_reference | 37 | 0.000 | grey: n=20, p=0.000; clear-specific: n=10, p=0.000; clear-none: n=7, p=0.000 |
| commons | uniform_fair | generic_network_language | 37 | 1.000 | grey: n=20, p=1.000; clear-specific: n=10, p=1.000; clear-none: n=7, p=1.000 |
| commons | mixed | specific_reference | 36 | 0.056 | clear-specific: n=10, p=0.200; clear-none: n=7, p=0.000; grey: n=19, p=0.000 |
| commons | mixed | generic_network_language | 36 | 0.667 | clear-specific: n=10, p=0.400; clear-none: n=7, p=0.143; grey: n=19, p=1.000 |
| triage | uniform_fair | specific_reference | 37 | 0.270 | clear-specific: n=10, p=0.600; grey: n=20, p=0.100; clear-none: n=7, p=0.286 |
| triage | uniform_fair | generic_network_language | 37 | 0.892 | clear-specific: n=10, p=1.000; grey: n=20, p=1.000; clear-none: n=7, p=0.429 |
| triage | mixed | specific_reference | 36 | 0.556 | grey: n=20, p=0.600; clear-specific: n=9, p=0.778; clear-none: n=7, p=0.143 |
| triage | mixed | generic_network_language | 36 | 0.806 | grey: n=20, p=1.000; clear-specific: n=9, p=1.000; clear-none: n=7, p=0.000 |

## What this does not resolve

This does not establish whether self-reports reflect the computation that actually produced the action. That limitation is unaffected by anything above and stays in the paper.
