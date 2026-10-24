"""E8: screened corrections on the new-business-aware developed prior, nested in a 5-fold CV grouped by customer (screening sees training folds only)."""
import sys; sys.path.insert(0, "part2")
import numpy as np, polars as pl
from sklearn.model_selection import GroupKFold
from lib import *
from adapt import Adapter
EXCL = set(["row_id", "policy_id", "customer_id", "address_id", "period_start", "period_end", "split", "y", "n", "ymax", "completion", "exposure", "lr_dev", "exposure_bad", "si_bad",
            "customer_service_contacts", "customer_since_year", "renewal_decision", "occupation", "make_model", "previous_insurer", "branch_id", "campaign_code"])
SHORT = {"motor": ["gender", "new_business", "driver_age_band", "urban_density", "region", "channel", "payment_method", "marital_status", "self_employed", "fuel_type", "cover_type", "vehicle_use", "years_licensed", "ncb_years"],
         "buildings": ["policyholder_age_band", "gender", "new_business", "urban_density", "region", "channel", "construction_type", "occupancy", "property_type", "flood_zone", "accidental_damage_cover"],
         "contents": ["gender", "new_business", "policyholder_age_band", "urban_density", "region", "channel", "tenure", "security_level", "accidental_damage_cover", "works_from_home"]}
TAG_ = sys.argv[1] if len(sys.argv) > 1 else "_nb"
alpha = float(sys.argv[2]) if len(sys.argv) > 2 else 0.02; ridge = float(sys.argv[3]) if len(sys.argv) > 3 else 100.0
res = {"M1": [], "adapt": []}; ys = []
for line in LINES:
    em = load(line, "em").filter(pl.col("split") == "train").join(pl.read_parquet(f"work/p2/devprior{TAG_}_{line}.parquet"), on="row_id")
    cands = SHORT[line]
    y = em["y"].to_numpy(); off = np.log(offset(em)) + em["lr_dev"].to_numpy(); ye = y; ys.append(ye); grp = em["customer_id"].to_numpy()
    m1, ad = np.zeros(len(y)), np.zeros(len(y)); chosen_all = []
    for tri, vai in GroupKFold(5).split(em, y, grp):
        tr, va = em[tri], em[vai]
        k = y[tri].sum() / np.exp(off[tri]).sum(); m1[vai] = k * np.exp(off[vai])
        a = Adapter(cands, alpha=alpha, ridge=ridge).fit(tr, y[tri], off[tri]); ad[vai] = a.predict(va) * np.exp(off[vai]); chosen_all.append(a.chosen)
    print(line, "M1", round(d2(ye, m1), 4), "adapt", round(d2(ye, ad), 4), "chosen per fold:", chosen_all, flush=True)
    res["M1"].append(m1); res["adapt"].append(ad)
    full = Adapter(cands, alpha=alpha, ridge=ridge).fit(em, y, off); print("   all-data screen:", [(c, s, k, f"{p:.1e}") for c, s, k, p in full.log]); print("   effects:", full.effects())
Y = np.concatenate(ys); print("pooled", {k: round(d2(Y, np.concatenate(v)), 4) for k, v in res.items()})
