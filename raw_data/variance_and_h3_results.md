# Variance decomposition and H3 equivalence test (real, from the 192-run dataset)

Status: **Both computed, pure-stdlib, from `tools/stats_main_study.py`
against the full completed main study. H3 is confirmed in one of its
two confirmatory cells but NOT the other, and this now holds even
after tripling the ambiguous cells' replicate count (8 -> 20, see
"Resolution after extra replicates" below) -- this is a real result,
not a bug or a small-sample artifact.**

Methodology: closed-form balanced fixed-effects ANOVA (sum-of-squares
over cell/marginal means, exact for this balanced 8-reps/cell design,
no numpy/scipy needed) as an explicit, documented approximation of the
manuscript's stated `outcome ~ alignment * topology * institution +
(1|seed)` mixed-effects model -- the `(1|seed)` term is the within-cell
residual here, not a fitted variance component. H3's equivalence test
uses bootstrap resampling (10,000 draws, percentile CI) instead of
parametric TOST, since no `scipy.stats.t` is available; same technique
reused for the real-vs-baseline permutation test once baseline data
exists at full scale.

## Variance decomposition

On the degree--payoff correlation `r` (fully_connected excluded --
structurally undefined, zero degree variance by construction; 2x2x2
design, topology = {clustered, scale_free}):

| Environment | Population | Topology | Sanctioning | Pop x Topo | Residual |
|---|---|---|---|---|---|
| Commons | 85.5% | 2.6% | 0.0% | 2.1% | 9.7% |
| Triage  | 9.8% | 55.7% | 0.4% | 3.3% | 28.8% |

On Gini (all 3 topology levels, full 2x3x2 design):

| Environment | Population | Topology | Sanctioning | Pop x Topo | Residual |
|---|---|---|---|---|---|
| Commons | 10.5% | 19.3% | 0.1% | 41.3% | 26.6% |
| Triage  | 35.9% | 32.9% | 0.4% | 2.7% | 26.9% |

Point estimates only, for a compact overview. Full 95% percentile
bootstrap CI (10,000 resamples, replicates resampled with replacement
within each cell) on every one of these values -- including the
interaction and residual terms omitted from the compact tables above
-- is in `anova_r.md` / `anova_gini.md`, not duplicated here.

Two things worth flagging before this goes anywhere near the paper:

1. **The r-based and Gini-based decompositions tell different
   stories**, and both are real. For `r`, commons is population-
   dominated (85.5%) while triage is topology-dominated (55.7%) --
   consistent with the already-reported clustered-underperforms-in-
   triage finding. For Gini, commons has a large population x topology
   interaction (41.3%) that swamps either main effect alone. The
   manuscript's placeholder framing ("topology 46%, alignment 11%,
   institution 4%, residual 39%, pooled across environments") doesn't
   match either real table -- it was an extrapolated illustrative
   number, and pooling across environments hides exactly the
   environment-dependence that turns out to be the more interesting
   real finding. This needs a real rewrite, not a placeholder swap.
2. Sanctioning's main-effect share is ~0% in every table -- consistent
   with (not proof of, see H3 below) "sanctioning is symbolic."

## H3: does sanctioning move Gini within a pre-specified null band?

**Pinned claim (confirmatory scope: uniform_fair x scale_free, both
environments):** sanctioning does not reduce Gini inequality of final
payoffs; the on/off effect on Gini is statistically indistinguishable
from zero within a pre-specified practical-equivalence margin of
+/-0.05. The other 10 cells (per environment) are descriptive only,
same asymmetric scope H1 itself uses.

| Env | Population | Topology | Confirmatory | n off/on | delta Gini | 95% CI | Equivalent? |
|---|---|---|---|---|---|---|---|
| Commons | uniform_fair | scale_free | **yes** | 20/20 | +0.0460 | [+0.0124, +0.0791] | **NO** |
| Triage  | uniform_fair | scale_free | **yes** | 8/8 | -0.0029 | [-0.0486, +0.0425] | yes |

**H3 is only confirmed in one of its two confirmatory cells.** In
triage/uniform_fair/scale_free (n=8) the CI sits entirely inside
+/-0.05 -- clean equivalence, matches the pinned claim. In
commons/uniform_fair/scale_free (n=20 -- extended from the original
n=8 specifically to check this boundary case, see "Resolution after
extra replicates" below), the CI is [+0.0124, +0.0791]: it excludes
zero (there is a real, detectable, small *increase* in Gini with
sanctioning on) and its upper bound exceeds the +/-0.05 margin -- so
this cell is neither "equivalent to zero" nor "a clearly large
effect," it's a real, modest, statistically non-zero increase that the
pre-specified margin doesn't resolve either way. More data narrowed
the CI (was [+0.0044, +0.0857] at n=8) without changing that
conclusion -- this is not a small-sample artifact.

**Implication for the paper's H3 as currently pinned:** the claim needs
either (a) narrowing to triage only (drop the "even in
scale-free/uniform-fair" framing that implied both), or (b) reframing
H3 as environment-conditional from the start, consistent with how the
topology finding itself turned out to be environment-dependent.
(Running more replicates specifically for this cell was already tried
-- see "Resolution after extra replicates" below -- and narrowed the
CI without resolving which side of the margin it lands on, so that
option is exhausted, not still open.) Descriptive cells (below, not
part of the confirmatory claim) all land inside the margin at current
replicate counts, including commons/uniform_fair/clustered (n=20:
+0.0101 [-0.0238, +0.0463], equivalent) -- at n=8 this cell had also
excluded zero and exceeded the margin, the same pattern as the
confirmatory cell, but resolved to clean equivalence once extended;
the confirmatory cell did not.

Full 12-row table (all cells, both environments, current replicate
counts) in `tools/reports/raw_exports/h3_equivalence_full.md`
(regenerable via `python3 stats_main_study.py h3`).

## Resolution after extra replicates (n=8 -> n=20, 2026-08-12)

Three cells were too close to call at n=8 to trust either way (see
STATUS.md/the conversation this came out of): commons/mixed/clustered
(H1's r looked null but noisy) and the two commons/uniform_fair cells
above (H3 boundary). 12 more replicates each (72 additional runs
total) resolved all three -- two cleanly, one against the original H3
framing:

| Cell | n=8 result | n=20 result | Resolution |
|---|---|---|---|
| commons/mixed/clustered (H1, r) | off: 0.020 [-0.136,0.175]; on: 0.048 [-0.108,0.202] | off: 0.089 [-0.009,0.186]; on: 0.065 [-0.034,0.162] | Point estimate moved up slightly, CI still spans/hugs zero -- resolves toward **genuinely weak/near-null**, not just an artifact of small n. |
| commons/uniform_fair/clustered (H3, descriptive) | +0.0501 [+0.003,+0.099], NOT equivalent | +0.0101 [-0.024,+0.046], **equivalent** | Resolved **in favour of H3** at this cell. |
| commons/uniform_fair/scale_free (H3, **confirmatory**) | +0.0435 [+0.004,+0.086], NOT equivalent | +0.0460 [+0.012,+0.079], **still NOT equivalent** | More data narrowed the CI but it still excludes zero and still exceeds the +/-0.05 margin. This is now a **resolved, not ambiguous, negative result for H3's original two-cell framing**: there is a real, small, statistically distinguishable increase in Gini from sanctioning in this specific confirmatory cell, and 20 replicates isn't a small-sample problem hiding equivalence -- it's a real effect too small to call "large" but too real to call "zero." |

**Bottom line for the manuscript**: H3 as originally pinned ("sanctioning
doesn't move Gini, confirmed in both uniform_fair x scale_free
cells") does not hold. The triage confirmatory cell supports it
cleanly; the commons confirmatory cell does not, and more data made
that clearer, not fuzzier. Recommend reframing H3 as
environment-conditional (matches how the topology/H1 finding turned
out to be environment-dependent too) rather than narrowing scope to
hide the commons result.

## Reproducing this

```
cd tools
python3 stats_main_study.py replicates --out replicate_metrics.csv
python3 stats_main_study.py anova --metric r --out anova_r.md
python3 stats_main_study.py anova --metric gini --out anova_gini.md
python3 stats_main_study.py h3 --out h3_equivalence.md
```
