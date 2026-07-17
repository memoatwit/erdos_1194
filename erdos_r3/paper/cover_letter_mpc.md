July 16, 2026

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

The revised study contains five results that I believe fit MPC's emphasis on
practical computation, comparative testing, reusable software, and
verification:

1. Six monolithic 24-hour baselines fail. A matched five-policy ablation then
   exposes a split-policy tradeoff. The emitted-cover objective is an exact
   conditioned independent-set count in the 3-AP hypergraph: global AP-degree
   reduces it from 12,582,912 to 96,847 cubes, but the surviving cubes are
   individually harder at the original CP-SAT wall cap.
2. A full two-stage CDCL survey closes 6,045 of 6,071 broad residuals
   (99.57%) with no feasible result, while 26 released instances remain as a
   sharply defined challenge tier.
3. On 20 byte-identical hard-pocket formulas run sequentially on matched AMD
   EPYC 7763 nodes, native CaDiCaL 3.0.0 and kissat 4.0.4 both close every
   instance; kissat wins all 20 pairs with a geometric-mean time ratio of
   1.477 (bootstrap 95% interval 1.332--1.655).
4. Six solve-time-stratified survivors from the alternative global-degree
   cover were independently rerun with proof logging. All six reproduce the
   survey CNF hashes, verify through DRAT-to-LRAT conversion, and are accepted
   by the formally verified cake_lpr checker. Separate end-to-end regressions
   recover the known exact values r_3(80)=22, r_3(90)=24, and r_3(100)=27
   using independently verified lower witnesses and cake_lpr-checked upper
   certificates.
5. Optimization-form HiGHS experiments show that window inequalities reduce
   the T1b node count by approximately 81% and tighten every tested LP and MIP
   upper bound to the decision threshold 44, but not below it.

The paper is accompanied by source code and benchmark generators at
https://github.com/memoatwit/erdos_1194/tree/main/erdos_r3 and versioned artifacts at
https://doi.org/10.5281/zenodo.20463334. A synchronized journal-submission
version of the archive will include the new formulas, solver outputs, proof
objects, hashes, model audit, and machine-readable provenance reported here,
including the six global-degree certificate bundles (15.71 GB DRAT and
54.96 GB LRAT in aggregate).
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
