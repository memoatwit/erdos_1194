# Overnight plan: anchor-layer search for Erdos #156

Date: May 16, 2026

## Current best state

The shifted-template mechanism is now formalized.  For a Sidon template \(B\),
the relative blocker set

\[
W(B)=B\cup(B+\Delta(B))\cup(B-\Delta(B))\cup\text{integer midpoints}(B)
\]

certifies shifted maximal Sidon sets whenever a shifted interval
\([1-s,N-s]\) lies inside \(W(B)\).

Current best finite construction:

```text
B20_local =
[0, 20, 35, 38, 39, 44, 46, 95, 132, 142,
 175, 267, 289, 301, 341, 410, 489, 594, 617, 681]
```

It has

```text
W(B20_local) contains [-273,693]
covers N=682..967
endpoint ratio = 967 / 20^3 = 0.120875
```

Together with the architecture-diversified beam path, deterministic
shifted-template witnesses are known for every `N=96..967`.

## Main overnight question

Can the anchor-layer architecture keep `endpoint/k^3` from decaying?

The decomposition of `B20_local` over `[-273,693]` shows:

```text
core-anchor difference events:   2637
anchor-anchor difference events: 2565
core-core difference events:      829
```

So the next search should not model anchors as merely translating the core.
Anchor-anchor differences are essential and should be optimized deliberately.

## Success criteria

Treat a run as meaningful if it does at least one of:

1. Produces a size \(k\ge 22\) template with endpoint ratio at least `0.120`.
2. Produces any size-20 template beating endpoint `967`.
3. Finds a repeated anchor-layer pattern that can be written as a parametric
   construction.
4. Gives strong negative evidence: wider local/beam searches still decay below
   `0.11` by \(k=24\).

## Priority 1: extend the fixed-core anchor-cover search

Use the 7-mark core:

```text
C = [0, 20, 35, 38, 39, 44, 46]
```

Run overlap-preserving beam search to larger sizes:

```bash
python3 erdos_156/beam_template_search.py \
  --B 0,20,35,38,39,44,46 \
  --k-max 24 \
  --beam-width 256 \
  --top 12 \
  --output erdos_156/results/template_anchor_cover_core7_k24_w256.json
```

If that finishes comfortably, try:

```bash
python3 erdos_156/beam_template_search.py \
  --B 0,20,35,38,39,44,46 \
  --k-max 28 \
  --beam-width 192 \
  --top 12 \
  --output erdos_156/results/template_anchor_cover_core7_k28_w192.json
```

Record the final endpoint ratio and whether the covered union remains
contiguous.

## Priority 2: local optimize the best endpoint template

Start from `B20_local` and push the one-swap/annealing neighborhood harder:

```bash
python3 erdos_156/local_optimize_template.py \
  --B 0,20,35,38,39,44,46,95,132,142,175,267,289,301,341,410,489,594,617,681 \
  --x-max 2500 \
  --steps 120000 \
  --restarts 16 \
  --seed 1560 \
  --output erdos_156/results/template_local_opt_156_arch20_deep.json
```

If it improves, immediately run a second pass from the improved `B`.

## Priority 3: diversified core/anchor architecture search

Run a broader seed search, but keep it bounded:

```bash
python3 erdos_156/search_template_architectures.py \
  --seed-k 8 \
  --seed-max 240 \
  --core-size 4 \
  --core-span 18 \
  --core-limit 80 \
  --offset-step 2 \
  --inner-beam 16 \
  --seed-limit 24 \
  --extend-k-max 18 \
  --extend-beam-width 96 \
  --print-top 12 \
  --output erdos_156/results/template_architecture_search_156_core4_broad_k18.json
```

If core-size 4 does not improve, run the analogous core-size 5 search:

```bash
python3 erdos_156/search_template_architectures.py \
  --seed-k 8 \
  --seed-max 260 \
  --core-size 5 \
  --core-span 22 \
  --core-limit 80 \
  --offset-step 3 \
  --inner-beam 12 \
  --seed-limit 20 \
  --extend-k-max 18 \
  --extend-beam-width 80 \
  --print-top 12 \
  --output erdos_156/results/template_architecture_search_156_core5_broad_k18.json
```

## Priority 4: formula extraction from any improvement

For any new best template, run:

```bash
python3 erdos_156/analyze_anchor_cover.py \
  --B <comma-separated-template> \
  --core 0,20,35,38,39,44,46 \
  --json-output erdos_156/results/anchor_cover_analysis_NEW.json \
  --md-output erdos_156/anchor_cover_analysis_NEW.md
```

Then inspect:

- main interval `[L,R]`;
- holes just outside `L` and `R`;
- source event split between core-anchor and anchor-anchor differences;
- anchor hit counts;
- normalized anchor positions;
- whether small differences still include a prefix from `1`.

## What to avoid overnight

- Do not spend time on exact \(N=125,k=7\) unless all construction searches
  are exhausted.
- Do not only report a larger endpoint.  Always report endpoint ratio
  `endpoint/k^3`.
- Do not treat finite improvement as asymptotic progress unless the ratio is
  stable or improving with \(k\).

## Morning summary format

Use this exact format:

```text
Best endpoint:
Best ratio:
Best template:
Covered interval:
Covered union if path-based:
Did local search improve? yes/no
Did broader seed search improve? yes/no
Source decomposition:
Interpretation:
Next recommended move:
```
