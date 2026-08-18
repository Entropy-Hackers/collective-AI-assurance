# Variance decomposition (gini), balanced fixed-effects ANOVA

Closed-form sum-of-squares over cell/marginal means (balanced design,
8 replicates/cell -- capped there even for the 3 cells with 20, to keep
this specific analysis balanced) -- an explicit approximation of the
manuscript's `outcome ~ alignment * topology * institution + (1|seed)`
mixed-effects model: the `(1|seed)` random effect is the within-cell
residual here, not a fitted variance component. Fit separately per
environment, matching the manuscript's stated analysis model.

Percentile bootstrap CI (95%, 10000 resamples, replicates
resampled with replacement within each cell) on every percentage below.

## commons

n = 8/cell, grand mean = 0.3719, SS total = 3.3560

| Source | % variance [95% CI] |
|---|---|
| population (alignment) | 10.5% [3.9, 17.4] |
| topology | 19.3% [8.9, 29.1] |
| sanctioning (institution) | 0.1% [0.0, 1.9] |
| population x topology | 41.3% [23.0, 56.1] |
| population x sanctioning | 0.0% [0.0, 1.2] |
| topology x sanctioning | 1.1% [0.0, 6.4] |
| three-way interaction | 1.1% [0.0, 6.2] |
| residual (within-cell, ~ (1\|seed)) | 26.6% [2.3, 48.5] |

## triage

n = 8/cell, grand mean = 0.3915, SS total = 0.7959

| Source | % variance [95% CI] |
|---|---|
| population (alignment) | 35.9% [26.5, 46.7] |
| topology | 32.9% [22.9, 44.6] |
| sanctioning (institution) | 0.4% [0.0, 2.7] |
| population x topology | 2.7% [0.6, 7.1] |
| population x sanctioning | 0.0% [0.0, 1.4] |
| topology x sanctioning | 0.6% [0.0, 3.4] |
| three-way interaction | 0.6% [0.0, 3.7] |
| residual (within-cell, ~ (1\|seed)) | 26.9% [17.0, 30.9] |

