# Main study -- real computed results (H1 + sanctioning)

Computed directly from `tools/reports/raw_exports/main_study/` -- pooled
degree-payoff Pearson r (95% CI via Fisher z, n = pooled agent-runs across
all found replicates in the cell), mean Gini of final net payoff (95% CI
across replicates), and compliance rate (fraction of persona-consistent
actions, pooled across all agents/rounds in the cell).

**Not included here** (real numbers, but need a separate pass): H2
LLM-judge self-report classification; non-LLM baseline comparison;
mixed-effects variance decomposition.

| Env | Population | Topology | Sanctioning | n reps | r [95% CI] | Gini [95% CI] | Compliance | Mean sanctions/run | Sanctioned/mean degree |
|---|---|---|---|---|---|---|---|---|---|
| commons | uniform_fair | fully_connected | off | 8/8 | n/a | 0.119 [-0.114, 0.351] | 100.0% | -- | -- |
| commons | uniform_fair | fully_connected | on | 8/8 | n/a | 0.000 [0.000, 0.000] | 100.0% | 0.0 | -- |
| commons | uniform_fair | clustered | off | 20/20 | 0.961 [0.953, 0.968] | 0.323 [0.298, 0.348] | 100.0% | -- | -- |
| commons | uniform_fair | clustered | on | 20/20 | 0.970 [0.963, 0.975] | 0.333 [0.307, 0.359] | 100.0% | 0.0 | -- |
| commons | uniform_fair | scale_free | off | 20/20 | 0.973 [0.967, 0.978] | 0.538 [0.516, 0.560] | 100.0% | -- | -- |
| commons | uniform_fair | scale_free | on | 20/20 | 0.981 [0.977, 0.985] | 0.584 [0.558, 0.611] | 100.0% | 0.1 | 0.54x |
| commons | mixed | fully_connected | off | 8/8 | n/a | 0.494 [0.475, 0.513] | 47.1% | -- | -- |
| commons | mixed | fully_connected | on | 8/8 | n/a | 0.480 [0.465, 0.495] | 43.1% | 24.0 | 1.00x |
| commons | mixed | clustered | off | 20/20 | 0.089 [-0.009, 0.186] | 0.423 [0.411, 0.435] | 45.9% | -- | -- |
| commons | mixed | clustered | on | 20/20 | 0.065 [-0.034, 0.162] | 0.416 [0.404, 0.429] | 37.4% | 38.5 | 1.03x |
| commons | mixed | scale_free | off | 8/8 | 0.353 [0.210, 0.482] | 0.394 [0.380, 0.409] | 42.8% | -- | -- |
| commons | mixed | scale_free | on | 8/8 | 0.298 [0.149, 0.433] | 0.395 [0.374, 0.417] | 39.4% | 29.0 | 1.59x |
| triage | uniform_fair | fully_connected | off | 8/8 | n/a | 0.428 [0.389, 0.467] | 83.1% | -- | -- |
| triage | uniform_fair | fully_connected | on | 8/8 | n/a | 0.479 [0.441, 0.517] | 80.0% | 0.5 | 1.00x |
| triage | uniform_fair | clustered | off | 8/8 | 0.381 [0.240, 0.506] | 0.367 [0.327, 0.407] | 88.9% | -- | -- |
| triage | uniform_fair | clustered | on | 8/8 | 0.466 [0.335, 0.579] | 0.354 [0.310, 0.399] | 89.6% | 0.8 | 0.96x |
| triage | uniform_fair | scale_free | off | 8/8 | 0.965 [0.952, 0.974] | 0.526 [0.490, 0.561] | 83.8% | -- | -- |
| triage | uniform_fair | scale_free | on | 8/8 | 0.947 [0.928, 0.961] | 0.523 [0.489, 0.557] | 85.1% | 2.8 | 1.68x |
| triage | mixed | fully_connected | off | 8/8 | n/a | 0.332 [0.305, 0.359] | 48.5% | -- | -- |
| triage | mixed | fully_connected | on | 8/8 | n/a | 0.340 [0.313, 0.368] | 47.9% | 0.1 | 1.00x |
| triage | mixed | clustered | off | 8/8 | 0.301 [0.153, 0.436] | 0.288 [0.272, 0.305] | 51.1% | -- | -- |
| triage | mixed | clustered | on | 8/8 | 0.362 [0.220, 0.490] | 0.295 [0.268, 0.321] | 51.6% | 1.4 | 1.00x |
| triage | mixed | scale_free | off | 8/8 | 0.714 [0.628, 0.782] | 0.375 [0.325, 0.426] | 48.0% | -- | -- |
| triage | mixed | scale_free | on | 8/8 | 0.650 [0.551, 0.732] | 0.392 [0.365, 0.418] | 47.2% | 3.0 | 2.08x |
