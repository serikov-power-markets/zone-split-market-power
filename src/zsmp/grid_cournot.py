"""Diagonalised Cournot equilibrium on the zonal German market (one zone against a north/south split), with plant owners.

Built on the system of `de-bidding-zones` (780-bus grid aggregated to two zones, 2024 fleet, 1,464 sampled hours, flow-based bounds on the net position
of the north). Owners come from the Bundesnetzagentur power plant list (operator names, data of 5 Nov 2026), grouped into parent firms and assigned to the
north or south zone by federal state. The list has no coordinates: ownership shares per zone and fuel are applied to the model's plant groups. Demand is
made elastic around the competitive one-zone price with an ASSUMED constant elasticity (a perfectly inelastic demand makes Cournot degenerate).

Equilibrium: each strategic firm chooses its output in the north and in the south from a grid of fractions of its available capacity, given the outputs of
the others (best-response iteration, vectorised over hours); the fringe (all other units, renewables must-run) supplies at marginal cost; the market clears
with the flow bounded by the flow-based limits. This is a zonal Cournot game with exogenous flow limits, not an MPEC or EPEC on the nodal network.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np
import pandas as pd

PGRID = np.arange(0.0, 602.0, 2.0)           # price grid, EUR/MWh; 600 is the price cap (assumption)
STATE_NORTH = {"SchleswigHolstein", "Hamburg", "Bremen", "Niedersachsen", "MecklenburgVorpommern", "Berlin", "Brandenburg", "SachsenAnhalt",
               "NordrheinWestfalen", "Sachsen"}   # assumed: the large plants of Saxony and North Rhine-Westphalia lie north of 51 degrees
ENERGY_CLASS = {"Braunkohle": "lignite", "Steinkohle": "coal", "Erdgas": "gas"}
PARENTS = [("RWE", r"\brwe\b"), ("EnBW", r"enbw"), ("Uniper", r"uniper|e\.on kraftwerke"), ("LEAG", r"leag|lausitz energie|mibrag|mitteldeutsche braunkohle|eph|jänschwalde|boxberg"),
           ("Vattenfall", r"vattenfall"), ("STEAG", r"steag"), ("Statkraft", r"statkraft"), ("EWE", r"\bewe\b"), ("Hamburger Energiewerke", r"hamburger energiewerke")]


def load_owner_shares(path: str) -> pd.DataFrame:
    """Share of each parent firm in the operating capacity (net, MW) of each zone and fuel class (lignite, coal, gas)."""
    import io
    text = open(path, encoding="latin1").read()
    d = pd.read_csv(io.StringIO(text[text.index("EinheitMastrNummer"):]), sep=";", low_memory=False)
    d = d[(d.Kraftwerksstatus == "InBetrieb") & d.Energietraeger.isin(ENERGY_CLASS)].copy()
    d["mw"] = pd.to_numeric(d.Nettonennleistung_MW.astype(str).str.replace(",", "."), errors="coerce")
    d = d[d.mw >= 10].copy()          # units of at least 10 MW; the list aggregates smaller ones
    d["fuel"] = d.Energietraeger.map(ENERGY_CLASS)
    d["zone"] = np.where(d.Bundesland.isin(STATE_NORTH), 0, 1)
    op = d.Anlagenbetreiber.fillna("").str.lower()
    d["parent"] = "other"
    for name, pat in PARENTS:
        d.loc[op.str.contains(pat, regex=True) & (d.parent == "other"), "parent"] = name
    t = d.groupby(["zone", "fuel", "parent"]).mw.sum().reset_index()
    t["share"] = t.mw / t.groupby(["zone", "fuel"]).mw.transform("sum")
    return t


@dataclass
class Market:
    D0: np.ndarray            # (H, 2) inelastic reference demand per zone
    RES: np.ndarray           # (H, 2) must-run renewables
    p0: np.ndarray            # (H,) reference price
    month: np.ndarray         # (H,) 0..11
    fringe: np.ndarray        # (12, 2, K) fringe supply at each grid price
    lo: np.ndarray            # (H,) bounds on net position of zone 0 (north)
    hi: np.ndarray
    elast: float
    firms: list
    cap: np.ndarray           # (12, F, 2) available capacity of strategic firms
    ccurve: list              # per (month, firm, zone): (cum_cap, cum_cost) arrays for the cost integral


def _cross(E: np.ndarray) -> np.ndarray:
    """Price at which excess demand E (H, K), falling in p, crosses zero (linear interpolation on the grid)."""
    neg = E <= 0
    k = np.where(neg.any(axis=1), neg.argmax(axis=1), len(PGRID) - 1)
    k0 = np.maximum(k - 1, 0)
    rows = np.arange(len(E))
    e0, e1 = E[rows, k0], E[rows, k]
    frac = np.where((e0 - e1) > 1e-9, e0 / np.maximum(e0 - e1, 1e-9), 0.0)
    p = PGRID[k0] + frac * (PGRID[k] - PGRID[k0])
    p = np.where(k == 0, 0.0, p)
    return np.where(~neg.any(axis=1), PGRID[-1], p)


def clear(m: Market, Q: np.ndarray, split: bool) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Zonal prices and north export for strategic output Q (H, 2). One zone if not split."""
    H = len(Q)
    P = PGRID[None, :]
    el = np.clip(1.0 - m.elast * (P - m.p0[:, None]) / m.p0[:, None], 0.0, None)
    ex = []
    for z in (0, 1):
        ex.append(m.D0[:, z, None] * el - m.RES[:, z, None] - Q[:, z, None] - m.fringe[m.month, z, :])
    pu = _cross(ex[0] + ex[1])
    ku = np.clip(np.searchsorted(PGRID, pu), 0, len(PGRID) - 1)
    rows = np.arange(H)
    F = -ex[0][rows, ku]                       # export of the north at the common price
    if not split:
        return pu, pu, F
    Fc = np.clip(F, m.lo, m.hi)
    binding = np.abs(Fc - F) > 1e-6
    pN = _cross(ex[0] + Fc[:, None])
    pS = _cross(ex[1] - Fc[:, None])
    return np.where(binding, pN, pu), np.where(binding, pS, pu), np.where(binding, Fc, F)


