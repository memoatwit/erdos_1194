July 2026

Dear Editors of *Mathematical Programming Computation*,

Please consider the manuscript **"Salem--Spencer sets as a cross-solver
benchmark: decomposition, certification, and split-policy effects at
r_3(212)"** for publication
in *Mathematical Programming Computation*.

The manuscript presents a reproducible computational study and benchmark
family built from the open frontier decision problem for OEIS A003002. Its
contribution is not a claimed resolution of r_3(212). Instead, it develops and
evaluates a witness-informed cube decomposition, quantifies the effect of
problem-specific window-cardinality cuts, compares CP-SAT, LP/MIP, and CDCL
formulations, and releases a graded instance library with machine-checkable
proof artifacts.

The revised study contains four results that I believe fit MPC's emphasis on
practical computation, comparative testing, reusable software, and
verification:

1. Six monolithic 24-hour baselines fail. A matched five-policy ablation then
   exposes a split-policy tradeoff: global AP-degree reduces the exact
   depth-24 cover from 12,582,912 to 96,847 cubes, but the surviving cubes are
   individually harder at the original CP-SAT wall cap.
2. A full two-stage CDCL survey closes 6,045 of 6,071 broad residuals
   (99.57%) with no feasible result, while 26 released instances remain as a
   sharply defined challenge tier.
3. Optimization-form HiGHS experiments show that window inequalities reduce
   the T1b node count by approximately 81% and tighten every tested LP and MIP
   upper bound to the decision threshold 44, but not below it.
4. End-to-end regressions recover the known exact values r_3(80)=22,
   r_3(90)=24, and r_3(100)=27 using independently verified lower witnesses,
   DRAT-to-LRAT conversion, and the formally verified cake_lpr checker.

The paper is accompanied by source code and benchmark generators at
https://github.com/memoatwit/erdos_1194 and versioned artifacts at
https://doi.org/10.5281/zenodo.20463334. A synchronized journal-submission
version of the archive will include the new formulas, solver outputs, proof
objects, hashes, model audit, and machine-readable provenance reported here.
The preprint is available as arXiv:2606.04016; it is not under consideration
at another journal.

The manuscript also reports a working hypothesis that the experiments
subsequently refuted. We retain that history because it illustrates the value
of archiving unresolved instances and rerunning them under controlled solver
and certificate pipelines.

Generative-AI use is disclosed in the manuscript. The author made all final
scientific and experimental decisions, independently checked the numerical
and mathematical claims, and takes full responsibility for the work.

Thank you for your consideration.

Sincerely,

Mehmet Ergezer  
Wentworth Institute of Technology  
ergezerm@wit.edu  
ORCID: 0000-0001-6627-3667
