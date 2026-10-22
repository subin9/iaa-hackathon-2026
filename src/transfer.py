"""Carry the level decisions of a probed submission over to a new blend.

Each row gets the probed submission's value times the ratio of the new blend to the
blend it was built from, then every line is rescaled to the probed submission's line
total. Line levels and segment factors measured on the public board stay as they were.

usage: transfer.py PROBED_CSV NEW_OUT BASE_LIST GROUP ...   (BASE_LIST comma-separated)
"""
import sys
import numpy as np, polars as pl
import make_sub
from make_sub import blend, per_line

probed, out, base = sys.argv[1], sys.argv[2], sys.argv[3].split(",")
groups = [g.split(",") for g in sys.argv[4:]]
old_df, old = blend("test", [["tabmp0", "tabmp1", "tabmp2", "tabmp3"]])
make_sub.BASE = base
new_df, new = blend("test", groups)
assert (old_df["row_id"] == new_df["row_id"]).all()
sub = pl.DataFrame({"row_id": old_df["row_id"]}).join(pl.read_csv(probed), on="row_id", how="left")
ln = old_df["line"].to_numpy()
p = sub["prediction"].to_numpy()
q = per_line(ln, p * new / old, p)
pl.DataFrame({"row_id": old_df["row_id"], "prediction": q}).write_csv(out)
print({l: round(float((new[ln == l] / old[ln == l]).std()), 4) for l in np.unique(ln)}, "row ratio sd per line")
