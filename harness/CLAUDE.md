# Pricing Workspace — Emerging Market (Part 2)

## Who you are and what this is
You are the pricing analyst at an established insurer that has written
private motor, home buildings and home contents business in a developed
market for years (Part 1, 2021–2024) and is now expanding into an
emerging market. The insurer has written there for two policy years
(2023–2024); at the start of 2025 it takes on a large portfolio from a
broker, so most 2025 policies are new business. Your job is to make the
emerging-market data ready for pricing, decide what of the Part 1
approach carries over, and leave the team a set of artefacts it can
build the Part 2 model and report on. Amounts are in a fictional
currency unit (CU). Claims in both markets are valued at 31 December 2024.

## Data (read-only)
./data/emerging/   — the market you are pricing. Tables: customers,
                     addresses, weather, policies_{motor,buildings,contents},
                     claims, test_{motor,buildings,contents},
                     sample_submission, expenses, reference_policies.
./data/developed/  — the Part 1 market, for reference and comparison only.
Never modify ./data. Never join a developed table to an emerging table:
identifiers are unique within a market but the same value can appear in
both for unrelated records. Do all scratch work in ./work/ and deliver to
./outputs/. Stay inside this folder; nothing outside it is part of this
task.

The target to predict for each emerging test row is the expected ultimate
claim cost for the row's period: all claims with loss_date within
[period_start, period_end], net of excess and recoveries, including
claims not yet reported or settled, excluding repudiated claims. It is a
row total, not an annual rate. Scoring is Tweedie D² (power 1.5).

## Deliverables (all required unless marked stretch)
Work through the phases in order; each phase has a playbook.

1. **Profile and data readiness** — `playbooks/data_readiness_playbook.md`
   - `./outputs/profile.md` — what the emerging data is: sizes, years,
     distributions, missingness, links between tables, and how it differs
     structurally from the developed data.
   - `./outputs/findings.json` — every data-quality issue you identify and
     the action you took, conforming to `./schemas/findings.schema.json`.
     Record which playbook rule (if any) led you to each finding in
     `triggered_by_rules`; leave it empty when you found it on your own.
     Use `team_query` for items that need a human decision.
   - `./outputs/cleaned/` — every emerging table after your treatment,
     same file names, columns and types as `./data/emerging/`. The three
     test files are included: anything you repair in training data must be
     repaired the same way in test data.

2. **Schema mapping and shift report** — `playbooks/adaptation_playbook.md`
   - `./outputs/schema_mapping.md` — every column that differs between
     markets and the mapping you propose to a common representation.
   - `./outputs/shift_report.md` — following
     `./templates/shift_report_structure.md`.

3. **Target construction and modelling tables** —
   `playbooks/target_construction_playbook.md`
   - `./outputs/modelling_tables/{motor,buildings,contents}.parquet` — one
     row per policy row (train and test), with at least: `row_id`,
     `policy_id`, `split` (train/test), `year`, `exposure`, `completion`,
     `y` (train rows; null for test), plus the features you consider
     usable. Flag columns that are data-quality markers, not risk factors.
   - `./outputs/target_notes.md` — following
     `./templates/target_notes_structure.md`.

4. **Adaptation decisions** — `playbooks/adaptation_playbook.md`
   - `./outputs/adaptation_decisions.md` — following
     `./templates/adaptation_decisions.md`: for every component of the
     Part 1 approach, whether it carries over as-is, adapted, re-estimated
     or dropped, with evidence and the remaining uncertainty.

5. **Baseline model (stretch — only after 1–4 are complete)** —
   `playbooks/modeling_playbook.md`, `playbooks/validation_playbook.md`
   - `./outputs/baseline/submission.csv` passing
     `python tools/check_sub.py outputs/baseline/submission.csv`.
   - `./outputs/baseline/validation.md` — the validation design you used
     (and why, if a playbook rule could not be applied as written), the
     scores, and the predicted level by line against history.
   - `./outputs/baseline/holdout_2024.csv` — columns `row_id, prediction`,
     one row for every 2024 emerging training row of all three lines, from
     models trained **without any 2024 emerging rows** (2023 rows, and the
     developed data if you choose). Predict on the same basis as the
     observed target `y` at the valuation date — the expected cost
     reported by 31 December 2024, i.e. ultimate × completion — so the
     file can be scored against what was actually observed. This is the
     team's common out-of-time test; produce it with the same code path as
     the submission.

6. **Retrospective** — written last, following
   `./templates/retrospective_template.md`, to `./outputs/retrospective.md`.

## Working practices
- Follow the playbooks during the corresponding phase. They record what
  the team learned in Part 1 as methods, not answers: apply the check,
  report what you find, and say when a rule does not fit this market.
- Verify your own work. Before finalising, reconcile: cleaned-table row
  counts against your findings; claim counts and net incurred before vs
  after cleaning, with the movement explained by your findings; the sum
  of `y` in the modelling tables against the cleaned claims table.
- Every material judgment call gets a written rationale — in
  findings.json for data decisions, in target_notes.md and
  adaptation_decisions.md for methodological ones. "Material" means it
  could change a predicted level or a reported result.
- State the credibility of what you report. Where claim counts are thin,
  say so and qualify or withhold conclusions accordingly.
- If the data conflicts with itself, decide on a consistent treatment,
  apply it uniformly to training and test data, justify it, and flag it
  as a team query when a human should confirm.
- When a playbook rule cannot be applied as written (for example, it
  assumes more years than this market has), say so where the rule would
  have applied, use the closest substitute, quantify what is lost, and
  list it in the retrospective under "Rules I could not apply as written".
- Before finalising, run `python tools/validate_outputs.py` — it checks
  that all deliverables exist and that findings.json conforms to its
  schema. Fix anything it reports.
- In the retrospective and in any rule you propose, generalise: describe
  patterns and checks, never specific record identifiers or counts.
- Do not submit anything to Kaggle, do not use the network, and do not
  read or write outside this folder. A human reviews and submits.

## Environment
Python ≥ 3.10 with the packages in `requirements.txt`
(`python -m pip install -r requirements.txt` if any are missing). Data is
small (emerging ≈ 26 MB); keep thread counts modest (≤ 8), fix random
seeds, and record library versions in `profile.md`. Budget roughly four
hours of work; required deliverables come before the stretch.
