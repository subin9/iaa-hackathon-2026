"""Build the 5-page report (HTML -> PDF). Run: PYTHONPATH=src:part2 .venv/bin/python part2/report/build_report.py [office_premium.csv]
Numbers come from work/p2/report_numbers.json, part2/probes.json, part2/final.json and the office premium table (default work/p2/office_final.csv,
written by part2/office_premium.py from the final submission); the text is in this file and every other number is copied from part2/LOG.md."""
import sys, json, base64
import polars as pl
from weasyprint import HTML

R = json.load(open("work/p2/report_numbers.json")); P = json.load(open("part2/probes.json")); FIN = json.load(open("part2/final.json"))
F1, F2 = FIN["part1"], FIN["part2"]
office = pl.read_csv(sys.argv[1] if len(sys.argv) > 1 else "work/p2/office_final.csv")
img = lambda n, w: f'<img src="data:image/png;base64,{base64.b64encode(open("part2/report/fig/" + n, "rb").read()).decode()}" style="width:{w}">'
lad = lambda k: f'{R[k]["pooled"]:.3f}'
pub = {v["name"]: v["public"] for v in P["versions"]}


def matrix():
    """Data x model table for the video and report; rendered only once the teammate's two scores are in part2/final.json ("matrix")."""
    m = F2.get("matrix", {})
    if not all(k in m for k in ("raw_ai", "clean_ai", "raw_ours", "clean_ours")): return ""
    return (f'<p><b>Data &times; model (public D&sup2;).</b></p><table style="width:70%"><tr><th></th><th>AI-proposed model, not optimised</th><th>Our pipeline with leaderboard levels</th></tr>'
            f'<tr><td>Competition files</td><td class="n">{m["raw_ai"]}</td><td class="n">{m["raw_ours"]}</td></tr><tr><td>Cleaned files</td><td class="n">{m["clean_ai"]}</td><td class="n">{m["clean_ours"]}</td></tr></table>')


def office_rows():
    out = []
    for r in office.iter_rows(named=True):
        out.append(f'<tr><td>{r["row_id"]}</td><td>{r["line"][:3]}</td><td>{r["channel"][:3]}</td><td class="n">{r["exposure"]:.2f}</td><td class="n">{r["risk"]:.0f}</td><td class="n">{r["fixed"]:.0f}</td>'
                   f'<td class="n">{r["cat_re"]:.0f}</td><td class="n">{r["variable"]:.0f}</td><td class="n">{r["commission"]:.0f}</td><td class="n">{r["tax"]:.0f}</td><td class="n">{r["profit"]:.0f}</td>'
                   f'<td class="n"><b>{r["office"]:.0f}</b></td><td class="n">{r["office_row"]:.0f}</td><td class="n">{r["written_premium"]:.0f}</td><td class="n">{r["vs_written"]:.2f}</td></tr>')
    return "\n".join(out)


CSS = """
@page { size: A4; margin: 11mm 12.5mm 11mm 12.5mm; @bottom-right { content: counter(page) " / " counter(pages); font-size: 7pt; color: #666; } }
body { font-family: 'DejaVu Sans', Arial, sans-serif; font-size: 8.4pt; line-height: 1.28; color: #111; }
h1 { font-size: 13.5pt; margin: 0 0 1mm 0; } h2 { font-size: 9.6pt; margin: 2.4mm 0 0.8mm 0; border-bottom: 0.6pt solid #1d4e89; color: #1d4e89; }
p { margin: 0.8mm 0; } ul { margin: 0.5mm 0 0.5mm 4mm; padding: 0; } li { margin: 0.25mm 0; }
table { border-collapse: collapse; width: 100%; margin: 1mm 0; font-size: 7.4pt; } th, td { border: 0.4pt solid #999; padding: 0.5mm 1.2mm; text-align: left; vertical-align: top; } th { background: #e8eef6; }
td.n, th.n { text-align: right; } .box { border: 0.8pt solid #1d4e89; background: #f3f7fc; padding: 1.5mm 2.6mm; margin: 1mm 0; }
.small { font-size: 7.2pt; color: #333; } .two { display: flex; gap: 3mm; } .two > div { flex: 1; } img { display: block; margin: 0 auto; }
table.office { font-size: 6.9pt; } table.office td, table.office th { padding: 0.25mm 1mm; } code { font-size: 7.3pt; }
"""

