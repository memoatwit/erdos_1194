# Monolithic-baseline experiment (for the Constraints revision)

**Question a referee will ask:** what happens if you skip the witness-split
entirely and hand the full unsplit `r_3(212) <= 43` decision instance to each
solver? This experiment answers it with six 24-hour runs.

## Running on Unity

```sh
cd ~/erdos_r3
sbatch baselines/submit_baseline_monolithic.sbatch
```

Six array cells: {CP-SAT, HiGHS MIP, CDCL} x {window bounds on, off}, each
with a 24 h solver cap. Results land in `results/baselines/*.json`.
Roughly 1,150 CPU-hours total; all cells are independent and resumable
(existing outputs are skipped).

## Expected outcome and how it enters the paper

The expected result is UNKNOWN across all six cells (if any cell returns
INFEASIBLE, that is a *new result* — the upper bound would be proved by a
single monolithic run, and for the CDCL cells the DRAT proof should be
verified with drat-trim and archived). A SAT/FEASIBLE row would disprove
`r_3(212) <= 43`; verify the witness with `r3_verify.py` before believing it.

Table stub for §3 (fill `status` and `bound/progress` from the JSONs):

| Paradigm | Windows | Wall | Status | Progress indicator |
|---|---|---|---|---|
| CP-SAT (8 workers) | on  | 24 h | ? | conflicts, branches |
| CP-SAT (8 workers) | off | 24 h | ? | conflicts, branches |
| HiGHS MIP (8 threads) | on  | 24 h | ? | nodes, dual bound |
| HiGHS MIP (8 threads) | off | 24 h | ? | nodes, dual bound |
| CDCL (1 core) | on  | 24 h | ? | conflicts |
| CDCL (1 core) | off | 24 h | ? | conflicts |

Suggested paper text hook: "None of the three paradigms makes measurable
progress on the monolithic instance within 24 hours (Table X), which is the
empirical justification for the witness-split architecture of §2.2."

## Instance exports (standard formats)

`r3_export_instances.py` (repo root) writes DIMACS CNF and MiniZinc for any
tier or the monolithic instance:

```sh
python3 r3_export_instances.py --monolithic --outdir export/
python3 r3_export_instances.py --monolithic --no-windows --outdir export/
for f in results/N212_K44_t1a25.jsonl results/N212_K44_t1b_minus_t1c.jsonl \
         results/N212_K44_t1c2.jsonl; do
  python3 r3_export_instances.py --jsonl "$f" --outdir export/
done
```

Note: the `--windows` CNF variants need a few GB of RAM to encode (22,154
window constraints expand under the sequential counter); run on Unity, not
a laptop. The MiniZinc exports are tiny in all variants.

These exports should be added to the Zenodo deposit (new version) and
mentioned in §5.5 so the benchmark is usable without the repo's Python
tooling. A CSPLib submission of the family is a natural follow-up.

## Follow-up (optional, referee-pleasing)

Cube-and-conquer head-to-head: compare witness-informed cubes against
`march_cu` lookahead cubes on a sampled chunk range. Not scripted yet;
worth doing if a referee asks whether the witness-informed policy matters.
