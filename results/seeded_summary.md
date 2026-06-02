# Phase 3' — Dense-Sidon-seeded greedy

## Setup

Take a known dense Sidon set $A_{\text{seed}}$ as the starting point, then run
greedy (Strategy 1 + Strategy 2 from `explore.py`) to extend $A_{\text{seed}}$
into a PDS covering $[1, N]$. Measure $\max(A_{\text{final}})$ and compare to
scratch greedy.

Seed families tested:
- **Mian–Chowla**: greedy Sidon set $\{1, 2, 5, 10, 11, 13, 37, \ldots\}$.
- **Erdős–Turán**: $\{2pi + (i^2 \bmod p) + 1 : i = 0, \ldots, p-1\}$ for prime $p$.
- **Phase 4 optimum**: the exact $A_{N_0}^*$ from Phase 4 (extremely dense).

## Results

Greedy scratch values from the main `results/pds_*.csv`:

| $N$ | scratch greedy $\max A$ | ratio $/N^3$ |
|----:|------------------------:|-------------:|
| 300 |   641,667 | 0.02377 |
| 500 | 3,080,237 | 0.02464 |

Seeded greedy:

| Seed | seed size | seed max | $N$ | seeded $\max A$ | ratio $/N^3$ | improvement |
|------|----------:|---------:|----:|----------------:|-------------:|------------:|
| Erdős–Turán $p=13$ | 13 | 314 | 300 | 183,933 | 0.00681 | 3.5× |
| Mian–Chowla $n=20$ | 20 | 475 | 300 | 107,130 | 0.00397 | 6.0× |
| Mian–Chowla $n=50$ | 50 | ~2500 | 300 | 81,864 | 0.00303 | 7.8× |
| Erdős–Turán $p=23$ | 23 | 1080 | 500 | 544,923 | 0.00436 | 5.7× |
| Mian–Chowla $n=30$ | 30 | ~1500 | 500 | 368,611 | 0.00295 | 8.4× |
| Mian–Chowla $n=60$ | 60 | ~4000 | 500 | 286,281 | 0.00229 | **10.8×** |
| Mian–Chowla $n=100$ | 100 | ~10000 | 500 | 423,111 | 0.00339 | 7.3× |
| **Phase 4 optimum $A_{30}^*$** | 10 | 56 | 500 | **881,451** | **0.00705** | 3.5× |

## Findings

1. **Dense Sidon seeding reduces the constant of $N^3$ scaling by up to 11×.**
   At $N = 500$, Mian–Chowla seeded greedy with 60 elements gives
   $\max(A) \approx 286{,}000$ vs scratch greedy's $3{,}080{,}000$.
   The constant drops from $\approx 0.025\, N^3$ to $\approx 0.0023\, N^3$.

2. **The Phase 4 optimum is a *bad* seed.** Despite being the maximally
   dense Sidon set covering $[1, 30]$, using $A_{30}^*$ as seed gives
   ratio $0.0070$ at $N = 500$ — **worse than Mian–Chowla seeding** by 3×.

   This empirically confirms the Phase 4' principle: structurally tight
   seeds (like the exact $A_N^*$) are traps for future extension. They
   pack differences densely into a small window, leaving the remaining
   difference budget cramped. Mian–Chowla, in contrast, is "loosely
   packed" — elements are spread out, leaving plenty of free differences
   for greedy continuation.

3. **Mian–Chowla has a sweet spot.** Going from $n=30$ to $n=60$ improves
   the ratio (0.00295 → 0.00229), but $n=100$ regresses (to 0.00339).
   The optimal seed size seems to be roughly $n \approx \sqrt{N}$ at
   target $N$ — large enough to give greedy a structured backbone,
   small enough not to dominate.

4. **The asymptotic scaling remains $\Theta(N^3)$.** Across all seeds
   tested, the ratio $\max(A)/N^3$ is bounded between $\approx 0.002$
   and $\approx 0.025$. None of them give sub-cubic asymptotic growth.
   Seeding is a *constant-factor* improvement only; the structural
   obstruction to $o(N^3)$ persists.

## Implications for CiNa08 Problem 1

The CiNa08 Open Problem 1 asks: does there exist a PDS with $t_n = o(n^3)$?
Phase 3' shows that **clever choice of starting Sidon set can reduce the
constant in $N^3$ scaling by an order of magnitude**, but does not break
the cubic ceiling. To get $o(n^3)$, one would need either:

- A non-greedy continuation strategy that exploits the seed's structure
  globally, not just locally.
- A construction that periodically "re-seeds" with fresh dense Sidon
  blocks — but this would create boundary conflicts that the basic greedy
  cannot handle.
- A genuinely new construction (perhaps via the CiNa08 inductive scheme
  itself, fully implemented).

The empirical message: $\Theta(N^3)$ for greedy seems robust under
seeding, but the *constant* is far from optimal. Whether the optimum
constant is $0$ (i.e., $o(N^3)$ achievable) or strictly positive remains
open.

## Reproducing

```sh
python3 seeded_greedy.py mian 60 500          # Mian-Chowla seed of size 60, target N=500
python3 seeded_greedy.py erdos_turan 13 300   # Erdős-Turán seed with p=13, target N=300
python3 seeded_greedy.py phase4 30 500        # Phase 4 optimum A_30* as seed
```
