# Shifted-template parametrization for Erdos #156

## The blocker set

Let \(B=\{b_1,\ldots,b_k\}\) be a finite Sidon set of integers.  Write

\[
\Delta(B)=\{|b_i-b_j|: i<j\}.
\]

For maximality, a new point \(x\) is blocked in exactly three ways:

1. \(x\in B\).
2. \(x\) creates a difference already in \(\Delta(B)\), meaning
   \(x\in b\pm\Delta(B)\) for some \(b\in B\).
3. \(x\) is the integer midpoint of two points of \(B\), so the two new
   differences from \(x\) collide.

Define the relative blocker set

\[
W(B)=B\cup(B+\Delta(B))\cup(B-\Delta(B))
     \cup\{(b_i+b_j)/2: i<j,\ b_i+b_j\equiv 0\pmod 2\}.
\]

If \(A=s+B\), then \(\Delta(A)=\Delta(B)\), midpoint blockers also shift by
\(s\), and the blocked set for \(A\) is exactly

\[
s+W(B).
\]

Thus \(s+B\) is a maximal Sidon subset of \([1,N]\) if and only if

\[
s+B\subset[1,N]
\quad\text{and}\quad
[1-s,N-s]\subset W(B).
\]

This is the clean parametrization: once \(B\) is fixed, all shifted maximality
questions are one-dimensional interval containment questions in \(W(B)\).

## Consecutive-interval lemma

Normalize \(B\) so that \(\min B=0\), and let \(M=\max B\).  Suppose \(W(B)\)
contains a consecutive interval \([L,R]\).  Then any integer shift \(s\)
satisfying

\[
\max(1,N-R)\le s\le \min(1-L,N-M)
\]

gives a maximal Sidon set

\[
A=s+B\subset[1,N].
\]

Indeed, \(s\ge 1\) and \(s\le N-M\) place \(A\) inside \([1,N]\), while
\(s\ge N-R\) and \(s\le 1-L\) imply

\[
[1-s,N-s]\subset[L,R]\subset W(B).
\]

Equivalently, for a fixed template interval \([L,R]\), the construction covers
all \(N\) for which the shift interval above is nonempty.  When \(L\le0\) and
\(M\le R\), this includes the full \(N\)-range

\[
M+1\le N\le R+1-L.
\]

A fixed template can only cover a bounded interval of \(N\).  To attack the
asymptotic Erdos problem, this lemma would need a family of templates \(B_t\)
with \(|B_t|=O(N_t^{1/3})\) and long consecutive intervals in \(W(B_t)\).

## The size-8 template

The strongest template found so far is

```text
B = [0, 40, 60, 61, 63, 67, 96, 112]
gaps(B) = [40, 20, 1, 2, 4, 29, 16]
```

It is a Sidon set with

```text
Delta(B) = [1, 2, 3, 4, 6, 7, 16, 20, 21, 23, 27, 29, 33, 35,
            36, 40, 45, 49, 51, 52, 56, 60, 61, 63, 67, 72, 96, 112]
```

For this \(B\), direct computation gives

```text
W(B) contains every integer from -7 through 136.
```

Here \(M=112\), \(L=-7\), and \(R=136\), so the shift condition becomes

\[
\max(1,N-136)\le s\le \min(8,N-112).
\]

Therefore the template gives a maximal Sidon set \(A=s+B\) for every

\[
113\le N\le144.
\]

The earlier structural pass only recorded \(120\le N\le144\), but the same
interval calculation also covers \(113\le N\le119\).  The feasible shifts are:

| \(N\) range | feasible shifts from the interval |
|---:|---|
| 113 | \(s=1\) |
| 114 | \(s=1,2\) |
| 115 | \(s=1,2,3\) |
| 116 | \(s=1,2,3,4\) |
| 117 | \(s=1,2,3,4,5\) |
| 118 | \(s=1,2,3,4,5,6\) |
| 119 | \(s=1,2,3,4,5,6,7\) |
| 120-137 | \(s=1,\ldots,8\) |
| 138 | \(s=2,\ldots,8\) |
| 139 | \(s=3,\ldots,8\) |
| 140 | \(s=4,\ldots,8\) |
| 141 | \(s=5,\ldots,8\) |
| 142 | \(s=6,7,8\) |
| 143 | \(s=7,8\) |
| 144 | \(s=8\) |

