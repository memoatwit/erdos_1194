# Session Handoff: Erdős `r_3(212)` Exact-Value Attempt

Checkpoint date: 2026-05-23

The long chronological handoff was archived at:

```text
erdos_r3/SESSION_HANDOFF_ARCHIVE_2026-05-23.md
```

This file is the short operational handoff for the next agent.

## Goal

Prove or refute the OEIS-frontier candidate:

```text
r_3(212) = 43
```

Lower bound is done: `results/N212_K43_witness.json` is a verified 43-point
3-AP-free subset of `[1,212]`.

Upper-bound target: prove no 44-point 3-AP-free subset of `[1,212]` exists.

Important conditional reduction:

```text
If r_3(211)=43, any 44-set in [1,212] must contain both 1 and 212.
```

This is encoded in:

```text
results/N212_K44_force_endpoints.json
```

## Current Bottom Line

Do **not** submit the full `12,582,912` depth-24 sweep under the current
CP-SAT architecture.

The best current evidence says:

- No FEASIBLE row has appeared in any completed Unity diagnostic.
- Window-cardinality bounds are very useful, but not enough.
- Reordering hot witness pins is not a meaningful lever.
- Pair-clause propagation is not a sufficient lever from the single benchmark.
- Raising the broad cap helps, but sampled broad UNKNOWNs do not collapse at
  120s or 300s.
- HiGHS long-wall can close some T1 survivors, but did not collapse the
  hard-pocket pilot: `3/5` closed after up to `8` hours, `2/5` remained
  `UNKNOWN` with dual bound still `0.0`.
- The remaining hard pocket looks structural and probably needs stronger bounds
  or a custom branch-and-bound approach.

Recommended next move: design a stronger bounding method for hard pockets
(`LP/ILP cuts`, custom B&B with node upper bounds, or a different mathematical
encoding). A methodology writeup may also be worthwhile.

## Key Files

Core tools:

```text
r3_cpsat.py
r3_split_cpsat.py
r3_slurm_emit.py
r3_collect.py
r3_tail_emit.py
r3_cost_model.py
r3_verify.py
```

Important data:

```text
results/N212_K43_witness.json
results/N212_K43_witness_degree_order.json
results/N212_K43_witness_enrichment_order.json
results/N212_K44_force_endpoints.json
results/b003002.txt
results/N212_K44_broad24_window_11575_111574.jsonl
results/N212_K44_window100k_recap_sample100.json
results/N212_K44_broad24_recap120_sample100.jsonl
results/N212_K44_broad24_recap300_sample100.jsonl
results/r3_mine_recap300.txt
results/r3_mine_recap120.txt
results/r3_mine_baseline_100k.txt
WRITEUP_OUTLINE.md
r3_highs_attack.py
submit_highs_attack_45.sbatch
```

Unity Python:

```bash
/work/pi_ergezerm_wit_edu/ergezerm_wit_edu-conda/envs/soft/bin/python
```

Unity project directory:

```text
~/erdos_r3
```

## Confirmed Results

### Window-Bound Broad Runs

Window constraints were the major improvement.

```text
10k window batch [1575,11575):
INFEASIBLE: 9835
UNKNOWN: 165
FEASIBLE: 0
UNKNOWN rate: 1.65%

100k window batch [11575,111575):
INFEASIBLE: 93,929
UNKNOWN: 6,071
FEASIBLE: 0
UNKNOWN rate: 6.071%
```

The 100k UNKNOWNs are pocketed, not uniform. The worst 5k bucket was:

```text
[61575,66575): 680 UNKNOWN / 5000 = 13.60%
```

Hot middle witness pins being forced out correlate with hardness:

```text
68, 70, 75, 76, 91
```

### Worst-Bucket A/B

Range:

```text
[61575,66575)
```

Results:

```text
baseline 60s degree order: 4320 INFEASIBLE, 680 UNKNOWN, 0 FEASIBLE, UNK 13.60%
reorder 60s enrich order: 4352 INFEASIBLE, 648 UNKNOWN, 0 FEASIBLE, UNK 12.96%
walltime 300s degree order: 4632 INFEASIBLE, 368 UNKNOWN, 0 FEASIBLE, UNK 7.36%
```

Interpretation: reordering barely helps; 300s helps but still leaves a large
hard pocket.

### Sample-500 Refinement Tail

The stratified sample-500 depth-16 refinement had:

```text
INFEASIBLE rows: 2,076,095
UNKNOWN rows: 10
FEASIBLE rows: 0
```

Further tail refinements eventually isolated six level-4 residuals.

Tail600 control over those six residuals:

```text
INFEASIBLE: 6
UNKNOWN: 0
FEASIBLE: 0
seconds by case: 63.06, 127.26, 599.74, 65.92, 132.85, 291.33
```

Interpretation: the hard tail is closable with longer caps, but one case nearly
used the full 600s cap.

### Pair-Clause Propagation Benchmark

Single residual:

```text
parent: results/refine_N212_K44_window100k_sample500_tail_level3_base65535_sub1535_subchunk3_next8_60.jsonl
parent chunk_id: 0
```

Results:

```text
control: INFEASIBLE in 67.843s
treatment (--pair-clauses-window 67,91): INFEASIBLE in 71.75s
```

Interpretation: pair clauses are not a sufficient lever from this trial. Keep
the flag available, but do not scale it based on this result.

### Broad-Cap Recap Sample

Sample:

```text
100 chunks sampled from the 6,071 UNKNOWNs in the 100k window batch
random seed: 5230
sample file: results/N212_K44_window100k_recap_sample100.json
```

Results:

```text
recap120 sample100: 31 INFEASIBLE, 69 UNKNOWN, 0 FEASIBLE
recap300 sample100: 55 INFEASIBLE, 45 UNKNOWN, 0 FEASIBLE
```

These are closure rates among chunks already UNKNOWN at 60s, not full-broad
UNKNOWN rates. Still, the result is negative for the “just raise the cap”
hypothesis.

### Hard-Pocket Structural Mining

Reports:

```text
results/r3_mine_recap300.txt
results/r3_mine_recap120.txt
results/r3_mine_baseline_100k.txt
```

Baseline 100k confirms the earlier broad hard-pocket signature:

```text
UNK rows: 6071 / 100000
Top OUT-enriched pins: 68, 75, 70, 76, 91
Top triple: [75=OUT,70=OUT,68=OUT]
  UNK support: 47.75%
  INF support: 10.23%
  log-odds: +2.082
Hot window [67,91]:
  UNK fixed_in mean: 1.28
  INF fixed_in mean: 3.11
```

