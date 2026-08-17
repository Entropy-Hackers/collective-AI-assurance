# Variance decomposition (r), balanced fixed-effects ANOVA

Closed-form sum-of-squares over cell/marginal means (balanced design,
8 replicates/cell -- capped there even for the 3 cells with 20, to keep
this specific analysis balanced) -- an explicit approximation of the
manuscript's `outcome ~ alignment * topology * institution + (1|seed)`
mixed-effects model: the `(1|seed)` random effect is the within-cell
residual here, not a fitted variance component. Fit separately per
environment, matching the manuscript's stated analysis model.

## commons

n = 8/cell, grand mean = 0.5724, SS total = 11.8006

| Source | % variance |
|---|---|
| population (alignment) | 85.5% |
| topology | 2.6% |
| sanctioning (institution) | 0.0% |
| population x topology | 2.1% |
| population x sanctioning | 0.0% |
| topology x sanctioning | 0.0% |
| three-way interaction | 0.0% |
| residual (within-cell, ~ (1\|seed)) | 9.7% |

## triage

n = 8/cell, grand mean = 0.5950, SS total = 5.4875

| Source | % variance |
|---|---|
| population (alignment) | 9.8% |
| topology | 55.7% |
| sanctioning (institution) | 0.4% |
| population x topology | 3.3% |
| population x sanctioning | 0.3% |
| topology x sanctioning | 1.6% |
| three-way interaction | 0.0% |
| residual (within-cell, ~ (1\|seed)) | 28.8% |

