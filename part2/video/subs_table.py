"""Print `kaggle competitions submissions --csv` as a narrow table for the screen recording: file, UTC time, public score, description.
usage: kaggle competitions submissions SLUG --csv | python3 part2/video/subs_table.py [N]"""
import csv, sys

rows = [r for r in csv.DictReader(l for l in sys.stdin if "," in l)][: int(sys.argv[1]) if len(sys.argv) > 1 else 22]
for r in rows:
    print(f"{r['fileName'][:26]:26s}  {r['date'][:16]}  {r['publicScore']:>8s}  {r['description'][:72]}")