This also explains the \(N=145\) failure for this template.  The relative
holes adjacent to the long interval are \(-8\notin W(B)\) and
\(137\notin W(B)\).  For any valid shift \(s\le8\), the point \(s+137\) lies
inside \([1,145]\) and is addable.  For any valid shift \(s\ge9\), the point
\(s-8\) lies inside \([1,145]\) and is addable.  Hence no shift of this
template works at \(N=145\).

## What this suggests next

This turns the construction search into a template search:

1. Build a Sidon template \(B\), preferably normalized with \(\min B=0\).
2. Compute \(W(B)\).
3. Maximize the length of consecutive intervals inside \(W(B)\), especially
   intervals with \(L\le0\) and \(R\ge\max B\).
4. Use the shift inequality to translate that interval into actual
   \(N\)-coverage.

The scale is plausible for Erdos #156 because a \(k\)-point Sidon set has about
\(k^2/2\) differences, and translating those differences by \(k\) anchors can
block on the order of \(k^3\) positions.  The hard part is arranging those
positions into a long interval rather than a sparse cloud.

The helper script for this calculation is:

```bash
python3 erdos_156/parametrize_template.py --n-min 113 --n-max 145
```

## One-point extensions

The other tool found the next natural extension

```text
B9 = [0, 40, 60, 61, 63, 67, 96, 112, 144].
```

This is still Sidon.  Its relative blocker set has longest consecutive
interval

```text
[-12, 148]
```

of length 161.  Since \(\max B9=144\), the shift rule is

\[
\max(1,N-148)\le s\le \min(13,N-144),
\]

which gives shifted maximal Sidon sets for every \(145\le N\le161\).  In
particular, for \(N=145\), \(s=1\) gives

```text
[1, 41, 61, 62, 64, 68, 97, 113, 145].
```

A further one-point extension also works:

```text
B10 = [0, 40, 60, 61, 63, 67, 96, 112, 144, 149].
```

Here \(W(B10)\) has longest consecutive interval

```text
[-29, 157]
```

of length 187, and \(\max B10=149\).  Thus

\[
\max(1,N-157)\le s\le \min(30,N-149),
\]

which covers every \(150\le N\le187\).  Together the current deterministic
shifted-template chain gives:

| size | template max | blocker interval | covered \(N\) | interval length / \(k^3\) |
|---:|---:|---|---|---:|
| 8 | 112 | `[-7,136]` | 113-144 | 0.281 |
| 9 | 144 | `[-12,148]` | 145-161 | 0.221 |
| 10 | 149 | `[-29,157]` | 150-187 | 0.187 |

So we now have construction-based maximal Sidon witnesses for every
\(113\le N\le187\), using size 8 up to 144, size 9 through 161, and size 10
through 187.

This is not yet the asymptotic mechanism.  For an \(O(N^{1/3})\) construction,
we need templates with covered \(N\) on the order of \(k^3\), which means the
covered interval should grow by order \(k^2\) when one mark is added.  The
observed endpoint extensions increase the maximum covered \(N\) by only
17 and then 26.  They are excellent finite structure, but the efficiency
currently decreases rather than stabilizing.

## Greedy chain continuation

To make the extension experiment reproducible, `extend_template_chain.py`
greedily appends one new mark at a time.  At each step it requires the next
template's covered \(N\)-range to overlap the previous range, and chooses the
legal append that maximizes the new covered endpoint.

Running

```bash
python3 erdos_156/extend_template_chain.py --k-max 20 --top 8
```

produced this chain:

| \(k\) | appended mark | max \(B\) | blocker interval | covered \(N\) | endpoint/\(k^3\) |
|---:|---:|---:|---|---|---:|
| 8 | - | 112 | `[-7,136]` | 113-144 | 0.2812 |
| 9 | 144 | 144 | `[-12,148]` | 145-161 | 0.2209 |
| 10 | 149 | 149 | `[-29,157]` | 150-187 | 0.1870 |
| 11 | 158 | 158 | `[-38,165]` | 159-204 | 0.1533 |
| 12 | 183 | 183 | `[-49,212]` | 184-262 | 0.1516 |
| 13 | 213 | 213 | `[-64,250]` | 214-315 | 0.1434 |
| 14 | 286 | 286 | `[-65,311]` | 287-377 | 0.1374 |
| 15 | 312 | 312 | `[-114,323]` | 313-438 | 0.1298 |
| 16 | 340 | 340 | `[-124,377]` | 341-502 | 0.1226 |
| 17 | 378 | 378 | `[-125,396]` | 379-522 | 0.1062 |
| 18 | 425 | 425 | `[-125,503]` | 426-629 | 0.1079 |
| 19 | 539 | 539 | `[-125,548]` | 540-674 | 0.0983 |
| 20 | 550 | 550 | `[-207,580]` | 551-788 | 0.0985 |

Representative start, middle, and endpoint witnesses from every row were
checked against the original `solve_156.py` verifier with no failures.  The
endpoint \(N=788\) uses the size-20 set

```text
[208, 248, 268, 269, 271, 275, 304, 320, 352, 357,
 366, 391, 421, 494, 520, 548, 586, 633, 747, 758]
```

The conclusion is negative for this greedy rule: it gives many deterministic
finite witnesses, but the normalized endpoint keeps drifting downward.  The
next computational step should be a beam search or local search that directly
optimizes interval length divided by \(k^3\), rather than greedily maximizing
the next endpoint.

## Beam search

The beam-search script `beam_template_search.py` keeps many templates at each
size and ranks them by

```text
best admissible blocker interval length / k^3.
```

With overlap required between consecutive covered ranges,

```bash
python3 erdos_156/beam_template_search.py --k-max 20 --beam-width 120 \
  --output erdos_156/results/template_beam_156_overlap_k20.json
```

finds a size-20 template

```text
[0, 40, 60, 61, 63, 67, 96, 112, 137, 142,
 151, 201, 259, 267, 301, 395, 482, 510, 608, 700]
```

with

```text
W(B) contains [-201,711], so it covers N=701-913.
```

The saved ancestry of this template has overlapping covered ranges whose union
is the full interval

```text
N = 113-913.
```

This improves the greedy size-20 endpoint ratio from \(788/20^3=0.0985\) to
\(913/20^3=0.1141\).  Representative start, midpoint, and endpoint witnesses
for every row in the path were checked with the original verifier.

A freer beam run without the overlap constraint,

```bash
python3 erdos_156/beam_template_search.py --k-max 16 --beam-width 80 \
  --no-require-overlap --x-factor 0.45 --x-window 360 \
  --output erdos_156/results/template_beam_156_free_k16.json
```

did not improve the size-16 density: it again reached endpoint ratio about
0.1355, but with gaps in the path coverage.  A one-swap local refinement around
the best size-20 overlap template, replacing any nonzero mark by any value up
to 1000, found no improvement.

Current reading: beam search is better than greedy and gives much stronger
finite coverage, but the normalized endpoint is still drifting downward.  The
next search should change the template architecture, not just tune endpoint
extensions of the same dense-core-plus-anchors motif.

## Architecture-diversified seeds

The script `search_template_architectures.py` generates seed templates from
compact Sidon cores placed at many offsets, completes them with anchors, and
then runs the beam extension from the best seeds.

The first core-4 pass found a different size-8 seed:

```text
B = [0, 20, 35, 38, 39, 44, 46, 95].
```

This seed is worse than the original at size 8 by interval density, but it
extends better.  Running

```bash
python3 erdos_156/beam_template_search.py \
  --B 0,20,35,38,39,44,46,95 \
  --k-max 20 --beam-width 120 \
  --output erdos_156/results/template_beam_156_arch_seed_core4_k20.json
```

gives a size-20 template

```text
[0, 20, 35, 38, 39, 44, 46, 95, 111, 132,
 142, 175, 267, 289, 301, 341, 410, 489, 594, 617]
```

with

```text
W(B) contains [-273,648], so it covers N=618-922.
```

The saved ancestry of this path has overlapping covered ranges whose union is

