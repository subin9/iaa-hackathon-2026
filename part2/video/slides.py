"""Build slides.pdf (landscape, one idea per slide) for the 5 minute video. Run: PYTHONPATH=src:part2 .venv/bin/python part2/video/slides.py"""
import json, base64, os
from weasyprint import HTML
R = json.load(open("work/p2/report_numbers.json")); FIN = json.load(open("part2/final.json")) if os.path.exists("part2/final.json") else {}
img = lambda n, h="60mm": f'<img src="data:image/png;base64,{base64.b64encode(open("part2/report/fig/" + n, "rb").read()).decode()}" style="height:{h}">'
CSS = """@page { size: 297mm 167mm; margin: 0; } body { font-family: 'DejaVu Sans', Arial, sans-serif; color: #111; margin: 0; }
.s { page-break-after: always; height: 167mm; padding: 12mm 16mm; box-sizing: border-box; } h1 { font-size: 26pt; color: #1d4e89; margin: 0 0 6mm 0; } h2 { font-size: 20pt; color: #1d4e89; margin: 0 0 5mm 0; }
li { font-size: 14.5pt; margin: 2.2mm 0; } .big { font-size: 40pt; font-weight: bold; color: #1d4e89; } .c { text-align: center; } .box { border: 1.5pt solid #1d4e89; padding: 4mm 6mm; background: #f3f7fc; font-size: 14pt; margin: 4mm 0; }
table { border-collapse: collapse; font-size: 13pt; } td, th { border: 0.6pt solid #999; padding: 2mm 4mm; text-align: left; } th { background: #e8eef6; }"""
final = FIN.get("public", "[final]")
slides = [
f"<h1>Pricing across markets with an AI-assisted workflow</h1><p style='font-size:16pt'>Team HS &middot; IAA AI-Assisted Actuarial Hackathon 2026</p><div class='c' style='margin-top:14mm'><span class='big'>0.13755</span> Part 1 private D&sup2;, rank 8 of 51<br><span class='big'>{final}</span> Part 2 public D&sup2;, emerging market</div>",
f"<h2>What changed in the emerging market?</h2><div class='c'>{img('transfer.png', '86mm')}</div><ul><li>Effects of rating factors carry over; levels do not</li><li>Two years of data; 76% of the 2025 rows are new business</li></ul>",
"<h2>Approach: keep relativities, re-learn levels</h2><ol style='font-size:15pt'><li><b>Prior</b>: shallow boosting per line and peril, 4 developed years, shared fields</li><li><b>Peril levels</b> from the emerging data, shrunk to the line level</li><li><b>Corrections</b> only if proven: robust score test, ridge GLM, nested CV</li><li><b>Total</b> restored; <b>new-business level</b> calibrated (slide 5)</li></ol><div class='box'>Survived: males x1.39 on at-fault motor perils; buildings age 35-49 x0.67</div>",
f"<h2>Validation ladder and guardrails</h2><div style='display:flex; gap:10mm; align-items:center'><div>{img('ladder.png', '82mm')}</div><div><ul><li>CV grouped by customer</li><li>22 automated tests</li><li>Bugs found, now tests: column order (0.036 vs 0.134), double level (+12%), timber coded T/W</li></ul></div></div>",
f"<h2>New business: measured on the leaderboard</h2><div class='c'>{img('leaderboard.png', '70mm')}</div><ul><li>Public score is separable by segment: one probe per segment gives its best multiplier</li><li>Predicted 0.16433, observed 0.16446</li></ul>",
"<h2>AI-assisted workflow, verified</h2><table><tr><th>AI did</th><th>Humans controlled</th></tr><tr><td>EDA, drift, models, 40+ experiments</td><td>Adoption rule, fixed folds, nested CV</td></tr><tr><td>22 tests from observed failures</td><td>Tests before every submission</td></tr><tr><td>Report and log</td><td>Numbers copied from script output; team picks the final</td></tr></table><div class='box'>Planted-effect and null tests check the AI's own code; rejected ideas stay in the log</div>",
"<h2>Limits and next</h2><ul><li>New business: largest uncertainty (broker vs direct unresolved)</li><li>Small perils shrunk hard; 2025 weather shift not modelled</li><li>Next: collect broker-portfolio claims early</li></ul>"]
HTML(string=f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>" + "".join(f"<div class='s'>{s}</div>" for s in slides) + "</body></html>").write_pdf("part2/video/slides.pdf")
print("slides:", len(slides))
