# Isolating the LLM-specific component (full-scale, real data)

Status: **Complete. 240-run baseline study (matching H1's exact 3
topology x 2 institution x 8-replicate design, real HTTP calls through
the same harness) vs. the real 192-run main study, permutation test
(10,000 shuffles) per environment/topology/sanctioning/strategy cell.**
Answers the "isn't this just graph arithmetic?" objection with real
data at real scale, not the 200-seed pilot-stage pure-simulation
comparison (`baseline_simulation_results.md`) this supersedes for the
main study's own conditions.

Full table: `tools/reports/raw_exports/baseline_vs_real_test.md`.
Reproducible: `python3 stats_main_study.py baseline --baseline-root
reports/raw_exports/baseline_study --out ...`.

## Commons: close to mechanically guaranteed once behaviour is uniform

The **fixed** baseline (flat contribute-10-every-round, no reciprocity
logic at all) is statistically indistinguishable from real uniform_fair
LLM behaviour in every commons/topology/sanctioning combination tested
(p = 0.77, 0.14, 0.09, 0.58 -- none below 0.05). The **random** baseline
is wildly different (p < 0.0001 everywhere, real r ~0.96-0.98 vs.
random r ~0.2-0.8). Reading: once behaviour is uniform (which it
essentially is here -- compliance ~100%, see H1), the degree-payoff
correlation this produces is close to a mechanical property of the
payoff structure, not an LLM-specific finding on its own -- confirms
the pilot-stage reading at full scale, not just 3-seed illustration.

## Triage/scale_free: a real, large, clearly significant LLM-specific effect

Here the story is different and this is the important positive
result. Real LLM data (r = 0.95-0.97) is significantly *higher* than
the **reciprocal** baseline (a trivial tit-for-tat: send back to
whoever sent to you last round) in both sanctioning arms:

| Sanctioning | real r | reciprocal-baseline r | diff | p |
|---|---|---|---|---|
| off | 0.967 | 0.671 | +0.296 | **0.0001** |
| on  | 0.950 | 0.708 | +0.243 | **0.0001** |

This is the real, full-scale version of the pilot-stage claim ("the
real, reciprocity-aware LLM agents produced *more* inequality than the
simple non-LLM reciprocal heuristic") -- now a large, unambiguous,
highly significant effect, not an illustrative single comparison.
Real data is also significantly different from **fixed** (p=0.014,
p=0.0025 -- small but real gaps, real slightly lower) and from
**random** (p<0.001, real much higher). So in this condition, real
LLM behaviour sits close to but measurably below "fixed", and far
above both "random" and "reciprocal" -- a genuinely LLM-specific
degree-payoff dynamic that a trivial reciprocity rule does not
reproduce.

## Triage/clustered: real LLM agents underperform even simple heuristics

Not anticipated at pilot scale, and worth flagging clearly before it
goes anywhere near the paper. In clustered topology specifically, real
LLM data is *lower* than the fixed baseline, not higher or
indistinguishable:

| Sanctioning | real r | fixed-baseline r | diff | p |
|---|---|---|---|---|
| off | 0.337 | 0.708 | -0.372 | **0.0009** |
| on  | 0.493 | 0.708 | -0.216 | **0.0008** |

And relative to the reciprocal baseline, real data is *higher*
(off: 0.337 vs 0.018, p=0.026; on: 0.493 vs 0.160, p=0.0069) -- so
real LLM behaviour in clustered triage lands *between* the reciprocal
and fixed baselines, closer to neither. Combined with the already-
reported clustered-underperforms-in-triage finding (H1: r=0.957
commons vs. r=0.381 triage for this topology) and the referral-pattern
figure (referrals split ~50/50 within-group vs. bridge, not
concentrated), this is now a three-way-confirmed pattern: something
about clustered topology specifically degrades the correlation signal
in the trust game relative to both real commons behaviour and even
trivial non-LLM heuristics. This deserves real discussion-section
attention, not a one-line mention -- it's a genuine open question, not
resolved by this dataset.

## What this changes for the manuscript's Section 4.2

The current text's framing ("public-goods baseline comparisons
indistinguishable... trust game's reciprocal baseline is where a
genuine LLM-specific effect appears") is directionally right but was
written from pilot-stage illustrative numbers. The real data:
sharpens the commons claim (now p-values from a real permutation test,
not "close in magnitude"), sharpens and strengthens the triage/
scale_free claim (p=0.0001, not just "68% awareness + higher r"), and
adds a genuinely new, unanticipated finding (triage/clustered
underperforming) that the current manuscript text doesn't mention at
all and should.