def cost_of(m: Market, f: int, z: int, q: np.ndarray) -> np.ndarray:
    out = np.zeros(len(q))
    for mo in range(12):
        sel = m.month == mo
        if sel.any():
            cc, cost = m.ccurve[mo][f][z]
            out[sel] = np.interp(q[sel], cc, cost)
    return out


def equilibrium(m: Market, split: bool, iters: int = 14, grid: int = 11, competitive: bool = False) -> dict:
    H, F = len(m.p0), len(m.firms)
    Kf = m.cap[m.month]                          # (H, F, 2)
    Q = np.zeros((H, F, 2)) if competitive else Kf * 0.5
    fr = np.linspace(0.0, 1.0, grid)
    hist = []
    if not competitive:
        for it in range(iters):
            change = 0.0
            for f in range(F):
                others = Q.sum(axis=1) - Q[:, f, :]
                best = np.full(H, -np.inf); bq = Q[:, f, :].copy()
                zones = [z for z in (0, 1) if Kf[:, f, z].max() > 0]
                grids = [(a, b) for a in fr for b in fr] if len(zones) == 2 else [(a, 0.0) if zones == [0] else (0.0, a) for a in fr]
                for a, b in grids:
                    q = np.stack([a * Kf[:, f, 0], b * Kf[:, f, 1]], axis=1)
                    pN, pS, _ = clear(m, others + q, split)
                    prof = pN * q[:, 0] + pS * q[:, 1] - cost_of(m, f, 0, q[:, 0]) - cost_of(m, f, 1, q[:, 1])
                    better = prof > best + 1e-9
                    best = np.where(better, prof, best); bq = np.where(better[:, None], q, bq)
                new = bq if it < 3 else 0.5 * Q[:, f, :] + 0.5 * bq        # damping after three undamped rounds against cycling on the grid
                change = max(change, float(np.abs(new - Q[:, f, :]).mean() / max(Kf.max(), 1.0)))
                Q[:, f, :] = new
            hist.append(change)
    pN, pS, flow = clear(m, Q.sum(axis=1), split)
    return {"pN": pN, "pS": pS, "flow": flow, "Q": Q, "change_history": hist}
