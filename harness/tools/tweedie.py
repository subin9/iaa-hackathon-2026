"""Tweedie deviance and D² (power 1.5 by default) — the competition metric.

Pure numpy so it runs without scikit-learn; matches
sklearn.metrics.d2_tweedie_score for 1 < power < 2.
"""
from __future__ import annotations

import numpy as np


def tweedie_deviance(y, mu, power: float = 1.5):
    y = np.asarray(y, dtype=float)
    mu = np.maximum(np.asarray(mu, dtype=float), 1e-9)
    p = power
    if not 1 < p < 2:
        raise ValueError("this helper covers 1 < power < 2")
    dev = 2 * (np.power(y, 2 - p) / ((1 - p) * (2 - p))
               - y * np.power(mu, 1 - p) / (1 - p)
               + np.power(mu, 2 - p) / (2 - p))
    return dev


def d2_tweedie(y, mu, power: float = 1.5, weights=None) -> float:
    """1 − deviance(model) / deviance(constant mean)."""
    y = np.asarray(y, dtype=float)
    mu = np.asarray(mu, dtype=float)
    w = np.ones_like(y) if weights is None else np.asarray(weights, dtype=float)
    dev_model = np.sum(w * tweedie_deviance(y, mu, power))
    ybar = np.sum(w * y) / np.sum(w)
    dev_null = np.sum(w * tweedie_deviance(y, np.full_like(y, ybar), power))
    return float(1 - dev_model / dev_null)


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    y = rng.gamma(1.2, 300, 10_000) * (rng.random(10_000) < 0.1)
    mu = np.maximum(y * 0.5 + 30, 1)
    print("d2 example:", round(d2_tweedie(y, mu), 4))
    try:
        from sklearn.metrics import d2_tweedie_score
        print("sklearn   :", round(d2_tweedie_score(y, mu, power=1.5), 4))
    except ImportError:
        pass
