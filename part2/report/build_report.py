"""Build the 5-page report (HTML -> PDF). Run: PYTHONPATH=src:part2 .venv/bin/python part2/report/build_report.py [office_premium.csv]
Numbers come from work/p2/report_numbers.json, part2/probes.json and the office premium table; the text is in this file."""
import sys, json, base64, html
import polars as pl
from weasyprint import HTML

R = json.load(open("work/p2/report_numbers.json")); P = json.load(open("part2/probes.json"))
import os
FIN = json.load(open("part2/final.json")) if os.path.exists("part2/final.json") else {}
office = pl.read_csv(sys.argv[1] if len(sys.argv) > 1 else "work/p2/office_v4.csv")
img = lambda n, w: f'<img src="data:image/png;base64,{base64.b64encode(open("part2/report/fig/" + n, "rb").read()).decode()}" style="width:{w}">'
lad = lambda k: f'{R[k]["pooled"]:.3f}'

def office_rows():
    out = []
    for r in office.iter_rows(named=True):
        out.append(f'<tr><td>{r["row_id"]}</td><td>{r["line"][:3]}</td><td>{r["channel"][:3]}</td><td>{r["exposure"]:.2f}</td><td>{r["risk"]:.0f}</td><td>{r["fixed"]:.0f}</td>'
                   f'<td>{r["cat_re"]:.0f}</td><td>{r["variable"] + r["commission"]:.0f}</td><td>{r["tax"]:.0f}</td><td>{r["profit"]:.0f}</td><td><b>{r["office"]:.0f}</b></td><td>{r["written_premium"]:.0f}</td><td>{r["vs_written"]:.1f}</td></tr>')
    return "\n".join(out)

CSS = """
@page { size: A4; margin: 12mm 13mm 12mm 13mm; }
body { font-family: 'DejaVu Sans', Arial, sans-serif; font-size: 8.7pt; line-height: 1.3; color: #111; }
h1 { font-size: 14pt; margin: 0 0 1mm 0; } h2 { font-size: 9.8pt; margin: 2.6mm 0 0.9mm 0; border-bottom: 0.6pt solid #1d4e89; color: #1d4e89; }
p { margin: 0.9mm 0; } ul { margin: 0.6mm 0 0.6mm 4mm; padding: 0; } li { margin: 0.3mm 0; }
table { border-collapse: collapse; width: 100%; margin: 1mm 0; font-size: 7.6pt; } th, td { border: 0.4pt solid #999; padding: 0.6mm 1.3mm; text-align: left; vertical-align: top; } th { background: #e8eef6; }
td.n, th.n { text-align: right; } .box { border: 0.8pt solid #1d4e89; background: #f3f7fc; padding: 1.6mm 2.8mm; margin: 1mm 0; }
.small { font-size: 7.4pt; color: #333; } .two { display: flex; gap: 3mm; } .two > div { flex: 1; } img { display: block; margin: 0 auto; }
table.office { font-size: 7pt; } table.office td, table.office th { padding: 0.3mm 1mm; } code { font-size: 7.6pt; }
"""