Recap300 survivors are much less clean:

```text
UNK rows: 45 / 100
Top single-pin log-odds: value 54 OUT, +1.087
Top high-coverage pair: [91=OUT,48=OUT]
  UNK support: 66.67%
  INF support: 36.36%
  log-odds: +1.226
Top triple patterns have log-odds up to +2.488 but low support (<= 8.89%).
Hot window [67,91]:
  UNK fixed_in mean: 1.00
  INF fixed_in mean: 1.35
```

Recap120 has some moderate signals, but no clean high-coverage separator:

```text
UNK rows: 69 / 100
Top pair: [70=OUT,54=OUT]
  UNK support: 73.91%
  INF support: 32.26%
  log-odds: +1.740
Top triple: [76=OUT,67=IN,54=OUT]
  UNK support: 20.29%
  INF support: 0.00%
  log-odds: +2.801
```

Interpretation: the broad 100k UNKNOWN population has a real middle-window
signature, but the harder 300s survivors do not reduce to a small, obvious
pattern that covers most cases. This weakens the case for a simple targeted
constraint and strengthens the case for a genuinely stronger solver/bounding
method.

### HiGHS MIP Prototype

Two artifacts were added:

```text
WRITEUP_OUTLINE.md
r3_highs_attack.py
submit_highs_attack_45.sbatch
```

`highspy` was installed in the Unity soft environment. A single hard survivor
smoke test ran for 300s and produced a sensible `UNKNOWN` row:

```text
chunk_id: 14331
status: UNKNOWN
seconds: 300.505
mip_nodes: 4019
lp_dual_bound: 0.0
```

The first full 45-task HiGHS array (`58516707`) failed immediately because
`submit_highs_attack_45.sbatch` pointed at the stale filename
`results/N212_K44_window100k_recap300_sample100.jsonl`. The correct collected
file is `results/N212_K44_broad24_recap300_sample100.jsonl`.

The SBATCH was patched and resubmitted, then completed:

```text
job: 58526635
array: 0-44%30
input: results/N212_K44_broad24_recap300_sample100.jsonl
output dir: results/highs45/
per-task MIP cap: 3600s
threads per task: 8
```

Aggregate result:

```text
INFEASIBLE: 0
UNKNOWN: 45
FEASIBLE: 0
total seconds: 162003.6
total mip_nodes: 3,181,316
```

Decision: HiGHS closed 0 of 45, so it does not justify escalating a generic
MIP/custom-B&B path under a one-hour cap. The later long-wall audit below
shows this was too pessimistic for the intermediate class, but not for the
hard core.

### HiGHS T1 Long-Wall Pilot

After the writeup draft, a small overnight diagnostic was submitted to test
whether the HiGHS dual bound moves under a much longer cap on the hardest T1
instances.

```text
job: 58672593
script: submit_highs_longwall_t1pilot.sbatch
input: results/N212_K44_broad24_recap300_residual45.jsonl
output dir: results/highs_t1_longwall5/
array: 0-4%5
selected residual45 row indices: 8, 32, 27, 11, 26
selected chunk_ids: 32637, 80765, 67327, 40766, 65373
per-task MIP cap: 28800s
threads per task: 8
logging: --log --mip-report-level 2 --log-dev-level 1
```

Completed result:

```text
INFEASIBLE: 3
UNKNOWN: 2
FEASIBLE: 0
total seconds: 103,767.076
total mip_nodes: 1,981,443
```

Per chunk:

```text
chunk 32637: UNKNOWN,     28,800.112s, 538,453 nodes, dual 0.0
chunk 40766: INFEASIBLE,  12,798.713s, 224,373 nodes, dual inf
chunk 65373: UNKNOWN,     28,800.092s, 512,667 nodes, dual 0.0
chunk 67327: INFEASIBLE,   7,877.973s, 151,411 nodes, dual inf
chunk 80765: INFEASIBLE,  25,490.186s, 554,539 nodes, dual inf
```

Interpretation: the 1-hour HiGHS result was too pessimistic; long-wall HiGHS
can close some of the T1 survivors. However, the pilot still did not collapse
the pocket, and the two unresolved chunks retained the uninformative dual bound
`0.0` through the full `8`-hour cap. So §4.3/§4.5 should be softened from
"HiGHS closes none" to "HiGHS closes some under long caps, but the surviving
subpocket remains dual-bound resistant."

### HiGHS Full-T1 Long-Wall Audit

After the 5-row pilot, the full T1 set was audited under the same `8`-hour
HiGHS cap:

```text
job: 58782313
script: submit_highs_longwall_t1full.sbatch
input: results/N212_K44_broad24_recap300_residual45.jsonl
output dir: results/highs_t1_longwall45/
array: 0-44%30
per-task MIP cap: 28800s
threads per task: 8
```

Completed result:

```text
INFEASIBLE: 25
UNKNOWN: 20
FEASIBLE: 0
total seconds: 901,072.538
total mip_nodes: 25,196,448
dual counts: inf = 25, 0.0 = 20
```

Unknown chunk IDs:

```text
14331, 15357, 24557, 32251, 32637,
32735, 36859, 40943, 40959, 48895,
63231, 64319, 65373, 77311, 81279,
89838, 93949, 97782, 110586, 110587
```

Interpretation: T1 splits cleanly into an intermediate class of `25` chunks
that HiGHS can close at multi-hour wall and a T1b hard core of `20` chunks
that remain `UNKNOWN` after the full cap with dual bound still `0.0`.

## Implementation Notes

Recent tool changes that matter:

- `r3_cpsat.py` supports `--pair-clauses-window LO,HI`.
- `r3_split_cpsat.py` threads that flag through.
- `r3_slurm_emit.py` supports phase-2 `--chunk-list`; it emits one sampled
  broad chunk per SLURM task using `--only-chunk-id`. It also supports
  `--hint-name`, so witness-ensemble pilots can use an alternate witness both
  as the split-vars source and as the CP-SAT hint.
- `r3_collect.py` supports `--chunk-list`, so sampled runs can be collected
  without fake missing IDs.
- `r3_tail_emit.py` supports multi-level tail refinement by using each input
  JSONL as its parent.
- `r3_alt_witness.py` is a standby generator for a structurally distinct
  43-point witness with a Hamming-distance constraint from the current witness.

Be careful with tail output naming. Include enough parent tag detail to avoid
collisions, e.g. include `base`, `sub`, and `subchunk`.

## What Not To Do

Do not launch:

```text
full 12.5M broad sweep
more broad scaling under 60s/120s/300s caps
large pair-clause broad run
```

