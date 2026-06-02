# 1. Introduction and background

Let `r_3(N)` denote the maximum size of a subset of `[1, N]` containing no
nontrivial three-term arithmetic progression. Equivalently,

```
  r_3(N) = max {|A| : A ⊆ [1, N], no a < b < c in A satisfy a + c = 2b}.
```

The asymptotic study of `r_3(N)` begins with Roth's theorem \cite{roth-1953}
and continues through Salem--Spencer and Behrend-type lower-bound
constructions \cite{salem-spencer-1942,behrend-1946} and modern
density-increment upper bounds, including work of Bloom--Sisask and
Kelley--Meka \cite{bloom-sisask-2023,kelley-meka-2023}. Those results
describe the large-`N` behavior of progression-free sets. The present paper is
about a different but complementary problem: exact finite computation at the
OEIS A003002 frontier.

OEIS A003002 tabulates exact values of `r_3(N)`. Cariboni's b-file currently
reaches `N = 211`, where `r_3(211) = 43`
\cite{oeis-a003002,cariboni-b003002}. The next natural decision problem is
therefore:

> Does there exist a `44`-element 3-AP-free subset of `[1, 212]`?

We found and independently verified a `43`-element 3-AP-free subset of
`[1, 212]`, so the lower bound `r_3(212) ≥ 43` is settled. The upper-bound
question is whether `r_3(212) ≤ 43`. Since `r_3(211) = 43`, any hypothetical
`44`-set in `[1, 212]` must contain both endpoints `1` and `212`; otherwise it
would translate or restrict to a `44`-set in `[1, 211]`. Thus the target is a
single finite feasibility problem with a strong necessary endpoint condition.

We attacked this feasibility problem computationally using a reproducible
CP-SAT architecture. The model uses Boolean variables `x_i`, one linear
constraint for each 3-term arithmetic progression, the decision equality
`sum_i x_i = 44`, endpoint forcing, reflection symmetry breaking, and
window-cardinality inequalities derived from the known values of `r_3(L)` for
`L ≤ 211`. To make the search tractable, we split the problem by assigning
high-degree variables from a verified `43`-witness, generating a deterministic
depth-`24` chunk space, and then refine residual `UNKNOWN` chunks recursively.

The campaign did not produce a formal proof of `r_3(212) = 43`. It did produce
three concrete outcomes.

First, we observed zero feasible `44`-sets across millions of CP-SAT
subproblems, including broad chunks, recursive refinements, wall-cap
recalibrations, and targeted A/B experiments. This is empirical evidence for
the expected value `r_3(212) = 43`, but it is not a certificate.

Second, we found that OEIS window-cardinality inequalities are essential. On
controlled broad-pass ranges, adding these inequalities reduced the `UNKNOWN`
rate by roughly `28` percentage points and also reduced aggregate solver time.
They are the main successful pruning layer of the campaign.

Third, and most importantly, we identified a structural hard pocket. The
largest retained broad run over `100,000` depth-`24` chunks left `6,071`
`UNKNOWN` chunks. A uniform random `100`-chunk sample of those `6,071`
was passed through a `300`-second recap, leaving `45` resistant survivors.
Re-attacking those `45` chunks with HiGHS, an
LP-relaxation-based MIP solver, closed `0 / 45` in one-hour-per-chunk runs.
A full eight-hour audit later closed `25 / 45`, but left `20 / 45`
`UNKNOWN`, all with dual bound still pinned at `0.0`. A subsequent pure
CDCL/SAT attack closed `18 / 20` of that LP-flat subset, while two chunks
remained `UNKNOWN` even under a 12-hour pure-CDCL cap and a 4-hour
windowed-CDCL diagnostic. Thus the obstruction is not merely a CP-SAT
propagation artifact: the final audited pocket, T1c, isolates two chunks that
resist every solver paradigm tested in this campaign.

The contribution of this paper is therefore methodological rather than a new
exact value of A003002. We provide:

1. A reproducible witness-split plus window-cardinality architecture for exact
   `r_3(N)` upper-bound search.
2. A detailed empirical account of the `N = 212, K = 44` campaign, including
   broad-pass counts, refinement behavior, and solver-time tradeoffs.
3. A characterization of the structural hard pocket. The pocket initially
   appeared invariant under CP-SAT-side tuning and HiGHS; after the CDCL break,
   it remains invariant only on the final two-chunk residual T1c.
4. A tiered benchmark release: the `25` HiGHS-closable T1a chunks, the
   `18` CDCL-closable T1b-minus-T1c chunks, the `2` T1c chunks, the `6,071`
   broad `UNKNOWN` chunks from the `100k` expansion batch, and the generator
   for the full depth-`24` sweep.

For reference, the benchmark tier notation used throughout the paper is:

| Symbol | Meaning |
|---|---|
| T1 | the `45` chunks that survived the `300`-s recap of a random `100`-chunk sample from the `6,071` broad UNKNOWNs |
| T1a | the `25` T1 chunks closed by the full `8`-h HiGHS audit |
| T1b | the `20` T1 chunks left UNKNOWN by the full `8`-h HiGHS audit, all with dual bound `0.0` |
| T1b ∖ T1c | the `18` T1b chunks closed by CDCL and independently verified by DRAT checking |
| T1c | the final two chunks `{40959, 48895}` that resist all tested paradigms |
| T2 | the `6,071` UNKNOWN chunks from the `100k` broad expansion batch |
| T3 | the full `12,582,912`-chunk AP-pruned depth-`24` sweep |

The rest of the paper is organized as follows. §2 describes the
architecture. §3 reports the computational campaign. §4 analyzes
the hard pocket across HiGHS and CDCL. §5 formulates the
remaining open problem as a benchmark release. §6 discusses
transferability, limitations, and what the campaign suggests about finite
`r_3` upper-bound search.
