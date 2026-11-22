# Proposition: when does splitting a bidding zone raise the markup of a strategic generator?

## Setting
- Importing zone S has linear demand Q(p) = alpha - beta p (alpha, beta > 0).
- Exporting zone N has a price-taking fringe with constant marginal cost c_f and ample capacity.
- S has n strategic generators with constant marginal cost c >= c_f and ample capacity; they compete in quantities (Cournot).
- The line N-S has capacity K >= 0. Write K_bar = alpha - beta c_f (the flow in the one-zone market), K_c = alpha - beta c (critical capacity), A = alpha - K and a0 = A - beta c = K_c - K. Note K_c < K_bar because c >= c_f.
- One zone: the market clears across the line; congestion is removed after the market by cost-based redispatch, which does not change the market price. Split: the market in S can import at most K.

## Statement
1. **One zone.** The price is c_f; the strategic generators produce nothing; the markup is 0.
2. **Split, K >= K_bar.** The line does not bind; the price is c_f as in the one zone.
3. **Split, K_c <= K < K_bar.** The price is the scarcity price A/beta in (c_f, c]; the strategic generators produce nothing; the markup is 0 and the line earns a congestion rent K (A/beta - c_f).
4. **Split, K < K_c.** The Cournot equilibrium is unique and symmetric:
   q_i = a0 / (n+1) per firm, price p = c + a0 / ((n+1) beta), markup mu = a0 / ((n+1) beta) = (K_c - K) / ((n+1) beta), profit per firm a0^2 / ((n+1)^2 beta).
5. **Hence** the split raises the markup of the strategic generators above its one-zone value (0) if and only if K < K_c. The markup rises linearly as K falls, d mu / d K = -1 / ((n+1) beta), and falls with the number of generators; as n grows it vanishes.
6. **Stackelberg.** With one leader and n-1 Cournot followers (n >= 2) in the split and K < K_c the leader produces a0/2, the followers together (n-1) a0 / (2n), the price is c + a0 / (2 n beta) and the markup a0 / (2 n beta), which is lower than the Cournot markup a0 / ((n+1) beta) for every n >= 2, and the leader earns more than a Cournot player.

## Proof
1. In the one zone the fringe supplies any quantity at c_f. No strategic generator can sell above c_f, and since c >= c_f it cannot sell at a profit; the price is c_f and its output is zero. (If c = c_f the generator is indifferent; the markup is still zero.)
2. If K >= K_bar the demand at price c_f, alpha - beta c_f = K_bar, can be imported in full, so the price is c_f.
3. If K < K_bar the imports at price c_f cannot cover the demand at c_f, so the price rises above c_f until demand falls to the import limit: p = (alpha - K)/beta = A/beta. A strategic generator would only sell if p > c. If A/beta <= c, equivalently K >= K_c, no strategic output is profitable at that price; the generators produce nothing (their output would have to be sold below cost), the price is A/beta and the line is congested.
4. If K < K_c then A/beta > c and the strategic generators face the residual inverse demand P(Q) = (A - Q)/beta for Q in [0, A], where Q is their total output; at any price p >= c >= c_f the imports are at the limit K, so the residual demand is as stated. Firm i maximises (P(Q) - c) q_i. The first-order condition is P(Q) - c + q_i P'(Q) = 0, that is A - Q - beta c - q_i = 0, i.e. Q + q_i = a0. The profit is strictly concave in q_i, so the first-order condition characterises the best response. Summing over i gives (n+1) Q = n a0, hence Q = n a0/(n+1), q_i = a0/(n+1), P = (A - Q)/beta = c + a0/((n+1) beta). The equilibrium is unique: the n first-order conditions say Q + q_i = a0 for every i, so all q_i are equal, and then (n+1) q = a0.
5. Combining 1 to 4, the markup after the split is zero for K >= K_c and a0/((n+1) beta) > 0 for K < K_c; the derivative and the dependence on n follow from the formula.
6. Taking the leader's output q_L as given, a follower's first-order condition is a0 - q_L - Q_F - q_f = 0 with Q_F = (n-1) q_f for symmetric followers, so q_f = (a0 - q_L)/n and Q_F = (n-1)(a0 - q_L)/n. The leader maximises (P - c) q_L with P - c = (a0 - q_L - Q_F)/beta = (a0 - q_L)/(n beta); the first-order condition gives q_L = a0/2. Then Q_F = (n-1) a0/(2n), Q = a0 (2n-1)/(2n) and P - c = a0/(2 n beta). For n >= 2, 2n > n+1, so the Stackelberg markup is lower than the Cournot markup. The leader's profit a0^2/(4 n beta) exceeds the Cournot profit a0^2/((n+1)^2 beta) because (n+1)^2 > 4n for n >= 2. QED.

## What the proposition does not cover
Capacity limits of the generators (then pivotal behaviour and capacity withholding enter; see the pivotal supplier check in `src/zsmp/empirical.py`), increasing marginal costs, demand in the exporting zone, repeated interaction, and the effect of redispatch on the strategic behaviour in the one-zone market (the one-zone result assumes that cost-based redispatch does not feed back into bidding, which is the benchmark of this study, not a fact).