Do not treat the 300s improvement as enough. It reduced the sampled prior-UNK
rate from `69%` at 120s to `45%` at 300s, but did not collapse it.

Also do not launch the witness-ensemble pilot until the HiGHS long-wall result
lands. The standby files are synced to Unity:

- `submit_alt_witness_alt1.sbatch` generates
  `results/N212_K43_witness_alt1_hamming20.json` and its degree-order split
  file.
- `submit_witness_ensemble_broad_alt1.sbatch` runs the comparable `[11575,
  111575)` 100k broad layer using that alternate witness as both split-vars and
  hint, writing shards to `results/broad24_window_alt1_11575_111574`.

There is also a standby full-T1 long-wall script:

- `submit_highs_longwall_t1full.sbatch` runs all `45` T1 rows with the same
  `8`-hour HiGHS cap used in the 5-row pilot, writing to
  `results/highs_t1_longwall45`. It is useful if we want to audit the
  intermediate-vs-hard-core split across all of T1, but costs up to
  `45 * 8 * 8 = 2,880` worker-hours.

Submitted after explicit go-ahead:

```text
job: 58782313
script: submit_highs_longwall_t1full.sbatch
array: 0-44%30
output dir: results/highs_t1_longwall45
per-task MIP cap: 28800s
threads per task: 8
submitted: 2026-05-25
```

When it finishes, aggregate `results/highs_t1_longwall45/*.jsonl`. Any
`FEASIBLE` row means stop and verify immediately. Otherwise this run audits
the T1 intermediate-vs-hard-core split across all `45` chunks.

Update, 2026-05-26:

- Full-T1 HiGHS long-wall job `58782313` completed with `25 INFEASIBLE`,
  `20 UNKNOWN`, `0 FEASIBLE`. The `20` UNKNOWN rows all retained flat
  `lp_dual_bound = 0.0`; these are the audited T1b hard core.
- T1b chunk IDs: `14331, 15357, 24557, 32251, 32637, 32735, 36859, 40943,
  40959, 48895, 63231, 64319, 65373, 77311, 81279, 89838, 93949, 97782,
  110586, 110587`.
- SAT/CDCL pipeline was added as the next solver-paradigm test:
  `r3_sat_attack.py`, `extract_t1b_residual20.py`, and
  `submit_sat_t1b.sbatch`.
- Unity has no standalone `kissat` or `cadical` binary on `PATH`, so
  `r3_sat_attack.py` now supports `--solver-binary pysat:auto`. The Unity
  Python env has `python-sat` installed in the user site and selects
  `cadical195`.
- The submitted SAT run is intentionally pure 3-AP/cardinality only:
  `--window-lengths none`, with `n_window_constraints = 0`. This tests CDCL
  separately from the window-bound machinery used by CP-SAT and HiGHS.

Submitted SAT/CDCL T1b run:

```text
job: 58832970
script: submit_sat_t1b.sbatch
array: 0-19%20
output dir: results/sat_t1b
per-task SAT cap: 14400s
threads per task: 1
solver backend: pysat:auto (cadical195 on Unity)
encoding: 3-AP + cardinality + endpoint + chunk pins; no window bounds
submitted: 2026-05-26
```

Monitor `results/sat_t1b/sat_attack_idx*.jsonl`. Status mapping:
`SAT` means a feasible 44-set candidate and must be verified immediately;
`UNSAT` means that T1b chunk is closed by CDCL; `UNKNOWN` means the 4h cap
expired.

Update, 2026-05-26 later:

- SAT/CDCL pure 3-AP T1b job `58832970` completed with `18 UNSAT`,
  `2 UNKNOWN`, `0 SAT`.
- Total recorded solver+encoding time across JSONL rows:
  `71,216.85474205017` seconds.
- The two residual SAT-UNKNOWN chunks after the 4h cap are `40959` and
  `48895`; both timed out at about `14,460` seconds.
- Interpretation: CDCL with only the core 3-AP/cardinality encoding closed
  `18/20` of the HiGHS-flat T1b hard core. This refutes the earlier
  solver-paradigm-invariance framing in the strong form. The remaining hard
  core is now T1c = `{40959, 48895}` for any next diagnostic.
- Proof artifact note: the run used `pysat:auto` (`cadical195`) and did not
  write DRAT/LRAT files. The JSON rows from this first run listed nominal
  `proof_path` values for `UNSAT` rows, but `results/sat_t1b/scratch` contains
  no `.drat` files. `r3_sat_attack.py` has since been corrected so future
  PySAT UNSAT rows report `proof_available = false` and `proof_path = null`.
  To get machine-checkable certificates for the 18 closures, rerun those rows
  with a proof-producing external SAT solver or explicit PySAT proof support.

Submitted follow-up SAT jobs:

```text
job: 58913424
script: submit_sat_t1b_proofs.sbatch
array: 0-17%6
output dir: results/sat_t1b_proofs
per-task SAT cap: 21600s
threads per task: 1
solver backend: pysat:auto with --pysat-with-proof (Glucose on Unity)
encoding: same pure 3-AP/cardinality setup as job 58832970
purpose: rerun the 18 UNSAT T1b closures with proof logging and retained CNFs
submitted: 2026-05-26
```

```text
job: 58913425
script: submit_sat_t1c_diag.sbatch
array: 0-3%4
output dir: results/sat_t1c_diag
tasks 0-1: T1c chunks {40959, 48895}, pure 3-AP, 12h cap
tasks 2-3: same chunks, window lengths {31, 100, 199}, totalizer windows, 4h cap
threads per task: 1
purpose: determine whether T1c is only a wall-time artifact or helped by a
small window-bound subset in CDCL
submitted: 2026-05-26
```

Monitor both for any `SAT` row first. A `SAT` row means a feasible 44-set
candidate and must be verified immediately with `r3_verify.py`. For proof
rows, also check that `proof_available` is true and that matching `.cnf` and
`.drat` files exist in `results/sat_t1b_proofs/scratch`.

Update, 2026-05-27:

- Proof-producing rerun job `58913424` completed with `17 UNSAT`, `1 UNKNOWN`,
  `0 SAT`.
- The `UNKNOWN` proof-rerun row is chunk `32735`, which previously closed
  UNSAT without proof logging in job `58832970`; it timed out here at about
  `21661.91` seconds under the proof-logging cap.
- `17` rows have `proof_available = true`; scratch contains `18` CNFs and
  `17` DRAT files.
