# Structural mining for Erdős #156

This file mines known maximal Sidon witnesses as coverage objects.
For a Sidon set `A`, an outside point is blocked by an existing difference
exactly when it lies in `A +/- Delta(A)`.  Midpoint blockers are tracked
separately.

## Size-8 frontier witnesses

| N | label | A | core4 | gaps | small diffs | diff cover | midpoint-only | median diff mult | essential diff points |
|---:|---|---|---|---|---|---:|---|---:|---:|
| 105 | exact | `[1, 3, 13, 34, 47, 50, 58, 88]` | `[34, 47, 50, 58]` | `[2, 10, 21, 13, 3, 8, 30]` | `[2, 3, 8, 10, 11, 12]` | 101/105 | `[7, 8, 30, 73]` | 2 | 10 |
| 110 | exact | `[11, 46, 50, 53, 59, 75, 83, 93]` | `[46, 50, 53, 59]` | `[35, 4, 3, 6, 16, 8, 10]` | `[3, 4, 6, 7, 8, 9, 10]` | 110/110 | `[]` | 3 | 8 |
| 115 | exact | `[1, 3, 43, 47, 53, 61, 66, 96]` | `[43, 47, 53, 61]` | `[2, 40, 4, 6, 8, 5, 30]` | `[2, 4, 5, 6, 8, 10]` | 111/115 | `[2, 27, 32, 81]` | 2 | 6 |
| 115 | hunt | `[17, 40, 43, 47, 56, 76, 78, 90]` | `[40, 43, 47, 56]` | `[23, 3, 4, 9, 20, 2, 12]` | `[2, 3, 4, 7, 9, 12]` | 113/115 | `[32, 84]` | 3 | 7 |
| 120 | v3-coverage | `[1, 7, 51, 55, 58, 69, 84, 100]` | `[51, 55, 58, 69]` | `[6, 44, 4, 3, 11, 15, 16]` | `[3, 4, 6, 7, 11]` | 115/120 | `[28, 31, 60, 79, 92]` | 2 | 9 |
| 120 | exact | `[43, 44, 56, 60, 75, 78, 86, 115]` | `[43, 44, 56, 60]` | `[1, 12, 4, 15, 3, 8, 29]` | `[1, 3, 4, 8, 11, 12]` | 119/120 | `[50]` | 3 | 8 |
| 125 | upper_witness | `[5, 42, 45, 49, 64, 76, 77, 87]` | `[42, 45, 49, 64]` | `[37, 3, 4, 15, 12, 1, 10]` | `[1, 3, 4, 7, 10, 11, 12]` | 124/125 | `[25]` | 3 | 14 |
| 125 | alternate_size8_witness | `[38, 48, 49, 61, 76, 80, 83, 120]` | `[61, 76, 80, 83]` | `[10, 1, 12, 15, 4, 3, 37]` | `[1, 3, 4, 7, 10, 11, 12]` | 124/125 | `[100]` | 3 | 13 |
| 130 | repair | `[14, 46, 51, 61, 81, 82, 90, 94]` | `[81, 82, 90, 94]` | `[32, 5, 10, 20, 1, 8, 4]` | `[1, 4, 5, 8, 9, 10, 12]` | 130/130 | `[]` | 3 | 15 |
| 135 | repair | `[8, 48, 68, 69, 71, 75, 104, 120]` | `[68, 69, 71, 75]` | `[40, 20, 1, 2, 4, 29, 16]` | `[1, 2, 3, 4, 6, 7]` | 131/135 | `[56, 58, 86, 112]` | 2 | 19 |
| 140 | repair | `[4, 44, 64, 65, 67, 71, 100, 116]` | `[64, 65, 67, 71]` | `[40, 20, 1, 2, 4, 29, 16]` | `[1, 2, 3, 4, 6, 7]` | 136/140 | `[52, 54, 82, 108]` | 2 | 22 |

## Observations

1. The dominant blocker is `A +/- Delta(A)`.  The size-8 witnesses above
   cover every point by translated existing differences except for at most
   a few midpoint-only points.
2. Tight adjacent or near-adjacent pairs are common but not universal.  They
   create very small differences, which help cover neighborhoods around
   every anchor.
