# Anchor-cover analysis for Erdős #156

## Template

- B: `[0, 20, 35, 38, 39, 44, 46, 95, 132, 142, 175, 267, 289, 301, 341, 410, 489, 594, 617, 681]`
- Core: `[0, 20, 35, 38, 39, 44, 46]`
- Anchors: `[95, 132, 142, 175, 267, 289, 301, 341, 410, 489, 594, 617, 681]`
- Best interval: `[-273, 693]`
- Covered N: `[682, 967]`
- Analyzed interval: `[-273,693]`
- Endpoint ratio: `0.120875`

## Difference structure

- Core differences: `[1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 15, 18, 19, 20, 24, 26, 35, 38, 39, 44, 46]`
- Full difference prefix from 1: `[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]`
- Number of full differences: `190`

## Source counts inside the interval

- Source event counts: `[('core_anchor', 2637), ('anchor_anchor', 2565), ('core_core', 829), ('midpoint', 91), ('in_B', 20)]`
- Point coverage category counts: `[('core_anchor', 919), ('anchor_anchor', 859), ('core_core', 495), ('midpoint', 91), ('in_B', 20)]`
- Low diff-multiplicity points: `84`
- Uncovered points in interval: `[]`

## Geometry

- Clusters with gap <= 25: `[[0, 20, 35, 38, 39, 44, 46], [95], [132, 142], [175], [267, 289, 301], [341], [410], [489], [594, 617], [681]]`
- Top anchor hits: `[(301, 323), (95, 323), (289, 321), (132, 321), (142, 320), (341, 320), (44, 319), (175, 319), (46, 319), (267, 318), (35, 316), (38, 316)]`
- Top difference hits: `[(12, 40), (11, 40), (10, 40), (9, 40), (8, 40), (7, 40), (6, 40), (5, 40), (4, 40), (3, 40), (2, 40), (1, 40), (75, 39), (74, 39), (69, 39), (64, 39), (60, 39), (57, 39), (56, 39), (52, 39)]`

## Edge behavior

The interval is maximal because adjacent holes appear just outside it.
For this template, the analyzed interval is `[-273,693]`; inspect
`edge_sources` in the JSON for the exact blockers around the two edges.