BODY = f"""
<h1>Pricing across markets with an AI-assisted workflow: from a developed to an emerging market</h1>
<p class="small">Team SU&sup2; (Kaggle team HS) &middot; IAA AI-Assisted Actuarial Hackathon 2026, Parts 1 and 2 &middot; code, tests and working logs in the team repository:
<code>src/</code> Part 1, <code>part2/</code> Part 2, <code>docs/</code> logs and AI use. All scores are Tweedie D&sup2; with power 1.5.</p>

<div class="box"><b>Results.</b> <b>Part 1</b> (developed market): private <b>{F1['private']}</b>, rank {F1['private_rank']} (public {F1['public']}). <b>Part 2</b> (emerging market, 209,063 test rows, 76% new business):
final submission <b>{F2['name']}</b>, public <b>{F2['public']}</b>, rank {F2['public_rank']}.
Without the last round of motor segment factors it scores {F2['without_segment_factors']['public']} ({F2['without_segment_factors']['name']}).
Of the Part 2 public score, an earlier version of the model without any leaderboard information reaches {F2['modelling_only_public']['public']} ({F2['modelling_only_public']['name']}); most of the rest comes from new-business and segment levels measured with disclosed leaderboard probes (section 6).<br>
<b>What carried us:</b> keep the developed-market relativities, re-learn the levels on two emerging years, add only the corrections the data can prove, and treat the 2025 new business as the main uncertainty.
<b>What we learned about validation:</b> after the levels were fitted, three changes that won in cross-validation did not win on the 2025 rows; the one late change that did was knowledge carried from the developed market (the fire slope on the wildfire index), not a pattern found in the two emerging years.</div>

<h2>1. Part 1: developed market (2021-2024, motor, buildings, contents)</h2>
<p><b>Target.</b> Incurred less recoveries per policy row, declined claims excluded; the unreported part is added with completion curves from the report lags of mature years (offset log(exposure &times; completion)); line trends fitted on mature years only.
<b>Validation.</b> Two time folds (train to 2022 / score 2023, train to 2023 / score 2024), never random folds, because a policy spans years. A change was adopted only if both folds moved the same way by more than the noise floor (about 0.0003) on three-seed averages; one seed moved by &plusmn;0.001.
<b>Model.</b> Equal-weight blend of shallow (3-leaf) LightGBM variants, frequency-severity boosting, CatBoost, GLM, EBM, MLP and TabM (per peril), times a policy credibility factor (12+N)/(12+L), with line and segment levels calibrated on the public board and shrunk for sampling noise.
<b>What paid most:</b> taking things out. 3-leaf trees beat deeper trees (0.1362 to 0.1379 on one model), and dropping weather, sales-channel, marketing and time columns gave +0.0002/+0.0007 on the two folds; tuning and extra model families were mostly noise.
Public score rose from 0.12708 (first file) to 0.12956 (eq20, the final); private {F1['private']}. Full log: <code>docs/part1_log.md</code>.</p>

<h2>2. Part 2: what changed in the emerging market</h2>
{img('transfer.png', '96%')}
<ul>
<li><b>Same structure.</b> Apart from coding and the channel mix (70% broker), the rating factors are distributed as in the developed market (PSI near 0), and their effects on cost agree (left, log correlation shown in the title).</li>
<li><b>Different levels.</b> Motor cost is 25% below the developed model, from 0.64 (bodily injury) to 1.28 (glass) by peril; escape of water is about 0.5. The climate differs (median hail days 14 vs 6, freezing days 19 vs 35, wildfire index 0.5 vs 0.1).</li>
<li><b>New effects.</b> Gender is recorded only here (and may be used for pricing): males cost 1.39&times; on the at-fault motor perils (frequency ratios 1.66 bodily injury, 1.30 own damage, 1.43 third-party property, 1.04 glass). Buildings policyholders aged 35-49 cost 0.67&times;.</li>
<li><b>New business.</b> 12-15% of the 109k training rows but 76% of the 2025 rows (a broker portfolio). Train-versus-test adversarial AUC 0.87-0.88, driven by new business, renewal count and campaign code.</li></ul>

<h2>3. Data quality</h2>
<table><tr><th style="width:48%">Finding</th><th>Treatment and effect</th></tr>
<tr><td>Exposure stored in days for some rows; sums insured keyed 1000&times; too large (both markets)</td><td>Exposure rebuilt from the period dates; sums above 100&times; the median divided by 1000</td></tr>
<tr><td>604 repeated claims under new ids (developed only); <code>customer_since_year</code> separates train from test (AUC 1.0); service contacts grow with each claim</td><td>Repeats dropped; both columns left out (Part 1 finding, kept in Part 2)</td></tr>
<tr><td>Developed <code>construction_type</code>: 11 spellings, timber coded T in 2021-22 and W from 2023 (a year flag in disguise; found when a mapping returned 90% missing)</td><td>Normalised to the four emerging codes; +0.005 D&sup2; on buildings. Part 1 had left the column as it came</td></tr>
<tr><td>Emerging <code>occupation</code> is free text (81 spellings of 20 jobs plus "Self-employed X")</td><td>Trimmed, case-folded, split into occupation and a self-employed flag</td></tr>
<tr><td>11-12 columns about 12% missing, independently and at the same rate in every year, channel, region and in the test rows</td><td>Random gaps: native handling in the trees. The teammate's cleaning (below) fills them from the same policy's other rows</td></tr>
<tr><td>Claims valued at 31 Dec 2024; the emerging market has no mature year</td><td>Developed completion curves, justified by equal report-lag percentiles (motor median 9 days, 90th percentile 44 vs 46)</td></tr></table>
<p><b>Data harness (teammate).</b> A rule book of method written from Part 1 (50 rules, rules not answers) was handed to an agent that audited the emerging files; each cycle's new findings became rules (50, 63, 67, 68) until a cycle found nothing new. The harness never sees evaluation data and never submits.
We diffed the cleaned files against the originals: the only change that reaches our tables is the missing vehicle and property fields filled from the same policy's other rows (90-100% agreement where both exist); the 36 claims it removes fall outside every policy period, so the target is unchanged.
Measured effect on our pipeline (same folds, paired bootstrap by customer): cleaned files alone +0.00009 (sd 0.00019); with the teammate's feature list (renewal count kept) +0.00098 (sd 0.00034). Our own repairs had already caught the large defects, as the teammate expected.</p>

<h2>4. Part 2 method, and what was carried over</h2>
<p><b>(1) Prior.</b> Per line and peril, 3-leaf LightGBM on the four developed years (Tweedie p=1.6, Poisson and extra-trees Tweedie variants averaged in log space; learning rate 0.05, 600 rounds, 900 for extra-trees), offset log(exposure &times; completion), cost capped at the 99.5th percentile with the cap load put back, on the fields both markets share. The peril predictions sum to the row prediction.
<b>(2) Levels.</b> One multiplier per peril from the emerging years, shrunk to the line level with weight n/(n+400), n = claims. <b>(3) Corrections.</b> Candidate factors are screened with a robust (sandwich) score test and fitted as a ridge Tweedie GLM with the prior as offset; gender (at-fault motor perils) and age band (buildings) survived nested cross-validation. <b>(4) Weather on one peril.</b> The tree prior leaves weather out and is flat above the developed maximum of the wildfire index (0.635), where 22% of the 2025 buildings rows lie; buildings fire gets the developed Poisson slope instead, log cost + 1.662 (wildfire index &minus; 0.528) (se 0.24 in the developed data, 1.55 with se 0.80 when fitted on the emerging rows; paired CV +0.00088). The final file averages this model with the earlier prior average (v9) in log space. <b>(5) Total</b> restored after shrinkage. <b>(6) Cell and segment levels</b> for new business and renewals from the public board (section 6).</p>
<table><tr><th style="width:24%">Carried over from Part 1</th><th style="width:34%">Re-learned or added in Part 2</th><th>Dropped, with the reason</th></tr>
<tr><td>Offset and completion curves, capped Tweedie target, 3-leaf trees, lean columns, level calibration with shrinkage</td><td>Peril levels, gender, buildings age band, new-business levels, construction recode, <code>new_business</code> and <code>renewal_count</code> in the prior</td><td>The seven-family blend (the prior is one family; averaging three variants added +0.002), experience rating (worse at every credibility), trend (no mature year), premium columns (A/E flat across quintiles), weather terms other than fire (glass on hail days +0.00018, storm, water, subsidence and flood zero or negative)</td></tr></table>

<h2>5. Validation and guardrails</h2>
<div class="two"><div>{img('ladder.png', '100%')}</div><div>
<p><b>Design.</b> 5-fold cross-validation grouped by customer on the 2023-24 emerging rows, pooled D&sup2; on reported cost; corrections screened inside each training fold; the developed prior never sees an emerging claim. Two models are compared on the same folds with a paired bootstrap by customer (2,000 resamples), which is much tighter than comparing two separate CV scores (the same model on two fold assignments scores 0.1414 and 0.1386).
The final recipe scores 0.1425 on the cleaned files (the ladder on the left was built with the earlier prior average, 0.1414).</p>
<p><b>22 automated tests</b> (<code>part2/tests</code>, run before each submission): exposure equals the dates, completion in (0,1], schemas and codes agree across markets, column order, finite priors, calibration, prediction proportional to exposure, no negative or missing predictions, the correction stage finds a planted effect and rarely a false one in 20 null runs, the probe solver recovers known multipliers, the file checker rejects bad files. Two tests that could not fail were found in review and fixed (mutation-checked).</p></div></div>
<p><b>Bugs the tests now catch.</b> LightGBM reads columns by position (a reordered frame gave 0.036 instead of 0.134); a double level correction inflated motor by 12%; a model meant to use emerging data only had received the prior columns (0.1244 became 0.1176).
<b>Decision rules fixed before each score.</b> For every late submission the keep-or-drop threshold was written in the log before the public score came back (for example: keep v11 unless it is more than 0.0003 below v9). The rule decided; nothing was re-argued after seeing a score.</p>

<h2>6. The leaderboard as a measurement, and what it cannot tell</h2>
{img('leaderboard.png', '96%')}
<p>Cross-validation cannot see new business (12-15% of training rows); the public board can (76% of test rows). The public deviance is a sum over rows, so it separates by segment: multiplying one segment by m gives Dev(m) = &sum;<sub>s</sub> 4[U<sub>s</sub> m<sub>s</sub><sup>-1/2</sup> + f T<sub>s</sub> m<sub>s</sub><sup>1/2</sup>] + constant, with T<sub>s</sub> known from our predictions. One probe per segment identifies the best multiplier.
On v2 it gave motor new business 1.40, buildings 1.23, contents 1.11, renewals 1.01, and predicted 0.16433 for the half-way file (observed {pub['v3_half']}). The seven probes on v5 (with v4 and v5) gave twelve cell levels (line &times; new business, with gender and channel for motor and the 35-49 age band for buildings), each shrunk by its sampling noise (sd of log m* 0.05 to 0.32 from bootstrap of training rows): v7, {pub['v7']}.
An independent review by a fresh agent found that the solvers dropped the Tweedie constant &minus;8&sum;&radic;y, which biased the factors away from 1; with the fix the corrected solution scores the same as v7, so v7 stayed. Over-fitting showed too: a seven-parameter structure predicted 0.17512 and returned {pub['v6']}.
All {len(P['probes_on_v2']) + len(P['probes_on_v5']) + len(P['probes_on_v1']) + len(P['probes_on_v10']) + len(P['probes_on_v13_cells'])} probes are listed in <code>part2/probes.json</code>. Expected private carry-over of the v5-to-v7 step: +0.0038 (sd 0.0022) against +0.0050 on the public rows.
The right panel shows the limit: once the cell levels were fitted, three changes inside the cells with paired CV gains (+0.00018, +0.00098 with P 0.998, +0.00075 with P 0.999) returned +0.00003, &minus;0.00056 and &minus;0.00063 on the public rows. The 2023-24 rows do not predict the 2025 broker book at this margin. The fourth bar is the exception: the fire term rests on 1,107 developed fires, and its CV gain (+0.00088) reappeared on the public rows (v12c, with the v9 average, +0.00086 against v10).
<b>Segment rounds.</b> Seven &times;1.2 probes on single motor segments of v10, chosen from out-of-fold residuals where the training new business had evidence, each solved on its own (best factor from the score change, public null deviance 8.60M) and shrunk by the sampling noise of the segment's public third: new business married 0.957, drivers 17-24 1.109, new business in regions E01 and E06 1.207, drivers 65+ 1.018, new business in E02 0.890, renewals paying monthly 0.932, new business for business use 0.813. The training new business points the same way where it has evidence (relative A/E 1.59 and 1.55 in E01 and E06, 0.87 in E02, 0.71 for business use). Applied to v12c and rescaled to the v7 cell totals: v13_cells, public {pub['v13_cells']} (without the rescaling {pub['v13_raw']}).
A second round on v13_cells, on segments from a fresh residual scan: motor new business with voluntary excess 500 1.339, two lines held 1.298, ncb 11 years or more 1.179, ncb 0 0.847, one prior claim 0.970, voluntary excess 0 1.018, contents new business in areas below 14.1&deg;C 0.918: v14_cells, public {pub['v14_cells']} (without the rescaling {pub['v14_raw']}).
In 9 of the 12 probes whose segment had a clear training residual, the residual pointed the same way as the board (not for married drivers, monthly-paying renewals and voluntary excess 0).</p>

<h2>7. Key judgments, final choice and remaining uncertainty</h2>
<table><tr><th style="width:15%">Judgment</th><th style="width:27%">Decision</th><th style="width:33%">Evidence</th><th>Cost of a 15% level error (public D&sup2;, probes on v5 = {pub['v5_full']})</th></tr>
<tr><td>Ultimate cost of 2023-24 claims</td><td>Developed completion curves by peril</td><td>No mature emerging year; report-lag percentiles match the developed market</td><td>Not measured separately (enters every level)</td></tr>
<tr><td>Level of the 2025 broker book (new business)</td><td>New-business flag in the prior, then cell levels from public probes, shrunk for sampling noise</td><td>76% of test rows against about 1,000 training claims; the developed market gives +8% motor, +13% buildings</td><td>Motor &minus;{pub['v5_full'] - [q['public'] for q in P['probes_on_v5'] if q['seg'] == 'motor_nb'][0]:.4f}, buildings &minus;{pub['v5_full'] - [q['public'] for q in P['probes_on_v5'] if q['seg'] == 'buildings_nb'][0]:.4f}, contents &minus;{pub['v5_full'] - [q['public'] for q in P['probes_on_v5'] if q['seg'] == 'contents_nb'][0]:.4f}</td></tr>
<tr><td>Renewal level and trend</td><td>2023-24 emerging level, no trend</td><td>Two years only; the board put renewals at 1.01 (v2) and 0.996 (v5) of the model</td><td>&minus;{pub['v5_full'] - [q['public'] for q in P['probes_on_v5'] if q['seg'] == 'renewal'][0]:.4f}</td></tr>
<tr><td>Gender</td><td>Used, on the at-fault motor perils only</td><td>Allowed in the emerging market; leaving it out costs 0.0015 (sd 0.0008) in paired CV</td><td>Not a level; needs sign-off before a tariff uses it</td></tr></table>
<p class="small">The cost column is the measured public loss when one segment of v5 was multiplied by 1.15 (probe files q5a to q5d). Motor new business is the judgment that matters most.</p>
<ul><li><b>Final Part 2 file: {F2['name']}</b>. {F2['why']}</li>
<li><b>New business</b> is the largest uncertainty: 76% of 2025 rows against about 1,000 training claims. The developed market gives +8% (motor) and +13% (buildings); the board moved motor levels by gender far beyond the GLM correction (cell factors applied to v5: new business male 1.19 against female 0.69, renewals 1.19 against 0.93). Whether this holds on the private rows is the main risk; the levels are shrunk for that reason.</li>
<li><b>Small perils.</b> Fire (70 claims), subsidence (52), flood (80 and 86) are shrunk to the line level; their 2025 level is uncertain by more than 30% (fire A/E was 3.34 in 2023 and 1.10 in 2024). 2025 is colder with fewer hail days than 2023-24; this shift is not modelled.</li>
<li><b>Governance.</b> Gender is used because the emerging market allows it; its effect size and counts are in the log, and it needs human sign-off before entering a tariff. The leaderboard-derived levels are a calibration, not a model, and are disclosed as such.</li></ul>

{matrix()}
<h2>8. AI-assisted workflow and how its output was verified</h2>
<table><tr><th style="width:14%">Stage</th><th style="width:43%">What the AI did (Claude Code agent; data harness agent)</th><th>Human control and verification</th></tr>
<tr><td>EDA, data</td><td>Profiles, drift (PSI, adversarial), one-way tables; code mapping across markets; the harness agent audited the files against the rule book</td><td>Counts checked against the raw data (the first construction mapping lost 90% of rows and was caught); harness findings reviewed by the actuary, two were defects the actuary had missed</td></tr>
<tr><td>Modelling</td><td>Prior, shrinkage, score-test screening, GLM; over 40 experiment scripts in Part 2 alone, most rejected (all kept with numbers in the logs)</td><td>Fixed folds and seeds, nested CV, paired bootstrap, adoption rules written before results</td></tr>
<tr><td>Review</td><td>A fresh agent reviewed the code without seeing our conclusions</td><td>Found the missing Tweedie constant and two tests that could not fail; both fixed and re-checked</td></tr>
<tr><td>Leaderboard</td><td>Built probe files and solved the segment levels</td><td>The team set the submission budget, approved each file, fixed keep rules in advance and chose the final; every probe disclosed</td></tr>
<tr><td>Writing</td><td>Working logs, this report, the office premium table</td><td>Every number copied from script output; the team reviews the text</td></tr></table>

<p><b>Reproducibility and governance.</b> Every experiment is a script in the repository with its result in the working logs (<code>docs/part1_log.md</code>, <code>part2/LOG.md</code>); every submitted version has a git tag; <code>part2/run_all.sh</code> rebuilds the submissions from the competition files, v7 and v11 rebuild byte for byte, v10 to within 3e-13 per row and v12c to v14_cells to within 1e-14 (relative). Competition data, the cleaned files and the Kaggle credential never enter the repository. Human review points: the submission budget, each submission, the keep rules, the use of gender and the final choice.</p>
<h2>9. Office premium for the 20 reference policies (final predictions)</h2>
<p class="small">Annual office premium P = (risk premium + fixed expense + catastrophe reinsurance) / (1 &minus; variable expense 15% &minus; commission &minus; premium tax 8% &minus; profit margin 8%), emerging rates from <code>expenses</code>.
Assumptions: the build-up is annual, because <code>written_premium</code> is an annual figure (its mean does not change with the row's exposure in the training files) and the fixed expense is quoted per policy-year, so the risk premium is the final prediction for the row divided by its exposure; the premium for the row's own period is P &times; exposure; catastrophe reinsurance is 12% of the risk premium for buildings and contents only; commission 0% direct, 20% broker.
Worked example, {office["row_id"][0]} (motor, direct, exposure {office["exposure"][0]:.2f}): risk {office["risk"][0]:.1f} + fixed 85 = {office["risk"][0] + 85:.1f}; divided by 1 &minus; 0.15 &minus; 0 &minus; 0.08 &minus; 0.08 = 0.69 gives P = {office["office"][0]:.1f}, of which variable expense {office["variable"][0]:.1f}, tax {office["tax"][0]:.1f}, profit {office["profit"][0]:.1f}; for the row's period {office["office_row"][0]:.1f}. Components add up to P for every row (checked in <code>part2/office_premium.py</code>).</p>
<table class="office"><tr><th>row</th><th>line</th><th>ch.</th><th class="n">expo</th><th class="n">risk</th><th class="n">fixed</th><th class="n">cat re</th><th class="n">var.</th><th class="n">comm.</th><th class="n">tax</th><th class="n">profit</th><th class="n">office P</th><th class="n">P &times; expo</th><th class="n">written</th><th class="n">P / written</th></tr>
{office_rows()}</table>
<p class="small">All amounts annual except P &times; expo. P / written above 1 means the current emerging tariff charges less than our technical premium. Across all 2025 rows (comparison-site rows left out, having no commission rate) the ratio is 2.19 (motor), 3.25 (buildings) and 2.67 (contents), exposure-weighted. This is consistent with the data: on 2023-24 the written premium ran ultimate loss ratios of 0.67, 1.14 and 0.70, while a broker premium keeps only 49% for claims after expenses, commission, tax and profit, and the fixed 85 CU is large next to a contents premium of about 130. The current tariff looks inadequate everywhere and most in buildings, where our confidence is also lowest (section 7). The emerging <code>expenses</code> table gives no comparison-site commission, although 5% of the 2025 rows come through that channel; none of the 20 reference policies does.
<b>Reproduce:</b> <code>part2/run_all.sh</code> rebuilds tables, priors, tests and every submitted version from the competition files; seeds, folds and library versions are fixed (<code>uv.lock</code>).</p>
"""
html_doc = f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{BODY}</body></html>"
doc = HTML(string=html_doc).render(); n = len(doc.pages); doc.write_pdf("part2/report/out/report.pdf"); open("part2/report/out/report.html", "w").write(html_doc)
print("pages:", n)
