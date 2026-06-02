# Two-scale template plan (#156, Phase 9 continuation)

## Why this architecture

Empirical: the broad-seed core-4 + local-opt family at $k = 18, 20, 24, 32$ fits
$L \approx 1.20 \cdot k^3 / (\log k)^{2.09}$ with $R^2 = 0.9989$ and
$L \cdot \log^2(k)/k^3$ in $[1.07, 1.09]$.  The anchor-cover decomposition shows
anchor-anchor difference events ($\approx 2660$) are nearly as numerous as
mixed core-anchor events ($\approx 2790$); they are doing cleanup, not design.
A two-scale construction promotes anchor-anchor differences from accidental
cleanup to the primary cover mechanism by making the anchor set itself Sidon
with controlled difference structure.

## Status as of May 17, 2026

The diagnostic extension of the broad-seed/local-opt family reached k=32:

```text
B32 =
[0,15,35,38,39,44,95,105,163,180,196,283,296,310,404,478,
 519,694,792,864,1019,1030,1051,1153,1183,1352,1438,1483,
 1909,1928,1956,2068]
```

For this template, `W(B)` contains `[-766,2145]`, so it covers
`N=2069..2912`.  The endpoint ratio is `2912/32^3 = 0.0888671875`, and
`2912*log(32)^2/32^3` is about `1.067`.  This supports the empirical
`k^3/log^2(k)` envelope for the broad-seed/local-opt architecture.  The
endpoint witness at `N=2912` was checked with `solve_156.py verify`.

The literal two-scale Minkowski product `B = a*S + C` failed as a construction
candidate: using the same nontrivial core in multiple macro tiles repeats
core-core differences, so the product is usually not Sidon.  The sweep in
`results/template_two_scale_156_sweep.json` found no valid Sidon/admissible
templates under this direct composition.

Singer sets remain useful as **seeds** for the existing beam search, but the
completed q=3 and q=7 seed runs through k=14 sit below or roughly comparable
to the broad-seed envelope.  A q=7 seed extension to k=20 with width 64 was
started as a diagnostic and stopped because it was much slower than expected;
do not treat that branch as completed evidence.

Next viable redesign: use different cores per macro tile, or modularly
perturb the core offsets, so that small within-tile differences are not
repeated.  A simple product with a fixed core cannot be the desired two-scale
construction.

## Construction

Pick:

- A small dense **core** $C \subset [0, w)$ of size $c$ chosen so $\Delta(C)$
  is an interval (or contains an interval) of small differences
  $[1, \delta]$ for some $\delta \ge c-1$.  Example reusable cores:
  - $C_1 = \{0, 1, 3, 7\}$ (Sidon, $\Delta = \{1,2,3,4,6,7\}$).
  - $C_2 = \{0, 1, 3, 7, 12, 20\}$ (Sidon, $\Delta$ covers $\{1..20\}\setminus\{15,18\}$, span 20).
  - $C_3 = \{0, 2, 7, 8, 11\}$ Sidon, $\Delta = \{1,2,3,4,5,6,7,8,9,11\}$.

- A macro-scale **anchor set** $S \subset [0, M)$ of size $s$ chosen to be
  Sidon, with pairwise differences $\Delta(S)$ as dense as possible inside
  $[0, M)$.  Choices:
  - **Singer**: $|S| = q+1$, $M = q^2 + q + 1$, $\Delta(S)$ hits every
    residue class mod $M$ exactly once (a *perfect* difference set).  Best
    possible density.
  - **Erdős-Turán $B_2$**: $S = \{2pi + (i^2 \bmod p) : 0 \le i < p\}$, size
    $p$, span $\sim 2p^2$.  No perfect cover but Sidon for free.
  - **Singer + dilation**: dilate $S$ by a constant $a > w$ to give breathing
    room for the core.  Then $S' = aS$ is Sidon with span $a \cdot (q^2+q)$.