- Verification job `58952533` failed immediately due concurrent `drat-trim`
  builds and the verifier looking for `.drat` files in the parent proof
  directory instead of `scratch/`.
- The verifier scripts were patched: proof lookup now points at
  `results/sat_t1b_proofs/scratch`, and the verification target set is the
  `17` chunks that actually emitted DRATs. Chunk `32735` is excluded and should
  be treated as a proof-timeout residual.
- Corrected verification job `58952708` was submitted with
  `submit_verify_t1b_proofs.sbatch` (`array=0-16%17`). It should produce
  verification shards for the `17` available DRAT proofs, then
  `aggregate_verifications.py` can build `verification.jsonl` and
  `verification_summary.json`.

Update, 2026-05-27 later:

- Corrected verification job `58952708` completed. The first pass verified
  `11 / 17` available DRAT proofs and timed out on `6 / 17`.
- `results/sat_t1b_proofs/verification_summary.json` on Unity reports
  `all_expected_present = true`, `all_verified = false`,
  `status_counts = {"VERIFIED": 11, "TIMEOUT": 6}`.
- Verified chunks: `14331, 15357, 24557, 32251, 32637, 36859, 65373, 89838,
  93949, 97782, 110586`.
- Verification-timeout chunks: `40943, 63231, 64319, 77311, 81279, 110587`.
- LRAT files were produced for the same `11` verified chunks. Total LRAT bytes
  reported: `6,471,521,323`.
- Local copies were pulled to
  `results/sat_t1b_proofs_verification_summary.json` and
  `results/sat_t1b_proofs_verification.jsonl`.
- Current certificate status: `11` machine-verified UNSAT closures, `6` DRATs
  need a longer verification pass, and chunk `32735` needs a longer
  proof-producing rerun if we want a DRAT for it.

Update, 2026-05-27 T1c diagnostic:

- SAT/CDCL T1c diagnostic job `58913425` completed with `4 UNKNOWN`, `0 SAT`,
  `0 UNSAT`.
- Pure 3-AP 12h arms:
  - chunk `40959`: `UNKNOWN`, `43260.21` seconds.
  - chunk `48895`: `UNKNOWN`, `43260.21` seconds.
- Windowed CDCL arms using totalizer windows for lengths `{31, 100, 199}`:
  - chunk `40959`: `UNKNOWN`, `14461.98` seconds,
    `309` window constraints.
  - chunk `48895`: `UNKNOWN`, `14461.78` seconds,
    `309` window constraints.
- No `SAT` row appeared. T1c did not shrink: the current hard core remains
  `{40959, 48895}` after pure-CDCL 12h and small-window CDCL 4h diagnostics.
- Interpretation: CDCL overturned the broad T1b hardness picture by closing
  `18 / 20`, but the two T1c chunks have now resisted CP-SAT, HiGHS, pure
  SAT/CDCL, and SAT/CDCL with a small window-bound subset.

Update, 2026-05-27 writeup + certificate cleanup:

- Final writeup patches were applied to:
  `WRITEUP_ABSTRACT.md`, `WRITEUP_SECTION_1.md`, `WRITEUP_SECTION_3.md`,
  `WRITEUP_SECTION_4.md`, `WRITEUP_SECTION_5.md`, and
  `WRITEUP_SECTION_6.md`; `WRITEUP_DRAFT.md` was regenerated from those
  sources.
- The final writeup framing is now:
  - `T1a`: `25` chunks closed by HiGHS at `8`h.
  - `T1b minus T1c`: `18` HiGHS-flat chunks closed by first CDCL run.
  - `T1c`: `{40959, 48895}`, resistant to CP-SAT, HiGHS LP-MIP,
    pure CDCL at `12`h, and windowed CDCL at `4`h.
- Research plan saved locally and synced as `R3_212_RESEARCH_PLAN.md`.
- Two small certificate-cleanup jobs were submitted on Unity:

```text
job: 59058393
script: submit_verify_t1b_timeouts_4h.sbatch
array: 0-5%6
target chunks: 40943, 63231, 64319, 77311, 81279, 110587
purpose: rerun drat-trim for the six 1h verification TIMEOUT proofs with a
         4h per-proof cap
output dir: results/sat_t1b_proofs/verification_shards_4h
```

```text
job: 59058394
script: submit_sat_t1b_32735_proof8h.sbatch
target chunk: 32735
purpose: rerun proof-producing pure CDCL for the one solver-closed chunk whose
         first proof-producing rerun timed out
output dir: results/sat_t1b_proof32735
```

For both cleanup jobs, inspect for any `SAT` row first. A `SAT` row means a
feasible 44-set candidate and must be verified immediately with `r3_verify.py`.
Expected outcomes are `VERIFIED` rows for job `59058393` and `UNSAT` with a
nonempty DRAT proof for job `59058394`.

Update, 2026-05-27 cleanup job results:

- Extended drat-trim job `59058393` completed only one additional verification:
  - chunk `81279`: `VERIFIED` in `6357.23` seconds; LRAT size
    `2,961,905,389` bytes.
- The other five 4h verification tasks did not produce final JSONL rows:
  `40943, 63231, 64319, 77311, 110587`.
  - SLURM states were `FAILED`, with the 4h jobs ending at the wall cap for
    all except `64319`, which failed earlier at `01:55:26`.
  - The SBATCH left empty `.tmp_*` files for those chunks because the verifier
    exits nonzero on non-VERIFIED outcomes and `set -e` stops before the final
    `mv`.
  - If rerunning, patch the verification SBATCH to preserve non-VERIFIED rows
    (move the tmp file even when the Python verifier exits nonzero), then give
    these five chunks a longer cap or more diagnostic logging.
- Chunk `32735` proof-producing rerun job `59058394` did not emit a result row
  or DRAT proof.
  - SLURM state: `OUT_OF_MEMORY`.
  - Runtime before OOM: `03:22:47`.
  - Max RSS: about `33.5G`, exceeding the requested `32G`.
  - Scratch contains only `chunk_00032735.cnf`; no proof was produced.
  - If rerunning, request substantially more memory (for example `64G`) or use
    a native external proof-producing SAT binary instead of the in-process
    PySAT proof path.

Update, 2026-05-27 Unity storage migration:

- Unity project storage was moved off the home filesystem.
- New canonical Unity path:
  `/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3`
- Compatibility symlink:
  `/home/ergezerm_wit_edu/erdos_r3 -> /work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3`
- The copy was verified with `rsync -aHn --delete`; the old home copy was then
  removed.
- Post-migration filesystem use on Unity:
  - `/home`: `4.0G / 100G` (`4%`)
  - `/work`: `339G / 1000G` (`34%`)
