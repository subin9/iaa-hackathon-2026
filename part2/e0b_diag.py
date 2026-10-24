"""E0b: why does the developed motor model rank emerging rows badly? Feature gain, and zero-shot D2 after dropping groups."""
import sys; sys.path.insert(0, "part2")
import numpy as np, polars as pl, lightgbm as lgb
from lib import *
P = dict(objective="tweedie", tweedie_variance_power=1.4, learning_rate=0.05, num_leaves=3, min_data_in_leaf=2000, feature_fraction=0.7,
         bagging_fraction=0.8, bagging_freq=1, lambda_l2=10.0, verbose=-1, num_threads=8)
line = sys.argv[1]
dev = load(line, "dev").filter(pl.col("split") == "train"); em = load(line, "em").filter(pl.col("split") == "train")
def run(drop, rounds=800, tag=""):
    X, Xe = features(dev, em, drop)
    y, load_f = cap_target(dev["y"].to_numpy(), 0.99); w = offset(dev); base = np.log(y.sum() / w.sum())
    m = lgb.train({**P, "seed": 0}, lgb.Dataset(X, y, init_score=np.log(w) + base), rounds)
    p = np.exp(base + m.predict(Xe, raw_score=True)) * offset(em) * load_f; ye = em["y"].to_numpy()
    print(f"{tag:34s} D2 {d2(ye, p):.4f} level-matched {d2(ye, p * ye.sum() / p.sum()):.4f} A/E {ye.sum() / p.sum():.3f}", flush=True)
    return m, X
base_drop = drop_cols()
m, X = run(base_drop, tag="base")
imp = sorted(zip(m.feature_importance("gain") / m.feature_importance("gain").sum(), X.columns), reverse=True)
print([(c, round(g, 3)) for g, c in imp[:14]])
vehicle = ["make_model", "engine_size_cc", "seats", "body_type", "transmission", "fuel_type", "driver_assist"]
groups = {"vehicle details": vehicle, "excess": ["voluntary_excess", "compulsory_excess"], "customer misc": ["occupation", "marital_status", "household_size", "years_at_address"],
          "geo": ["urban_density", "flood_zone", "distance_to_river_km", "elevation_m", "soil_type", "year_built", "property_age", "bedrooms", "roof_type", "energy_rating", "basement", "trees_within_5m", "listed_building", "solar_panels", "property_type"],
          "payments": ["missed_payments_12m", "customer_service_contacts"]}
for k, v in groups.items():
    run(base_drop + [c for c in v if c in dev.columns], tag="drop " + k)
run(base_drop + [c for g in groups.values() for c in g if c in dev.columns], tag="drop all groups")
