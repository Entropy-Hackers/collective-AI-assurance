# Cross-model robustness: final, 4 models at full replicate scale

Status: **Complete.** DeepSeek (main study), Qwen3.5-122b, GLM-5.2,
Mistral-medium-3.5 all at the main study's own 8-replicate standard
on the two central cells (uniform_fair x scale_free, both
environments) -- not pilot scale. All four free/no-cost, all via
e-INFRA CZ except DeepSeek (main study itself).

## Results

| Model | Commons r [95% CI] | Triage r [95% CI] |
|---|---|---|
| DeepSeek-v4-flash (main study) | 0.973 [0.967, 0.978] | 0.965 [0.952, 0.974] |
| Qwen3.5-122b | 0.983 [0.977, 0.988] | 0.952 [0.935, 0.965] |
| GLM-5.2 | 0.979 [0.972, 0.985] | 0.960 [0.946, 0.971] |
| Mistral-medium-3.5 | 0.981 [0.974, 0.986] | 0.954 [0.938, 0.966] |

## Heterogeneity test (Cochran's Q / I^2)

Requested once 3+ models are at real scale (2 models isn't worth
testing). Pure-stdlib implementation (`cochran_q_heterogeneity.py`,
regularized incomplete gamma function for the chi-square p-value,
verified against known chi-square critical values before trusting it
on real data). Fisher-z transformed correlations, fixed-effect
weighting by n-3.

| Environment | Q | df | p | I^2 | Pooled r |
|---|---|---|---|---|---|
| Commons | 4.467 | 3 | 0.215 | 32.8% | 0.9795 |
| Triage  | 2.284 | 3 | 0.516 | 0.0%  | 0.9581 |

**Neither environment shows statistically significant heterogeneity.**
The observed spread across providers (r=0.95-0.99) is consistent with
sampling noise around one shared effect, not real between-provider
variance -- I^2=0% in triage means essentially none of the observed
variation is attributable to real heterogeneity; commons' I^2=33% is
higher but still far from significant at n=4 providers (p=0.215).

**This is a real, quantified upgrade from the manuscript's current
framing** ("two-model comparison at full scale, three further
backends only at pilot scale and therefore not reported") to: four
independent model providers/architectures replicate H1 at full
replicate scale with no statistically detectable heterogeneity between
them (Cochran's Q, p>0.2 both environments).

## What's still not at full scale

- **GPT-4o**: pilot scale only (3 replicates), dropped from further
  MUG spend by decision (2026-08-11).
- **Mistral-Large-3** (the MUG-hosted version -- distinct from
  Mistral-medium-3.5 above, which is a different model via e-INFRA
  CZ): blocked, MUG gateway permanently IP-banned this host for
  repeated auth failures. Needs the user to resolve with MedUniGraz,
  not a code/data problem.

## Note on GLM-5.2 and Mistral: resolved via a different path than originally planned

Both were previously stuck: GLM-5.2 via the paid z.ai gateway (cost-
excluded 2026-08-07 after a real cost surprise), Mistral-Large-3 via
MUG (IP-banned). Both are now unblocked via e-INFRA CZ instead --
`glm-5.2` and `mistral-medium-3.5` are different, free, hosted
endpoints on the same gateway already used for DeepSeek/Qwen, found
live-available via `curl .../v1/models` on 2026-08-12. Strictly
better than the original paths for these two, not a workaround.

## Reproducing this

```
cd tools
python3 cochran_q_heterogeneity.py
```
