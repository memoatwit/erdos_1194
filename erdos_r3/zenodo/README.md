# `r_3(212)` computational campaign artifacts

This dataset accompanies the preprint
*Witness-split + window-cardinality refinement for `r_3(N)`: architecture,
empirical results, and a structural hard pocket*.

Dataset DOI: <https://doi.org/10.5281/zenodo.20463334>

It contains the large proof and solver artifacts that are too large for arXiv
ancillary files. The small benchmark files and Lean proof-search targets can
also be uploaded to arXiv; this Zenodo bundle is the citable archive for the
heavy DRAT / LRAT / solver-output material.

## Scope

The campaign studies the frontier decision problem

```text
Does there exist a 44-element 3-AP-free subset of [1, 212]?
```

No feasible 44-set was found. The lower bound `r_3(212) >= 43` is witnessed by
`results/N212_K43_witness.json`; the remaining unit gap is
`r_3(212) in {43, 44}`.

The most certificate-ready result in this dataset is:

```text
T1b \ T1c: 18 / 18 CDCL-closed chunks have DRAT proofs independently
verified by drat-trim.
```

The remaining hard core is:

```text
T1c = {40959, 48895}
```

These two chunks resisted CP-SAT, HiGHS LP-MIP, pure CDCL at 12h, and windowed
CDCL at 4h in this campaign.

## Recommended archive layout

Use this layout in the Zenodo upload, preserving relative paths where possible:

```text
r3-212-campaign-v1/
  README.md
  MANIFEST.sha256
  environment/
    unity_versions.txt
    python_packages.txt
    slurm_jobs.tsv
  small/
    N212_K43_witness.json
    N212_K44_force_endpoints.json
    N212_K44_t1a25.jsonl
    N212_K44_t1b_minus_t1c.jsonl
    N212_K44_t1c2.jsonl
    N212_K44_window100k_unknowns.jsonl
    b003002.txt
  lean/
    R3Base.lean
    R3_212_Witness.lean
    R3_T1c_40959.lean
    R3_T1c_48895.lean
    README.md
    verify_lean_sanity.sh
  code/
    r3_sat_attack.py
    verify_t1b_proofs.py
    aggregate_verifications.py
    r3_verify.py
    r3_split_cpsat.py
    r3_cpsat.py
    r3_highs_attack.py
    r3_collect.py
  sat_t1b_proofs/
    verification_all.jsonl
    verification_summary_final.json
    cnf/
      chunk_XXXXXXXX.cnf
    drat/
      chunk_XXXXXXXX.drat
    lrat_final2_24h/
      chunk_00032735.lrat
      chunk_00063231.lrat
  logs/
    slurm_logs/
    highs45/
    highs_t1_longwall45/
    sat_t1b/
    sat_t1c_diag/
```

The CNF and DRAT directories should contain the 18 verified
`T1b \ T1c` chunks:

```text
14331 15357 24557 32251 32637 32735 36859 40943 63231
64319 65373 77311 81279 89838 93949 97782 110586 110587
```

Some large archives in the Zenodo record may be split into `.part-*` files to
stay below upload limits. After downloading all parts into one directory,
reconstruct them with:

```bash
cat r3-212-campaign-v1-drat-part2.tar.part-* > r3-212-campaign-v1-drat-part2.tar
cat r3-212-campaign-v1-lrat-32735.tar.part-* > r3-212-campaign-v1-lrat-32735.tar
```

The standalone file `RECONSTRUCT_SPLIT_ARCHIVES.txt` in the Zenodo record
contains the same reconstruction commands for downloaders.

## Canonical verification files

The canonical certificate summary is:

```text
results/sat_t1b_proofs/verification_summary_final.json
```

Expected key fields:

```json
{
  "all_expected_present": true,
  "all_verified": true,
  "expected_count": 18,
  "verified_count": 18,
  "status_counts": {"VERIFIED": 18}
}
```

The matching detail file is:

```text
results/sat_t1b_proofs/verification_all.jsonl
```

It has one summary row followed by one best verification row per chunk.

## LRAT note

The final verifier pass used the correct `drat-trim -L` option and produced
actual LRAT files for:

```text
32735
63231
```

Earlier directories named `lrat_4h` and `lrat_12h` were produced before the
flag correction. Those files came from lowercase `drat-trim -l`, which emits
trimmed DRAT lemmas, not LRAT. Keep them only if useful for provenance; do not
describe them as LRAT certificates.

## Re-verifying the DRAT proofs

From the repository root after unpacking this dataset:

```bash
python verify_t1b_proofs.py \
  --proofs-dir sat_t1b_proofs/drat \
  --cnfs-dir sat_t1b_proofs/cnf \
  --output sat_t1b_proofs/reverification.jsonl \
  --drat-trim ./drat-trim \
  --time-limit 86400 \
  --exit-zero-on-nonverified
```

To verify a single chunk:

```bash
python verify_t1b_proofs.py \
  --proofs-dir sat_t1b_proofs/drat \
  --cnfs-dir sat_t1b_proofs/cnf \
  --output /tmp/verify_32735.jsonl \
  --drat-trim ./drat-trim \
  --chunk-id 32735 \
  --time-limit 86400 \
  --emit-lrat \
  --lrat-dir /tmp/lrat
```

The two slowest certificates in the campaign were:

```text
63231: drat-trim VERIFIED in 49,758.11 s
32735: drat-trim VERIFIED in 80,960.68 s
```

Large-memory / long-wall runs are normal for these two chunks.

## Checking for feasible witnesses

Any solver row with status `SAT` or `FEASIBLE` would be a candidate 44-set and
must be checked with:

```bash
python r3_verify.py <candidate-witness-json>
```

No such row exists in this release.

## Checksums

Generate `MANIFEST.sha256` at the archive root before upload:

```bash
find . -type f ! -name MANIFEST.sha256 -print0 \
  | sort -z \
  | xargs -0 shasum -a 256 > MANIFEST.sha256
```

After download, verify with:

```bash
shasum -a 256 -c MANIFEST.sha256
```

## Suggested Zenodo metadata

Title:

```text
Artifacts for the r_3(212) witness-split computational campaign
```

Description:

```text
Large proof and solver artifacts for a computational campaign on the
unit-gap problem r_3(212) in {43,44}. The archive includes benchmark JSONL
instances, Lean proof-search targets for the T1c hard core, CNF/DRAT proof
artifacts for the 18 CDCL-closed T1b \\ T1c chunks, drat-trim verification
summaries showing 18/18 VERIFIED, and SLURM solver logs from CP-SAT, HiGHS,
and CDCL runs.
```

Keywords:

```text
additive combinatorics; arithmetic progressions; r_3(N); SAT; DRAT; LRAT;
CP-SAT; HiGHS; Lean; AlphaProof Nexus; OEIS A003002
```

Related identifiers:

```text
isSupplementTo: <arXiv DOI or arXiv URL once assigned>
isSupplementTo: <GitHub repository URL / commit SHA>
```

License recommendation: CC-BY 4.0 for metadata and logs; confirm whether proof
artifacts and third-party solver outputs should inherit the repository license
or be released under CC0.

## Citation

Cite the dataset as:

```bibtex
@dataset{ergezer_r3_212_artifacts_2026,
  author       = {Ergezer, Mehmet},
  title        = {Artifacts for the r_3(212) witness-split computational campaign},
  year         = {2026},
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.20463334},
  url          = {https://doi.org/10.5281/zenodo.20463334}
}
```
