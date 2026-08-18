# Why collective AI assurance cannot target agents or networks in isolation

Companion repository for the study, providing its code and data.

## Abstract

> AI governance increasingly targets coordination between agents
> rather than agents in isolation, but which feature of an interacting
> population produces a collective outcome is untested. We varied
> agent disposition, topology, interaction mechanic, and peer
> sanctioning factorially across 264 runs of two multi-agent games,
> with matched non-LLM baselines and four model families. Structural
> and behavioural causes prove separable: a non-reasoning bot exactly
> reproduces the public-goods game's degree–payoff relationship, while
> in the trust game agents generate significantly more degree-linked
> inequality than a minimal reciprocal rule. Neither prosociality nor
> awareness prevents unequal outcomes: agents following an identical
> fairness persona at rates from 84% to 100% produced near-identical
> structural inequality, and articulating one's own position conferred
> no payoff advantage. Most consequentially, whether disposition or
> topology explains the outcome inverts between environments, driven
> by the mechanic alone. Collective assurance therefore cannot be
> assigned to a fixed level of the system: its appropriate target
> depends on the causal structure of the interaction mechanism.

The manuscript and its supplementary information (`manuscript.tex`,
`supplement.tex`) document the full experimental design, statistical
methodology, and results. This repository provides the underlying
data and code for independent verification.

## Contents

- `manuscript.tex` / `.pdf` — manuscript.
- `supplement.tex` / `.pdf` — supplementary information: agent
  personas, round prompts, tool schema, non-LLM baseline strategies,
  self-report classification pipeline, network topology generation,
  and model/API configuration.
- `figures/` — network topology and referral-pattern diagrams (source
  and rendered).
- `results_data.csv` / `results_summary.md` — main-study results:
  degree–payoff correlation, Gini coefficient, compliance rate, and
  sanctioning statistics, per experimental condition.
- `baseline_comparison.md` — comparison against non-LLM baseline
  strategies, run through the same experimental harness and design as
  the main study.
- `h2_results.md` / `h2_by_cell.md` — an earlier, superseded H2
  classification pass (46,157 texts, the original 192-run study only);
  kept for provenance. The current H2 results (59,440 texts, including
  later replicates and a corrected classifier prompt) are
  `raw_data/h2_full_results_v2.md` and `raw_data/h2_full_by_cell_v2.csv`
  — use those, not the top-level files.
- `raw_data/` — full underlying data and analysis code (see below).

## Data availability

Agents' free-text justifications for their actions (a corpus of
approximately 59,000 items) are published in aggregated form only —
classification rates per agent per run, and prevalence rates per
experimental condition (`raw_data/h2_per_agent.csv`,
`raw_data/h2_full_by_cell_v2.csv`) — rather than as raw text.

The exception is a 148-item stratified calibration sample, published
in full in `raw_data/h2_calibration/`: two independent human codings,
the adjudicated ground truth with reasoning for each disputed item,
and the classifier output used to validate the automated
classification pipeline against human judgment. This sample underlies
the calibrated prevalence estimate reported in the manuscript and is
published in full so that estimate remains independently checkable.

All other raw experimental exports retain every structural field
needed to reproduce the reported statistics — actions, payoffs,
network structure, timestamps — with only the free-text justification
fields removed.

## `raw_data/` contents

- `commons/`, `triage/` — raw run exports for the main study, across
  all experimental conditions.
- `baseline_study/` — raw run exports for the non-LLM baseline
  comparison.
- `qwen_crossmodel/`, `glm_crossmodel/`, `mistral_medium_crossmodel/`
  — raw run exports for the cross-model replication.
- `h2_calibration/` — the 148-item calibration sample and its
  associated coding, adjudication, and prevalence-estimation outputs
  (see Data availability, above).
- `h2_full_by_cell_v2.csv`, `h2_per_agent.csv` — aggregated self-report
  classification results, by condition and by agent.
- `analyze_main_study.py`, `stats_main_study.py`, `h2_judge.py`,
  `h2_calibration_analysis.py`, and related scripts — reproduce every
  results file above from the raw data.

## Reproducing the analysis

```
cd raw_data
python3 analyze_main_study.py --out results_data.csv --md results_summary.md
python3 stats_main_study.py h3 --out h3_equivalence.md
python3 cochran_q_heterogeneity.py
```

Both `.tex` files are self-contained (embedded bibliography) and
compile with a standard two-pass `pdflatex` run.
