"""Two-node model of a bidding zone split.

Setup. Importing zone S has linear demand Q(p) = alpha - beta p. Exporting zone N holds a price-taking fringe with constant
marginal cost c_f and ample capacity. S holds n >= 1 strategic generators with constant marginal cost c >= c_f and ample
capacity. The line N-S has capacity K >= 0.

One zone: the market clears across the line (congestion is removed afterwards by cost-based redispatch, which does not
change the market price). The fringe is perfectly elastic at c_f, so the price is c_f and strategic generators produce
nothing.

Split: imports are at most K. The residual demand of the strategic generators is alpha - K - beta p (for prices above c_f).
Competitive benchmark price p_c = min((alpha - K)/beta, c) when K < K_bar = alpha - beta c_f, else c_f.
Cournot among n generators on that residual demand: total quantity n (A - beta c) / (n+1), price c + (A - beta c) / ((n+1) beta).
Notation: A = alpha - K (demand left after full import), K_c = alpha - beta c (critical import capacity).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Model:
    alpha: float
    beta: float
    c_f: float
    c: float
    n: int = 1

    @property
    def k_bar(self) -> float:            # flow in the one-zone market
        return self.alpha - self.beta * self.c_f

    @property
    def k_crit(self) -> float:           # import capacity below which the strategic generators are pivotal
        return self.alpha - self.beta * self.c


def one_zone(m: Model) -> dict:
    return {"price": m.c_f, "strategic_quantity": 0.0, "markup": 0.0, "import": max(m.alpha - m.beta * m.c_f, 0.0)}


def split_competitive(m: Model, K: float) -> dict:
    if K >= m.k_bar:
        return {"price": m.c_f, "strategic_quantity": 0.0, "import": m.k_bar}
    p_scarce = (m.alpha - K) / m.beta
    if p_scarce <= m.c:
        return {"price": p_scarce, "strategic_quantity": 0.0, "import": K}
    q = m.alpha - K - m.beta * m.c
    return {"price": m.c, "strategic_quantity": q, "import": K}


def split_cournot(m: Model, K: float) -> dict:
    """Symmetric Cournot equilibrium of n strategic generators on the residual demand."""
    if K >= m.k_bar:
        return {"price": m.c_f, "strategic_quantity": 0.0, "markup": 0.0, "import": m.k_bar}
    A = m.alpha - K
    if A - m.beta * m.c <= 0:                       # residual demand at cost c is empty: scarcity price, no production
        return {"price": A / m.beta, "strategic_quantity": 0.0, "markup": 0.0, "import": K}
    q_tot = m.n * (A - m.beta * m.c) / ((m.n + 1))
    price = (A - q_tot) / m.beta
    return {"price": price, "strategic_quantity": q_tot, "markup": price - m.c, "import": K}


def split_stackelberg(m: Model, K: float) -> dict:
    """One leader and n-1 Cournot followers on the residual demand (n >= 2); n = 1 is the monopoly."""
    A = m.alpha - K
    if K >= m.k_bar or A - m.beta * m.c <= 0:
        return split_cournot(m, K)
    n = m.n
    if n == 1:
        return split_cournot(m, K)
    # inverse demand P = (A - Q)/beta, marginal cost c; followers' best response q_f = (A - beta c - q_L)/n (n-1 followers)
    # follower total (n-1) q_f = (n-1)(A - beta c - q_L)/n; leader maximises (P - c) q_L
    a0 = A - m.beta * m.c
    q_L = a0 / 2.0
    q_F = (n - 1) * (a0 - q_L) / n
    Q = q_L + q_F
    price = (A - Q) / m.beta
    return {"price": price, "strategic_quantity": Q, "markup": price - m.c, "import": K, "leader_quantity": q_L}


def markup_change(m: Model, K: float) -> float:
    """Markup after the split minus markup in the one zone (zero)."""
    return split_cournot(m, K)["markup"] - one_zone(m)["markup"]
