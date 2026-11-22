# Does splitting a bidding zone raise market power in the importing zone?

Research study with three parts: an analytic two-node model with a proposition and proof (when does a split raise the markup of a strategic generator, and by how much), numerical checks of the closed forms, and an empirical check on the hourly results of [de-bidding-zones](https://github.com/serikov-energy-systems/de-bidding-zones) (1,464 sampled hours of 2024 on the 780-bus German grid): in how many hours the mechanism of the proposition can operate. A fourth item, the exact solution of the two-stage recourse problem of an electric bus scheduling instance by L-shaped decomposition, is in [hamburg-ebus-scheduling](https://github.com/serikov-energy-systems/hamburg-ebus-scheduling) (`src/ebus/lshaped.py`).

**What is not done.** A numerical equilibrium problem with equilibrium constraints (MPEC or diagonalised EPEC) on the 780-bus grid with strategic owners is not built. The plant data carry no owner, so strategic firms there would be assumptions; the empirical part uses stylised equal firms and says so. The proposition has ample generator capacities and a price-taking fringe; it is a model of a mechanism, not an estimate of market power in Germany.

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