- Existing scripts that use `$HOME/erdos_r3` should continue to work through
  the symlink, but new runbooks should prefer the `/work/.../erdos_r3`
  canonical path.

Update, 2026-05-27 Lean benchmark packaging:

- Lean 4 / Mathlib 4 benchmark files now live under `lean/`:
  - `R3Base.lean`: shared `r_3` / chunk-problem definitions.
  - `R3_212_Witness.lean`: verified `43`-set lower-bound witness, intended to
    discharge by `decide`.
  - `R3_T1c_40959.lean` and `R3_T1c_48895.lean`: sorry-bodied AlphaProof-style
    targets for the two T1c chunks, expected answer `false`.
  - `README.md`: provenance and usage notes.
- Added `lean/verify_lean_sanity.sh`, which creates a temporary
  `lake new R3 math` project (or uses `--project PATH`), copies the files into
  the `R3/` module tree, and times `lake env lean` on the base, witness, and
  T1c files.
- The writeup now frames T1c as both a JSONL solver benchmark and a Lean
  formal-proof-search target. The Lean files still need a Unity sanity run once
  a Lean/Lake toolchain is available on PATH.

Update, 2026-05-27 certificate cleanup handoff:

- Patched `verify_t1b_proofs.py` with `--exit-zero-on-nonverified` so
  TIMEOUT / NOT_VERIFIED / ERROR rows are still durable JSONL outputs.
- Patched the verification SBATCH wrapper to move temp JSONL files even when
  the verifier returns a non-VERIFIED outcome.
- Submitted two follow-up jobs on Unity under the work-backed project path:

```text
job: 59155561
script: submit_verify_t1b_timeouts_12h.sbatch
array: 0-4%5
target chunks: 40943, 63231, 64319, 77311, 110587
purpose: rerun drat-trim for the five remaining verification TIMEOUT proofs
         with a 12h per-proof cap and durable JSONL rows for all outcomes
output dir: results/sat_t1b_proofs/verification_shards_12h
lrat dir: results/sat_t1b_proofs/lrat_12h
```

```text
job: 59155562
script: submit_sat_t1b_32735_proof64g.sbatch
target chunk: 32735
purpose: rerun proof-producing pure CDCL for the one CDCL-closed chunk whose
         proof-producing rerun OOM'd at 32G; this rerun requests 64G and 12h
output dir: results/sat_t1b_proof32735_64g
```

- Unity has no `kissat` or `cadical` binary on PATH or in visible modules, so
  chunk `32735` is rerunning through the known-good PySAT/Glucose proof path.
- Before submitting, a safety grep found no `SAT` rows in existing SAT follow-up
  outputs. Any `SAT` row in these jobs still means a feasible 44-set candidate
  and must be checked immediately with `r3_verify.py`.

Update, 2026-05-28 certificate cleanup results and final verifier pass:

- Jobs `59155561` and `59155562` completed; no `SAT` rows appeared.
- `59155561` (`r3_drat_verify12h`) verified four of the five remaining
  emitted DRAT proofs:
  - `40943`: `VERIFIED` in `30717.49` seconds.
  - `64319`: `VERIFIED` in `8135.34` seconds.
  - `77311`: `VERIFIED` in `18241.18` seconds.
  - `110587`: `VERIFIED` in `18389.39` seconds.
  - `63231`: reported `s TIMEOUT` after `40000.73` seconds.
- This moves the emitted-proof certificate tally to `16 VERIFIED / 17`:
  the previous `12` plus `40943, 64319, 77311, 110587`.
- `59155562` (`r3_sat_32735_p64g`) succeeded:
  - chunk `32735`: `UNSAT`, proof available.
  - Runtime: `13468.14` seconds.
  - Max RSS from SLURM: about `46.1G`.
  - DRAT path:
    `results/sat_t1b_proof32735_64g/scratch/chunk_00032735.drat`
    (about `11G`).
- Two toolchain bugs/findings were fixed after reading these outputs:
  - `verify_t1b_proofs.py` now parses `s TIMEOUT` from `drat-trim` as
    `TIMEOUT`, not `ERROR`.
  - The verifier now passes `drat-trim -t <seconds>` explicitly. `drat-trim`
    defaults to `40000` seconds otherwise, which is why the 12h `63231` run
    stopped before the intended Python timeout.
  - The verifier now uses uppercase `-L` for LRAT output. Lowercase `-l`
    emits trimmed DRAT lemmas, not LRAT.
- Submitted final verifier cleanup job:

```text
job: 59383874
script: submit_verify_t1b_final2_24h.sbatch
array: 0-1%2
target chunks:
  task 0: 63231 (rerun with explicit drat-trim -t 86400)
  task 1: 32735 (verify the newly emitted 64G proof)
purpose: try to promote certificate tally from 16/18 to 18/18 for
         T1b \ T1c, with actual LRAT output via drat-trim -L
output dir: results/sat_t1b_proofs/verification_shards_final2_24h
lrat dir: results/sat_t1b_proofs/lrat_final2_24h
```

- Existing earlier files under `lrat_4h` / `lrat_12h` were produced with
  lowercase `-l`; treat them as trimmed DRAT lemma files despite the directory
  name. New `lrat_final2_24h` outputs use the correct LRAT flag.

Update, 2026-05-29 final verifier results:

- Final verifier job `59383874` completed cleanly; no `SAT` rows appeared.
- Both final chunks verified:
  - `63231`: `VERIFIED` in `49758.11` seconds.
    - DRAT size: `8,382,747,830` bytes.
    - LRAT (`-L`) size: `19,450,578,821` bytes.
  - `32735`: `VERIFIED` in `80960.68` seconds.
    - DRAT size: `10,895,617,956` bytes.
    - LRAT (`-L`) size: `31,167,112,547` bytes.
- Certificate tally for `T1b \ T1c` is now clean:
  `18 / 18` CDCL-resolved chunks have emitted DRAT proofs independently
  verified by `drat-trim`.
- `T1c` remains unchanged: chunks `40959` and `48895` are still the only
  audited residual, resistant to CP-SAT, HiGHS LP-MIP, pure CDCL at `12h`,
  and windowed CDCL at `4h`.
- Writeup files were updated to replace the intermediate `12 / 17` certificate
  language with the final `18 / 18` verified-DRAT result. Be careful with
  wording around LRAT: older `lrat_4h` / `lrat_12h` outputs used drat-trim
  lowercase `-l` and are trimmed DRAT lemmas, while `lrat_final2_24h` uses the
  correct uppercase `-L`.

