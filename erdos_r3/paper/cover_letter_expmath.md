# Cover letter — Experimental Mathematics

Mehmet Ergezer
Wentworth Institute of Technology
550 Huntington Avenue
Boston, MA 02115, USA
ergezerm@wit.edu
ORCID: 0000-0001-6627-3667

June 10, 2026

The Editors
Experimental Mathematics

Dear Editors,

I am pleased to submit the manuscript *"Witness-split + window-cardinality
refinement for r_3(N): architecture, empirical results, and a structural hard
pocket"* for consideration in Experimental Mathematics. The preprint is posted
at arXiv:2606.04016 (https://arxiv.org/abs/2606.04016). All campaign artifacts,
including verified DRAT/LRAT proofs and the Lean encoding of the residual
problem, are deposited at Zenodo (DOI 10.5281/zenodo.21413746).

The paper describes a reproducible computational framework for upper-bound
search on r_3(N), the maximum size of a 3-term-arithmetic-progression-free
subset of [1, N]. Applied to the OEIS A003002 frontier case N = 212, K = 44,
the campaign found no feasible 44-element 3-AP-free subset of [1, 212] across
millions of CP-SAT subproblems, providing strong empirical support for the
conjectural value r_3(212) = 43 without producing a formal proof. The technical
contribution is methodological:

  1. A witness-split + window-cardinality CP-SAT architecture that is
     parametric in (N, K) and reusable for r_3(N') at adjacent N.

  2. A characterization of the structural hard pocket of the residual that
     resists CP-SAT propagation, recursive refinement, redundant Tseitin
     clauses, wall-cap extension, and HiGHS LP-relaxation MIP. A subsequent
     CDCL/SAT attack closes 18 of the 20 LP-paradigm-resistant chunks, all
     with independently verified DRAT proofs (verified by drat-trim).

  3. A genuinely paradigm-resistant residual T1c, of size 2, that survives
     CP-SAT, HiGHS, pure CDCL at a 12-hour wall, and CDCL with windowed
     cardinality at a 4-hour wall. T1c is released both as JSONL solver
     instances and as a Lean 4 formal-proof-search encoding compatible with
     AlphaProof Nexus-style EVOLVE-BLOCK conventions.

I believe Experimental Mathematics is the natural venue for this work. The
campaign is squarely within the journal's stated scope: an experimental and
reproducibility-focused investigation of a frontier integer-sequence value,
with a release-grade dataset of verified machine-checkable certificates, an
honestly negative methodological result (no value of r_3(212) is proved), and
a precise open problem framed for follow-on attack. The paper would benefit
from review by specialists in additive combinatorics, constraint solving, and
formal verification.

The work is not under consideration at another journal. The preprint
arXiv:2606.04016 was posted to establish a citable timestamp; this is standard
practice for the field and consistent with Experimental Mathematics' position
on preprints.

# Disclosure of generative-AI use

In accordance with the Taylor & Francis AI Policy:

Generative AI tools (Anthropic Claude Sonnet 4.5 / Claude Opus 4.6, accessed
via the Claude Code agent interface during 2026; and OpenAI Codex, GPT-5,
accessed via the Codex agent interface during 2026) were used during the
preparation of this manuscript. The use was as follows:

  * Drafting and revision assistance for the manuscript sections. The
    author provided the campaign data, the technical results, the empirical
    interpretation, and the headline framing decisions. The AI tool was used
    to draft initial section text from author-provided notes, propose
    structural improvements (subsection ordering, transition phrasing,
    benchmark-tier organization), and run consistency sweeps for numbers
    and cross-references across drafts. Every claim in the final manuscript
    was reviewed, verified, and either accepted, edited, or rejected by the
    author.

  * Drafting assistance for repository scaffolding (build scripts,
    bibliography seed, LaTeX driver, ancillary-file packaging), including
    the preparation of journal-submission support files. All code was
    reviewed and the build outputs were verified by the author before
    submission.

  * Computational orchestration assistance during the campaign (Unity
    SLURM scripts, results aggregation, proof-verification wrappers).
    The mathematical content of the campaign and all solver-paradigm,
    encoding, and bound design decisions were made by the author.

The AI tools did not generate mathematical claims, did not select or run the
underlying computational experiments without author direction, and did not
serve as authors. All mathematical conclusions, the campaign design, the
formal-conjecture framing, and the manuscript's central scientific argument
are the author's own.

The author confirms that the manuscript complies in full with the Taylor &
Francis AI Policy.

# Suggested reviewers

The following specialists are well-positioned to review the manuscript:

  * Thomas F. Bloom, University of Manchester
    (expert on density-increment methods for r_3 and Erdős upper-bound
    problems; maintains erdosproblems.com).

  * Marijn J. H. Heule, Carnegie Mellon University
    (expert on DRAT/LRAT proof certificates and drat-trim; would be
    well-placed to assess the verification chain).

  * Lorenzo Cariboni
    (maintains the OEIS A003002 b-file at the current frontier; the natural
    expert on the prior numerical record).

  * Olof Sisask, Stockholm University
    (additive combinatorics; co-author of the Bloom-Sisask density-increment
    framework cited in the manuscript).

# Data and reproducibility

All data, code, verified proofs, and the Lean formalization required to
reproduce the campaign and verify every certificate-track claim are available
under open license at:

  * Preprint: arXiv:2606.04016
  * Dataset: 10.5281/zenodo.21413746 (CC-BY)

I look forward to the editor's response and the reviewers' comments.

Sincerely,

Mehmet Ergezer
Wentworth Institute of Technology
