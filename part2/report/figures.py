"""Figures of the Part 2 report. Run from the repo root: PYTHONPATH=src:part2 .venv/bin/python part2/report/figures.py"""
import sys, json; sys.path.insert(0, "part2"); sys.path.insert(0, "src")
import numpy as np, polars as pl
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from lib import *

plt.rcParams.update({"font.size": 8, "axes.spines.top": False, "axes.spines.right": False, "axes.titlesize": 8.5, "axes.titleweight": "bold"})
LC = {"motor": "#1f77b4", "buildings": "#d62728", "contents": "#2ca02c"}
OUT = "part2/report/fig/"


def rel_table(df, c):
    s = df[c]
    if s.dtype.is_numeric() and s.dtype != pl.Boolean and s.n_unique() > 8:
        v = s.to_numpy().astype(float); e = np.unique(np.quantile(v[~np.isnan(v)], np.linspace(0, 1, 6)[1:-1]))
        lvl = pl.Series([("NA" if np.isnan(x) else f"q{int(np.searchsorted(e, x))}") for x in v])
    else:
        lvl = s.cast(pl.Utf8).fill_null("NA")
    t = df.with_columns(lvl=lvl).group_by("lvl").agg(w=(pl.col("exposure") * pl.col("completion")).sum(), y=pl.col("y").sum(), n=pl.col("n").sum())
    return {r["lvl"]: (r["y"] / r["w"] / (t["y"].sum() / t["w"].sum()), r["n"]) for r in t.iter_rows(named=True)}


def fig_transfer():
    FACT = {"motor": ["driver_age_band", "ncb_years", "years_licensed", "vehicle_use", "urban_density", "voluntary_excess", "prior_claims_5y", "cover_type"],
            "buildings": ["occupancy", "flood_zone", "urban_density", "roof_type", "basement", "property_type"],
            "contents": ["tenure", "security_level", "urban_density", "flood_zone", "works_from_home", "lodgers"]}
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.7), gridspec_kw={"width_ratios": [1, 1.25]})
    allx, ally = [], []
    for line in LINES:
        dev, em = load(line, "dev").filter(pl.col("split") == "train"), load(line, "em").filter(pl.col("split") == "train")
        for c in FACT[line]:
            a, b = rel_table(dev, c), rel_table(em, c)
            for lv in set(a) & set(b):
                if a[lv][1] >= 300 and b[lv][1] >= 80:
                    ax[0].scatter(a[lv][0], b[lv][0], s=10 + b[lv][1] / 40, color=LC[line], alpha=0.65, lw=0); allx.append(np.log(a[lv][0])); ally.append(np.log(b[lv][0]))
    lim = [0.35, 2.6]; ax[0].plot(lim, lim, color="grey", lw=0.8, ls="--"); ax[0].set_xscale("log"); ax[0].set_yscale("log"); ax[0].set_xlim(lim); ax[0].set_ylim(lim)
    from matplotlib.ticker import FixedLocator, FixedFormatter, NullLocator
    for a in (ax[0].xaxis, ax[0].yaxis): a.set_major_locator(FixedLocator([0.5, 1, 2])); a.set_major_formatter(FixedFormatter(["0.5", "1", "2"])); a.set_minor_locator(NullLocator())
    ax[0].set_xlabel("developed market, relative cost per exposure"); ax[0].set_ylabel("emerging market"); ax[0].set_title(f"Factor effects carry over (log corr {np.corrcoef(allx, ally)[0, 1]:.2f})")
    for line in LINES: ax[0].scatter([], [], color=LC[line], label=line, s=14)
    ax[0].legend(frameon=False, loc="upper left", fontsize=7)
    # peril level: actual / developed prior on the emerging rows (per-peril prior without any emerging data)
    rows = []
    for line in LINES:
        em = load(line, "em").filter(pl.col("split") == "train").join(pl.read_parquet(f"work/p2/devperil_v_avg_{line}.parquet"), on="row_id")
        for p in model2_perils(em):
            mu = np.exp(em[f"lrp_{p}"].to_numpy()) * em["exposure"].to_numpy() * em[f"compk_{p}"].to_numpy(); rows.append((line, p, em[f"y_{p}"].sum() / mu.sum(), int(em[f"n_{p}"].sum())))
    ypos = np.arange(len(rows))[::-1]
    ax[1].barh(ypos, [r[2] for r in rows], color=[LC[r[0]] for r in rows], height=0.7); ax[1].axvline(1, color="k", lw=0.8)
    ax[1].set_yticks(ypos); ax[1].set_yticklabels([f"{r[1].replace('_', ' ')} ({r[3]})" for r in rows], fontsize=6.5)
    ax[1].set_xlabel("actual cost / developed prior, by peril (claims)"); ax[1].set_title("Levels do not carry over")
    fig.tight_layout(); fig.savefig(OUT + "transfer.png", dpi=220); plt.close(fig)