## Best Next Options

1. Finish certificate cleanup for the CDCL-closed T1b chunks.
   - Monitor jobs `59058393` and `59058394`.
   - If `32735` emits a DRAT, verify it with `drat-trim`.

2. Treat T1c as the research target.
   - Native SAT solver comparison on chunks `40959` and `48895`.
   - Cardinality-encoding sweep.
   - Larger window-family encodings if memory permits.
   - Lean/formal-proof-search encoding for AlphaProof-style systems.
   - Custom branch-and-bound or new additive-combinatorial bounds.

3. Do not submit the full `12,582,912` sweep until some method moves T1c.

## Safety Rule

Any FEASIBLE row means the candidate upper bound is false or the encoding is
wrong. Immediately verify the witness with `r3_verify.py` before doing anything
else.

## Update: 2026-07-12 venue-strengthening campaign

The corrected paper review identified that the previous HiGHS
`mip_dual_bound=0.0` values were non-diagnostic because those models used a
zero objective with `sum(x)=44`. Four replacement/follow-up experiments are
now running from the work-backed project directory:

```text
61729241  r3_t2_kissat_full  full 6,071-row T2 kissat pass
61729294  r3_cdcl_ctrl       CaDiCaL 3.0.0 vs kissat 4.0.4 on all 20 T1b CNFs
61729298  r3_highs_opt       maximize sum(x), LP + MIP, windows off/on on T1b
61729302  r3_known_reg       exact-value regressions at N=100,150,200
```

Unity's normal QOS permits at most 2,000 submitted jobs, so job `61729241`
uses 1,518 array tasks with four sequential chunks per task. The controlled
CDCL preflight produced matching CNF SHA-256 hashes for both solver arms. The
optimization-form HiGHS preflight on chunk `14331` produced LP optimum `74.5`
and, after five seconds, MIP incumbent `36` with upper bound `64`, confirming
that the new formulation reports meaningful bounds. At the first live check,
the full T2 pass had 24 completed rows, all `UNSAT`, with no `SAT` rows.

Do not update manuscript result tables until each job has complete aggregate
counts and the paired CNF hashes have been checked. Any `SAT`/`FEASIBLE` result
still overrides every other action and requires immediate witness verification.

### Completed: optimization-form HiGHS job 61729298

All 40 T1b arms completed (20 chunks with windows off, 20 with windows on),
each after a continuous LP solve followed by a two-hour binary MIP maximizing
`sum(x)`. No feasible size-44 witness appeared and no arm certified an upper
bound below 44.

- Windows off:
  - LP optima: `73.0` to `84.5` (median `76.5`).
  - MIP incumbents: `39` to `40`.
  - MIP upper bounds: `46` to `57` (median `49.5`).
  - All 20 reached the two-hour cap; total `32,089,555` MIP nodes.
- Windows on:
  - LP optima: numerically `44.0` on all 20 chunks.
  - MIP incumbents: `39` to `40`.
  - MIP upper bounds: numerically `44.0` on all 20 chunks, never below the
    target by the experiment's certification tolerance.
  - All 20 reached the two-hour cap; total `6,014,774` MIP nodes.

Interpretation: the valid window inequalities dramatically tighten the
relaxation and reduce node counts, but leave a one-unit integer proof gap at
the target. This replaces the invalid interpretation of the earlier
zero-objective `mip_dual_bound=0.0` outputs.

### Completed: controlled CDCL job 61729294

The native-solver comparison completed all 40 tasks on deterministic,
no-window CNFs for the 20 T1b chunks:

- Native CaDiCaL 3.0.0: `20/20 UNSAT`, median `734.0 s`, p90 `9,700.0 s`,
  maximum `28,635.8 s`, total `79,421.8 s`.
- Kissat 4.0.4: `20/20 UNSAT`, median `429.0 s`, p90 `3,467.8 s`, maximum
  `13,425.5 s`, total `42,782.3 s`.
- All `20/20` paired `cnf_sha256` values match.
- Kissat was faster on 19 of 20 pairs; the median paired ratio
  `CaDiCaL_seconds / kissat_seconds` was `1.38`.
- T1c chunk `40959`: CaDiCaL `28,635.8 s`, kissat `13,425.5 s`.
- T1c chunk `48895`: CaDiCaL `18,077.7 s`, kissat `9,963.9 s`.
- No `SAT` row appeared.

Interpretation: the earlier failure of the PySAT-bundled CaDiCaL configuration
at 12 hours does not generalize to current native CaDiCaL 3.0.0. T1c remains a
useful hard tier and separates performance, but not solvability, between the
two current native CDCL solvers under the tested 12-hour cap. Manuscript text
that calls T1c “Kissat-only” or treats it as a CaDiCaL/Kissat solvability
separation must be replaced with this controlled result.

### Completed: full T2 Kissat job 61729241

The full 6,071-row T2 survey completed with no `SAT` row:

- `5,959 UNSAT` (`98.16%` solver-reported closure).
- `112 UNKNOWN` (`1.84%`) at the two-hour per-chunk cap.
- Median solver time: `180.537 s`.
- p90 solver time: `1,294.351 s`.
- Maximum solver time: `7,200.034 s`.
- Aggregate solver time: `3,576,567.153 s` (`993.49` single-core hours).

These are survey outcomes without proof logging. Treat the 5,959 closures as
solver-reported `UNSAT`, not as certificate-backed proof steps. The 112-row
residual is the measured T2 tail for any later long-wall or proof-producing
experiment. Do not extrapolate the T2 rate to the full T3 partition without
qualification.

### Completed: known-value regression job 61729302

The attempted exact-value regression did not produce an end-to-end checked
upper-bound certificate:

- `N=100`, known value 27: the size-27 lower witness was found and independently
  verified (`OPTIMAL`, `368.56 s`), but the size-28 Kissat attack remained
  `UNKNOWN` after 12 hours.
- `N=150`, known value 35: the one-hour lower-witness search remained `UNKNOWN`,
  and the size-36 Kissat attack remained `UNKNOWN` after 12 hours.
- `N=200`, known value 41: the one-hour lower-witness search remained `UNKNOWN`,
  and the size-42 Kissat attack remained `UNKNOWN` after 12 hours.
- No upper-bound proof was verified for any of the three points.

The run validates the witness/encoder plumbing at `N=100` but does not satisfy
the planned MPC gate of recovering a known exact value end to end. Partial DRAT
files from timed-out Kissat runs are not certificates and must not be presented
as such.

### Venue decision after the four experiments

