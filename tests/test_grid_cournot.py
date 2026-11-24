import numpy as np
import pytest

from zsmp import grid_cournot as G


def toy_market(D0=1000.0, p0=50.0, elast=0.5, cap=2000.0, c=20.0, fringe=None):
    K = len(G.PGRID)
    fr = np.zeros((12, 2, K)) if fringe is None else fringe
    cc = [[[(np.array([0.0, cap]), np.array([0.0, c * cap])), (np.array([0.0, 0.0]), np.array([0.0, 0.0]))]] for _ in range(12)]
    return G.Market(D0=np.array([[D0, 0.0]]), RES=np.zeros((1, 2)), p0=np.array([p0]), month=np.array([0]), fringe=fr,
                    lo=np.array([-1e9]), hi=np.array([1e9]), elast=elast, firms=["A"], cap=np.tile(np.array([[[cap, 0.0]]]), (12, 1, 1)), ccurve=cc)


def test_monopoly_matches_closed_form():
    D0, p0, e, c = 1000.0, 50.0, 0.5, 20.0
    m = toy_market(D0, p0, e, 2000.0, c)
    A, B = p0 * (1 + 1 / e), p0 / (e * D0)             # inverse demand p = A - B q for q = D(p)
    q_star = (A - c) / (2 * B)
    eq = G.equilibrium(m, False, grid=201, iters=3)
    assert eq["Q"][0, 0, 0] == pytest.approx(q_star, rel=0.02)
    assert eq["pN"][0] == pytest.approx(A - B * q_star, rel=0.02)


def test_competitive_price_equals_marginal_cost_with_enough_fringe():
    K = len(G.PGRID)
    fr = np.zeros((12, 2, K)); idx = np.searchsorted(G.PGRID, 30.0)
    fr[:, 0, idx:] = 5000.0                            # fringe larger than demand at a cost of 30
    m = toy_market(fringe=fr)
    eq = G.equilibrium(m, False, competitive=True)
    assert eq["pN"][0] == pytest.approx(30.0, abs=2.0)


def test_flow_limit_separates_prices():
    K = len(G.PGRID)
    fr = np.zeros((12, 2, K))
    fr[:, 0, np.searchsorted(G.PGRID, 20.0):] = 3000.0     # cheap north
    fr[:, 1, np.searchsorted(G.PGRID, 80.0):] = 3000.0     # dear south
    m = toy_market(fringe=fr)
    m.D0 = np.array([[500.0, 1500.0]]); m.hi = np.array([300.0]); m.lo = np.array([-300.0])
    eq = G.equilibrium(m, True, competitive=True)
    assert eq["pS"][0] > eq["pN"][0] + 10.0 and eq["flow"][0] == pytest.approx(300.0, abs=1.0)
    free = G.equilibrium(m, False, competitive=True)
    assert free["pN"][0] == pytest.approx(free["pS"][0])


def test_owner_shares_sum_to_one():
    t = G.load_owner_shares(str(__import__("pathlib").Path(__file__).resolve().parents[1] / "data" / "raw" / "Kraftwerksliste_BNetzA_2026-11-05.csv"))
    assert (t.groupby(["zone", "fuel"]).share.sum().round(6) == 1.0).all()
