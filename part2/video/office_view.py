"""Print the office premium table (part2/office_premium.py output) in 100 columns for the screen recording.
usage: python3 part2/video/office_view.py OFFICE.csv"""
import csv, sys

print(f"{'row':10s} {'line':9s} {'channel':7s} {'expo':>5s} {'risk':>7s} {'fixed':>6s} {'cat re':>6s} {'loads':>7s} {'office P':>9s} {'written':>8s} {'P/written':>9s}")
for r in csv.DictReader(open(sys.argv[1])):
    f = {k: float(v) for k, v in r.items() if k not in ("row_id", "line", "channel")}
    loads = f["variable"] + f["commission"] + f["tax"] + f["profit"]
    print(f"{r['row_id']:10s} {r['line']:9s} {r['channel']:7s} {f['exposure']:5.2f} {f['risk']:7.1f} {f['fixed']:6.0f} {f['cat_re']:6.1f} {loads:7.1f} {f['office']:9.1f} {f['written_premium']:8.1f} {f['vs_written']:9.2f}")