3. A recurring motif is a dense core of 4 or 5 marks plus one or two distant
   anchors.  The core manufactures many small differences; the distant
   anchors turn those differences into long-range coverage near the ends.
4. The witnesses are not simple translates of one template.  Reflection and
   shifting produce useful near-misses, but the successful sets vary in
   where their tight pair and long anchor live.
5. The right abstraction is likely a Sidon set whose difference set is a
   sparse ruler and whose translates by the anchors form a bounded-overlap
   cover of `[1,N]`.

## Construction Hypothesis

The data suggests trying to build \(A\) in two layers:

1. Choose a small Sidon core \(C\) with many controlled small differences,
   ideally a compact Golomb ruler whose difference set has short intervals
   such as `{1,3,4}` or `{1,2,3,4,6,7}`.
2. Add distant anchors \(u,v,\ldots\) so the mixed differences
   `u-C`, `v-C`, and `v-u` translate the core's local coverage across the
   low and high ends of `[1,N]`.

In this language, maximality is close to the covering condition

```text
[1,N] subset A + (A-A)
```

with a few leftover holes allowed if they are exact midpoints of pairs of
elements of `A`.  A proof of Erdős #156 would need an infinite family of such
integer Sidon sets with `|A| = O(N^(1/3))`.

## Finite Template Found Overnight

The clearest finite pattern so far is the 8-mark Golomb-ruler template

```text
B = [0, 40, 60, 61, 63, 67, 96, 112]
gaps(B) = [40, 20, 1, 2, 4, 29, 16]
```

The first structural pass found shifts for every `N` from 120 through 144.
The later parametrization in `template_parametrization.md` explains why the
same template actually works for every `N` from 113 through 144.  The relative
blocker set `W(B)` contains the consecutive interval `[-7,136]`, so any shift
with `max(1,N-136) <= s <= min(8,N-112)` gives a maximal Sidon subset of
`[1,N]`.  No shift of this template works at `N=145`.  This is still finite
data, but it is a more concrete object than the unrelated-looking individual
witnesses.

Two one-point extensions have also been checked:

```text
B9  = [0, 40, 60, 61, 63, 67, 96, 112, 144]       covers N=145-161
B10 = [0, 40, 60, 61, 63, 67, 96, 112, 144, 149]  covers N=150-187
```

Together these shifted templates give deterministic construction witnesses for
every `N=113-187`.  The efficiency currently decreases with size, so this is
best treated as a finite structural chain rather than an asymptotic family.

## Per-witness details

### N=105 exact

- A: `[1, 3, 13, 34, 47, 50, 58, 88]`
- normalized: `[0.0095, 0.0286, 0.1238, 0.3238, 0.4476, 0.4762, 0.5524, 0.8381]`
- gaps: `[2, 10, 21, 13, 3, 8, 30]`
- densest core4: `{'core': [34, 47, 50, 58], 'span': 24, 'gaps': [13, 3, 8], 'diffs': [3, 8, 11, 13, 16, 24], 'small_diffs': [3, 8, 11]}`
- densest core5: `{'core': [13, 34, 47, 50, 58], 'span': 45, 'gaps': [21, 13, 3, 8], 'diffs': [3, 8, 11, 13, 16, 21, 24, 34, 37, 45], 'small_diffs': [3, 8, 11]}`
- differences: `[2, 3, 8, 10, 11, 12, 13, 16, 21, 24, 30, 31, 33, 34, 37, 38, 41, 44, 45, 46, 47, 49, 54, 55, 57, 75, 85, 87]`
- coverage: `105/105` total, `101/105` by existing differences
- midpoint-only points: `[7, 8, 30, 73]`
- low diff-multiplicity points: `7-8, 18, 28, 30, 53, 65, 69, 73, 82, 87, 93, 97, ...(+1)`
- anchor hit counts: `[(50, 46), (58, 46), (47, 45), (34, 38), (88, 36), (13, 34), (3, 29), (1, 28)]`
- top difference hit counts: `[(2, 15), (12, 14), (10, 14), (3, 14), (11, 14), (8, 14), (13, 13), (16, 13), (33, 12), (31, 12), (21, 12), (24, 12)]`

