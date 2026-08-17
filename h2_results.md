# H2 self-report classification, full-scale results

Status: **Complete. LLM-judge (deepseek-v4-flash, e-INFRA CZ, free)
over all 46,157 unique agent-round reason texts from the completed
192-run main study (55,238 total agent-round texts, deduplicated).
Zero classification failures.** Supersedes the pilot-stage validation
sample (30 items) as the actual H2 result -- that sample was for
validating the classifier against human coding, not for reporting H2
itself at scale.

Full per-cell table: `tools/reports/h2_full_results.md` (also
`raw_exports/h2_full_by_cell.csv`). Reproducible:
`python3 run_h2_full.py --out reports/h2_full_results.md --csv
reports/raw_exports/h2_full_by_cell.csv` (takes ~85min at e-INFRA CZ's
max_parallel=4; results are cached by exact text, so a rerun after any
new data only classifies what's new).

## Headline: confirms "mechanic-dependent, not a fixed property" -- real numbers differ from the pilot-stage placeholder

Uniform-fair population, pooled across topology/sanctioning (real
range shown, not a single pooled number, since it varies by cell --
see full table):

| Dimension | Commons (uniform_fair) | Triage (uniform_fair) | Manuscript's placeholder |
|---|---|---|---|
| Aware % | 0.1% -- 0.6% | 82.2% -- 90.7% | "4%" / "64%" |
| Fair % | 100.0% (every cell) | 74.9% -- 85.8% | "97%" / "55%" |

The direction the placeholder guessed (aware: commons near-zero,
triage much higher; fair: commons near-100%, triage lower) is
confirmed. The magnitudes are real and different from the
placeholder's guesses in both dimensions -- most notably triage
awareness is far higher than guessed (82-91% real vs. 64% placeholder)
and commons awareness is essentially zero, not 4%.

## A real pattern the placeholder didn't have at all: mixed vs. uniform_fair goes in *opposite* directions by environment

| Population | Commons aware % | Triage aware % |
|---|---|---|
| uniform_fair | 0.1 -- 0.6% | 82.2 -- 90.7% |
| mixed | 9.1 -- 12.2% | 58.8 -- 60.4% |

Mixed population agents show *more* structural-awareness language than
uniform_fair in commons (9-12% vs <1%), but *less* in triage (~59% vs
82-91%). Not something the pilot-stage placeholder anticipated (it
only had uniform_fair pilot numbers) -- worth its own sentence in
Results, not folded silently into the uniform_fair-only claim.

## Sanctioning's effect on H2 language: small, inconsistent direction

Comparing on vs. off within each population/topology (see full CSV for
all 24 rows) -- no large, consistent shift in either aware% or fair%
when sanctioning is active. Consistent with the already-reported
finding that sanctioning is symbolic (targets high-degree agents
correctly, doesn't change the resource ledger) -- it doesn't appear to
meaningfully change how agents talk about their reasoning either.

## Cross-model robustness: Qwen3.5-122b confirms H1 at real replicate scale (not pilot 2-4 reps)

Separately from H2, the cross-model scale-up (2 central cells --
uniform_fair x scale_free, both environments -- 8 replicates each,
free via e-INFRA CZ) landed while this was running:

| Environment | Qwen3.5-122b r [95% CI] | DeepSeek r [95% CI] (main study) |
|---|---|---|
| Commons | 0.983 [0.977, 0.988] | 0.973 [0.964, 0.980] |
| Triage  | 0.952 [0.935, 0.965] | 0.965 [0.952, 0.974] |

Essentially identical to DeepSeek's own main-study numbers, at the
same 8-replicate standard (not the 2-10 pilot-scale replicates the
other four models still have). This is real evidence H1 is not a
DeepSeek-specific artifact, for the first time at a replicate count
that would satisfy the same standard applied to DeepSeek itself.
Mistral-Large-3's equivalent scale-up is blocked (MUG gateway IP ban,
needs the user to resolve with MedUniGraz) -- GPT-4o and GLM-5.2
remain at pilot scale only, not attempted here (GPT-4o dropped per
2026-08-12 decision to skip it on MUG; GLM already excluded from
further spend since 2026-08-07).
