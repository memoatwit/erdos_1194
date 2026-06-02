# Overnight structure summary (#156)

## Main update

The structural mining pass found a reusable size-8 template:

```text
B = [0, 40, 60, 61, 63, 67, 96, 112]
gaps(B) = [40, 20, 1, 2, 4, 29, 16]
```

For every \(N=113,\ldots,144\), at least one shift \(A=s+B\) is a maximal
Sidon subset of \([1,N]\).  The same template fails at \(N=145\).

The mechanism is now parametrized.  For a template \(B\), define

\[
W(B)=B\cup(B+\Delta(B))\cup(B-\Delta(B))\cup\text{integer midpoints}(B).
\]

Then \(s+B\) is maximal in \([1,N]\) exactly when \(s+B\subset[1,N]\) and
\([1-s,N-s]\subset W(B)\).  For the size-8 template above, \(W(B)\) contains
the full interval \([-7,136]\), so any shift satisfying

\[
\max(1,N-136)\le s\le \min(8,N-112)
\]

works.  This inequality is nonempty exactly for \(113\le N\le144\).  It also
explains the \(N=145\) failure.  The adjacent relative holes are
\(-8\notin W(B)\) and \(137\notin W(B)\); shifts \(s\le8\) expose the hole
\(137\), while shifts \(s\ge9\) expose the hole \(-8\).

This is still finite data, not an asymptotic construction, but it is the
clearest pattern so far: a dense core `[60, 61, 63, 67]` creates small
differences `{1,2,3,4,6,7}`, while anchors `0,40,96,112` move that local
coverage across the interval.

Follow-up one-point extensions now give a longer deterministic chain:

| size | template | blocker interval | covered N |
|---:|---|---|---|
| 8 | `[0,40,60,61,63,67,96,112]` | `[-7,136]` | 113-144 |
| 9 | `[0,40,60,61,63,67,96,112,144]` | `[-12,148]` | 145-161 |
| 10 | `[0,40,60,61,63,67,96,112,144,149]` | `[-29,157]` | 150-187 |

So the shifted-template construction now gives witnesses for every
\(113\le N\le187\).  The growth is not yet the right asymptotic story: the
blocker-interval lengths divided by \(k^3\) decrease from about 0.281 to
0.221 to 0.187.

The greedy continuation script extends this finite chain to size 20, ending
with coverage \(N=551,\ldots,788\).  The endpoint ratio is then
\(788/20^3\approx0.0985\), so the greedy rule is useful as a witness factory
but is not behaving like the desired asymptotic construction.

A beam search that optimizes blocker-interval length divided by \(k^3\) does
better.  The best overlap-preserving size-20 beam path has covered-range union
\(N=113,\ldots,913\), ending with a size-20 template covering
\(N=701,\ldots,913\).  Its endpoint ratio is \(913/20^3\approx0.1141\).
This improves the finite witnesses but still trends downward compared with the
size-8/9/10 ratios.

A diversified architecture search found a better seed,
`[0,20,35,38,39,44,46,95]`.  Extending it to size 20 gives covered-range union
\(N=96,\ldots,922\), ending with a size-20 template covering
\(N=618,\ldots,922\).  Its endpoint ratio is \(922/20^3=0.11525\).  A small
core-5 pass rediscovered the same seed as the best extension.

Local optimization around that size-20 template made one useful replacement,
`111 -> 681`, producing a local optimum with
\(W(B)\supset[-273,693]\).  This template covers \(N=682,\ldots,967\) and
raises the endpoint ratio to \(967/20^3=0.120875\).  Together with the
architecture beam path, deterministic shifted-template witnesses now cover
\(N=96,\ldots,967\).

The geometry is still the same broad motif: a 7-mark dense core
`[0,20,35,38,39,44,46]` creates small differences, including every
`1..12`, and sparse anchors translate those blockers across the long interval.

Freezing that 7-mark core and searching only for anchors gives a size-20
fixed-core beam chain with covered union \(N=47,\ldots,935\).  The anchor-cover
decomposition of the local optimum shows why this is not a simple translated
core-difference formula: over the interval `[-273,693]`, core-anchor
differences contribute 2637 blocker events, but anchor-anchor differences
contribute a comparable 2565 events.  A scalable formula would need to design
the anchor layers so their pairwise differences fill the gaps between mixed
core-anchor translates.

