# r_3(212) Research Plan After T1c

Date: 2026-05-27

## Current State

- Certified lower bound: `r_3(212) >= 43`, via
  `results/N212_K43_witness.json`.
- Upper-bound target: rule out every `44`-element 3-AP-free subset of
  `[1,212]`; no feasible candidate has appeared in any completed diagnostic.
- Audited hard-core split:
  - `T1a`: `25` recap300 survivors closed by HiGHS at `8`h.
  - `T1b minus T1c`: `18` HiGHS-flat chunks closed by pure CDCL.
  - `T1c`: chunks `{40959, 48895}`, still `UNKNOWN` under CP-SAT, HiGHS,
    pure CDCL at `12`h, and windowed CDCL at `4`h.
- Certificate status for `T1b minus T1c`:
  - `11` DRAT proofs verified by `drat-trim`.
  - `6` DRAT proofs timed out under the `1`h verifier.
  - chunk `32735` closed in the first CDCL run but timed out under the first
    proof-producing rerun.

## Immediate Cleanup

1. Run extended `drat-trim` on the `6` verification-timeout proofs.
   - Chunks: `40943, 63231, 64319, 77311, 81279, 110587`.
   - Current script: `submit_verify_t1b_timeouts_4h.sbatch`.
   - Success condition: all six become `VERIFIED`, raising certificate
     coverage from `11 / 17` to `17 / 17` emitted proofs.

2. Run longer proof-producing CDCL on chunk `32735`.
   - Current script: `submit_sat_t1b_32735_proof8h.sbatch`.
   - Success condition: `UNSAT` with nonempty DRAT proof.
   - Follow-up if successful: verify the resulting DRAT with `drat-trim`.

These cleanup jobs do not change the mathematical hard core. They improve the
release-quality certificate story for chunks already closed by CDCL.

## Research Track A: Focused SAT on T1c

Goal: determine whether T1c is genuinely beyond CDCL or only beyond the
current encoding.

Experiments, in order:

1. Native solver comparison on T1c.
   - Run Kissat/CaDiCaL binaries directly if available, not only PySAT.
   - Use pure 3-AP/cardinality/pins first, then windowed encodings.

2. Cardinality-encoding sweep.
   - Totalizer, sequential counter, cardinality network, BDD/PB encodings.
   - Keep all other clauses fixed.
   - Decision rule: if one encoding closes either T1c chunk, promote it to a
     two-chunk proof-producing rerun.

3. Window-family sweep.
   - Already tested `{31, 100, 199}`.
   - Next subsets: hot middle lengths, all small `L <= 60`, and full OEIS
     windows if memory allows.
   - Record clause count and memory, not just status.

4. Proof-producing T1c run only after a solver/encoding closes one chunk.
   - Do not spend proof-logging overhead until a non-proof run closes.

## Research Track B: Formal / AlphaProof-Ready Benchmark

Goal: make T1c usable by proof-search systems rather than only SAT/MIP tools.

1. Define a compact Lean statement for a fixed T1c row:
   - Boolean membership over `[1,212]`.
   - endpoint forcing,
   - fixed-in/fixed-out chunk pins,
   - cardinality `44`,
   - no 3-AP triples.

2. Generate two Lean files, one per T1c chunk.

3. Check whether AlphaProof Nexus / Gemini-style systems can attack the
   resulting finite contradiction. The public `formal-conjectures` repo did
   not appear to contain an A003002 / `r_3(N)` formalization as of
   2026-05-25, so the first deliverable is the formalization itself.

## Research Track C: Custom Branch-And-Bound

Goal: exploit structure generic solvers miss.

1. Start with the two T1c fixed assignments only.
2. Branch on variables ranked by AP-degree inside the remaining undecided
   region.
3. At each node, compute fast upper bounds:
   - residual graph maximum independent-set relaxation,
   - window-cardinality residual capacity,
   - clique cover / coloring bound on the conflict graph,
   - reflection-dominance pruning where compatible with fixed pins.
4. Success criterion: close at least one T1c chunk within a few CPU-hours.

If this works on T1c, only then consider scaling to the `6,071` broad
UNKNOWNs.

## Research Track D: New Additive Bounds

Goal: add constraints not equivalent to the existing 3-AP clauses or single
window bounds.

Candidates:

1. Multi-window partition bounds using simultaneous A003002 capacities across
   disjoint or overlapping intervals.
2. Difference-graph / sumset bounds specialized to the middle-out pattern.
3. Low-degree SDP/Lasserre relaxation for the T1c fixed assignments.
4. Fourier/density-increment finite certificates, if a usable finite form can
   be extracted.

Decision rule: test every proposed bound on T1c first. A bound that does not
move T1c should not be scaled to the broad residual.

## What Not To Do Yet

- Do not submit the full `12,582,912` depth-24 sweep.
- Do not run another broad cap-only campaign.
- Do not scale recursive refinement until T1c has a working closure mechanism.

The next real mathematical milestone is simple: close either `40959` or
`48895` by a method that emits a checkable certificate or a reproducible
solver transcript.