- **Combined template**: $B = \{s' + c : s' \in S', c \in C\}$ with
  $|B| = sc$ (assuming the offsets don't collide, i.e. $a > w$ and $a$
  large enough).

## Why this should help

$W(B)$ now contains:

1. **Core-core in each tile** (small): around each $s' \in S'$, the core $C$
   creates blockers $s' + (C \pm \Delta(C)) \cup (C + \text{mid}(C))$.  Each
   tile contributes a small dense cluster of width $\le w + 2\delta$.

2. **Anchor-anchor differences** (large, *designed*): for $s'_1, s'_2 \in S'$,
   the differences $s'_2 - s'_1$ live in $a \cdot \Delta(S)$.  If $S$ is
   Singer (perfect difference set), $\Delta(S)$ hits every residue mod $M$
   once, so $a \cdot \Delta(S) \subset [a, aM]$ is a *predictably distributed*
   spread of differences.

3. **Cross-tile (core-anchor)**: differences of form $a \cdot \Delta(S) + (c_2 - c_1)$
   for $c_1, c_2 \in C$.  Each $a$-tile difference shifts by the
   $|\Delta(C)|$-many small differences, *filling the gaps* between
   pure $a \cdot \Delta(S)$ residues.

The total difference count is $\binom{sc}{2} = sc(sc-1)/2$ and the support
$[0, aM]$ has length $aM = a(q^2+q+1) - 1$.  For $W(B)$ to contain a
$\Theta(k^3) = \Theta(s^3 c^3)$ interval, we want the differences to
**tile** $[1, aM]$ with overlap.  The natural calibration is:

- $a \approx w + 2\delta + 1$ (no gap between adjacent core tiles after
  difference cover);
- $aM \approx a \cdot (q^2+q+1) = (q+1)^2 \cdot a / (1 + 1/(q+1)) \approx s^2 a$.

So if $a$ scales like $c^2$ (Sidon density: $|\Delta(C)| = c(c-1)/2$
differences in $[1, w]$ with $w \sim c^2$), and $|B| = sc$, then
$aM \sim s^2 c^2$, while $|B|^3 = s^3 c^3$.  This is off by a factor
$sc$, meaning the construction *doesn't immediately reach* the $k^3$
target — we get $L \sim |B|^3 / |B| \sim |B|^2$.  Wait, let me recompute.

Actually: $aM \sim s^2 c^2$ but we have $sc(sc-1)/2 \sim (sc)^2 / 2$ differences
to place in support of length $\sim s^2 c^2$.  Density $\sim 1/2$.  Each
difference being one of $|\Delta(B)|$, we cover most points.  Length of
longest interval in $W(B)$ should be near $aM$ if Singer.  So
$L \sim s^2 c^2 = (sc)^2 / 1 = k^2$ for $k = sc$.

This is *worse* than the current $k^3 / \log^2(k)$.  We need the anchor
set sparser.

**Reformulation.** Pick $a$ to scale like $c^3$ instead, with $c$ small but
fixed (e.g. $c=4, 6$), so each tile has interior interval $\Theta(c^2) =
O(1)$ and tiles are spaced $\Theta(c^3) = O(1)$ apart with the core differences
$\Delta(C) \cup -\Delta(C)$ filling gaps near each tile center.  Then for
fixed $c$, varying $s$, $|B| = sc = \Theta(s)$ and $L = aM = \Theta(s^2)$,
giving $L \sim k^2 / c$.  Still $k^2$, not $k^3$.

So **pure Singer×core tiles produce $L \sim k^2$**, asymptotically worse than
$k^3 / \log^c k$.  We need to use $c$ growing too.

**Final calibration attempt.** Let $c$ grow with $s$.  Pick $c \sim s^{1/2}$
so $k = sc \sim s^{3/2}$.  Then anchor span $a M \sim a s^2$.  Pick $a \sim
c^2 = s$, so $aM \sim s^3$.  Compare to $k^3 = s^{9/2}$: we have
$L / k^3 \sim s^3 / s^{9/2} = s^{-3/2} \to 0$.  Even worse.

**Different angle: anchor set is itself short.**  In the current empirical
family, max(B) at $k=24$ is 1051, and $L = 1490$, so the blocker interval
extends roughly $\max(B) \cdot 1.42$ to the right of $\max(B)$.  The
construction's strength is that $W(B)$ extends BEYOND $[0, \max(B)]$ on both
sides.  A two-scale construction needs the same property: the leftward
extension (negative blocker support) needs to be growing.

Concrete recipe to try first:

1. $C = \{0, 1, 3, 7\}$, $c = 4$, $\delta = 7$, span $w = 7$.
2. $S$ = Singer in $\mathbb{Z}_{13}$ ($q = 3$): $S_0 = \{0, 1, 3, 9\}$, size 4.
3. $a = 10$ (so core fits inside each $a$-tile with one unit slack).
4. $B = S_0 \cdot a + C = \{0+C, 10+C, 30+C, 90+C\}$, size 16.

That's a starting test.  Generalize $S$ to $q = 5, 7, 11, ...$ Singer in
$\mathbb{Z}_{q^2+q+1}$, with $c = 4$ or $c = 6$ core.

## Plan

1. Write `two_scale_template.py`:
   - Singer difference set generator for prime $q$.
   - $B_2$ Erdős-Turán fallback for arbitrary $p$.
   - Compose $B = a \cdot S + C$.
   - Check Sidon, compute $W(B)$, longest admissible interval, ratio.
2. Sweep $(c \in \{4, 5, 6\}, q \in \{3, 5, 7, 11, 13\}, a$ in a small range).
3. For each $k = sc$, record $L/k^3$ and $L \cdot \log^p(k) / k^3$ for
   $p = 0, 1, 2$.  Compare to broad-seed envelope.
4. If a single point shows $L \cdot \log^2(k)/k^3 > 1.2$ or $L/k^3 > 0.13$
   at $k \ge 24$, this is a hit.  Iterate.
5. If all points sit on or below the broad-seed envelope, the architecture
   does not help and we should plan C (formal obstruction).
