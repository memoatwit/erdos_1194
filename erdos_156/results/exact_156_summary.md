# Erdős #156 exact-search summary

Computed by `erdos_156/solve_156.py` plus fixed-size exact checkers
`erdos_156/search156.cpp`, `erdos_156/search156_v3.cpp`, and
`erdos_156/search156_v4.cpp`.

| N | status | m(N) | witness A | m/N^(1/3) | m/(N log N)^(1/3) |
|---:|---|---:|---|---:|---:|
| 5 | solved | 3 | `[1, 2, 4]` | 1.7544 | 1.4971 |
| 10 | solved | 3 | `[2, 5, 6]` | 1.3925 | 1.0545 |
| 15 | solved | 4 | `[1, 2, 4, 12]` | 1.6219 | 1.1636 |
| 20 | solved | 4 | `[1, 8, 12, 13]` | 1.4736 | 1.0222 |
| 25 | solved | 5 | `[1, 2, 4, 10, 23]` | 1.7100 | 1.1581 |
| 30 | solved | 5 | `[1, 4, 11, 15, 17]` | 1.6091 | 1.0700 |
| 35 | solved | 5 | `[1, 12, 13, 18, 22]` | 1.5286 | 1.0015 |
| 40 | solved | 5 | `[3, 16, 17, 24, 26]` | 1.4620 | 0.9462 |
| 45 | solved | 6 | `[1, 2, 4, 19, 23, 31]` | 1.6869 | 1.0804 |
| 50 | solved | 6 | `[1, 2, 15, 22, 24, 27]` | 1.6287 | 1.0336 |
| 55 | solved | 6 | `[1, 8, 22, 25, 31, 44]` | 1.5777 | 0.9933 |
| 60 | solved | 6 | `[1, 18, 21, 30, 36, 40]` | 1.5326 | 0.9580 |
| 65 | solved | 6 | `[9, 25, 26, 32, 40, 45]` | 1.4923 | 0.9268 |
| 70 | solved | 7 | `[8, 23, 27, 29, 40, 47, 52]` | 1.6985 | 1.0487 |
| 75 | solved | 7 | `[15, 24, 25, 39, 42, 47, 58]` | 1.6599 | 1.0194 |
| 80 | solved | 7 | `[25, 34, 36, 40, 48, 64, 65]` | 1.6246 | 0.9928 |
| 85 | solved | 7 | `[23, 33, 44, 45, 58, 61, 63]` | 1.5921 | 0.9685 |
| 90 | solved | 7 | `[13, 29, 36, 37, 51, 57, 62]` | 1.5620 | 0.9461 |
| 95 | solved | 7 | `[3, 37, 39, 43, 51, 54, 78]` | 1.5341 | 0.9255 |
| 100 | solved | 7 | `[8, 42, 44, 48, 56, 59, 83]` | 1.5081 | 0.9065 |
| 105 | solved | 8 | `[1, 3, 13, 34, 47, 50, 58, 88]` | 1.6957 | 1.0157 |
| 110 | solved | 8 | `[11, 46, 50, 53, 59, 75, 83, 93]` | 1.6697 | 0.9967 |
| 115 | solved | 8 | `[1, 3, 43, 47, 53, 61, 66, 96]` | 1.6451 | 0.9790 |
| 120 | solved | 8 | `[43, 44, 56, 60, 75, 78, 86, 115]` | 1.6219 | 0.9623 |
| 125 | solved | 8 | `[5, 42, 45, 49, 64, 76, 77, 87]` | 1.6000 | 0.9466 |

## Notes

- `m(N)` is the minimum size of an inclusion-maximal Sidon subset of `[1,N]`.
- Finite exact data is only a structure-finding tool; it is not by itself progress on the asymptotic problem.
- Frontier note: `N=125` is now solved. A resumable v4 first-element split
  proved `k=7` infeasible over all canonical first elements `1..63`; the
  size-8 witness `[5, 42, 45, 49, 64, 76, 77, 87]` gives `m(125)=8`. See
  `exact_156_N125.json` and `exact_156_N125_k7_split.json`.
- Upper-bound note: structural mining found a shifted size-8 template that
  gives maximal Sidon sets for every `N=120..144`; see
  `template_156_size8_120_144.json`. These are upper bounds only, not exact
  values beyond `N=120`.
