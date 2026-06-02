# Anchor-cover analysis for Erdős #156

## Template

- B: `[0, 15, 35, 38, 39, 44, 46, 95, 114, 136, 157, 202, 238, 288, 346, 373, 413, 507, 594, 647]`
- Core: `[0, 15, 35, 38, 39, 44, 46]`
- Anchors: `[95, 114, 136, 157, 202, 238, 288, 346, 373, 413, 507, 594, 647]`
- Best interval: `[-225, 742]`
- Covered N: `[648, 968]`
- Analyzed interval: `[-225,742]`
- Endpoint ratio: `0.121000`

## Difference structure

- Core differences: `[1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 15, 20, 23, 24, 29, 31, 35, 38, 39, 44, 46]`
- Full difference prefix from 1: `[1, 2, 3, 4, 5, 6, 7, 8, 9]`
- Number of full differences: `190`

## Source counts inside the interval

- Source event counts: `[('core_anchor', 2789), ('anchor_anchor', 2664), ('core_core', 840), ('midpoint', 91), ('in_B', 20)]`
- Point coverage category counts: `[('core_anchor', 905), ('anchor_anchor', 860), ('core_core', 502), ('midpoint', 91), ('in_B', 20)]`
- Low diff-multiplicity points: `91`
- Uncovered points in interval: `[]`

## Geometry

- Clusters with gap <= 25: `[[0, 15, 35, 38, 39, 44, 46], [95, 114, 136, 157], [202], [238], [288], [346], [373], [413], [507], [594], [647]]`
- Top anchor hits: `[(238, 337), (346, 337), (288, 336), (157, 336), (202, 335), (136, 332), (373, 332), (114, 330), (413, 327), (95, 326), (44, 311), (46, 311)]`
- Top difference hits: `[(95, 40), (94, 40), (92, 40), (90, 40), (88, 40), (87, 40), (86, 40), (85, 40), (81, 40), (80, 40), (79, 40), (76, 40), (75, 40), (70, 40), (68, 40), (67, 40), (66, 40), (62, 40), (60, 40), (58, 40)]`

## Edge behavior

The interval is maximal because adjacent holes appear just outside it.
For this template, the analyzed interval is `[-225,742]`; inspect
`edge_sources` in the JSON for the exact blockers around the two edges.