### N=110 exact

- A: `[11, 46, 50, 53, 59, 75, 83, 93]`
- normalized: `[0.1, 0.4182, 0.4545, 0.4818, 0.5364, 0.6818, 0.7545, 0.8455]`
- gaps: `[35, 4, 3, 6, 16, 8, 10]`
- densest core4: `{'core': [46, 50, 53, 59], 'span': 13, 'gaps': [4, 3, 6], 'diffs': [3, 4, 6, 7, 9, 13], 'small_diffs': [3, 4, 6, 7, 9]}`
- densest core5: `{'core': [46, 50, 53, 59, 75], 'span': 29, 'gaps': [4, 3, 6, 16], 'diffs': [3, 4, 6, 7, 9, 13, 16, 22, 25, 29], 'small_diffs': [3, 4, 6, 7, 9]}`
- differences: `[3, 4, 6, 7, 8, 9, 10, 13, 16, 18, 22, 24, 25, 29, 30, 33, 34, 35, 37, 39, 40, 42, 43, 47, 48, 64, 72, 82]`
- coverage: `110/110` total, `110/110` by existing differences
- midpoint-only points: `[]`
- low diff-multiplicity points: `9, 23, 31, 39, 73, 95, 103-104`
- anchor hit counts: `[(50, 50), (53, 50), (59, 50), (46, 49), (75, 45), (83, 41), (93, 37), (11, 35)]`
- top difference hit counts: `[(4, 16), (7, 16), (3, 16), (9, 16), (6, 16), (8, 16), (10, 16), (13, 15), (16, 15), (25, 14), (22, 14), (24, 14)]`

### N=115 exact

- A: `[1, 3, 43, 47, 53, 61, 66, 96]`
- normalized: `[0.0087, 0.0261, 0.3739, 0.4087, 0.4609, 0.5304, 0.5739, 0.8348]`
- gaps: `[2, 40, 4, 6, 8, 5, 30]`
- densest core4: `{'core': [43, 47, 53, 61], 'span': 18, 'gaps': [4, 6, 8], 'diffs': [4, 6, 8, 10, 14, 18], 'small_diffs': [4, 6, 8, 10]}`
- densest core5: `{'core': [43, 47, 53, 61, 66], 'span': 23, 'gaps': [4, 6, 8, 5], 'diffs': [4, 5, 6, 8, 10, 13, 14, 18, 19, 23], 'small_diffs': [4, 5, 6, 8, 10]}`
- differences: `[2, 4, 5, 6, 8, 10, 13, 14, 18, 19, 23, 30, 35, 40, 42, 43, 44, 46, 49, 50, 52, 53, 58, 60, 63, 65, 93, 95]`
- coverage: `115/115` total, `111/115` by existing differences
- midpoint-only points: `[2, 27, 32, 81]`
- low diff-multiplicity points: `2, 10, 25, 27-28, 32, 40, 69, 75, 81`
- anchor hit counts: `[(61, 46), (53, 45), (66, 45), (47, 44), (43, 41), (96, 38), (3, 29), (1, 28)]`
- top difference hit counts: `[(2, 15), (4, 14), (10, 14), (18, 14), (6, 14), (14, 14), (19, 14), (8, 14), (13, 14), (5, 14), (42, 13), (40, 13)]`

### N=115 hunt

- A: `[17, 40, 43, 47, 56, 76, 78, 90]`
- normalized: `[0.1478, 0.3478, 0.3739, 0.4087, 0.487, 0.6609, 0.6783, 0.7826]`
- gaps: `[23, 3, 4, 9, 20, 2, 12]`
- densest core4: `{'core': [40, 43, 47, 56], 'span': 16, 'gaps': [3, 4, 9], 'diffs': [3, 4, 7, 9, 13, 16], 'small_diffs': [3, 4, 7, 9]}`
- densest core5: `{'core': [43, 47, 56, 76, 78], 'span': 35, 'gaps': [4, 9, 20, 2], 'diffs': [2, 4, 9, 13, 20, 22, 29, 31, 33, 35], 'small_diffs': [2, 4, 9]}`
- differences: `[2, 3, 4, 7, 9, 12, 13, 14, 16, 20, 22, 23, 26, 29, 30, 31, 33, 34, 35, 36, 38, 39, 43, 47, 50, 59, 61, 73]`
- coverage: `115/115` total, `113/115` by existing differences
- midpoint-only points: `[32, 84]`
- low diff-multiplicity points: `2, 16, 22, 32, 84, 95-96, 100, 105`
- anchor hit counts: `[(56, 51), (40, 50), (47, 50), (76, 50), (43, 49), (78, 48), (90, 40), (17, 37)]`
- top difference hit counts: `[(3, 16), (7, 16), (16, 16), (4, 16), (13, 16), (9, 16), (2, 16), (14, 16), (12, 16), (23, 15), (20, 15), (22, 15)]`