All four jobs are complete and no `SAT`/`FEASIBLE` result appeared. The full T2
census, controlled native CDCL comparison, and optimization-form HiGHS study
materially strengthen the computational paper. The missing piece for an MPC
submission is still at least one known-value regression with a checked
upper-bound certificate, together with the planned Zenodo refresh. Without
that repair, `Constraints` remains the recommended submission venue.

## Update: 2026-07-13 MPC submission gate

Two time-boxed follow-ups were submitted after the completed venue campaign:

```text
61757222  r3_exact_cal  12-cell known-exact calibration
61757223  r3_t2_cad12  native CaDiCaL 12h on the 112-row T2 residual
```

Job `61757222` tests `N = 100, 90, 80, 70, 60, 50` under two compact
encodings: pure 3-AP/cardinality and sparse windows at lengths 31 and `N-1`.
Each upper-bound target receives a one-hour Kissat cap without proof logging.
Only the largest successful cases should be rerun with lower witnesses,
archived CNFs, DRAT/LRAT output, `drat-trim -L`, and `cake_lpr`.

Job `61757223` uses current native CaDiCaL 3.0.0 on the 112 `UNKNOWN` rows
from the completed T2 survey, with a 12-hour cap and no proof logging. The
extracted residual is
`results/baselines/t2_full/residual_unknown112.jsonl` with SHA-256
`7157661e21e192878f73aa02a0ddfc9e51cd43f491bc3946029276605767cff3`.
A preflight regeneration of chunk `16383` matched the earlier Kissat formula
hash exactly:
`16a44b4072941d6909e3e0423d1bb87011918c19e8b17a4d909f834b03a1b1eb`.

Both jobs are survey/calibration runs. Their `UNSAT` rows are solver-reported,
not certificate-backed. Do not submit proof-producing follow-ups until the
complete aggregates are reviewed. Any `SAT` row still requires immediate
verification with `r3_verify.py` and overrides the campaign plan.

### Completed: known-exact calibration job 61757222

All 12 calibration cells returned solver-reported `UNSAT`; no `SAT` row
appeared. Results by `N` and encoding arm:

| N | target K | pure seconds | pure vars / clauses | sparse seconds | sparse vars / clauses |
|---:|---:|---:|---:|---:|---:|
| 100 | 28 | 2,057.550 | 1,444 / 13,696 | 1,623.786 | 21,200 / 53,792 |
| 90 | 25 | 968.317 | 1,274 / 11,176 | 1,256.470 | 18,074 / 45,278 |
| 80 | 23 | 304.361 | 1,104 / 8,906 | 356.784 | 15,012 / 37,142 |
| 70 | 21 | 47.061 | 934 / 6,886 | 48.897 | 12,014 / 29,384 |
| 60 | 20 | 2.571 | 772 / 5,124 | 4.915 | 9,132 / 22,096 |
| 50 | 17 | 1.048 | 622 / 3,624 | 1.423 | 6,238 / 15,030 |

The largest three proof-producing candidates are `N=100`, `N=90`, and
`N=80`. Both encodings close each case, but the pure formulation is much
smaller and is the default candidate for certificate generation. Before any
submission, each selected case still needs a verified lower witness and an
upper proof checked against its archived CNF with `drat-trim -L` and
`cake_lpr`.

At the same checkpoint, job `61757223` had emitted one row: chunk `16383`
closed `UNSAT` in `2,754.215 s`, with its CNF SHA-256 matching the earlier
Kissat survey formula. The remaining CaDiCaL tasks were still running or
throttle-pending.

### Completed: T2 residual CaDiCaL job 61757223

All 112 residual rows completed under native CaDiCaL 3.0.0 at a 12-hour cap:

- `86 UNSAT` (`76.79%` of the Kissat residual).
- `26 UNKNOWN` at the cap.
- `0 SAT`.
- `112/112` CNF SHA-256 values matched the corresponding two-hour Kissat
  survey formulas.
- Median solver time: `23,238.075 s` (`6.46 h`).
- p90 solver time: `43,200.039 s` (the 12-hour cap).
- Maximum solver time: `43,200.047 s`.
- Aggregate solver time: `2,818,577.749 s` (`782.94` single-core hours).

Across the two-solver T2 portfolio, the measured census is now
`6,045 UNSAT / 26 UNKNOWN / 0 SAT` over all 6,071 rows, for a solver-reported
closure rate of `99.57%`. These remain survey results without proof logging;
they are not certificate-backed proof steps and do not cover the full T3
partition.

The final 26-row residual chunk IDs are:

```text
32767 49151 57343 61439 64511 65023 65279 65407 65534 65535
77823 79871 81919 86015 90111 94207 96255 97279 97791 98301
98302 98303 102399 106495 108543 110591
```

This materially satisfies the T2-reduction part of the MPC gate. The next
submission-gate action is the proof-producing exact regression suite at
`N=100,90,80`.

### Submitted: certified exact-value suite job 61848180

The three selected pure encodings were submitted as concurrent array cells:

```text
61848180  r3_exact_cert  N=100,90,80 lower witnesses + DRAT/LRAT/cake_lpr
```

Each cell uses one CPU, 64 GB RAM, and a 72-hour wall cap. Large artifacts are
kept outside `/work`:

- `N=100`: `/scratch4/workspace/ergezerm_wit_edu-soft_speech/r3_exact_certified/N100`
- `N=90`: `/scratch3/workspace/ergezerm_wit_edu-superfund/r3_exact_certified/N90`
- `N=80`: `/scratch4/workspace/ergezerm_wit_edu-soft_speech/r3_exact_certified/N80`

The task requires the regenerated pure CNF SHA-256 to equal the corresponding
calibration hash before accepting a certificate. It then runs proof-producing
Kissat 4.0.4, `drat-trim -L`, and the formally verified `cake_lpr` checker.
Compact provenance is written to
`results/baselines/known_exact_certified/N*/provenance.json` under `/work`.

`cake_lpr` was built from pinned commit
`a4323b203cc9ecd584ba7da9e3fff08135a09d5f`; the Unity binary SHA-256 is
`b25551c853c7b7fe6a9059bcddd81a46fb4ed952b842e1080697f8122ee0c8ca`.
Its bundled example passed `s VERIFIED UNSAT` before submission.

### Partial result and N=100 rerun

Job `61848180` completed two of the three exact certificates end-to-end:

- `N=80`: verified size-22 witness; target 23 `UNSAT`; calibration CNF hash
  matched; DRAT verified and converted to LRAT; `cake_lpr` returned
  `VERIFIED`. Kissat took `228.408 s`, drat-trim `318 s`, and cake_lpr
  `59 s`. The DRAT and LRAT sizes are about 275 MB and 1.02 GB.
