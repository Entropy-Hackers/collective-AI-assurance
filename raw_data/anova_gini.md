# Variance decomposition (gini), balanced fixed-effects ANOVA

Closed-form sum-of-squares over cell/marginal means (balanced design,
8 replicates/cell -- capped there even for the 3 cells with 20, to keep
this specific analysis balanced) -- an explicit approximation of the
manuscript's `outcome ~ alignment * topology * institution + (1|seed)`
mixed-effects model: the `(1|seed)` random effect is the within-cell
residual here, not a fitted variance component. Fit separately per
environment, matching the manuscript's stated analysis model.

## commons

n = 8/cell, grand mean = 0.3719, SS total = 3.3560

| Source | % variance |
|---|---|
| population (alignment) | 10.5% |
| topology | 19.3% |
| sanctioning (institution) | 0.1% |
| population x topology | 41.3% |
| population x sanctioning | 0.0% |
| topology x sanctioning | 1.1% |
| three-way interaction | 1.1% |
| residual (within-cell, ~ (1\|seed)) | 26.6% |

## triage

n = 8/cell, grand mean = 0.3915, SS total = 0.7959

| Source | % variance |
|---|---|
| population (alignment) | 35.9% |
| topology | 32.9% |
| sanctioning (institution) | 0.4% |
| population x topology | 2.7% |
| population x sanctioning | 0.0% |
| topology x sanctioning | 0.6% |
| three-way interaction | 0.6% |
| residual (within-cell, ~ (1\|seed)) | 26.9% |