### N=120 v3-coverage

- A: `[1, 7, 51, 55, 58, 69, 84, 100]`
- normalized: `[0.0083, 0.0583, 0.425, 0.4583, 0.4833, 0.575, 0.7, 0.8333]`
- gaps: `[6, 44, 4, 3, 11, 15, 16]`
- densest core4: `{'core': [51, 55, 58, 69], 'span': 18, 'gaps': [4, 3, 11], 'diffs': [3, 4, 7, 11, 14, 18], 'small_diffs': [3, 4, 7, 11]}`
- densest core5: `{'core': [51, 55, 58, 69, 84], 'span': 33, 'gaps': [4, 3, 11, 15], 'diffs': [3, 4, 7, 11, 14, 15, 18, 26, 29, 33], 'small_diffs': [3, 4, 7, 11]}`
- differences: `[3, 4, 6, 7, 11, 14, 15, 16, 18, 26, 29, 31, 33, 42, 44, 45, 48, 49, 50, 51, 54, 57, 62, 68, 77, 83, 93, 99]`
- coverage: `120/120` total, `115/120` by existing differences
- midpoint-only points: `[28, 31, 60, 79, 92]`
- low diff-multiplicity points: `2, 26, 28, 31, 41, 59-60, 68, 79, 83, 92, 101, 110, ...(+1)`
- anchor hit counts: `[(58, 45), (55, 44), (69, 44), (51, 43), (84, 39), (100, 37), (7, 31), (1, 28)]`
- top difference hit counts: `[(6, 15), (4, 15), (3, 15), (7, 14), (18, 14), (14, 14), (11, 14), (15, 14), (16, 14), (33, 13), (29, 13), (26, 13)]`

### N=120 exact

- A: `[43, 44, 56, 60, 75, 78, 86, 115]`
- normalized: `[0.3583, 0.3667, 0.4667, 0.5, 0.625, 0.65, 0.7167, 0.9583]`
- gaps: `[1, 12, 4, 15, 3, 8, 29]`
- densest core4: `{'core': [43, 44, 56, 60], 'span': 17, 'gaps': [1, 12, 4], 'diffs': [1, 4, 12, 13, 16, 17], 'small_diffs': [1, 4, 12]}`
- densest core5: `{'core': [56, 60, 75, 78, 86], 'span': 30, 'gaps': [4, 15, 3, 8], 'diffs': [3, 4, 8, 11, 15, 18, 19, 22, 26, 30], 'small_diffs': [3, 4, 8, 11]}`
- differences: `[1, 3, 4, 8, 11, 12, 13, 15, 16, 17, 18, 19, 22, 26, 29, 30, 31, 32, 34, 35, 37, 40, 42, 43, 55, 59, 71, 72]`
- coverage: `120/120` total, `119/120` by existing differences
- midpoint-only points: `[50]`
- low diff-multiplicity points: `2, 5, 8, 10-11, 37, 50, 106, 113`
- anchor hit counts: `[(44, 52), (60, 52), (75, 52), (56, 51), (78, 51), (43, 51), (86, 47), (115, 31)]`
- top difference hit counts: `[(1, 16), (4, 16), (3, 16), (13, 15), (17, 15), (32, 15), (12, 15), (16, 15), (31, 15), (34, 15), (19, 15), (22, 15)]`

### N=125 upper_witness

