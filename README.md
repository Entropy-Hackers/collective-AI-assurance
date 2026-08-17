# AMS results paper — Overleaf handoff

- `manuscript.tex` / `.pdf` — main paper draft, target Nature Machine
  Intelligence. Every illustrative number is wrapped in `\ph{...}`
  (renders blue) — search for `\ph{` to find every value that still
  needs to be replaced with a real measurement from the files below.
- `supplement.tex` / `.pdf` — Supplementary Information (prompts, tool
  schema, baseline strategies, H2 pipeline, topology generation,
  model/API configuration). No `\ph{}` markers — it's methods, not
  results.
- `figures/` — topology structural comparison, plus temporal referral
  diagrams for one clustered and one scale-free replicate (SVG source
  + rendered PDF).
- `results_data.csv` / `results_summary.md` — H1 + sanctioning, real
  computed numbers from the completed 192-run main study: pooled
  degree--payoff Pearson r with 95% CI, Gini with CI, compliance rate,
  sanctioning stats, one row per cell.
- `h2_results.md` / `h2_by_cell.md` — H2 self-report classification
  (LLM-judge), **superseded by `raw_data/h2_full_results_v2.md`** (see
  status section — the judge prompt had a real bug, fixed 2026-08-12,
  these top-level copies still reflect the pre-fix numbers).
- `baseline_comparison.md` — the non-LLM baseline vs. real LLM
  permutation test ("is H1 just graph arithmetic?"), matching H1's
  exact 8-replicate design, not a pilot-scale simulation.
- `variance_and_h3_results.md` (see `raw_data/`) — balanced ANOVA
  variance decomposition and the H3 sanctioning-equivalence bootstrap
  test.
- `raw_data/cross_model_final.md` — **4 models now at full replicate
  scale** (DeepSeek, Qwen3.5-122b, GLM-5.2, Mistral-medium-3.5) plus a
  Cochran's Q / I^2 heterogeneity test across them (neither environment
  shows significant heterogeneity — p=0.22 commons, p=0.52 triage).
