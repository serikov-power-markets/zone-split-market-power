import numpy as np
import pytest
from scipy.optimize import minimize_scalar

from zsmp import analytic as an

M = an.Model(alpha=100.0, beta=1.0, c_f=20.0, c=40.0, n=1)


def _profit(q_own, q_others, A, beta, c):
    price = max((A - q_own - q_others) / beta, 0.0)
    return (price - c) * q_own


def test_critical_capacity_and_monopoly_markup():
    assert M.k_crit == 60.0 and M.k_bar == 80.0
    r = an.split_cournot(M, 30.0)          # A = 70, residual at cost = 30, monopoly quantity 15
    assert r["strategic_quantity"] == pytest.approx(15.0)
    assert r["markup"] == pytest.approx((M.alpha - 30.0 - M.beta * M.c) / (2 * M.beta))
    assert r["price"] == pytest.approx(55.0)


def test_markup_zero_above_critical_capacity_and_positive_below():
    for K in (60.0, 70.0, 80.0, 120.0):
        assert an.markup_change(M, K) == pytest.approx(0.0)
    for K in (0.0, 20.0, 59.0):
        assert an.markup_change(M, K) > 0


def test_cournot_matches_numerical_best_responses():
    for n in (1, 2, 3, 5):
        m = an.Model(100.0, 1.0, 20.0, 40.0, n)
        K = 25.0
        A = m.alpha - K
        r = an.split_cournot(m, K)
        q = r["strategic_quantity"] / n
        # best response of one generator to the others' equilibrium quantity
        res = minimize_scalar(lambda x: -_profit(x, (n - 1) * q, A, m.beta, m.c), bounds=(0, A), method="bounded",
                              options={"xatol": 1e-9})
        assert res.x == pytest.approx(q, abs=1e-5)


def test_markup_falls_with_number_of_generators_and_closed_form():
    K = 10.0
    mus = []
    for n in (1, 2, 4, 8):
        m = an.Model(100.0, 1.0, 20.0, 40.0, n)
        mu = an.split_cournot(m, K)["markup"]
        assert mu == pytest.approx((m.alpha - K - m.beta * m.c) / ((n + 1) * m.beta))
        mus.append(mu)
    assert all(a > b for a, b in zip(mus, mus[1:]))


def test_stackelberg_leader_advantage():
    m = an.Model(100.0, 1.0, 20.0, 40.0, 2)
    cour, stack = an.split_cournot(m, 20.0), an.split_stackelberg(m, 20.0)
    assert stack["strategic_quantity"] > cour["strategic_quantity"]     # more output, lower price
    assert stack["price"] < cour["price"]
    # leader earns more than a Cournot player
    A, c = m.alpha - 20.0, m.c
    q_L = stack["leader_quantity"]
    pi_L = (stack["price"] - c) * q_L
    pi_C = (cour["price"] - c) * cour["strategic_quantity"] / 2
    assert pi_L > pi_C


def test_competitive_benchmark_between():
    for K in (0.0, 30.0, 70.0):
        c = an.split_competitive(M, K)["price"]
        s = an.split_cournot(M, K)["price"]
        assert s >= c - 1e-12
