# Cover letter — Constraints (Springer)

Mehmet Ergezer
Wentworth Institute of Technology
550 Huntington Avenue, Boston, MA 02115, USA
ergezerm@wit.edu | ORCID: 0000-0001-6627-3667

July 12, 2026

The Editors
Constraints

Dear Editors,

I am pleased to submit the manuscript *"Salem-Spencer sets as a
cross-solver benchmark: a witness-informed decomposition for
r_3(212)"* for consideration in
Constraints as a **benchmark paper**.

The paper presents the Salem–Spencer family (OEIS A003002) as a natural,
scalable constraint-solving benchmark, and reports a reproducible campaign
on its frontier instance: does a 44-element subset of [1, 212] exist with
no three-term arithmetic progression? The family separates solver
technologies at three measured heights, which is what makes it valuable
as a benchmark. The main contributions:

1. A measured difficulty ladder. None of six tested monolithic CP-SAT,
   HiGHS, or CaDiCaL configurations resolves the instance in 24 hours.
   Under a witness-informed cube-and-conquer split, HiGHS closes 25 of 45
   selected survivors; CaDiCaL closes 18 of the remaining 20 with verified
   DRAT proofs; and the final two audited subproblems fall to kissat 4.0.4,
   again with independently verified certificates.
2. A reproducible solver-configuration separation. The two hardest audited
   chunks defeat the tested PySAT/CaDiCaL configuration at 12 hours but are
   certified by kissat within 6.5 hours. The manuscript states the build and
   configuration caveat explicitly and releases the formulas for controlled
   remeasurement. A fresh kissat survey closes 99/100 sampled broad residuals
   within two hours (median 122 s; Wilson 95% interval 94.6%-99.8%).
3. A problem-specific pruning family (window-cardinality implied
   constraints derived from known r_3(L) values) that produces the largest
   measured CP-SAT improvement, reducing the unresolved rate by 28 percentage
   points — a concrete data point on the value of domain constraints
   over solver tuning.
4. A tiered instance release (JSONL plus DIMACS CNF and MiniZinc
   exports) with controlled A/B experiments behind every design claim.

The code, benchmark instances, result logs, 18 CaDiCaL DRAT certificates,
and a Lean 4 encoding are openly released (arXiv:2606.04016; Zenodo DOI
10.5281/zenodo.20463334, CC-BY). The two certified kissat formula/proof
pairs and provenance records will be included in a versioned Zenodo update
before journal publication. The campaign is reproducible from the released
scripts and archived inputs.

This manuscript is not under consideration elsewhere. An earlier version
was briefly considered at a mathematics journal and was not sent to
review; the present version is reframed for the constraint-programming
community, which is its natural audience. A preprint is posted on arXiv
to establish a citable timestamp.

**Declarations.** The author has no competing interests. Computations
were performed on the Unity HPC platform (MGHPCC). Generative-AI tools
were used for drafting and revision, code assistance, experiment planning,
and computational orchestration under the author's direction, as disclosed
in the manuscript; the author made all final scientific decisions and takes
full responsibility for all content.

Suggested reviewers with directly relevant expertise:

- Marijn J. H. Heule, Carnegie Mellon University — SAT solving of
  Ramsey-type combinatorial problems; DRAT/drat-trim verification.
- Laurent Perron, Google — OR-Tools CP-SAT lead.
- Ciaran McCreesh, University of Glasgow — proof logging and certified
  constraint solving.
- Jakob Nordström, University of Copenhagen / Lund University —
  proof complexity and certified solving.

Thank you for your consideration.

Sincerely,
Mehmet Ergezer
