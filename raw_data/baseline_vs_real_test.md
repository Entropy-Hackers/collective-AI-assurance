# Real LLM (uniform_fair) vs. non-LLM baseline: permutation test

Is H1's degree-payoff correlation close to mechanically guaranteed by 
the payoff structure once behaviour is uniform, or specific to real LLM 
agent behaviour? Two-sided permutation test (10,000 shuffles) on the 
difference in mean within-replicate r between the real uniform_fair LLM 
runs and each non-LLM strategy, matched by environment/topology/
sanctioning (8 replicates each side).

| Env | Topology | Sanctioning | Strategy | real r (mean) | baseline r (mean) | diff | p |
|---|---|---|---|---|---|---|---|
| commons | clustered | off | fixed | 0.962 | 0.960 | +0.0025 | 0.7670 |
| commons | clustered | off | random | 0.962 | 0.205 | +0.7572 | 0.0000 |
| commons | clustered | on | fixed | 0.970 | 0.960 | +0.0105 | 0.1398 |
| commons | clustered | on | random | 0.970 | 0.205 | +0.7653 | 0.0000 |
| commons | scale_free | off | fixed | 0.973 | 0.982 | -0.0089 | 0.0943 |
| commons | scale_free | off | random | 0.973 | 0.808 | +0.1657 | 0.0000 |
| commons | scale_free | on | fixed | 0.983 | 0.986 | -0.0025 | 0.5758 |
| commons | scale_free | on | random | 0.983 | 0.813 | +0.1707 | 0.0000 |
| triage | clustered | off | fixed | 0.337 | 0.708 | -0.3716 | 0.0009 |
| triage | clustered | off | random | 0.337 | 0.349 | -0.0125 | 0.9121 |
| triage | clustered | off | reciprocal | 0.337 | 0.018 | +0.3191 | 0.0256 |
| triage | clustered | on | fixed | 0.493 | 0.708 | -0.2156 | 0.0008 |
| triage | clustered | on | random | 0.493 | 0.349 | +0.1435 | 0.1533 |
| triage | clustered | on | reciprocal | 0.493 | 0.160 | +0.3330 | 0.0069 |
| triage | scale_free | off | fixed | 0.967 | 0.982 | -0.0157 | 0.0142 |
| triage | scale_free | off | random | 0.967 | 0.850 | +0.1167 | 0.0001 |
| triage | scale_free | off | reciprocal | 0.967 | 0.671 | +0.2961 | 0.0001 |
| triage | scale_free | on | fixed | 0.950 | 0.983 | -0.0333 | 0.0025 |
| triage | scale_free | on | random | 0.950 | 0.818 | +0.1323 | 0.0021 |
| triage | scale_free | on | reciprocal | 0.950 | 0.708 | +0.2425 | 0.0001 |
