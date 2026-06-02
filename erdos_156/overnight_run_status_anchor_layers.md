# Overnight run status: anchor-layer search

Date started: May 16, 2026

## Completed so far

### Priority 1: fixed-core anchor-cover beam

Core:

```text
[0, 20, 35, 38, 39, 44, 46]
```

Run:

```bash
python3 erdos_156/beam_template_search.py \
  --B 0,20,35,38,39,44,46 \
  --k-max 24 \
  --beam-width 256 \
  --top 12 \
  --output erdos_156/results/template_anchor_cover_core7_k24_w256.json
```

Result:

```text
covered union: N=47..1453
best final row: k=24, covered N=1055..1453
endpoint ratio: 1453 / 24^3 = 0.1051
```

Follow-up run:

```bash
python3 erdos_156/beam_template_search.py \
  --B 0,20,35,38,39,44,46 \
  --k-max 28 \
  --beam-width 192 \
  --top 12 \
  --output erdos_156/results/template_anchor_cover_core7_k28_w192.json
```

Result:

```text
covered union: N=47..2122
best final row: k=28, covered N=1471..2122
endpoint ratio: 2122 / 28^3 = 0.0967
```

Interpretation: fixed-core anchor-cover beams produce long contiguous finite
coverage, but the endpoint ratio decays below 0.11 by k=24 and below 0.10 by
k=28.  This is negative evidence for this fixed-core anchor-chain architecture.

### Priority 2: deeper local optimization

Run:

```bash
python3 erdos_156/local_optimize_template.py \
  --B 0,20,35,38,39,44,46,95,132,142,175,267,289,301,341,410,489,594,617,681 \
  --x-max 2500 \
  --steps 120000 \
  --restarts 16 \
  --seed 1560 \
  --output erdos_156/results/template_local_opt_156_arch20_deep.json
```

Result:

```text
no improvement
best remains: W(B) contains [-273,693], covered N=682..967
endpoint ratio: 967 / 20^3 = 0.120875
```

Interpretation: `B20_local` is locally saturated under the tested one-swap and
annealing neighborhood.

### Priority 3: broad core-4 architecture search

Run:

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

Result:

```text
best seed: [0, 15, 35, 38, 39, 44, 46, 95]
covered union through best path: N=96..758
best final row: k=18, covered N=511..758
endpoint ratio: 758 / 18^3 = 0.1299725652
```

Validation: representative start/middle/end witnesses for every row in the
best path passed the original `solve_156.py` verifier.

Interpretation: the broader core-4 search found a better size-18 architecture
than the prior fixed-core path.  It should be extended to k=20 or k=24 before
spending more time on broader seed searches.

### May 17 continuation: extend broad core-4 seed, then local optimize

Seed:

```text
[0, 15, 35, 38, 39, 44, 46, 95]
```

Extension run:

```bash
python3 erdos_156/beam_template_search.py \
  --B 0,15,35,38,39,44,46,95 \
  --k-max 20 \
  --beam-width 160 \
  --top 12 \
  --output erdos_156/results/template_beam_156_new_seed_core4_k20.json
```

Result:

```text
covered union: N=96..934
best final row: k=20, covered N=648..934
endpoint ratio: 934 / 20^3 = 0.11675
```

Because this came close to the existing size-20 record, a local pass was run:

```bash
python3 erdos_156/local_optimize_template.py \
  --B 0,15,35,38,39,44,46,95,114,136,157,202,238,288,346,373,413,507,519,647 \
  --x-max 1800 \
  --steps 50000 \
  --restarts 8 \
  --seed 1701 \
  --output erdos_156/results/template_local_opt_156_new_seed_core4_k20.json
```

Result:

```text
best size-20 template:
[0,15,35,38,39,44,46,95,114,136,157,202,238,288,346,373,413,507,594,647]
W(B) contains [-225,742]
covered N=648..968
endpoint ratio: 968 / 20^3 = 0.121
```

This improves the previous size-20 endpoint from 967 to 968.  A second local
pass found no further improvement.

Anchor-cover decomposition for this new size-20 record was written to:

```text
erdos_156/results/anchor_cover_analysis_156_new_seed_k20.json
erdos_156/anchor_cover_analysis_new_seed_k20.md
```

Source event counts over `[-225,742]`:

```text
core-anchor:   2789
anchor-anchor: 2664
core-core:      840
midpoint:        91
in-template:     20
```

The same seed was extended to k=24:

```bash
python3 erdos_156/beam_template_search.py \
  --B 0,15,35,38,39,44,46,95 \
  --k-max 24 \
  --beam-width 192 \
  --top 12 \
  --output erdos_156/results/template_beam_156_new_seed_core4_k24.json
```

Beam result:

```text
covered union: N=96..1442
best final row: k=24, covered N=1020..1442
endpoint ratio: 1442 / 24^3 = 0.10431
```

Local optimization then improved the k=24 endpoint:

```text
first local pass:  N=1054..1451
second local pass: N=1052..1490
```

Best size-24 template:

```text
[0,15,35,38,39,44,95,105,163,180,196,283,296,310,404,478,519,694,792,845,864,1019,1030,1051]
```

It has `W(B)` containing `[-361,1128]`, so it covers `N=1052..1490`, with
endpoint ratio `1490 / 24^3 = 0.1077835648`.  Combined with the broad seed's
beam ancestry, this gives deterministic shifted-template coverage through
`N=1490`.

Validation: representative start/middle/end shifts for the new k=20 and k=24
templates passed the interval lemma checks, both templates are Sidon with their
claimed consecutive blocker intervals, and the original `solve_156.py verify`
checker confirmed the endpoint witnesses at `N=968` and `N=1490`.

## Morning checks

1. Completed: extended the best broad core-4 seed to k=20 and k=24.
2. Completed: local optimization improved the size-20 endpoint to `968` and
   the size-24 endpoint to `1490`.
3. Completed: ran `analyze_anchor_cover.py` on the new size-20 record.
4. Next: compare the new k=24 template's anchor-layer geometry against the
   fixed-core k=24 template, then decide whether to broaden core-5 or mine a
   formula from the k=20/k=24 pair.
