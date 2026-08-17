# H2 classifier validation: keyword vs. LLM-judge

Judge model: `deepseek-chat` (DeepSeek), temperature 0, blind to keyword labels.
Sample: 120 reason texts (60 commons, 60 triage), seed=42.

## Dimension: `aware`
- Keyword classifier: 45/120 positive (37.5%)
- LLM judge: 52/120 positive (43.3%)
- Raw agreement: 92.5%
- Cohen's kappa: 0.845
  - commons/uniform_fair: n=27, kw_pos=0, judge_pos=0, agreement=100.0%, kappa=1.000
  - commons/mixed: n=33, kw_pos=0, judge_pos=5, agreement=84.8%, kappa=0.000
  - triage/uniform_fair: n=31, kw_pos=29, judge_pos=30, agreement=90.3%, kappa=-0.045
  - triage/mixed: n=29, kw_pos=16, judge_pos=17, agreement=96.6%, kappa=0.930

## Dimension: `fair`
- Keyword classifier: 79/120 positive (65.8%)
- LLM judge: 80/120 positive (66.7%)
- Raw agreement: 87.5%
- Cohen's kappa: 0.720
  - commons/uniform_fair: n=27, kw_pos=27, judge_pos=27, agreement=100.0%, kappa=1.000
  - commons/mixed: n=33, kw_pos=16, judge_pos=16, agreement=93.9%, kappa=0.879
  - triage/uniform_fair: n=31, kw_pos=25, judge_pos=27, agreement=74.2%, kappa=0.053
  - triage/mixed: n=29, kw_pos=11, judge_pos=10, agreement=82.8%, kappa=0.627

## Human calibration (2026-08-06)

Third anchor, requested after the keyword-vs-judge comparison above:
blind human coding (the project lead) of the same 30-item spot-check
sample, against a fixed operational definition
(`raw_exports/h2_human_coding_sheet.md`, `..._aware_redo.md`).

**First pass on `aware` was unusable** (29/30 marked positive,
kappa≈0.04–0.06 against both automated classifiers) — a definition
drift, not a real disagreement: the coder had drifted from "references
a specific other agent's structural position or reciprocity history"
toward "the text contains any justification at all" (nearly every
text does). Caught via a concrete tell — two near-identical texts
("My patient's needs come first..." vs "My patient comes first...")
received opposite labels. Redone with two anchor examples (one clear
yes, one clear no) added directly to the sheet; `fair` needed no
redo (solid on the first pass).

**Final result, both dimensions in the "substantial agreement" range**
(Landis & Koch, 0.61–0.80):

| Dimension | Human vs. keyword | Human vs. judge | Keyword vs. judge (this n=30) |
|---|---|---|---|
| aware | κ=0.713 | κ=0.661 | κ=0.661 |
| fair  | κ=0.789 | κ=0.658 | κ=0.724 |

The judge tracks the human anchor about as closely as the keyword
classifier does — the LLM-judge switch to primary H2 metric
(2026-08-05) is now validated against all three anchors (keyword,
judge, human), not just the first two. Worth keeping the definition
drift as a documented methods note: it's a real illustration of how
easy it is for even a careful human coder to drift from an operational
definition without a concrete example pinned down, which is exactly
the failure mode the two automated classifiers don't have (they apply
the same rule every time) — arguably a point in favour of using the
LLM judge at main-study scale, where redoing thousands of texts by
hand isn't an option anyway.

## Re-validation against the actual full-scale configuration (2026-08-12)

The validation above (and the numbers in the table) used
`validate_h2_classifier.py`'s own judge call: `deepseek-chat` (the
unpinned floating alias, before the later pinning fix) against
DeepSeek's own commercial API. The actual full-192-run H2
classification (`run_h2_full.py`) uses `h2_judge.py`'s current
config: the pinned `deepseek-v4-flash`, routed through e-INFRA CZ, not
DeepSeek's commercial API (switched 2026-08-12, "wir verwenden
deepseek ja nur in CZ"). Different serving infrastructure for a
nominally-same model name is exactly the kind of thing that shouldn't
be assumed identical without checking -- so the same blind 30-item
human-coded sample was re-run through the current config
(`revalidate_h2_judge.py`).

| Dimension | Original (DeepSeek commercial API, `deepseek-chat`) | Current (e-INFRA CZ, pinned `deepseek-v4-flash`) |
|---|---|---|
| aware | κ=0.661 | κ=0.661 -- **identical** |
| fair  | κ=0.658 | κ=0.507 -- **dropped, substantial -> moderate** (Landis & Koch: 0.61-0.80 vs. 0.41-0.60) |