```text
N = 96-922.
```

This improves the previous size-20 endpoint from \(913\) to \(922\), and the
ratio from \(0.114125\) to \(0.11525\).  A smaller core-5 architecture pass
rediscovered the same seed as its best extension, so at these parameters the
best alternative still has a compact 4-point dense core.

This is useful evidence for option 1+2: diversified seeds do matter, but the
best improvement is incremental.  The current best computational conclusion is
that shifted templates can give long deterministic finite coverage, while the
known architectures still show a downward \(N/k^3\) trend.

## Local optimization and geometry

The local optimizer `local_optimize_template.py` starts from a fixed-size
template and tries one-mark replacements, followed by simulated annealing.
Starting from the best architecture-diversified size-20 template, a single
replacement improved the endpoint:

```text
111 -> 681
```

The resulting template is

```text
B20_local =
[0, 20, 35, 38, 39, 44, 46, 95, 132, 142,
 175, 267, 289, 301, 341, 410, 489, 594, 617, 681].
```

It is Sidon and has

```text
W(B20_local) contains [-273,693], so it covers N=682-967.
```

This improves the size-20 endpoint ratio to

\[
967/20^3 = 0.120875.
\]

A second pass, using exhaustive one-swap search up to replacement value 1400
and annealing, found no further improvement.  Therefore this template is a
local optimum for the tested one-swap neighborhood.

Combining this local template with the previous architecture-diversified path
gives deterministic shifted-template witnesses for every

```text
N = 96-967.
```

The geometry of the local optimum is more revealing than the numeric gain:

```text
dense core: [0, 20, 35, 38, 39, 44, 46]
remaining anchors: [95, 132, 142, 175, 267, 289, 301, 341,
                    410, 489, 594, 617, 681]
```

The dense core has gaps

```text
[20, 15, 3, 1, 5, 2]
```

and the full template creates all differences \(1,2,\ldots,12\).  Those small
differences explain the right endpoint: \(681+d\) covers \(682,\ldots,693\)
inside the relative blocker interval.  The main interval is flanked by holes:

```text
... -274, [-273, ..., 693], 694 ...
```

So the construction is still best understood as a compact small-difference
core plus many sparse anchors that translate those local blockers across a
long interval.  This supports the formula-extraction direction, but it also
shows why the current architecture may decay: the number of anchors is growing,
yet the longest consecutive blocker interval is only about \(0.12k^3\) at
\(k=20\).

## Anchor-cover model

To test the core-plus-anchor reading directly, `beam_template_search.py` was
run from only the 7-mark core

```text
C = [0, 20, 35, 38, 39, 44, 46].
```

With overlap required, the fixed-core beam search produced a size-20 anchor
chain whose covered union is

```text
N = 47-935.
```

The final fixed-core beam template is

```text
[0, 20, 35, 38, 39, 44, 46, 60, 94, 111,
 123, 156, 227, 255, 313, 381, 413, 500, 552, 627]
```

with interval `[-259,675]`, covering `N=628-935`.  A no-overlap fixed-core
run to size 16 recovered the architecture-search seed path and did not improve
density.

The source decomposition for the local optimum is in
`anchor_cover_analysis.md` and `results/anchor_cover_analysis_156.json`.
Inside the main interval `[-273,693]`, blocker events split as:

```text
core-anchor differences:   2637 events
anchor-anchor differences: 2565 events
core-core differences:      829 events
midpoints:                   91 events
in B:                        20 events
```

As point coverage categories, core-anchor differences hit 919 of the 967
relative points, anchor-anchor differences hit 859, and core-core differences
hit 495.  This is the key formula-extraction warning: anchors are not just
passively translating a fixed core-difference set.  Anchor-anchor differences
are doing almost as much work as mixed core-anchor differences.

The best current conceptual model is therefore:

1. Choose a compact Sidon core that manufactures many small differences.
2. Choose anchor layers so mixed core-anchor differences cover most of the
   interval.
3. Arrange anchor-anchor differences to fill the large gaps between those
   mixed translates.

That third item is the hard part for a proof.  A purely “core differences
translated by anchors” formula is probably too weak for the observed best
templates.
