"""E2: Cournot equilibrium with owners on the German zonal market, one zone against a north/south split.
Usage: python scripts/run_grid_cournot.py [--elasticity 0.1] [--hours N]
Needs the sibling repository de-bidding-zones (system, hours and flow-based bounds) and the Bundesnetzagentur power plant list CSV."""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BZ = ROOT.parent / "de-bidding-zones"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(BZ / "src"))
from bzones import data as D                       # noqa: E402
from zsmp import grid_cournot as G                 # noqa: E402

KWL = ROOT / "data" / "raw" / "Kraftwerksliste_BNetzA_2026-11-05.csv"
FUEL_OF = {"lignite": "lignite", "coal": "coal", "gas_ccgt": "gas", "gas_ocgt": "gas", "gas_st": "gas"}
STRATEGIC = ["RWE", "EnBW", "Uniper", "LEAG", "STEAG", "Vattenfall", "Statkraft", "EWE", "Hamburger Energiewerke"]


def build(elast: float, nhours: int | None, strategic_min_share: float = 0.0):
    s = D.build_system(split_lat=51.0)
    fp = D.fuel_prices()
    hs = pd.read_csv(BZ / "results" / "main" / "hourly.csv", parse_dates=["time"]).set_index("time")
    if nhours:
        hs = hs.iloc[:: max(len(hs) // nhours, 1)]
    h = D.hourly().loc[hs.index]
    sh = G.load_owner_shares(str(KWL))
    fl = s.fleet.copy()
    fl["zone"] = s.zone[fl.bus.to_numpy()]
    fl["avail"] = [D.AVAILABILITY[t] for t in fl.tech]
    firms = [f for f in STRATEGIC if f in set(sh.parent)]
    # demand and must-run renewables per zone and hour
    res_n = []
    D0 = np.zeros((len(h), 2)); RES = np.zeros((len(h), 2))
    for i, (ts, r) in enumerate(h.iterrows()):
        res = (s.res_share.wind_onshore * r.wind_onshore + s.res_share.wind_offshore * r.wind_offshore + s.res_share.solar * r.solar).to_numpy()
        dem = s.load_w * r.load
        for z in (0, 1):
            D0[i, z] = dem[s.zone == z].sum(); RES[i, z] = res[s.zone == z].sum()
    zone_of_model = lambda z: 0 if z == 0 else 1   # model zone 0 = north (y >= 51), 1 = south, same convention as the list
    # note: bzones zone = (y < split) -> 1 means SOUTH; the same convention is used for the owner list (north = 0)
    month = h.index.month.to_numpy() - 1
    K = len(G.PGRID)
    fringe_all = np.zeros((12, 2, K)); fringe_ex = np.zeros((12, 2, K))
    cap = np.zeros((12, len(firms), 2))
    ccurve = []
    for mo in range(12):
        cost = D.marginal_costs(fl.reset_index(drop=True), mo + 1, fp)
        rows = []
        per_firm = {f: {0: [], 1: []} for f in firms}
        for g, (tech, z, mw, av, c) in enumerate(zip(fl.tech, fl.zone, fl.mw, fl.avail, cost)):
            avail_mw = mw * av
            cls = FUEL_OF.get(tech)
            frac_strat = 0.0
            if cls:
                for f in firms:
                    x = sh[(sh.zone == z) & (sh.fuel == cls) & (sh.parent == f)].share.sum()
                    if x > strategic_min_share:
                        per_firm[f][z].append((c, avail_mw * x)); frac_strat += x
            rows.append((z, c, avail_mw, 1.0 - min(frac_strat, 1.0)))
        for z, c, a, fr in rows:
            idx = np.searchsorted(G.PGRID, c)           # supplies at prices >= cost
            fringe_all[mo, z, idx:] += a
            fringe_ex[mo, z, idx:] += a * fr
        cc_m = []
        for f in firms:
            cc_f = []
            for z in (0, 1):
                u = sorted(per_firm[f][z])
                capv = np.array([0.0] + [x[1] for x in u]).cumsum() if u else np.array([0.0, 0.0])
                costv = np.array([0.0] + [x[0] * x[1] for x in u]).cumsum() if u else np.array([0.0, 0.0])
                cc_f.append((capv, costv))
                cap[mo, firms.index(f), z] = capv[-1]
            cc_m.append(cc_f)
        ccurve.append(cc_m)
    p0 = np.clip(hs.price_one.to_numpy(), 10.0, 300.0)
    lo, hi = hs.fb_min.to_numpy(), hs.fb_max.to_numpy()
    mk = lambda fr: G.Market(D0, RES, p0, month, fr, lo, hi, elast, firms, cap, ccurve)
    return mk(fringe_all), mk(fringe_ex), hs, firms, sh


def main(elast: float, nhours: int | None, tag: str):
    comp, strat, hs, firms, sh = build(elast, nhours)
    out = {"elasticity": elast, "hours": len(hs), "firms": firms}
    for name, split in (("one_zone", False), ("split", True)):
        c = G.equilibrium(comp, split, competitive=True)
        e = G.equilibrium(strat, split)
        for k, v in (("competitive", c), ("cournot", e)):
            out[f"{name}_{k}"] = {"price_north": float(v["pN"].mean()), "price_south": float(v["pS"].mean()),
                                  "load_weighted": float(((v["pN"] * strat.D0[:, 0] + v["pS"] * strat.D0[:, 1]).sum()) / strat.D0.sum()),
                                  "flow_mean": float(v["flow"].mean())}
        out[f"{name}_cournot"]["change_history"] = e["change_history"]
        ref_n, ref_s = (hs.price_one, hs.price_one) if not split else (hs.price_north_fb, hs.price_south_fb)
        out[f"{name}_check_competitive_vs_lp"] = {"mean_abs_diff_north": float(np.abs(c["pN"] - ref_n.to_numpy()).mean()),
                                                  "mean_abs_diff_south": float(np.abs(c["pS"] - ref_s.to_numpy()).mean()),
                                                  "corr_south": float(np.corrcoef(c["pS"], ref_s.to_numpy())[0, 1])}
        out[f"{name}_markup_south"] = float((e["pS"] - c["pS"]).mean())
        out[f"{name}_markup_north"] = float((e["pN"] - c["pN"]).mean())
        out[f"{name}_markup_weighted"] = out[f"{name}_cournot"]["load_weighted"] - out[f"{name}_competitive"]["load_weighted"]
        np.save(ROOT / "results" / f"grid_cournot_{tag}_{name}.npy", np.c_[e["pN"], e["pS"], c["pN"], c["pS"], e["flow"]])
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / f"grid_cournot_{tag}.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--elasticity", type=float, default=0.1)
    ap.add_argument("--hours", type=int, default=None)
    ap.add_argument("--tag", default="e0.1")
    a = ap.parse_args()
    main(a.elasticity, a.hours, a.tag)