BODY = f"""
<h1>Pricing across markets with an AI-assisted workflow: from a developed to an emerging market</h1>
<p class="small">Team HS &middot; IAA AI-Assisted Actuarial Hackathon 2026, Parts 1 and 2 &middot; code, tests and working log: repository <code>iaa-hackathon</code> (<code>src/</code> for Part 1, <code>part2/</code> for Part 2)</p>

<div class="box"><b>Summary.</b> <b>Part 1</b> (developed market): Tweedie D&sup2; <b>0.13755</b> on the private leaderboard, rank 8 of 51 (best 0.13923). <b>Part 2</b> (emerging market, 209,063 test rows, 76% new business): public D&sup2; <b>{FIN.get('public', 'to be filled')}</b>.
What carried Part 2: <b>keep the developed-market relativities, re-learn the levels, add only the corrections two emerging years can prove, and treat new business as the main uncertainty.</b>
In cross-validation on the emerging rows a model trained on emerging data alone reaches {lad('B emerging-data model only (LightGBM)')}, the Part 1 model ported unchanged {lad('C Part 1 prior ported unchanged')}, the final pipeline {lad('F final: E + screened corrections')} (a constant rate per line: {lad('A constant rate per line')}).
New business is not visible in that cross-validation (12-15% of the rows) and moved the public score most; section 6 shows how we measured it and the limits of that measurement.</div>

<h2>1. Part 1 in brief (developed market, 2021-2024, three lines)</h2>
<p>Target: incurred less recoveries per policy row, declined claims excluded; ultimate cost via completion curves from report lags of mature years; offset log(exposure x completion); trend per line fitted on mature years (+3.4%, +6.3%, +5.4% a year).
Equal-weight blend of shallow (3-leaf) gradient boosting, frequency-severity boosting, CatBoost, GLM, EBM and neural nets, with credibility adjustment per policy and a level calibration on the public leaderboard (public 0.12956, private 0.13755).
What we learned and reused in Part 2: the data are close to a multiplicative structure (3-leaf trees beat 15-leaf trees by 0.0016), weather, sales and marketing columns add noise, averaging more models stops paying at about 0.0002, and levels are the cheapest thing to get wrong.</p>

<h2>2. Data and quality: what was wrong and what was done</h2>
<table><tr><th>Finding (script)</th><th>Treatment</th></tr>
<tr><td>Exposure stored in days for some rows; sums insured keyed 1000x too large (both markets; <code>prep*.py</code>)</td><td>Exposure rebuilt from period dates; sums above 100x the median divided by 1000</td></tr>
<tr><td>604 claims repeat another claim under a new id in the developed file, none in the emerging file</td><td>Exact repeats dropped (the check runs on both)</td></tr>
<tr><td>Developed <code>construction_type</code> has 11 spellings, and timber is coded T in 2021-22 and W from 2023 (found when a mapping to the emerging codes returned 90% missing)</td><td>Normalised to 4 codes (BRK, STN, WOD, MIX). Left alone, the letter is a year flag; the fix gave +0.005 D&sup2; on buildings</td></tr>
<tr><td>Emerging <code>occupation</code> is free text: 80 spellings of 20 jobs, plus "Self-employed X"</td><td>Trimmed, case-folded, split into occupation and a self-employed flag</td></tr>
<tr><td>11-12 columns are about 12% missing, independently, at the same rate in every year, channel, region and in the test rows</td><td>Treated as random gaps: native handling in trees, no missingness features</td></tr>
<tr><td>Claims valued at 31 Dec 2024; the emerging market has no mature year to measure completion</td><td>Completion curves from developed accident years 2021-22, justified by equal report-lag percentiles (motor median 9 days, 90th percentile 44 vs 46)</td></tr>
<tr><td>Fields in one market only: exact age, mileage, telematics, credit band (developed); age band, gender (emerging)</td><td>The transferred model uses age bands and shared fields; gender enters at the correction stage</td></tr></table>

<h2>3. What changed in the emerging market</h2>
{img('transfer.png', '100%')}
<ul>
<li><b>Same structure.</b> Apart from coding, the channel mix (70% broker) and new business, the rating factors are distributed as in the developed market (PSI near 0), and their effects on cost agree (figure, left).</li>
<li><b>Different levels.</b> Motor cost is 25% below the developed model, from 0.64 (bodily injury) to 1.28 (glass) by peril; escape of water is about 0.5 in buildings and contents. The climate differs (median hail days 14 vs 6, freezing days 19 vs 35, wildfire index 0.5 vs 0.1), and 2025 is colder and less hail-prone than 2023-24 (freezing days 29 vs 21 and 17; hail days 11 vs 14 and 17).</li>
<li><b>New effects.</b> Males cost 1.39x females on the at-fault motor perils (frequency ratios 1.66 bodily injury, 1.30 own damage, 1.43 third-party property, 1.04 glass); buildings policyholders aged 35-49 cost 0.67x. Neither effect exists in the developed market (gender is not recorded there).</li>
<li><b>New business.</b> 12-15% of training rows but 76% of 2025 rows (a broker portfolio; 83% carry a campaign code, 19% of training rows do). The train-versus-test adversarial AUC is 0.87-0.88 and is driven by exactly these columns.</li></ul>

<h2>4. Method, and what changed from Part 1 to Part 2</h2>
<p><b>(1) Prior.</b> Per line and peril, shallow LightGBM (3 leaves; Tweedie p=1.4, Poisson and extra-trees variants averaged in log space) on the four developed years, offset log(exposure x completion), cost capped at the 99.5th percentile with the cap load put back, on features both markets share (vehicle details, weather, marketing, history and premium left out; <code>new_business</code> kept after it added +0.0002 and +0.0006 on the two Part 1 validation years). The peril predictions sum to the row prediction.
<b>(2) Levels.</b> One multiplier per peril from the emerging years, shrunk to the line level with weight n/(n+400), n = claims. <b>(3) Corrections.</b> Candidate factors are screened with a robust (sandwich) score test and fitted as a ridge Tweedie GLM with the prior as offset (the penalty equals 100 claims of prior weight); gender (at-fault motor perils) and age band (buildings) survived nested cross-validation. <b>(4) Total.</b> The training total is restored after shrinkage. <b>(5) New-business level</b>, from the public leaderboard (section 6).</p>
<table><tr><th style="width:23%">Carried over from Part 1</th><th style="width:38%">Re-learned or added in Part 2</th><th>Dropped, with the reason</th></tr>
<tr><td>Offset, completion curves, capped Tweedie target, shallow trees, lean features</td><td>Peril levels, gender, buildings age band, new-business level, construction recode</td><td>Blend of seven families (the prior is one family; averaging variants added +0.002), experience rating (worse at every credibility), line trend (no mature year; renewal level checked on the leaderboard), premium features (carry no information beyond the model: A/E flat across quintiles)</td></tr></table>
<p class="small">Also tried and rejected: boosting corrections on the prior (0.1339 vs 0.1337), the developed prediction as a feature, GLM-initialised trees, weather in the prior (helps glass and storm per peril, not the line D&sup2;), vehicle details and make codes (no effect, and their codes are not comparable across markets).</p>

<h2>5. Validation and guardrails</h2>
<div class="two"><div>{img('ladder.png', '100%')}</div><div>
<p><b>Design.</b> 5-fold cross-validation grouped by customer on the 2023-24 emerging rows (a customer is never on both sides), pooled Tweedie D&sup2; (p=1.5) on reported cost, as in the competition; corrections are screened inside each training fold. The developed prior never sees an emerging claim.</p>
<p><b>22 automated tests</b> (<code>part2/tests</code>): exposure equals the dates; completion in (0,1], 1 for test rows; developed and emerging schemas and codes agree; feature column order; finite priors; calibration on training rows; prediction proportional to exposure; no negative or NaN predictions; the correction stage finds a planted effect and, in 20 null runs, rarely a false one; the probe solver recovers known multipliers; the submission checker rejects bad files.</p></div></div>
<p><b>Bugs the tests now catch.</b> LightGBM reads columns by position, so a reordered frame gave D&sup2; 0.036 instead of 0.134. A double level correction inflated motor predictions by 12% (found by comparing mean predicted rates with the previous version). A model that was supposed to use emerging data only had silently received the prior columns (fixed: 0.1244 became 0.1176).</p>

<h2>6. Using the leaderboard as a measurement, and what it showed</h2>
{img('leaderboard.png', '100%')}
<p>Public D&sup2; is a sum over rows, so it is separable by segment: Dev(m) = &sum;<sub>s</sub> 4[U<sub>s</sub> m<sub>s</sub><sup>-1/2</sup> + f T<sub>s</sub> m<sub>s</sub><sup>1/2</sup>], where T<sub>s</sub> is known from our predictions and U<sub>s</sub> is not. One probe per segment (multiply that segment by 1.2) identifies U<sub>s</sub> and gives the best multiplier m*<sub>s</sub> = U<sub>s</sub>/(f T<sub>s</sub>); the public share f cancels.
On version v2 the method gave 1.40 (motor new business), 1.23 (buildings), 1.11 (contents) and 1.01 (renewals), and it predicted 0.16433 for the half-way point; the leaderboard returned <b>0.16446</b>. This is a disclosed use of the leaderboard (ten submissions a day; every probe is listed in <code>part2/probes.json</code>); the sampling error of a multiplier is about 3% and we shrink them {FIN.get('shrink', '(see final version)')}. {FIN.get('note', '')}</p>

<h2>7. Uncertainty and limitations</h2>
<ul><li><b>Small perils.</b> Fire (70 claims), subsidence (52), flood (80 and 86) are shrunk to the line level; their 2025 level is uncertain by more than 30%. The 99.5% cap load rests on 9,258 claims.</li>
<li><b>New business</b> is the largest uncertainty: 76% of 2025 rows against about 1,000 training claims. The developed market gives +8% (motor) and +13% (buildings), the emerging rows more (motor A/E 1.23, standard error 0.15), the leaderboard more again. Whether the uplift sits in the broker channel (A/E 1.25 on 555 claims against 0.94 on 206 for direct) is unresolved.</li>
<li><b>Year effects.</b> 2024 claims are 80-97% complete and open case estimates were low in the developed market; the renewal level was confirmed on the leaderboard (multiplier 1.01). The 2025 weather shift is not modelled.</li>
<li><b>Governance.</b> Gender is used because the emerging market allows it. It is a rating correction whose effect size and sample counts are in the log, and a human must review it before it enters a tariff. All submissions and the final choice are the team's decision.</li></ul>

<h2>8. AI-assisted workflow and how its output was verified</h2>
<table><tr><th style="width:16%">Stage</th><th>What the AI did</th><th>Human control and verification</th></tr>
<tr><td>EDA, drift</td><td>Wrote and ran profile, PSI, adversarial and one-way scripts; proposed hypotheses (missingness, campaign codes, weather)</td><td>Hypotheses tested before use; campaign-code identities were noise (year-to-year correlation 0.1-0.35)</td></tr>
<tr><td>Data repair</td><td>Mapped codes between markets; the first mapping dropped 90% of construction types</td><td>Output counted against the raw data; the T/W recode found by cross-tabulating by year</td></tr>
<tr><td>Modelling</td><td>Implemented prior, shrinkage, score-test screening and the GLM; ran 40+ experiments including rejected ones</td><td>Fixed folds and seeds, nested CV, adoption rule (both validation years or a clear CV gain); negative results kept in the log</td></tr>
<tr><td>Testing</td><td>Wrote 22 tests from the failures observed</td><td>Tests run before every submission; planted-effect and null tests check the AI's own correction code</td></tr>
<tr><td>Writing</td><td>Working log, this report, the office premium table</td><td>Every number copied from script output; assumptions stated; the team reviews text and picks the final submission</td></tr></table>

<h2>9. Office premium for the 20 reference policies</h2>
<p class="small">P = (risk premium + fixed expense + catastrophe reinsurance) / (1 - variable expense 15% - commission - premium tax 8% - profit margin 8%), emerging rates from <code>expenses</code>. Assumptions: fixed expense 85 CU per policy-year, pro-rated by exposure; catastrophe reinsurance 12% of the risk premium for buildings and contents only; commission 0% direct, 20% broker. Risk premium = final prediction for the row, in CU.</p>
<table class="office"><tr><th>row</th><th>line</th><th>ch.</th><th class="n">expo</th><th class="n">risk</th><th class="n">fixed</th><th class="n">cat re</th><th class="n">var+comm</th><th class="n">tax</th><th class="n">profit</th><th class="n">office</th><th class="n">written</th><th class="n">ratio</th></tr>
{office_rows()}</table>
<p class="small">Ratio = office premium / current written premium. For most buildings rows the written premium is far below the modelled office premium (flood zone, new-business loading), so the current emerging tariff looks inadequate there; confidence is low for these rows (section 7).</p>
<p class="small"><b>Reproduce:</b> <code>part2/run_all.sh</code> rebuilds tables, priors, checks and the base submission; <code>part2/probes.json</code> and <code>part2/probe.py</code> apply the segment multipliers; seeds, folds and library versions are fixed (<code>uv.lock</code>).</p>
"""
html_doc = f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{BODY}</body></html>"
doc = HTML(string=html_doc).render(); n = len(doc.pages); doc.write_pdf("part2/report/out/report.pdf"); open("part2/report/out/report.html", "w").write(html_doc)
print("pages:", n)
