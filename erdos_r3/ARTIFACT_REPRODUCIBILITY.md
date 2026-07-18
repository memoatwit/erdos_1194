# Artifact Reproducibility Guide

This guide maps the manuscript's main computational claims to the smallest
released artifact and check needed to inspect them. Large CNF and proof files
are versioned at [Zenodo](https://doi.org/10.5281/zenodo.21413746); compact
generators, summaries, and manuscript sources live in the public
[`constraints-submission-v1.5` repository snapshot](https://github.com/memoatwit/erdos_1194/tree/constraints-submission-v1.5/erdos_r3).

## Fast Checks

Run from `erdos_r3/` with Python 3.10 or newer.

The retained Unity runs used Python 3.12.12, OR-Tools 9.15.6755, HiGHS
1.14.0, and PySAT 1.9.dev4. Recreate that Python stack with:

```bash
conda env create -f environment.yml
conda activate r3-212-campaign
```

Native CaDiCaL, kissat, `drat-trim`, and `cake_lpr` are intentionally built
outside the Python environment. Versioned build entry points are under
`baselines/build_*.sh`; the artifact provenance records the binary SHA-256
used for each certified run.

### Verify the lower-bound witness

```bash
python3 r3_verify.py results/N212_K43_witness.json
```

Expected: size `43`, `is_3ap_free: true`.

### Independently regenerate the high-level model

```bash
python3 r3_model_audit.py \
  --N 212 --K 44 \
  --bfile results/b003002.txt \
  --force-endpoints 1 212 \
  --output /tmp/N212_K44_model_audit.json
cmp /tmp/N212_K44_model_audit.json results/N212_K44_model_audit.json
```

Expected: `11,130` AP inequalities, `22,154` active window inequalities,
monotone unit increments in the b-file, and byte-identical JSON output.
This audit uses only the Python standard library and does not import any
solver adapter.

### Rebuild the manuscript

```bash
cd paper
make
```

The maintained LaTeX body is `paper/paper.body.tex`. The Markdown section
files are drafting history and do not overwrite it.

## Claim-to-Artifact Map

| Manuscript claim | Compact artifact | Heavy or executable artifact |
|---|---|---|
| Verified 43-element witness | `results/N212_K43_witness.json` | `r3_verify.py` |
| High-level model counts and hashes | `results/N212_K44_model_audit.json` | `r3_model_audit.py` |
| Historical T1a/T1b/T1c ladder | `results/N212_K44_t1a25.jsonl`, `N212_K44_t1b_minus_t1c.jsonl`, `N212_K44_t1c2.jsonl` | T1 CNF/DRAT/provenance bundle on Zenodo |
| All 20 audited T1b chunks close under native CDCL; matched paired time ratio 1.477 | `results/cdcl_paired_amd7763_summary.json` | native CaDiCaL/kissat same-node outputs, pair summaries, and hashes on Zenodo |
| T2 portfolio closes 6,045/6,071 | `results/baselines/t2_full/residual_unknown112_summary.json` | complete kissat and residual-CaDiCaL JSONLs on Zenodo |
| Exact values at N=80,90,100 recovered end to end | `results/baselines/known_exact_certified/N*/` | CNF, DRAT, LRAT, and `cake_lpr` checker logs on Zenodo |
| Split-policy cover-size/hardness tradeoff | `results/split_policy_ablation_summary.json` | `baselines/r3_split_policy_ablation.py` and its SLURM driver |
| Alternative global-degree cover has 96,847 cubes | `results/global_degree_survivor_sample100_summary.json` | survivor generator and solver-arm outputs |
| Global-degree survivor sample: CP-SAT 0/100, kissat 79/100 | `results/global_degree_survivor_solver_summary.json` | `results/global_degree_survivor_cpsat100.jsonl`, `results/global_degree_survivor_kissat100.jsonl`, and the two SLURM drivers |
| Six solve-time-stratified survivor closures verify end to end | `results/global_degree_cert_sample6_verification_summary.json` | per-chunk provenance locally; CNF, DRAT, and LRAT artifacts in project scratch / Zenodo release |
| Independent full-cover identity check | `results/global_degree_cover_independent_audit.json` | production Python generator, standalone C enumerator, and canonical survivor-list hashes |

## Certificate Chain

For each certified UNSAT formula, preserve this chain together:

1. the exact DIMACS CNF;
2. the solver-emitted DRAT proof;
3. SHA-256 hashes for both files;
4. the `drat-trim` verification or DRAT-to-LRAT conversion log;
5. the LRAT file where retained;
6. the independent `cake_lpr` result for the exact-value regressions;
7. solver binary version, command line, wall cap, and hardware metadata.

An UNSAT status without this chain is described in the manuscript as
solver-attested, not certified.

## Re-running the Matched Studies on Unity

The SLURM files are configured for the Unity work path
`/work/pi_ergezerm_wit_edu/ergezerm_wit_edu/erdos_r3`. Adjust `--account`,
`--partition`, `--constraint`, and `--chdir` for another cluster.

```bash
# Five-policy paired split ablation.
sbatch baselines/submit_split_policy_ablation.sbatch

# Hardware-matched native CaDiCaL/kissat comparison.
sbatch baselines/submit_cdcl_paired_amd7763.sbatch

# Targeted conquer-phase sample from global-degree survivors.
sbatch baselines/submit_global_degree_survivor_cpsat.sbatch
sbatch baselines/submit_global_degree_survivor_kissat.sbatch

# Independent C-versus-Python audit of the complete 96,847-cube cover.
sbatch baselines/submit_global_degree_cover_audit.sbatch

# Six solve-time-stratified, proof-producing global-degree survivors.
sbatch baselines/submit_global_degree_cert_sample6.sbatch
```

All array outputs are resumable. A `SAT` or `FEASIBLE` result is urgent and
must be checked with `r3_verify.py` before any aggregate claim is updated.
The released fixed-seed sample uses seed `20260716`. Its compact summary
records `100 UNKNOWN` for CP-SAT and `79 UNSAT / 21 UNKNOWN` for kissat, with
a kissat Wilson 95% closure interval of `70.0%--85.8%`. The survey did not
emit proof objects, so those 79 rows are solver-attested rather than certified.
The certificate sample is selected deterministically at solve-time quantiles
`0, .2, .4, .6, .8, 1` from those 79 rows. Each task requires its regenerated
CNF hash to equal the survey hash before DRAT-to-LRAT conversion and
`cake_lpr` checking. All six completed `UNSAT` with matching hashes,
`drat-trim` verification, LRAT output, and `cake_lpr` acceptance. Reproduce
the compact aggregate with:

```bash
python3 baselines/r3_analyze_global_degree_cert_sample.py
```

The hardware-matched CDCL summary is reproduced with:

```bash
python3 baselines/r3_analyze_cdcl_paired.py \
  --input-glob 'results/cdcl_paired_amd7763/paired_idx*.json' \
  --cadical-glob 'results/cdcl_paired_amd7763/cadical_idx*.jsonl' \
  --kissat-glob 'results/cdcl_paired_amd7763/kissat_idx*.jsonl' \
  --output results/cdcl_paired_amd7763_summary.json
```

The analyzer checks all 20 raw CaDiCaL/kissat formula hashes against each
other and their pair summaries before computing paired statistics.

## Scope

The release does not claim a proof of `r_3(212)=43`. A proof requires
certificate-checked closure of every cube in one complete T3 cover. The
historical witness-numeric cover has `12,582,912` cubes; the audited global
AP-degree cover has `96,847`. Solver-attested closure of sampled or partial
covers is empirical evidence only.
