# H3's residual effect: cue artifact, not institutional power (resolved)

Status: **Complete, decisive.** H3's confirmatory
commons/uniform_fair/scale_free cell showed a real, small, non-zero
increase in Gini when sanctioning was on (see
`variance_and_h3_results.md`) that a bootstrap equivalence test never
resolved as "no effect," even at n=20. Andreas's hypothesis: this is
a prompt-presentation artifact (the textual cue that sanctioning is
possible changes behaviour on its own) rather than a real
institutional effect (agents actually being sanctioned, or the threat
having real teeth, changing the outcome). Tested directly with a new
third condition.

## Method

Added `sanctioning_cue` as a value distinct from `sanctioning` in
`--institutions` (`run_commons.py`/`run_triage.py`, 2026-08-16):
appends the identical `SANCTIONING_CLAUSE` to the round prompt, but
does **not** set `institutions.sanctioning_enabled=True` on the
backend -- confirmed directly (`curl .../sanction` under this
condition returns `403 sanctioning is not enabled in this experiment
condition`) that every `/sanction` call is still rejected, regardless
of the cue. `society_sanction` is unconditionally in every agent's
tool schema either way (`SOCIETY_TOOLS` in `lightweight_agent.py`
never varies) -- only the prompt cue and the backend's enforcement now
vary independently, which they didn't before (both were driven by the
same `"sanctioning" in institutions` check).

Ran 8 replicates of `sanctioning_cue` on the confirmatory cell
(commons/uniform_fair/scale_free), same harness, same registries as
the real main study.

## Result

| Condition | n | Gini [95% CI] |
|---|---|---|
| off (no cue, no power) | 8 | 0.538 [0.481, 0.596]* |
| **cue_only** (cue, no power) | 8 | **0.606 [0.549, 0.662]** |
| on (cue, real power) | 8 | 0.559 [0.497, 0.622]* |

*first 8 replicates of the n=20 off/on data, matched to `cue_only`'s
n=8 for a fair like-for-like comparison; the full n=20 numbers are in
`variance_and_h3_results.md`.

Bootstrap CI on the deltas (10,000 resamples, same method as H3's own
equivalence test):

| Comparison | delta Gini | 95% CI | Excludes zero? |
|---|---|---|---|
| cue_only - off | +0.081 | [+0.011, +0.145] | **yes** |
| on - cue_only  | -0.044 | [-0.106, +0.021] | no |

**The cue alone reproduces the full effect.** cue_only is
significantly higher than off (real, non-zero increase from the cue
by itself, no institutional power involved at all). on vs. cue_only
shows no significant difference -- if anything cue_only's point
estimate is *higher* than on's. This is the pattern predicted by the
prompt-presentation-artifact hypothesis, not the real-institutional-
effect hypothesis (which would predict cue_only tracks off, not on).

## Implication for the paper

H3's residual commons/uniform_fair/scale_free effect should be
attributed to the sanctioning *cue* changing agent behaviour (plausibly
more self-protective/defensive extraction once agents are told
sanctioning is a live possibility), not to sanctioning *actually
happening* or having real teeth -- consistent with, and now
mechanistically explaining, the already-established finding that
sanctioning doesn't touch the resource ledger (Section 4.4). This
strengthens rather than undermines the paper's "sanctioning is
symbolic" claim: even the mere announcement of a symbolic institution
measurably changes behaviour, while the institution's real
enforcement adds nothing detectable on top of that.

## Reproducing this

```
cd tools
python3 run_commons.py --service-url <mainstudy-url> --admin-token <token> \
  --agents <20 uniform_fair commons agents> --topology scale_free \
  --inter-cluster-edges 40 --rounds 15 --institutions reputation,sanctioning_cue \
  --reset-first --agent-mode lightweight --lightweight-registry <registry> \
  --lightweight-base-url <e-infra-cz-url> --lightweight-model deepseek-v4-flash \
  --max-parallel 4 --timeout 120
```