## New upper-bound data

| N | result | witness or best near-miss |
|---:|---|---|
| 125 | \(m(N)\le 8\) | `[5, 42, 45, 49, 64, 76, 77, 87]` |
| 130 | \(m(N)\le 8\) | `[14, 46, 51, 61, 81, 82, 90, 94]`; template witness `[8, 48, 68, 69, 71, 75, 104, 120]` also works |
| 135 | \(m(N)\le 8\) | `[8, 48, 68, 69, 71, 75, 104, 120]` |
| 140 | \(m(N)\le 8\) | `[4, 44, 64, 65, 67, 71, 100, 116]` |
| 144 | \(m(N)\le 8\) | `[8, 48, 68, 69, 71, 75, 104, 120]` |
| 145 | \(m(N)\le 9\) | size 8 not found; best size-8 near-miss `[28, 42, 73, 75, 78, 79, 100, 138]` leaves `2` addable; size-9 witness `[1, 32, 52, 56, 65, 73, 95, 100, 101]` |

No new lower-bound certifications were run.  Exact \(m(N)\) remains certified
only through \(N=120\), and \(N=125\) remains \(7\le m(125)\le 8\).

## Files added

- `mine_structure.py`: computes coverage, dense cores, and translated-difference statistics.
- `local_repair_156.py`: exhaustive radius-swap repair around a fixed near-miss.
- `parametrize_template.py`: computes \(W(B)\), long intervals in \(W(B)\), and feasible shifts.
- `structure_mining.md`: current structural report.
- `template_parametrization.md`: shifted-template lemma and the size-8 calculation.
- `results/structure_156.json`: machine-readable structural metrics.
- `results/template_156_size8_120_144.json`: shifted-template data.
- `results/template_156_parametrized.json`: machine-readable parametrized template data.
- `results/template_156_size9_145_161.json`: size-9 shifted-template data.
- `results/template_156_size10_150_187.json`: size-10 shifted-template data.
- `extend_template_chain.py`: greedy one-point extension search.
- `results/template_chain_156_greedy.json`: generated size-8 through size-20 chain.
- `beam_template_search.py`: beam search for high-density shifted templates.
- `search_template_architectures.py`: diversified dense-core-plus-anchor seed search.
- `results/template_beam_156_overlap_k20.json`: overlap-preserving beam search to size 20.
- `results/template_beam_156_free_k16.json`: no-overlap beam search to size 16.
- `results/template_architecture_search_156_core4_k16.json`: core-4 seed architecture search.
- `results/template_architecture_search_156_core5_k16.json`: core-5 seed architecture search.
- `results/template_beam_156_arch_seed_core4_k20.json`: size-20 beam from the best new seed.
- `local_optimize_template.py`: one-swap plus annealing local optimizer.
- `results/template_local_opt_156_arch20.json`: local improvement from 922 to 967 endpoint.
- `results/template_local_opt_156_arch20_pass2.json`: second local pass, no further improvement.
- `analyze_anchor_cover.py`: source decomposition for the anchor-cover model.
- `anchor_cover_analysis.md`
- `results/anchor_cover_analysis_156.json`
- `results/template_anchor_cover_core7_k20.json`: fixed-core anchor beam to size 20.
- `results/template_anchor_cover_core7_free_k16.json`: no-overlap fixed-core anchor beam to size 16.
- `overnight_plan_anchor_layers.md`: proposed next overnight run plan.
- `results/repair_156_N130_k8.json`
- `results/repair_156_N135_k8.json`
- `results/repair_156_N140_k8.json`
- `results/repair_156_N140_k9.json`
- `results/repair_156_N145_k8_frontier.json`
- `results/repair_156_N145_k9.json`

## Next move

The next constructive question is whether this finite parametrization can be
grown into a family.  In abstract form, look for Sidon sets

```text
A = anchors union dense_core
```

where the dense core creates a short interval of small differences and the
anchors translate those blockers so that

```text
[L,R] subset W(B)
```

with \(R-L+1\) on the order of \(|B|^3\), preferably while
\(\max B=O(|B|^3)\).

The concrete next overnight plan is in `overnight_plan_anchor_layers.md`.