def model2_perils(df):
    return sorted(c[4:] for c in df.columns if c.startswith("lrp_"))


def fig_ladder():
    r = json.load(open("work/p2/report_numbers.json")); names = list(r)
    lab = ["constant rate\nper line", "emerging data\nonly (GBM)", "Part 1 prior\nported as is", "prior +\nline level", "prior + shrunk\nperil levels", "final: + gender,\nage-band"]
    fig, ax = plt.subplots(figsize=(3.6, 2.5)); x = np.arange(len(names)); v = [r[k]["pooled"] for k in names]
    ax.bar(x, v, color=["#bbbbbb", "#bbbbbb", "#8fb4d9", "#5b8fc4", "#3a6fa8", "#1d4e89"], width=0.7)
    for i, a in enumerate(v): ax.text(i, a + 0.002, f"{a:.3f}", ha="center", fontsize=7)
    ax.set_xticks(x); ax.set_xticklabels(lab, fontsize=5.8); ax.set_ylim(0, 0.16); ax.set_ylabel("pooled D2, 5-fold CV by customer"); ax.set_title("Validation ladder (emerging 2023-24 rows)")
    fig.tight_layout(); fig.savefig(OUT + "ladder.png", dpi=220); plt.close(fig)


def fig_leaderboard():
    p = json.load(open("part2/probes.json")); fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.4), gridspec_kw={"width_ratios": [1.2, 1]})
    names = [v["name"] for v in p["versions"]]; sc = [v["public"] for v in p["versions"]]
    ax[0].plot(range(len(sc)), sc, "o-", color="#1d4e89")
    for i, s in enumerate(sc): ax[0].text(i, s + 0.0006, f"{s:.4f}", ha="center", fontsize=7)
    ax[0].set_xticks(range(len(names))); ax[0].set_xticklabels(names); ax[0].set_ylim(0.145, 0.170); ax[0].set_ylabel("public D2"); ax[0].set_title("Public leaderboard by version")
    m = p["solved_on_v2"]; k = list(m); ax[1].barh(range(len(k))[::-1], [m[x] for x in k], color="#d9822b", height=0.6); ax[1].axvline(1, color="k", lw=0.8)
    ax[1].set_yticks(range(len(k))[::-1]); ax[1].set_yticklabels([x.replace("_nb", " new business").replace("renewal", "renewals") for x in k]); ax[1].set_xlabel("best multiplier on v2 (from segment probes)")
    for i, x in enumerate(k): ax[1].text(m[x] + 0.01, len(k) - 1 - i, f"{m[x]:.2f}", va="center", fontsize=7)
    ax[1].set_xlim(0.8, 1.6); ax[1].set_title("New business is under-priced by v2")
    fig.tight_layout(); fig.savefig(OUT + "leaderboard.png", dpi=220); plt.close(fig)


if __name__ == "__main__":
    fig_transfer(); fig_ladder(); fig_leaderboard(); print("figures written to", OUT)
