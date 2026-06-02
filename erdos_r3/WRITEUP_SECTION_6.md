# 6. Discussion

We close with three observations: what the architecture transfers to,
where it breaks down, and what the campaign suggests about the
broader proof-search problem class for `r_3` upper bounds.

## 6.1 Reusability for adjacent `N`

The five-component architecture of §2 is parametric in `N` and `K`
and depends on two external inputs: a verified `(K - 1)`-element
lower-bound witness for `r_3(N)` and the OEIS A003002 b-file prefix
for window-cardinality pruning at lengths `L ≤ N - 1`. Both inputs
are standard finite data at the current frontier: exact values through
`N = 211` are tabulated by Cariboni/OEIS A003002, and any new run also
requires an explicit verified lower-bound witness at the target size.
We expect the architecture to apply directly to
`N ∈ \{213, …, 220\}` once such witnesses are supplied, with three caveats:

1. The depth of the broad split (`d = 24` for `N = 212`) is empirical
   and likely needs to grow with `N`. The number of feasible-after-pruning
   chunks at depth `d` scales roughly geometrically with the size of the
   witness, so the broad layer for larger `N` will emit more chunks, and
   per-chunk cost will also rise as the number of variables and 3-AP triples
   grows.
2. The `r_3(N)` value drops slowly as `N` grows, so the equality
   `sum x_i = K` becomes harder to refute by simple cardinality
   arguments. We expect the `UNK` rate at the `60`-s wall cap to
   grow with `N`.
3. The endpoint-forcing argument generalizes: if `r_3(N - 1) = K - 1`,
   then any `K`-element 3-AP-free subset of `[1, N]` contains both
   endpoints. This is the only structural input from prior work that
   the architecture exploits; everything else is `N`-uniform.

Within the OEIS A003002 frontier, the architecture is therefore a
drop-in tool for any incremental `r_3(N')` upper-bound attempt, with
the same caveat the present campaign documents: the hard pocket of §4
will likely have an analogue at larger `N`, possibly more severe.

## 6.2 Limitations

The campaign's main limitation is the unresolved hard pocket itself.
Even granting all five CP-SAT levers and the HiGHS substitution, the
architecture cannot close `r_3(212) ≤ 43` without an additional idea.
Section 5 frames this as an open problem; here we record three
narrower limitations of the present implementation:

- **Machine-checkable certificates cover the CDCL-resolved T1b ∖ T1c chunks,
  but not the full campaign.** Follow-up proof-producing runs emitted DRAT
  proofs for all `18` CDCL-resolved T1b ∖ T1c chunks, and independent
  `drat-trim` verification confirmed all `18 / 18`. The `25` HiGHS-closed T1a
  chunks and the `~93,929` broad-pass CP-SAT INFEASIBLE returns remain
  solver-attested rather than third-party-verified; closing this remaining
  gap would require either a SAT re-encoding of each chunk or a verified
  LP-duality-style certificate format we are not aware of in the open MIP
  ecosystem.
- **Compute coverage is incomplete.** The campaign processed
  `100,000` of the `12,582,912` AP-pruned depth-`24` chunks at the
  broad layer, plus refinements on small samples. A full sweep would require
  orders of magnitude more worker-hours under the present parameters and was
  not justified by the available evidence, given the hard-pocket diagnosis.
- **Witness dependence is structural, not adversarial.** The broad
  split is anchored to one specific `43`-witness. A different
  witness would induce a different chunk-ID space and possibly a
  different hard pocket. We did not test whether the hard pocket
  is witness-invariant; if it is not, alternative witnesses might
  bypass the T1c residual of §4.3.
- **The Lean benchmark is not yet upstreamed.** We did not find a public
  A003002 / `r_3(N)` entry in `google-deepmind/formal-conjectures` as of the
  campaign date. The repository includes a Lean 4 formalization of the witness
  and T1c targets, but upstreaming and independent typechecking in that
  ecosystem remain follow-on work.

The third limitation is the most interesting follow-on: a witness-
ensemble version of the broad split, in which the chunk space is
the disjoint union of split-prefixes from multiple distinct
`43`-witnesses, would either reveal an easier alternative covering
of the search space or confirm that the hard pocket is intrinsic
to the constraint family rather than to one witness.

## 6.3 What the campaign suggests about `r_3` upper-bound search

The dominant finding is now more precise than the original CP-SAT/HiGHS
comparison. LP-paradigm methods — CP-SAT-style propagation on the bounded
model and HiGHS LP-MIP — fail uniformly on the `20` T1b chunks with flat dual
bounds, while CDCL closes `18 / 20` of them. The residual T1c set has size
`2` and is the only audited pocket that remains resistant across every tested
paradigm.

Two narrower suggestions follow from the lever inventory of §4.4.
First, the window-cardinality family from OEIS A003002 is doing
nearly all of the work that generic constraint propagation can do;
the `~28`-percentage-point reduction it produces is not matched by
any other intervention at any cost. Second, the levers that *should*
have moved the residual under standard MIP/CP intuition — variable
reordering, pair-AND Tseitin propagators, walltime extension to the
plateau — moved it by less than two percentage points each. The
residual is not lying in wait for a smarter generic search.

The exception is the CDCL paradigm switch (§4.3), which closes `18 / 20` of
T1b. We treat that as a qualitative change of proof system, not another lever
inside the LP-relaxation family.

Combined, these suggest that the most productive next experiment is
not another CP-SAT or MIP variant but either (i) a stronger SAT/proof-search
attack on T1c, (ii) a tighter upper-bound family on `sum x_i`
(Fourier-analytic, multi-window partition, or SDP-derived; §5.4), or
(iii) a custom branch-and-bound that hard-codes the reflection symmetry and
any per-instance dominance relations the generic solvers cannot infer. The
benchmark release of §5 is built to support exactly this kind of follow-on.

We end with the working conjecture of §4.5: T1c corresponds to a
low-dimensional pocket in the depth-`24` assignment lattice along which the LP
relaxation gap is tight and the integer infeasibility certificate, while
present, is not learned by current CDCL encodings under the tested wall caps. A
proof or refutation of this conjecture would be the cleanest mathematical
outcome of the campaign that does not require closing the full unit gap
directly.
