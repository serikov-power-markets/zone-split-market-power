# Does splitting a bidding zone raise market power in the importing zone?

Research study with three parts: an analytic two-node model with a proposition and proof (when does a split raise the markup of a strategic generator, and by how much), numerical checks of the closed forms, and an empirical check on the hourly results of [de-bidding-zones](https://github.com/serikov-energy-systems/de-bidding-zones) (1,464 sampled hours of 2024 on the 780-bus German grid): in how many hours the mechanism of the proposition can operate. A fourth item, the exact solution of the two-stage recourse problem of an electric bus scheduling instance by L-shaped decomposition, is in [hamburg-ebus-scheduling](https://github.com/serikov-energy-systems/hamburg-ebus-scheduling) (`src/ebus/lshaped.py`).

**What is not done.** A numerical equilibrium problem with equilibrium constraints (MPEC) or an EPEC on the nodal 780-bus grid is not built; v0.2 (below) solves a zonal Cournot game with real owners and exogenous flow limits instead. The proposition has ample generator capacities and a price-taking fringe; it is a model of a mechanism, not an estimate of market power in Germany.

## Question
Does splitting a bidding zone raise market power in the importing zone, and how large can the effect be?

## Proposition (`docs/proposition.md`, with proof)
Importing zone S: demand alpha - beta p. Exporting zone N: price-taking fringe at marginal cost c_f. S: n strategic generators with marginal cost c >= c_f in a Cournot game. Line capacity K. Let a0 = (alpha - beta c) - K.

- One zone: the price is c_f, the strategic generators produce nothing, the markup is zero.
- Split with K >= alpha - beta c_f: the line does not bind, nothing changes.
- Split with alpha - beta c <= K < alpha - beta c_f: the price rises to the scarcity price (alpha - K)/beta in (c_f, c], the line earns a congestion rent, the strategic markup is still zero.
- Split with K < alpha - beta c: unique Cournot equilibrium, markup a0 / ((n+1) beta), price c + a0 / ((n+1) beta), profit per firm a0^2 / ((n+1)^2 beta).
- **The split raises the strategic markup if and only if K < alpha - beta c**, linearly in the shortfall, falling with the number of firms. With one leader and n-1 followers the markup is a0 / (2 n beta), lower than the Cournot markup, and the leader earns more.

The closed forms are checked against numerical best responses in `tests/test_analytic.py` (n = 1, 2, 3, 5; the markup at K = 30 for alpha = 100, beta = 1, c = 40 is 15).

## Empirical check on the hourly results of the German study (`results/empirical_check.json`)
- **The line binds in many hours.** The one-zone market sends a median 10.5 GW from the north to the south, the flow-based limit has a median of 11.0 GW; in 49% of the 1,464 hours the one-zone flow is above the flow-based limit (by 3.2 GW on average), and in 72% of hours above a static limit at the 10th percentile of the flow-based capacity. So the first condition of the proposition, an import-constrained south, is met in about half of the hours.
- **Whether a firm is pivotal depends on concentration.** The pivotal supplier index of the largest of n equal firms in the south (40.3 GW of available dispatchable capacity at 85% availability, southern load 55% of the national load, southern shares of wind 21% and solar 50%, all assumptions) is positive in the following shares of hours:

| Firms in the south | one zone | split, flow-based | split, static limit |
|---|---:|---:|---:|
| 1 | 98.0% | 98.2% | 98.6% |
| 2 | 5.9% | 11.8% | 14.6% |
| 3 | 0.07% | 0.27% | 1.2% |
| 4 | 0% | 0% | 0% |

With two equal firms the split doubles the number of pivotal hours, with four none are pivotal in the sample. The mechanism of the proposition can operate in a split south with two or three large firms; with a fragmented south it does not.

## v0.2: Cournot equilibrium with plant owners on the German zonal market (`src/zsmp/grid_cournot.py`, `scripts/run_grid_cournot.py`, `results/grid_cournot_*.json`)
**Question.** With the real ownership of the thermal fleet, does a north/south split raise the markup, and where?

**Method.** The system, the demand, the renewables and the flow-based bounds on the net position of the north are those of the 200 sampled hours (every seventh of the 1,464) of `de-bidding-zones` (2024 fleet, 780-bus grid reduced to two zones, split at 51 degrees). Owners come from the Bundesnetzagentur power plant list (data of 5 Nov 2026, units of at least 10 MW in operation, `data/raw/`): operators are grouped into parent firms (RWE, EnBW, Uniper, LEAG, STEAG, Statkraft, Hamburger Energiewerke; Vattenfall and EWE have no lignite, coal or gas capacity in the list under this grouping) and assigned to the north or south zone by federal state (Saxony and North Rhine-Westphalia counted as north, because their large plants lie north of 51 degrees). The list has no coordinates, so the ownership share of a firm in a zone and fuel is applied to the model's plant groups of that zone and fuel. All other units (including all renewables, which run at zero cost) form a price-taking fringe at marginal cost. Each firm chooses its output in the north and in the south on a grid of 11 fractions of its available capacity; prices follow from market clearing with the flow bounded by the flow-based limits; best responses are iterated 14 times (damped after three rounds). Demand is made elastic around the competitive one-zone price with a **constant elasticity assumed at 0.05, 0.1 and 0.25**, because with perfectly inelastic demand Cournot gives the price cap whenever a firm is pivotal; the price cap is 600 EUR/MWh (assumed). At elasticity 0.1 the competitive benchmark (all units price takers) reproduces the price of the linear programme of `de-bidding-zones` with a mean absolute difference of 0.56 EUR/MWh in one zone and 1.1 (north) and 1.4 (south) in the split, correlation 0.98-0.999. The solver is checked against the closed-form monopoly output and price in a toy market (`tests/test_grid_cournot.py`).

**Results (200 hours, EUR/MWh).**
| Elasticity | Markup one zone (load-weighted) | Markup split (load-weighted) | Split, north | Split, south | Hours with markup above 5, one zone | Hours with markup above 5, split |
|---|---:|---:|---:|---:|---:|---:|
| 0.05 | 2.78 | 2.82 | 3.54 | 1.90 | 11.4% | 31.9% |
| 0.10 | 2.20 | 2.48 | 3.18 | 1.65 | 6.2% | 29.0% |
| 0.25 | 1.88 | 2.08 | 2.71 | 1.34 | 4.3% | 23.8% |

- **The split raises the markup mostly in the hours when the line binds, and it raises it in the north.** The line binds in 59% of the sampled hours in the competitive split. At elasticity 0.1 the markup in the north is 4.4 EUR/MWh in these hours against 1.4 in the other hours. The load-weighted mean changes little (+0.04 to +0.28 EUR/MWh, below 0.3% of the price), but the share of hours with a markup above 5 EUR/MWh rises from 4-11% to 24-32%.
- **Why the north.** The lignite owners (LEAG 52% and RWE 42% of the northern lignite capacity in the list) sit in the north, and the south is nearly atomistic: 82% of its gas capacity belongs to firms outside the grouped parents. When the line binds, the northern firms lose the export outlet and face a smaller residual demand; the importing south has few strategic units. This fits the proposition above (markup rises when the line binds) but not its setting (strategic generators in the importing zone): with the real ownership the mechanism acts on the exporting side.
- **Convergence.** The mean change of the outputs between rounds falls to 3e-7 of the largest capacity in one zone and to 2e-4 to 5e-4 in the split (damped best response on an 11-point grid; the split does not settle exactly).

**Limits.** Zonal game with exogenous flow limits (taken from the competitive dispatch of the study), no redispatch, no nodal equilibrium, no EPEC; ownership by federal state; list of units of 10 MW and above; demand elasticity and price cap assumed; a one-shot game for each hour without dynamics or contracts; 200 of 1,464 hours. Not an estimate of market power in Germany and not a forecast of a real split.

## Limits
- The proposition rests on a price-taking fringe, constant marginal costs and ample capacity; it does not cover capacity withholding, increasing costs or a feedback of redispatch on bidding in the one zone.
- Pivotality is an indicator for the possibility of market power, not an estimate of markups; the firm count, the regional shares and the availability are assumptions.
- The hourly results come from the island model of the German study (no imports or exports), 1,464 sampled hours of 2024.
- No MPEC on the grid (see above).

## Run
```
pip install -e .
python -m zsmp.empirical
pytest
```