- A: `[5, 42, 45, 49, 64, 76, 77, 87]`
- normalized: `[0.04, 0.336, 0.36, 0.392, 0.512, 0.608, 0.616, 0.696]`
- gaps: `[37, 3, 4, 15, 12, 1, 10]`
- densest core4: `{'core': [42, 45, 49, 64], 'span': 22, 'gaps': [3, 4, 15], 'diffs': [3, 4, 7, 15, 19, 22], 'small_diffs': [3, 4, 7]}`
- densest core5: `{'core': [45, 49, 64, 76, 77], 'span': 32, 'gaps': [4, 15, 12, 1], 'diffs': [1, 4, 12, 13, 15, 19, 27, 28, 31, 32], 'small_diffs': [1, 4, 12]}`
- differences: `[1, 3, 4, 7, 10, 11, 12, 13, 15, 19, 22, 23, 27, 28, 31, 32, 34, 35, 37, 38, 40, 42, 44, 45, 59, 71, 72, 82]`
- coverage: `125/125` total, `124/125` by existing differences
- midpoint-only points: `[25]`
- low diff-multiplicity points: `3, 13, 21, 25, 51, 78, 85, 93, 97, 103, 105, 107, ...(+3)`
- anchor hit counts: `[(49, 51), (76, 51), (77, 51), (45, 50), (64, 50), (42, 49), (87, 48), (5, 31)]`
- top difference hit counts: `[(3, 16), (4, 16), (1, 16), (37, 15), (7, 15), (22, 15), (34, 15), (35, 15), (19, 15), (31, 15), (32, 15), (15, 15)]`

### N=125 alternate_size8_witness

- A: `[38, 48, 49, 61, 76, 80, 83, 120]`
- normalized: `[0.304, 0.384, 0.392, 0.488, 0.608, 0.64, 0.664, 0.96]`
- gaps: `[10, 1, 12, 15, 4, 3, 37]`
- densest core4: `{'core': [61, 76, 80, 83], 'span': 22, 'gaps': [15, 4, 3], 'diffs': [3, 4, 7, 15, 19, 22], 'small_diffs': [3, 4, 7]}`
- densest core5: `{'core': [48, 49, 61, 76, 80], 'span': 32, 'gaps': [1, 12, 15, 4], 'diffs': [1, 4, 12, 13, 15, 19, 27, 28, 31, 32], 'small_diffs': [1, 4, 12]}`
- differences: `[1, 3, 4, 7, 10, 11, 12, 13, 15, 19, 22, 23, 27, 28, 31, 32, 34, 35, 37, 38, 40, 42, 44, 45, 59, 71, 72, 82]`
- coverage: `125/125` total, `124/125` by existing differences
- midpoint-only points: `[100]`
- low diff-multiplicity points: `2, 13, 18, 20, 22, 28, 32, 40, 47, 74, 100, 104, ...(+2)`
- anchor hit counts: `[(48, 51), (49, 51), (76, 51), (80, 51), (61, 50), (83, 50), (38, 47), (120, 31)]`
- top difference hit counts: `[(1, 16), (4, 16), (3, 16), (10, 15), (11, 15), (23, 15), (13, 15), (28, 15), (32, 15), (35, 15), (12, 15), (27, 15)]`

### N=130 repair

- A: `[14, 46, 51, 61, 81, 82, 90, 94]`
- normalized: `[0.1077, 0.3538, 0.3923, 0.4692, 0.6231, 0.6308, 0.6923, 0.7231]`
- gaps: `[32, 5, 10, 20, 1, 8, 4]`
- densest core4: `{'core': [81, 82, 90, 94], 'span': 13, 'gaps': [1, 8, 4], 'diffs': [1, 4, 8, 9, 12, 13], 'small_diffs': [1, 4, 8, 9, 12]}`
- densest core5: `{'core': [61, 81, 82, 90, 94], 'span': 33, 'gaps': [20, 1, 8, 4], 'diffs': [1, 4, 8, 9, 12, 13, 20, 21, 29, 33], 'small_diffs': [1, 4, 8, 9, 12]}`
- differences: `[1, 4, 5, 8, 9, 10, 12, 13, 15, 20, 21, 29, 30, 31, 32, 33, 35, 36, 37, 39, 43, 44, 47, 48, 67, 68, 76, 80]`
- coverage: `130/130` total, `130/130` by existing differences
- midpoint-only points: `[]`
- low diff-multiplicity points: `8, 11-12, 20-21, 28, 32, 40, 68, 88, 101, 106-108, 116`
- anchor hit counts: `[(81, 52), (82, 52), (51, 51), (46, 50), (61, 50), (90, 48), (94, 46), (14, 36)]`
- top difference hit counts: `[(5, 16), (10, 16), (1, 16), (9, 16), (13, 16), (8, 16), (12, 16), (4, 16), (32, 15), (15, 15), (35, 15), (36, 15)]`

