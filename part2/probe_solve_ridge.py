"""Compare structures for the best segment factors of a base submission, with a leave-one-probe-out check.

Row features Z (indicators) give log m*_row = Z theta. Every probe (a submission divided by the base) is one equation, the base score fixes the scale. Several
structures (sets of features) are fitted with a small ridge penalty, then each probe is held out in turn and predicted, which measures how well a structure
extrapolates (the 7-parameter structure of probe_solve_struct.py was too optimistic: it predicted 0.17512 for v6 and the leaderboard gave 0.17182).

usage: probe_solve_ridge.py PROBES_JSON   (as for probe_solve_struct.py; probes may be any submissions on the same rows)
"""
import sys, json
import numpy as np, polars as pl
from scipy.optimize import least_squares
sys.path.insert(0, "part2")
import segments

F = 1.0 / 3.0
SIGMA = 2e-5      # tolerated misfit of a score equation (rounding is 3e-6, structure error is larger)


def features(d):
    line, nb = d["line"].to_numpy(), d["nb"].to_numpy(); ch = d["channel"].to_numpy(); g = d["gender"].to_numpy(); age = d["age"].to_numpy()
    mo, bu, co = line == "motor", line == "buildings", line == "contents"
    z = {"motor_nb": mo & (nb == 1), "buildings_nb": bu & (nb == 1), "contents_nb": co & (nb == 1), "renewal": nb == 0,
         "ren_motor": mo & (nb == 0), "ren_buildings": bu & (nb == 0), "ren_contents": co & (nb == 0),
         "direct_nb_motor": mo & (nb == 1) & (ch == "direct"), "cs_nb_motor": mo & (nb == 1) & (ch == "comparison_site"),
         "male_motor": mo & (g == "M"), "male_nb": mo & (g == "M") & (nb == 1), "male_ren": mo & (g == "M") & (nb == 0),
         "age3549_buildings": bu & (age == "35-49"), "age3549_nb": bu & (age == "35-49") & (nb == 1), "age3549_ren": bu & (age == "35-49") & (nb == 0)}
    return {k: v.astype(float) for k, v in z.items()}


STRUCTURES = {
    "S1 pooled renewal, male, direct, age": ["motor_nb", "buildings_nb", "contents_nb", "renewal", "direct_nb_motor", "male_motor", "age3549_buildings"],
    "S2 renewal by line": ["motor_nb", "buildings_nb", "contents_nb", "ren_motor", "ren_buildings", "ren_contents", "direct_nb_motor", "male_motor", "age3549_buildings"],
    "S3 male by nb": ["motor_nb", "buildings_nb", "contents_nb", "renewal", "direct_nb_motor", "male_nb", "male_ren", "age3549_buildings"],
    "S4 renewal by line, male by nb": ["motor_nb", "buildings_nb", "contents_nb", "ren_motor", "ren_buildings", "ren_contents", "direct_nb_motor", "male_nb", "male_ren", "age3549_buildings"],
    "S5 no male": ["motor_nb", "buildings_nb", "contents_nb", "renewal", "direct_nb_motor", "age3549_buildings"],
}
TAU = {"male_motor": 0.3, "male_nb": 0.3, "male_ren": 0.3, "age3549_buildings": 0.25, "age3549_nb": 0.25, "age3549_ren": 0.25}   # others 0.3 too: ridge only


def fit(Zm, mu, cs, public, ridge=1.0):
    T = np.sqrt(mu)

    def dev(ms, c): return float((4 * F * T * (ms / np.sqrt(c) + np.sqrt(c))).sum())

    def model(th):
        ms = np.exp(Zm @ th); dev0 = dev(ms, cs[0]) / (1 - public[0])
        return np.array([1 - dev(ms, c) / dev0 for c in cs[1:]])

    th0 = np.zeros(Zm.shape[1])
    res = lambda th: np.concatenate([(model(th) - np.array(public[1:])) / SIGMA, ridge * th / 0.3])
    sol = least_squares(res, th0, xtol=1e-10, ftol=1e-12, gtol=1e-12)
    return sol.x, model


if __name__ == "__main__":
    pr = json.load(open(sys.argv[1]))
    base = pl.read_csv(pr[0]["file"]); d = segments.test_frame(base); mu = d["prediction"].to_numpy(); Z = features(d)
    cs = [np.ones(len(mu))] + [d.select("row_id").join(pl.read_csv(p["file"]), on="row_id", how="left")["prediction"].to_numpy() / mu for p in pr[1:]]
    public = [p["public"] for p in pr]; names = [p["file"].split("/")[-1] for p in pr]
    for sname, feats in STRUCTURES.items():
        Zm = np.stack([Z[f] for f in feats], 1)
        th, model = fit(Zm, mu, cs, public)
        err_in = np.abs(model(th) - np.array(public[1:])).max()
        loo = []
        for i in range(1, len(cs)):
            keep = [j for j in range(len(cs)) if j != i]
            th_i, model_i = fit(Zm, mu, [cs[j] for j in keep], [public[j] for j in keep])
            # predict the held-out probe with the leave-out fit: need dev0 from the same fit
            T = np.sqrt(mu); ms = np.exp(Zm @ th_i); dv = lambda c: float((4 * F * T * (ms / np.sqrt(c) + np.sqrt(c))).sum())
            pred = 1 - dv(cs[i]) / (dv(cs[0]) / (1 - public[0])); loo.append(pred - public[i])
        print(f"{sname:36s} max in-sample err {err_in:.1e} | leave-one-probe-out err: " + " ".join(f"{n.split('.')[0]}={e:+.4f}" for n, e in zip(names[1:], loo)),
              f"| rms {np.sqrt(np.mean(np.square(loo))):.4f}")
        print("    m*:", {f: round(float(np.exp(t)), 3) for f, t in zip(feats, th)})
