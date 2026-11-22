"""Check of the proposition on the hourly results of the German bidding zone study (de-bidding-zones, 1,464 sampled
hours of 2024): in how many hours does the import capacity of the south bind against the flow of the one-zone market, and
in how many hours would a firm in the south be pivotal for the residual demand?

Pivotal supplier index for the largest of n equal firms in the south: PSI = D_S - RES_S - K - (A_S - a_firm), pivotal if
PSI > 0, where D_S is southern load, RES_S southern renewable output, K the import capacity (the realised imports in the
one-zone market, the flow-based limit in the split), A_S the available dispatchable capacity in the south and a_firm = A_S / n.
Assumptions, all stated in the README: south load 55% of the national load (the study puts 45% in the north), southern
share of wind 21% (upper bound from the study) and of solar 50%, availability of dispatchable capacity 85%, n = 4 equal firms.
The numbers are indicators of when the mechanism of the proposition can operate, not estimates of market power.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DISPATCHABLE = {"Natural Gas", "Hard Coal", "Lignite", "Nuclear", "Oil", "Hydro", "Solid Biomass", "Biogas", "Waste"}


def south_dispatchable_mw(lat_split: float = 51.0, availability: float = 0.85) -> float:
    d = pd.read_csv(ROOT / "data" / "raw" / "powerplants_de.csv.gz")
    d = d[d.Fueltype.isin(DISPATCHABLE) & (d.lat < lat_split) & (d.DateOut.isna() | (d.DateOut > 2024))]
    d = d[~d.Technology.fillna("").str.contains("Pumped|Run-Of-River", case=False)]
    return float(d.Capacity.sum() * availability)


def pivotal_share(h: pd.DataFrame, K: np.ndarray, a_south: float, n_firms: int = 4, load_share: float = 0.55,
                  wind_share: float = 0.21, solar_share: float = 0.5) -> dict:
    d_s = h["load"].to_numpy() * load_share
    res_s = h["wind"].to_numpy() * wind_share + h["solar"].to_numpy() * solar_share
    psi = d_s - res_s - K - (a_south - a_south / n_firms)
    return {"share_pivotal": float((psi > 0).mean()), "mean_psi_when_pivotal": float(psi[psi > 0].mean()) if (psi > 0).any() else 0.0}


def run() -> dict:
    h = pd.read_csv(ROOT / "data" / "raw" / "de_bidding_zones_hourly.csv")
    f1 = h["np_north_one"].to_numpy()          # MW north exports to the south in the one-zone market
    k_fb = h["fb_max"].to_numpy()              # flow-based limit on the north's net position
    binding = f1 > k_fb + 1.0
    a_s = south_dispatchable_mw()
    ntc = float(np.percentile(k_fb, 10))
    out = {
        "hours": int(len(h)),
        "share_hours_import_capacity_binds_flowbased": float(binding.mean()),
        "share_hours_binds_ntc_p10": float((f1 > ntc + 1.0).mean()),
        "mean_excess_when_binding_mw": float((f1 - k_fb)[binding].mean()) if binding.any() else 0.0,
        "median_one_zone_flow_mw": float(np.median(f1)), "median_fb_limit_mw": float(np.median(k_fb)),
        "south_dispatchable_mw": a_s,
        "pivotal_one_zone": pivotal_share(h, np.maximum(f1, 0.0), a_s),
        "pivotal_split_flowbased": pivotal_share(h, np.minimum(np.maximum(f1, 0.0), k_fb), a_s),
        "pivotal_split_ntc": pivotal_share(h, np.minimum(np.maximum(f1, 0.0), ntc), a_s),
    }
    out["pivotal_by_number_of_firms"] = {
        str(n): {"one_zone": pivotal_share(h, np.maximum(f1, 0.0), a_s, n)["share_pivotal"],
                 "split_flowbased": pivotal_share(h, np.minimum(np.maximum(f1, 0.0), k_fb), a_s, n)["share_pivotal"],
                 "split_ntc": pivotal_share(h, np.minimum(np.maximum(f1, 0.0), ntc), a_s, n)["share_pivotal"]}
        for n in (1, 2, 3, 4)}
    price = h[["price_north_fb", "price_south_fb"]]
    out["share_hours_price_gap_over_1"] = float(((price.price_south_fb - price.price_north_fb) > 1).mean())
    out["mean_price_gap_when_gap"] = float((price.price_south_fb - price.price_north_fb)[(price.price_south_fb - price.price_north_fb) > 1].mean())
    return out


if __name__ == "__main__":
    import json
    r = run()
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "empirical_check.json").write_text(json.dumps(r, indent=2))
    print(json.dumps(r, indent=2))