- `raw_data/h2_full_results_v2.md`, `h2_per_agent.csv` — the corrected,
  current H2 numbers (cell-level and per-agent, judge + keyword side
  by side) and the H2-vs-structural-position correlation
  (`h2_vs_structure.py`'s output) the manuscript's H2 section actually
  needs but the cell-aggregate-only output couldn't answer.
- `raw_data/` — the full raw data behind every number above (see its
  own section below).

Everything needed to independently re-derive every results file in
this folder from first principles is in `raw_data/`. Both `.tex` files
are self-contained (embedded bibliography, no external `.bib`) and
compile standalone with a plain two-pass `pdflatex` run.

## Status as of this handoff (2026-08-12)

All of the following are **complete, real data, at full replicate
scale** — nothing in this list is pilot-scale or simulated unless
explicitly marked:

- **Main study**: 192/192 runs, 0 failures, all 24 cells at 8/8
  replicates.
- **H1 + sanctioning** (`results_data.csv`): computed.
- **H2 self-report classification** — LLM-judge over every agent-round
  reason text, all 264 run exports (192 main study + 72 extra
  replicates), 59,440 unique texts, 0 classification failures. **The
  `fair`-dimension judge prompt had a real bug** (false positives on
  purely self-interested text, an undefined boundary case) found via
  re-validation against human coding — kappa vs. human went 0.658 (pre-
  e-INFRA-CZ) → 0.507 (post-switch, buggy) → **0.857 (fixed)**. Use
  `raw_data/h2_full_results_v2.md` and `h2_per_agent.csv`, not the
  top-level `h2_results.md`/`h2_by_cell.md` (pre-fix). Full story:
  `raw_data/h2_classifier_validation.md`.
- **Non-LLM baseline comparison** (`baseline_comparison.md`): 240
  additional runs (fixed/random/reciprocal strategies, matching H1's
  exact topology x institution x 8-replicate design, run through the
  same live harness as the real LLM runs — not the old 200-seed pure
  simulation). Permutation test per cell. This is a load-bearing
  result: confirms commons is close to mechanically guaranteed once
  behaviour is uniform, and finds a large, highly significant (p=0.0001)
  genuine LLM-specific effect in triage/scale_free — plus an
  unanticipated finding (triage/clustered: real LLM data
  *underperforms* even the simple baselines) that isn't in the
  manuscript at all yet.
- **Variance decomposition + H3** (`raw_data/variance_and_h3_results.md`):
  closed-form balanced ANOVA (pure Python, no numpy/scipy) and a
  bootstrap equivalence test for "sanctioning doesn't reduce Gini."
  **H3 confirmed in only one of its two confirmatory cells** (triage,
  not commons) — and this is now resolved, not ambiguous: the
  commons/uniform_fair/scale_free cell was re-run at n=20 (up from 8)
  specifically to check this, and the CI narrowed but still excludes
  both zero and the +/-0.05 margin. Read this file before stating H3
  as a clean result — the manuscript's original two-cell framing does
  not hold as written.
- **Cross-model — 4 of 5 models now at full replicate scale**
  (`raw_data/cross_model_final.md`): DeepSeek (main study), Qwen3.5-122b,
  GLM-5.2, Mistral-medium-3.5 — all free via e-INFRA CZ except DeepSeek
  itself, all at the same 8-replicate/2-central-cell standard, not
  pilot scale. r=0.95-0.99 across all four in both environments.
  **Cochran's Q / I^2 heterogeneity test**: neither environment shows
  statistically significant heterogeneity between providers (Q=4.47,
  p=0.22, I^2=33% commons; Q=2.28, p=0.52, I^2=0% triage) — the
  observed spread is consistent with noise around one shared effect,
  not real between-provider variance. A real upgrade from "two-model
  comparison... three further backends only at pilot scale."
  GPT-4o remains pilot-scale only (dropped from further MUG spend).
  Mistral-**Large**-3 (the MUG-hosted model, distinct from
  Mistral-**medium**-3.5 above which is a different model via e-INFRA
  CZ) remains blocked — MUG gateway IP-banned this host for repeated
  auth failures, needs the user to resolve with MedUniGraz, not a
  code/data problem.
- **H2 vs. structural position** (`raw_data/h2_vs_structure.md`): does
  awareness language actually correlate with an agent's own degree/
  payoff, as the manuscript's pilot-stage text claims it doesn't?
  Checked for real at n=960-1920 agent-replicates per cell — small in
  magnitude but often statistically distinguishable from zero at this
  sample size (e.g. triage/uniform_fair: aware vs. degree r=-0.183,
  aware vs. net_payoff r=+0.135, opposite signs in the same cell). "No
  correlation" overclaims a clean null; "small but real, not the
  outcome driver" is the defensible framing.

- **H3's residual effect: resolved as a cue artifact, not
  institutional power** (`raw_data/sanctioning_cue_artifact_test.md`,
  2026-08-16). A new `sanctioning_cue` institution condition (prompt
  cue present, backend still rejects every `/sanction` call with 403 —
  confirmed directly) run 8x on the confirmatory cell shows the cue
  *alone* reproduces the full Gini increase (cue_only vs. off: delta
  +0.081, CI [+0.011,+0.145], excludes zero) while cue_only vs. on
  (real power) shows no difference (CI includes zero). The residual
  H3 effect is agents reacting to being *told* sanctioning is
  possible, not to sanctioning actually happening — strengthens
  rather than undermines the "sanctioning is symbolic" claim.

- **H2 calibration -- COMPLETE, adjudicated** (`raw_data/h2_calibration_analysis.md`,
  `raw_data/h2_calibration/h2_calibration.md`, 2026-08-16): two human
  coders independently coded a 148-item stratified sample on two
  dimensions (`specific_reference`, `generic_network_language`); the
  21 disputed items are now adjudicated (`h2_adjudicated.csv`, reasoned
  decisions, not majority vote -- see the file's own notes for each).
  **The pre-stated expectation that keyword~specific_reference and
  judge~(specific_reference OR generic_network_language) does NOT
  hold** -- both classifiers best match specific_reference alone;
  judge is just a substantially better detector of it than keyword
  (final adjudicated kappa 0.573 vs 0.369). Inter-coder kappa is
  unstable per-cell exactly as warned (1.000 trivial in one cell,
  0.033 in another) -- pooling would have hidden this again.
  **Stratum-reweighted prevalence is computed on the final adjudicated
  ground truth** (`h2_stratum_sizes.csv` supplied 2026-08-16) -- cite
  the "FINAL (adjudicated ground truth)" table in `h2_calibration.md`'s
  Step 4, not the per-coder tables (robustness check only) or the raw
  sample prevalence in Step 4b (not a population estimate at all). One
  caveat still open: N_cell for commons/mixed is ~6.5% higher than
  this repo's own direct corpus count, not reconciled, flagged in the
  file. Commons cells (both populations) have inherently wide CIs --
  their dominant strata (grey for uniform_fair, clear-none for mixed)
  have only 7-20 sample items, a real limit adjudication can't fix.
  Triage's strata are well-populated (8,675/5,379/336 and
  5,311/3,154/5,940) -- that's the number worth leaning on.

**Still open, not run**: extending the baseline/cross-model scale-up
to more than the two central cells; Mistral-Large-3/GPT-4o at real
replicate scale (blocked/deprioritized, see above).

## `raw_data/` contents

- `commons/`, `triage/` — all 192 main-study run exports (JSON),
  `rep1.json`-`rep8.json` per cell (plus reps 9-20 for the three cells
  originally too close to call at n=8: commons/mixed/clustered and
  commons/uniform_fair/{clustered,scale_free} — see
  `variance_and_h3_results.md` for why).
- `baseline_study/` — all 240 non-LLM baseline run exports.
- `qwen_crossmodel/`, `glm_crossmodel/`, `mistral_medium_crossmodel/` —
  16 run exports each, the three e-INFRA CZ cross-model scale-ups.
- `h2_full_by_cell.csv` (superseded, pre-fix) / `h2_full_by_cell_v2.csv`
  (current) — cell-level H2. `h2_per_agent.csv` — per-agent-per-
  replicate H2, judge and keyword classifiers side by side.
  `baseline_vs_real_test.md` — the baseline-comparison source data.
- `h2_calibration/` — the two human coders' raw 148-item coding sheets
  (`h2_coding_sheet_coder1/2.csv`), the per-text judge export
  (`h2_judge_by_text.csv`), `h2_adjudication_needed.csv` (the 21
  disputed items as found) and `h2_adjudicated.csv` (the same 21,
  resolved -- full 148-item sheet, reasoning in
  `h2_calibration_analysis.md`), `h2_stratum_sizes.csv` (population
  stratum sizes for the reweighting), and `h2_calibration.md`/`.csv`
  (inter-coder kappa, classifier-construct mapping, and the FINAL
  adjudicated stratum-reweighted prevalence -- the citable number).
- `analyze_main_study.py`, `stats_main_study.py`, `h2_judge.py`,
  `run_h2_full.py`, `h2_per_agent.py`, `h2_vs_structure.py`,
  `revalidate_h2_judge.py`, `cochran_q_heterogeneity.py`,
  `h2_calibration_analysis.py` — every analysis script used above,
  root-path-aware (auto-detect this folder's layout vs. the main
  repo's `tools/` layout) and re-runnable
  directly here, e.g.:
  ```
  cd raw_data
  python3 analyze_main_study.py --out results_data.csv --md results_summary.md
  python3 stats_main_study.py h3 --out h3_equivalence.md
  python3 cochran_q_heterogeneity.py
  ```
- `run_main_study.sh` — the exact orchestration script (model,
  topology/institution parameters per cell, replicate count, timeouts)
  that produced the main-study runs.

Model/API configuration, prompts, and tool schema are documented in
`supplement.tex` (S1-S3, S7), not duplicated again here. Full
engineering/methods history (H2 classifier validation, harness fixes,
the pre-flight checklist, the MUG IP-ban incident) lives in `tools/`
and `tools/STATUS.md` in the main repo, not in this folder.
