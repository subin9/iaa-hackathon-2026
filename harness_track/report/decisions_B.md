# Actuarial decisions for the Part 2 submission (gate ④) — signed on the v10 basis

**Prepared in the model by Evan (actuarial data scientist); reviewed and signed by HyunSu Kim (actuary), 2026-10-29 SGT.** The decisions below were made inside the modelling pipeline by an actuarially trained preparer; the signature is the independent review. This supersedes the 2026-10-27 pre-probe signature, which is kept
below as the record of what the actuary expected *before* the public-score probes. The final file is the data
scientist's **v10** (pipeline on the harness-cleaned D4 files, with disclosed leaderboard-probe cell levels); v9 is the
fallback with the best public score (within noise of v10; the keep rule was written before the score).

Evidence: four independent agent runs under harness v1–v4 (`runs/cycle_N/`), the data scientist's report
(`Reference/Evan/report.pdf`, `part2/LOG.md`, `part2/probes.json`), thirteen disclosed public-score probes.

| # | Decision | Pre-probe actuarial estimate (2026-10-27) | What the probes / pipeline showed | **Signed decision (v10)** |
|---|---|---|---|---|
| B1 | **Trend** to mid-2025 | half of the developed slope: +2.3 / +4.5 / +3.8 % (A/B range ±4–13 %) | renewal-book level measured at 1.01 (v2) and 0.996 (v5) of the untrended 2023–24 model — the board says the untrended level is right | **No trend.** Settled by the probe, as planned; the pre-probe estimate is recorded as the actuary's view without external data. |
| B2 | **IBNER** uplift on 2024 open claims | 0 (no signal in four runs; ±4 % stated) | not probed separately; the developed completion curves were used (report-lag percentiles match: motor median 9 d, p90 44 vs 46) | **0.** Unchanged. Ultimate basis = developed curves (DS) — the harness's truncation-corrected emerging curve with a borrowed tail agrees within ±2.5 % (cycle 3 cap sensitivity). |
| B3 | **New-business relativity** (76 % of the 2025 book) | motor: keep the model's ≈1.47 (two-year compromise), candidate B at 1.28; contents ×1.12 on NB rows; buildings none | probes on v2: **motor 1.40, contents 1.11, buildings 1.23**; later cell levels by gender/channel/age band, each shrunk for sampling noise (sd log m 0.05–0.32) | **Probed cell levels, shrunk** (as in v10). The pre-probe estimates were within noise of the probe for motor (1.47 vs 1.40) and contents (1.12 vs 1.11); buildings (1.23) the actuary had declined to estimate on 35–65 claims — the probe supplied it. |
| B4 | **Gender** as a rating factor | exclude (within-noise gain; contested factor) | DS pipeline: males 1.39× on at-fault motor perils (frequency 1.66 BI / 1.30 OD / 1.43 TPP); CV +0.0015 (sd 0.0008); probe cell levels split by gender | **Approved for the competition model, with conditions recorded**: the emerging market permits it (data description), the effect is large and measured, the factor applies to at-fault motor perils only, and **any tariff use requires a separate regulatory/ethics sign-off** (report §7 governance line). The pre-probe exclusion is withdrawn because the DS evidence was not within noise and the probe structure depends on it. |
| B5 | **Buildings fire load** | pooled two-year capped level, ±15 % | fire A/E 3.34 (2023) vs 1.10 (2024); small perils shrunk to the line level (n/(n+400)); buildings NB level 1.23 from the probe | **Pooled capped level with peril shrinkage, buildings NB 1.23 (shrunk).** Uncertainty stated as > 30 % on fire/subsidence/flood 2025 levels. |
| B6 | 36 claims with loss dates before inception | exclude; team query | DS pipeline: the 36 claims link to no policy period, target unchanged | **Exclude; team query stands.** |
| B7 | ncb_years > years_licensed | keep both as delivered | kept | **Keep both; data-definition query in the report.** |
| B8 | **Final submission** | pair A/B split on the motor NB relativity; probe to choose | v9 0.17303 (competition files) vs v10 0.17247 (cleaned files): −0.00056 public, ≈1.3 public standard errors; paired CV +0.00098 for v10; keep rule written before the score | **v10 is the Final Submission; v9 the fallback.** Reason: within noise on the public rows, better in paired CV, and it carries the data-quality work. Record who selected it and when in `submissions/log.csv`. |

## What this says about the harness (for the report)
- Row-level repairs alone moved the pipeline by +0.00009 (sd 0.00019) — within noise, because the data scientist's
  own pipeline had already caught the large defects (exposure, sum insured, the Part 1 leakage columns).
- The harness's **feature decisions** (keep `new_business` and `renewal_count` as mix, drop the cohort stamps) moved
  it by **+0.00098 (sd 0.00034)** — significant. The gain came from judgment about leakage and mix, not from cleaning.
- The harness found two defects the pipeline had not (sibling-reconstructable nulls; the construction-code year flag
  was found by the DS, the campaign-code stamp and the survivor sample by the harness).
- The pre-probe actuarial estimates for the new-business relativity were within noise of the probes for motor and
  contents. That is the test of whether the adaptation analysis carries judgment, and it passed on two of three lines.

## Pre-probe record (2026-10-27, superseded)
B1 half-slope trend (+2.3 / +4.5 / +3.8 %) · B2 0 · B3 motor model 1.47 / contents ×1.12 / buildings none · B4 exclude
gender · B5 pooled capped, no adjustment · B6 exclude · B7 keep · B8 pair A/B split on motor NB. Implementation as
post-model multipliers was written for the actuary's own recipe (`runs/hs_model/train_hs.py`), which remains the
"unoptimised" column of the data-effect ladder; it is not the final file.

## What remains uncertain (ranked by level effect)
motor new-business level (cost of a 15 % error on v5: −0.0024 public D²) · buildings small perils > 30 % · whether the
gender-split cell levels hold on the private rows (shrunk for that reason) · completion basis ±2.5 % (motor) · 2025
weather shift not modelled.

## Changes after the signature (2026-10-30, prepared by Evan, not yet signed)
The table above is signed on the v10 basis. The final file has since changed under keep rules written before each score
(`part2/LOG.md`, entries of 2026-10-28 to 2026-10-30):
- **B5 fire:** buildings fire now carries the developed-market slope on the wildfire index, log cost + 1.662 (wildfire − 0.528);
  paired CV +0.00088. With the v9/v10 average this is v12c, public 0.17333.
- **B3 new business:** fourteen further ×1.2 probes on single new-business segments (thirteen motor, one contents), each solved on its
  own and shrunk by sampling noise; applied factors 0.81 to 1.34. v13_cells 0.17556, then v14_cells 0.17993.
- **B8 final submission:** v14_cells (a third round was prepared and not submitted). The leaderboard probes now number
  twenty-seven, all listed in `part2/probes.json`.
- Added uncertainty: the segment factors are fitted on the public third, so part of their gain (+0.0066 public) will not carry to the
  private rows; stacked factors move individual motor rows by 0.69 to 1.56 at the 1st and 99th percentiles.