**`aware` is unaffected. `fair` is not.** On the exact same 30 items,
`fair` agreement with the human anchor measurably degraded when
switching from DeepSeek's own API to e-INFRA CZ's hosted version --
not just noise at n=30 (same items, same human labels, only the
judge's serving backend changed). Human-positive/judge-positive counts:
18 human-positive vs. 19 judge-positive on this run (see
`revalidate_h2_judge.py`'s output for the raw counts). This does not
invalidate the H2 `aware` results (unaffected) but means the `fair`
dimension's real-scale numbers (`h2_full_scale_results.md`) carry a
weaker validation claim than originally stated -- "substantial
agreement" no longer holds for `fair` under the configuration actually
used at scale.

## Prompt fix, 2026-08-12: root cause found and fixed, not just documented

Inspected all 7 `fair` and 5 `aware` disagreements individually rather
than treating the kappa drop as unexplained noise. Two real,
fixable patterns, not random serving-backend variance:

1. **False positives on purely self-interested "my own patient"
   text.** "My patient's needs come first; keeping the full dose for
   them" and "own patient gets the full resource every round" were
   both labelled `fair=true` despite having zero cooperation/group
   framing. Root cause: the old prompt's own example phrase "best for
   the network/patients" pattern-matches against bare "patient"
   mentions regardless of whether the network is actually invoked.
2. **Undefined boundary** between a general fairness statement and a
   specific-relationship reciprocity statement ("TMX-10 reciprocated
   generously... continuing the strongest proven cooperative
   relationship") -- human and judge drew this line differently
   because the prompt never said which way it should go.

Fixed by adding explicit anchor examples to `JUDGE_PROMPT_TEMPLATE`
(same technique that fixed the `aware` dimension's original definition
drift): an explicit self-interested-vs-group-serving contrast for
`fair`, and an explicit ruling that specific-relationship cooperation
language counts as `fair=true` too. Re-validated on the identical
30-item sample:

| Dimension | Original (commercial API) | e-INFRA CZ, prompt v1 | e-INFRA CZ, prompt v2 (fixed) |
|---|---|---|---|
| fair  | κ=0.658 | κ=0.507 | **κ=0.857** |
| aware | κ=0.661 | κ=0.661 | **κ=0.724** |

Both dimensions now exceed the original validation, not just recover
to it. The cache is versioned by prompt (`h2_judge.py`'s
`PROMPT_VERSION`/`DEFAULT_CACHE_PATH`) specifically so a prompt change
like this can never silently mix old and new classifications under one
cache key again. The full corpus (all runs including the 72 extra
replicates, ~59k unique texts) is being fully re-classified under
prompt v2 -- `h2_full_scale_results.md`'s numbers predate this fix and
will be refreshed once that completes.

## Disagreement examples (up to 8 per dimension)

### `aware` disagreements
- **commons/mixed__clustered__rep2/MX-03** — kw=False, judge=True: "Pool is small and there's a free-rider; I'll keep the commons alive with a modest contribution but hold back more until others show reciprocity."
- **triage/uniform_fair__clustered__rep3/TUF-11** — kw=True, judge=False: "Refer in good faith to TUF-15, whose overall record of using referred resources best serves patients; trusting the network over the long run."
- **commons/mixed__clustered__rep1/MX-10** — kw=False, judge=True: "Still paying my fair share to keep the commons alive despite heavy over-extraction by others."
- **commons/mixed__scale_free__rep3/MX-07** — kw=False, judge=True: "Continuing my fair contribution to keep the shared pool alive despite persistent over-extraction by others."
- **commons/mixed__scale_free__rep2/MX-18** — kw=False, judge=True: "Contributions keep getting absorbed by others; taking direct value while the pool is at a reasonable level."
- **commons/mixed__fully_connected__rep2/MX-18** — kw=False, judge=True: "The pool is down to 5 and gets drained every round anyway; I'll recover a little of what I've put in rather than keep subsidizing free-riders."
- **triage/uniform_fair__clustered__rep2/TUF-06** — kw=False, judge=True: "Still cooperating fully; but TUF-02's reputation has slipped, so route this referral to a fully trusted partner (TUF-10) this round."
- **triage/uniform_fair__scale_free__rep1/TUF-17** — kw=False, judge=True: "Staying true to my cooperative role; TUF-06 remains the strongest node with the best long-run reciprocity record."

### `fair` disagreements
- **commons/mixed__clustered__rep2/MX-03** — kw=False, judge=True: "Pool is small and there's a free-rider; I'll keep the commons alive with a modest contribution but hold back more until others show reciprocity."
- **triage/uniform_fair__scale_free__rep1/TUF-19** — kw=True, judge=False: "TUF-07 leads the network in reputation (8.0); I'll keep trusting the flow to the best-placed specialist."
- **triage/uniform_fair__scale_free__rep2/TUF-03** — kw=True, judge=False: "Network remains cooperative; noting TUF-01's lagging reputation, I continue the rotation by referring the full dose to a well-reputed colleague."
- **triage/mixed__clustered__rep3/TMX-04** — kw=False, judge=True: "Consistent positive reciprocity across rounds; keeping up good-faith referrals to the highest-regarded colleague."
- **triage/uniform_fair__fully_connected__rep3/TUF-02** — kw=False, judge=True: "Recent returns have been sparse, but my cumulative position is still strongly positive and TUF-03 remains the only flagged colleague; I stay consistent with my stance and keep referring in good faith "
- **triage/uniform_fair__scale_free__rep2/TUF-05** — kw=False, judge=True: "Round 6: TUF-02 continues to return strong value on every referral (20 back again last round); keeping the resource flowing through this well-placed colleague remains best for the whole network."
- **triage/uniform_fair__fully_connected__rep1/TUF-04** — kw=False, judge=True: "Round 7: continued positive reciprocation from the network; referring on to another colleague in good faith rather than hoarding."
- **commons/mixed__scale_free__rep1/MX-09** — kw=True, judge=False: "Past the midpoint with the pool rebuilt to 16.5 and the cooperative core still replenishing, I'll take a larger share now since extraction clearly maximizes my payoff."