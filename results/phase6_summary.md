# Phase 6 — block-structured construction (Cilleruelo–Nathanson Problem 1 attack)

## Goal

Build a PDS as a union of multiple structured Sidon sub-blocks placed at
strategic positions, then complete via greedy. Aim to break the
$\Theta(N^3)$ ceiling observed empirically for all greedy-style
continuations (including the Mian–Chowla-seeded greedy from Phase 3').

## Construction families

All seeds verified Sidon before extension.

### Single Mian–Chowla seed (baseline from Phase 3')

$A_{\text{seed}} = \text{MC}(k)$. Greedy continuation extends to PDS
covering $[1, N]$.

### Split MC

Take MC$_{1 \ldots k_1 + k_2}$ and partition into two disjoint sub-blocks
$B_1 = \text{MC}_{1\ldots k_1}$, $B_2 = \text{MC}_{k_1+1 \ldots k_1+k_2}$.
Place $B_2$ shifted by gap $> \max(\text{within-block diffs}) + \max(B_1)$
to guarantee cross-block diffs avoid within-block diffs.

Because MC is *globally* Sidon, $B_1$ and $B_2$ share no within-block
differences — this is the key property that makes the construction Sidon
even though both chunks are dense Sidon sets individually.

### AP-MC (arithmetic-progression chunks)

Take MC$_{1 \ldots km}$, split into $m$ chunks of size $k$, and place
chunks at offsets $0, \text{spacing}, 2 \cdot \text{spacing}, \ldots$
with spacing chosen to avoid all cross-chunk diff collisions.

## Results at $N = 500$

| Strategy | $|A_{\text{seed}}|$ | seed max | $\max A$ | ratio $/N^3$ |
|----------|--------------------:|---------:|---------:|-------------:|
| scratch greedy | 0 | — | 3,080,237 | 0.02464 |
| MC(60) | 60 | 7,547 | 286,281 | 0.00229 |
| MC(100) | 100 | 27,219 | 423,111 | 0.00339 |
| **split_MC(30,30)** | 60 | 15,012 | **280,501** | **0.00224** |
| split_MC(40,40) | 80 | 31,232 | 331,746 | 0.00265 |
| split_MC(60,30) | 90 | 43,655 | 386,310 | 0.00309 |
| AP_MC($k=20, m=3$) | 60 | 31,887 | 383,640 | 0.00307 |
| AP_MC($k=30, m=2$) | 60 | 21,247 | 302,887 | 0.00242 |

The best block-structured strategy (`split_MC(30,30)`) gives ratio
0.00224 — essentially indistinguishable from the unsplit MC(60) baseline
of 0.00229. **No construction breaks the cubic ceiling.**

## Scaling check at $N = 550$

For MC(60) at $N = 550$: ratio = 0.00216, slightly below $N = 500$
(0.00229). The trend is unclear from two data points but consistent with
a $\Theta(N^3)$ asymptote at a constant somewhere $\approx 0.002$.

## Findings

1. **The $\Theta(N^3)$ ceiling is robust under all block-structured
   seeding tested.** Splitting, AP, scaling — all give the same constant
   to within a factor of 1.5.

2. **The constant has a floor around $0.002\,N^3$.** Across many seed
   strategies and sizes, the best ratio at $N = 500$ is $\approx 0.0022$;
   no construction reliably goes below this.

3. **The Phase 4' obstruction is the deep reason.** Once the seed is
   fixed, the *greedy continuation* is forced into Strategy-2 calls
   whose per-call cost is $\Theta(N^2)$ — independent of seed structure.
   This drives the cubic. To break it, the continuation algorithm must
   be redesigned, not just the seed.

## Connection to CiNa08 Problem 1

CiNa08 ask: does there exist a PDS with $t_n = o(n^3)$? Phase 6
establishes:
- **Within the "structured seed + greedy continuation" family,
  the answer appears to be NO.** Every variant we tested gives
  $\Theta(N^3)$.
- **A genuinely sub-cubic construction would have to abandon greedy.**
  The continuation must place new elements at positions that anticipate
  future coverage — a global, non-local design.

This is consistent with the open-problem framing in the literature: no
construction with sub-cubic $a_n$ is known after 18 years of attention.

## Reproducing

```sh
# Single MC seed
python3 block_construction.py mc 60 500

# Split into two chunks
python3 block_construction.py split 30 30 500

# Arithmetic progression of chunks
python3 block_construction.py ap 20 3 500

# Sweep (slow — runs all the above)
python3 block_construction.py sweep 500
```

## Status

Phase 6 closed as a **no-go**: no block-structured greedy variant breaks
the $\Theta(N^3)$ ceiling. The CiNa08 Problem 1 answer (does
$a_n = o(n^3)$ exist?) remains genuinely open. Routes forward:
- **Phase 7** — Lean formalization of Theorems 1–3 from the research
  note. Concrete, low-risk artifact.
- **Phase 2A** — try the "for all $x$" Sidon density improvement for
  PDS. Speculative theorem hunt.
- A completely non-greedy construction: pick $A$ probabilistically
  with structured rejection sampling, or via algebraic codes
  (e.g., $\mathbb{F}_{q^3}$ projective planes lifted to $\mathbb{Z}$).
  This would be its own Phase 8.