### N=135 repair

- A: `[8, 48, 68, 69, 71, 75, 104, 120]`
- normalized: `[0.0593, 0.3556, 0.5037, 0.5111, 0.5259, 0.5556, 0.7704, 0.8889]`
- gaps: `[40, 20, 1, 2, 4, 29, 16]`
- densest core4: `{'core': [68, 69, 71, 75], 'span': 7, 'gaps': [1, 2, 4], 'diffs': [1, 2, 3, 4, 6, 7], 'small_diffs': [1, 2, 3, 4, 6, 7]}`
- densest core5: `{'core': [48, 68, 69, 71, 75], 'span': 27, 'gaps': [20, 1, 2, 4], 'diffs': [1, 2, 3, 4, 6, 7, 20, 21, 23, 27], 'small_diffs': [1, 2, 3, 4, 6, 7]}`
- differences: `[1, 2, 3, 4, 6, 7, 16, 20, 21, 23, 27, 29, 33, 35, 36, 40, 45, 49, 51, 52, 56, 60, 61, 63, 67, 72, 96, 112]`
- coverage: `135/135` total, `131/135` by existing differences
- midpoint-only points: `[56, 58, 86, 112]`
- low diff-multiplicity points: `16, 18, 21-22, 25, 27, 30, 34, 38, 56, 58, 61, 63, ...(+9)`
- anchor hit counts: `[(68, 50), (69, 49), (71, 49), (75, 48), (48, 43), (104, 39), (120, 34), (8, 34)]`
- top difference hit counts: `[(1, 16), (3, 16), (7, 16), (2, 16), (6, 16), (4, 16), (20, 14), (21, 14), (23, 14), (27, 14), (29, 14), (16, 14)]`

### N=140 repair

- A: `[4, 44, 64, 65, 67, 71, 100, 116]`
- normalized: `[0.0286, 0.3143, 0.4571, 0.4643, 0.4786, 0.5071, 0.7143, 0.8286]`
- gaps: `[40, 20, 1, 2, 4, 29, 16]`
- densest core4: `{'core': [64, 65, 67, 71], 'span': 7, 'gaps': [1, 2, 4], 'diffs': [1, 2, 3, 4, 6, 7], 'small_diffs': [1, 2, 3, 4, 6, 7]}`
- densest core5: `{'core': [44, 64, 65, 67, 71], 'span': 27, 'gaps': [20, 1, 2, 4], 'diffs': [1, 2, 3, 4, 6, 7, 20, 21, 23, 27], 'small_diffs': [1, 2, 3, 4, 6, 7]}`
- differences: `[1, 2, 3, 4, 6, 7, 16, 20, 21, 23, 27, 29, 33, 35, 36, 40, 45, 49, 51, 52, 56, 60, 61, 63, 67, 72, 96, 112]`
- coverage: `140/140` total, `136/140` by existing differences
- midpoint-only points: `[52, 54, 82, 108]`
- low diff-multiplicity points: `12, 14, 17-18, 21, 23, 26, 30, 34, 52, 54, 57, 59, ...(+12)`
- anchor hit counts: `[(64, 50), (65, 50), (67, 50), (71, 50), (44, 43), (100, 43), (116, 38), (4, 31)]`
- top difference hit counts: `[(1, 16), (3, 16), (2, 16), (20, 15), (21, 15), (23, 15), (7, 15), (6, 15), (4, 15), (16, 15), (40, 14), (27, 14)]`
