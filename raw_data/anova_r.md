# Variance decomposition (r), balanced fixed-effects ANOVA

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

n = 8/cell, grand mean = 0.5724, SS total = 11.8006

| Source | % variance [95% CI] |
|---|---|
| population (alignment) | 85.5% [80.0, 91.2] |
| topology | 2.6% [0.8, 5.4] |
| sanctioning (institution) | 0.0% [0.0, 0.9] |
| population x topology | 2.1% [0.5, 4.6] |
| population x sanctioning | 0.0% [0.0, 1.0] |
| topology x sanctioning | 0.0% [0.0, 0.9] |
| three-way interaction | 0.0% [0.0, 0.9] |
| residual (within-cell, ~ (1\|seed)) | 9.7% [5.1, 12.3] |

## triage

n = 8/cell, grand mean = 0.5950, SS total = 5.4875

| Source | % variance [95% CI] |
|---|---|
| population (alignment) | 9.8% [3.4, 20.0] |
| topology | 55.7% [45.0, 67.4] |
| sanctioning (institution) | 0.4% [0.0, 3.4] |
| population x topology | 3.3% [0.3, 10.5] |
| population x sanctioning | 0.3% [0.0, 3.8] |
| topology x sanctioning | 1.6% [0.0, 6.2] |
| three-way interaction | 0.0% [0.0, 2.5] |
| residual (within-cell, ~ (1\|seed)) | 28.8% [16.7, 34.0] |

