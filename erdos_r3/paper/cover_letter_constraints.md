# Cover letter — Constraints (Springer)

Mehmet Ergezer
Wentworth Institute of Technology
550 Huntington Avenue, Boston, MA 02115, USA
ergezerm@wit.edu | ORCID: 0000-0001-6627-3667

July 3, 2026

The Editors
Constraints

Dear Editors,

I am pleased to submit the manuscript *"Salem–Spencer sets as a
cross-paradigm solver benchmark: a witness-split CP-SAT campaign on
r_3(212) and a paradigm-resistant residual"* for consideration in
Constraints as a **benchmark paper**.

The paper presents the Salem–Spencer family (OEIS A003002) as a natural,
scalable constraint-solving benchmark, and reports a reproducible campaign
on its frontier instance: does a 44-element subset of [1, 212] exist with
no three-term arithmetic progression? The family separates solver
technologies at three measured heights, which is what makes it valuable
as a benchmark. The main contributions:

1. A layered separation result. No paradigm touches the monolithic
   instance in 24 hours (CP-SAT, HiGHS MIP, and CDCL all fail, with the
   MIP dual bound pinned at 0.0). Under a witness-informed
   cube-and-conquer split, LP-paradigm methods fail uniformly on an
   LP-flat pocket; CDCL (CaDiCaL) closes most of it with verified DRAT
   proofs; and the two hardest audited subproblems, which defeat CaDiCaL
   at 12 hours, fall to kissat 4.0.4 well within that budget, with DRAT
   certificates independently verified end-to-end. The benchmark thus
   separates solvers *within* the CDCL paradigm — rarer and arguably
   more useful than separating paradigms.
2. An honestly reported refuted conjecture: the pocket we believed (and
   documented) to be paradigm-resistant collapsed under a
   competition-grade solver, relocating the hardness boundary from
   paradigm to implementation. A kissat survey then closes 99/100 of a
   fresh broad-residual sample (median 122 s), repricing the full
   certified sweep — and with it the unit-gap problem
   r_3(212) ∈ {43, 44} — as a bounded computation.
3. A problem-specific pruning family (window-cardinality implied
   constraints derived from known r_3(L) values) that outperforms every
   generic lever tested, reducing the unresolved rate by 28 percentage
   points — a concrete data point on the value of domain constraints
   over solver tuning.
4. A tiered instance release (JSONL plus DIMACS CNF and MiniZinc
   exports) with controlled A/B experiments behind every design claim.

All instances, solver scripts, result logs, verified DRAT/LRAT
certificates, and a Lean 4 encoding of the hardest tier are openly
released (arXiv:2606.04016; Zenodo DOI 10.5281/zenodo.20463334, CC-BY).
The campaign is reproducible end-to-end from the released scripts.

This manuscript is not under consideration elsewhere. An earlier version
was briefly considered at a mathematics journal and was not sent to
review; the present version is reframed for the constraint-programming
community, which is its natural audience. A preprint is posted on arXiv
to establish a citable timestamp.

**Declarations.** The author has no competing interests. Computations
were performed on the Unity HPC platform (MGHPCC). Generative-AI tools
were used for drafting assistance and computational orchestration under
the author's direction, as disclosed in the manuscript; the author takes
full responsibility for all content.

Suggested reviewers with directly relevant expertise:

- Marijn J. H. Heule, Carnegie Mellon University — SAT solving of
  Ramsey-type combinatorial problems; DRAT/drat-trim verification.
- Laurent Perron, Google — OR-Tools CP-SAT lead.
- Ciaran McCreesh, University of Glasgow — proof logging and certified
  constraint solving.
- Jakob Nordström, University of Copenhagen / Lund University —
  proof complexity and certified solving; LP/CDCL paradigm boundaries.

Thank you for your consideration.

Sincerely,
Mehmet Ergezer