- `N=90`: verified size-24 witness; target 25 `UNSAT`; calibration CNF hash
  matched; DRAT verified and converted to LRAT; `cake_lpr` returned
  `VERIFIED`. Kissat took `837.473 s`, drat-trim `1,146 s`, and cake_lpr
  `143 s`. The DRAT and LRAT sizes are about 735 MB and 2.49 GB.

The `N=100` cell stopped before upper solving because its fresh one-worker
size-27 witness search returned `UNKNOWN` at the two-hour cap. This was not a
certificate failure. The prior known-regression run already contains a
size-27 witness marked verified at
`results/baselines/known_regression/N100/lower_witness.json`. The array script
now prefers such a previously audited witness and independently rechecks it
with `r3_verify.py`.

Only `N=100` was resubmitted as job `61850319`. It reused and reverified the
audited witness, generated the pure target-28 CNF in scratch4, and entered the
proof-producing Kissat phase.

### Completed: certified exact-value suite

Job `61850319` completed `N=100` end-to-end:

- The reused size-27 witness passed independent verification.
- Kissat returned `UNSAT` for target 28 in `3,275.385 s` on the pure
  3-AP/cardinality CNF (`1,444` variables, `13,696` clauses).
- The CNF SHA-256 matched the calibration hash exactly:
  `39d2caaa9511593252c4a1d7c71c73e498bb5a6eea1dac34e9c55cc22b100b8b`.
- `drat-trim -L` verified the 1.487 GB DRAT proof and emitted a 4.643 GB LRAT
  proof in `5,658 s`.
- The formally verified `cake_lpr` checker returned `VERIFIED` in `431 s`.

The MPC exact-regression gate is therefore complete: the repository now has
independently verified lower witnesses and formally checked upper
certificates for `r_3(80)=22`, `r_3(90)=24`, and `r_3(100)=27`. All three
pure CNF hashes matched their calibration formulas. No SAT result appeared.

### Completed: global-degree survivor conquer sample

Jobs `61862519` and `61862520` evaluated the same fixed-seed sample of 100
cubes drawn uniformly from the 96,847-cube global AP-degree cover (seed
`20260716`):

- Historical window-bounded CP-SAT, eight workers, 60-s cap: `100 UNKNOWN`,
  median `60.0383 s`, retained total `6,006.5006 s`.
- Native kissat 4.0.4, one worker, pure 3-AP/cardinality CNF, two-hour cap:
  `79 UNSAT / 21 UNKNOWN / 0 SAT`, median `1,819.7459 s`, retained total
  `290,969.9646 s`.
- Kissat closure estimate: `79.0%`, Wilson 95% interval `70.02%--85.83%`.

The sample confirms a cover-size/conquer-cost tradeoff. Global AP-degree
shrinks the complete cover from 12,582,912 to 96,847 cubes, but none of its
sampled survivors closes under the historical CP-SAT cap. Kissat closes most
within two hours. These 79 closures are solver-attested because the survey did
not retain proof objects. Compact artifacts are
`results/global_degree_survivor_{cpsat100,kissat100}.jsonl` and
`results/global_degree_survivor_solver_summary.json`.

### Completed: final cover audit and certificate-transfer sample

- Job `61883592`: independent C-versus-Python audit of the complete global
  AP-degree cover. It completed `VERIFIED`: both implementations agree on the
  24 split variables, 132 minimal masks, 96,847 survivors, and the canonical
  ordered survivor-list SHA-256
  `44da22d51937282e209dbeec7c2369516ec499fd8d39fbf63b798c268f1d6464`.
- Job `61883609`: six proof-producing kissat cells selected at solve-time
  quantiles `0, .2, .4, .6, .8, 1` among the 79 closed survivor rows. Selected
  chunk IDs are `15764552, 15729936, 2128016, 8520965, 9471264, 2168896`;
  prior solve times span `87.34--6492.29 s`.
- Every certificate cell requires survey-identical CNF SHA-256, DRAT
  verification and conversion to LRAT, and `cake_lpr` acceptance. Heavy files
  are split between the existing scratch3 and scratch4 project workspaces.

Job `61883609` completed all six cells successfully:

- `6/6 UNSAT`, all regenerated CNF hashes equal the corresponding survey
  hashes, all DRAT proofs verify and convert to LRAT, and all LRAT
  certificates are accepted by `cake_lpr`.
- Proof-producing solve time: `131.740--10,316.086 s`, median `2,285.183 s`,
  total `20,032.267 s`.
- `drat-trim`: `162--19,634 s`, median `3,388 s`, total `35,618 s`.
- `cake_lpr`: `40--1,663 s`, median `551 s`, total `3,930 s`.
- Artifact totals: CNF `6,078,080` bytes, DRAT `15,712,553,602` bytes, LRAT
  `54,963,026,605` bytes.
- Compact artifacts are the six files under
  `results/global_degree_cert_sample6_provenance/` and
  `results/global_degree_cert_sample6_verification_summary.json`.

### Completed: hardware-matched native CDCL job 61861327

All 20 array cells completed on AMD EPYC 7763 nodes. Each cell ran native
CaDiCaL 3.0.0 and kissat 4.0.4 sequentially on the same generated CNF, with
solver order alternating by array index:

- Both solvers: `20/20 UNSAT`, `0 SAT`; all raw-row and pair-summary CNF
  SHA-256 values agree.
- CaDiCaL: median `584.694 s`, p90 `10,613.074 s`, maximum `31,044.407 s`,
  total `81,849.325 s`.
- kissat: median `416.407 s`, p90 `4,683.541 s`, maximum `13,426.027 s`,
  total `45,482.096 s`.
- Kissat is faster on `20/20` pairs. The geometric mean of
  `CaDiCaL_seconds / kissat_seconds` is `1.476653`; 10,000-resample bootstrap
  95% CI `1.331767--1.655085`; median ratio `1.390206`.
- Order-stratified geometric means: `1.551165` for CaDiCaL-then-kissat and
  `1.405721` for kissat-then-CaDiCaL.
- T1c chunk `40959`: CaDiCaL `31,044.407 s`, kissat `13,426.027 s`.
- T1c chunk `48895`: CaDiCaL `17,792.671 s`, kissat `13,134.653 s`.

Compact local artifacts are `results/cdcl_paired_amd7763_summary.json` and
the 20 paired plus 40 raw solver rows under `results/cdcl_paired_amd7763/`.
