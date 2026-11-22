import numpy as np
import pandas as pd

from zsmp import empirical as em


def test_pivotal_logic():
    h = pd.DataFrame({"load": [100.0, 100.0], "wind": [0.0, 0.0], "solar": [0.0, 0.0]})
    # south demand 55, supply of the others 40 (a_south 80, 2 firms: 80 - 40), K = 10 -> PSI = 55 - 10 - 40 = 5 > 0
    r = em.pivotal_share(h, np.array([10.0, 30.0]), 80.0, n_firms=2)
    assert r["share_pivotal"] == 0.5 and abs(r["mean_psi_when_pivotal"] - 5.0) < 1e-9


def test_more_firms_fewer_pivotal_hours():
    h = pd.DataFrame({"load": np.linspace(60, 140, 50), "wind": 0.0, "solar": 0.0})
    K = np.full(50, 5.0)
    shares = [em.pivotal_share(h, K, 100.0, n)["share_pivotal"] for n in (1, 2, 3, 4)]
    assert all(a >= b for a, b in zip(shares, shares[1:]))
