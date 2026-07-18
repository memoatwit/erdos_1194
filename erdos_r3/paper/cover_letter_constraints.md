# Cover letter - Constraints

Mehmet Ergezer
Wentworth Institute of Technology
550 Huntington Avenue, Boston, MA 02115, USA
ergezerm@wit.edu | ORCID: 0000-0001-6627-3667

July 18, 2026

The Editors
*Constraints*

Dear Editors,

Please consider the manuscript **"Salem--Spencer sets as a
constraint-solving benchmark: decomposition, certification, and split-policy
effects at r_3(212)"** for publication in *Constraints*.

The manuscript studies a natural finite-domain feasibility family at the
frontier of OEIS A003002. It does not claim to resolve r_3(212). Instead, it
develops and evaluates a reproducible constraint-solving methodology that
combines implied window-cardinality constraints, deterministic cube
decomposition, controlled solver comparisons, and independently checkable
infeasibility certificates.

The main contributions for the constraint-programming community are:

1. A witness-informed CP-SAT architecture in which valid window-cardinality
   constraints reduce the controlled unresolved rate by about 28 percentage
   points, substantially more than the generic search interventions tested.
2. A matched five-policy split ablation and independent exhaustive cover
   audit that quantify a cover-size versus conquer-cost tradeoff. Global
   AP-degree reduces the complete depth-24 cover from 12,582,912 to 96,847
   cubes, but produces harder survivors under the historical CP-SAT cap.
3. Controlled configuration-level comparisons on released formulas. Native
   CaDiCaL 3.0.0 and kissat 4.0.4 close all 20 hard-pocket instances on
   matched hardware; a two-stage CDCL survey closes 6,045 of 6,071 broad
   residuals and leaves a compact 26-instance challenge tier.
4. A certificate and regression pipeline. Selected closures yield LRAT
   certificates accepted by the formally verified cake_lpr checker, while
   end-to-end tests recover the known exact values r_3(80)=22, r_3(90)=24,
   and r_3(100)=27 from independently checked lower and upper evidence.

The released benchmark is intended for research on decomposition,
problem-specific implied constraints, search configuration, empirical
hardness, and auditable constraint solving. It includes deterministic
generators, tiered JSONL and CNF instances, matched solver outputs, model and
cover audits, proof objects, hashes, and machine-readable provenance.

Source code and compact artifacts are available in the
[tagged GitHub snapshot](https://github.com/memoatwit/erdos_1194/tree/constraints-submission-v1.5/erdos_r3).
The versioned dataset is archived on
[Zenodo](https://doi.org/10.5281/zenodo.21413746), and the preprint is
available as [arXiv:2606.04016](https://arxiv.org/abs/2606.04016).
ARTIFACT_REPRODUCIBILITY.md maps the principal claims to
their data and reproduction commands; the N=80 exact-value regression is the
fastest complete check and runs in minutes on a workstation. The manuscript
is not under consideration elsewhere.

Generative-AI use is disclosed in the manuscript. The author made all final
scientific and experimental decisions, reviewed the generated text and code,
independently checked the reported claims, and takes full responsibility for
the work. The author declares no competing interests.

Thank you for your consideration.

Sincerely,

Mehmet Ergezer
Wentworth Institute of Technology
ergezerm@wit.edu
ORCID: 0000-0001-6627-3667
