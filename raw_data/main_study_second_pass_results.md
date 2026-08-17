# Second-pass results: H2 (fixed prompt, full corpus), 4-model cross-model confirmation, H2-vs-structure

Status: **All complete.** Follows up on `main_study_results.md` and
`h2_full_scale_results.md` with (1) the corrected full-corpus H2
classification after the `fair`-dimension prompt fix, (2) two more
models (GLM-5.2, Mistral-medium-3.5) confirmed at real replicate
scale via e-INFRA CZ, and (3) the actual H2-vs-structural-position
correlation the manuscript's H2 section describes but the earlier
cell-aggregate-only output couldn't answer.

## Cross-model: 4 of 5 models now at real replicate scale

All via e-INFRA CZ except DeepSeek (main study, 192 runs). Same 2
central cells (uniform_fair x scale_free, both environments), 8
replicates each -- the main study's own standard, not pilot scale.

| Model | Commons r [95% CI] | Triage r [95% CI] |
|---|---|---|
| DeepSeek-v4-flash (main study) | 0.973 [0.967, 0.978] | 0.965 [0.952, 0.974] |
| Qwen3.5-122b | 0.983 [0.977, 0.988] | 0.952 [0.935, 0.965] |
| GLM-5.2 | 0.979 [0.972, 0.985] | 0.960 [0.946, 0.971] |
| Mistral-medium-3.5 | 0.981 [0.974, 0.986] | 0.954 [0.938, 0.966] |

Remarkably consistent -- all four models land in r=0.95-0.99 across
both environments. H1 is clearly not specific to any one model,
architecture, or provider. GPT-4o remains the only pilot-scale
exception (dropped from further MUG spend); Mistral-Large-3 (the MUG
version, distinct from this e-INFRA CZ Mistral-medium-3.5) remains
blocked by the MUG IP ban.

GLM-5.2 and Mistral-medium-3.5 were previously either cost-excluded
(GLM, via the paid z.ai gateway) or infrastructure-blocked (Mistral,
via MUG) -- both are free and unblocked via e-INFRA CZ instead, a
strictly better path than the original providers for these two.

## H2, full corpus, prompt v2 (fixed)

All 264 run exports (192 main-study + 72 extra replicates), 59,440
unique texts, re-classified under the fixed prompt (see
`h2_classifier_validation.md` for the fix and re-validation). Real
shifts from the v1 numbers reported in `h2_full_scale_results.md`,
not just noise -- direction is consistent but magnitude moved,
especially in triage:

| Population | Env | v1 aware % range | v2 aware % range | v1 fair % range | v2 fair % range |
|---|---|---|---|---|---|
| uniform_fair | commons | 0.1-0.6% | 0.1-0.2% | 100.0% | 100.0% |
| uniform_fair | triage | 82.2-90.7% | 68.9-81.4% | 74.9-85.8% | 87.2-91.8% |
| mixed | commons | 9.1-12.2% | 6.4-9.2% | 48.1-52.7% | 49.2-53.6% |
| mixed | triage | 58.8-60.4% | 52.8-55.3% | 37.9-44.8% | 47.1-50.0% |

`fair` went up in triage (both populations) -- the fixed prompt now
correctly counts specific-relationship cooperation language as
`fair=true`, which the old prompt under-counted. `aware` went down
across the board -- the fixed prompt no longer over-triggers on
generic pool-state or "despite over-extraction by others" phrasing.
Full table: `h2_full_results_v2.md` / `raw_exports/h2_full_by_cell_v2.csv`.

## H2 vs. structural position: does awareness track advantage?

The manuscript claims "advantaged and disadvantaged agents talk about
reciprocity at similar rates" (pilot-stage, illustrative). Checked for
real: `h2_per_agent.py` builds per-agent-per-replicate aware/fair
rates (5,280 agent-replicate rows, all 264 runs), joined against each
agent's own degree and net payoff (`h2_vs_structure.py`).

| Population/env | n | aware vs degree | aware vs net_payoff |
|---|---|---|---|
| commons/uniform_fair | 1920 | r=+0.049 [+0.004,+0.093] | r=+0.034 [-0.010,+0.079] |
| commons/mixed | 1440 | r=-0.089 [-0.140,-0.038] | r=-0.039 [-0.091,+0.012] |
| triage/uniform_fair | 960 | r=-0.183 [-0.244,-0.122] | r=+0.135 [+0.073,+0.197] |
| triage/mixed | 960 | r=+0.005 [-0.058,+0.069] | r=-0.039 [-0.091,+0.012] |

**Correct framing: small in magnitude, but at this sample size
(n=960-1920), several are statistically distinguishable from zero.**
"No correlation" is not quite right -- "a real but small correlation,
not the driver of the outcome" is more accurate and more defensible.
The most interesting real pattern: in triage/uniform_fair, awareness
language correlates *negatively* with degree (r=-0.183) but
*positively* with net payoff (r=+0.135) -- the same population/
environment, opposite signs depending on which structural variable you
check. Worth a real sentence in the paper rather than the pilot's flat
"did not correlate" framing, which slightly overclaims a clean null.

## Reproducing this

```
cd tools
python3 h2_per_agent.py --out reports/raw_exports/h2_per_agent.csv
python3 h2_vs_structure.py --h2-csv reports/raw_exports/h2_per_agent.csv
python3 run_h2_full.py --out reports/h2_full_results_v2.md --csv reports/raw_exports/h2_full_by_cell_v2.csv
```
