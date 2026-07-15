# Artifact Reproducibility Guide

This guide maps the manuscript's main computational claims to the smallest
released artifact and check needed to inspect them. Large CNF and proof files
are versioned at [Zenodo](https://doi.org/10.5281/zenodo.20463334); compact
generators, summaries, and manuscript sources live in this repository.

## Fast Checks

Run from `erdos_r3/` with Python 3.10 or newer.

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
| All 20 audited T1b chunks close under native CDCL | same T1b/T1c JSONLs | native CaDiCaL/kissat same-formula outputs and hashes on Zenodo |
| T2 portfolio closes 6,045/6,071 | `results/baselines/t2_full/residual_unknown112_summary.json` | complete kissat and residual-CaDiCaL JSONLs on Zenodo |
| Exact values at N=80,90,100 recovered end to end | exact-certificate provenance summaries on Zenodo | CNF, DRAT, LRAT, and `cake_lpr` checker logs on Zenodo |
| Split-policy cover-size/hardness tradeoff | `results/split_policy_ablation_summary.json` | `baselines/r3_split_policy_ablation.py` and its SLURM driver |
| Alternative global-degree cover has 96,847 cubes | `results/global_degree_survivor_sample100_summary.json` | survivor generator and solver-arm outputs |

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
```

All array outputs are resumable. A `SAT` or `FEASIBLE` result is urgent and
must be checked with `r3_verify.py` before any aggregate claim is updated.

## Scope

The release does not claim a proof of `r_3(212)=43`. A proof requires
certificate-checked closure of every cube in one complete T3 cover. The
historical witness-numeric cover has `12,582,912` cubes; the audited global
AP-degree cover has `96,847`. Solver-attested closure of sampled or partial
covers is empirical evidence only.
