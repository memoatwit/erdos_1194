# arXiv submission plan

Target: arXiv preprint, math.CO primary, cs.DM and cs.LO secondary.

This document is a single-pass checklist for converting `WRITEUP_DRAFT.md`
into a publishable arXiv preprint. Skip any item already done.

---

## 1. Identity and metadata

- [ ] **Title.** Current working title:
      *"Witness-split + window-cardinality refinement for r_3(N):
      architecture, empirical results, and a structural hard pocket."*
      Consider shortening; arXiv listings truncate at ~120 chars.

- [ ] **Author list.** Single-author or multi-author? Confirm order, ORCID,
      affiliation, contact email. Mehmet Ergezer (Wentworth Institute of
      Technology) at minimum.

- [ ] **MSC 2020 codes.** Suggested:
      - `11B25` Arithmetic progressions (primary)
      - `11Y16` Algorithms; complexity (computational number theory)
      - `68W30` Symbolic computation and algebraic computation
      - `68V20` Formalization in mathematics
      - `90C10` Integer programming (for the HiGHS / CP-SAT framing)

- [ ] **ACM Computing Classification System (optional secondary).**
      - `G.2.1` Combinatorics
      - `F.4.1` Mathematical Logic (for SAT/CDCL)
      - `I.2.3` Deduction and Theorem Proving

- [ ] **arXiv categories.**
      - Primary: `math.CO`
      - Secondary: `cs.DM` (Discrete Math)
      - Optional tertiary: `cs.LO` (Logic in CS — justified by the
        DRAT/LRAT certificate release and the Lean encoding)

- [ ] **arXiv "Comments" field** (the metadata line, not the paper body).
      Format: `X pages, Y figures, Z tables; ancillary files: JSONL
      benchmarks, verified DRAT summaries, Lean encoding. Source code at
      https://github.com/memoatwit/erdos_1194/tree/mpc-submission-v1.2/erdos_r3.`

- [ ] **License.** Default to CC-BY 4.0 unless an institutional contract
      requires otherwise. arXiv perpetual non-exclusive is the minimum.

---

## 2. Manuscript conversion

The writeup is in markdown across `WRITEUP_SECTION_{1..6}.md` + abstract.
Convert to LaTeX with the following workflow.

- [ ] **Pandoc first pass.** From the repo root:
      ```
      pandoc paper/sections-concatenated.md \
        -o paper/paper.body.tex \
        --to=latex --top-level-division=section --wrap=preserve
      ```
      The output is a near-clean LaTeX body. Pandoc handles
      headings, lists, tables, code blocks, blockquotes, and math
      reasonably; expect to hand-fix:
      - `\section{}` numbering (drop pandoc's auto numbering if any)
      - Inline math: the markdown uses backticked Unicode (`r_3(N)`,
        `≥`, `∖`, etc.) — convert to `$r_3(N)$`, `$\geq$`, `$\setminus$`
      - Tables: pandoc emits `longtable` by default; consider `tabularx`
        for the §3.1 / §5.2 layouts
      - Cross-references: section refs (`§4.3`, `§5.2`) become `\S\ref{...}`
        once labels are in place

- [ ] **`paper/paper.tex` (driver).** Skeleton provided in this repo.
      Imports the body, sets up frontmatter, bibliography, ancillary
      file declarations. Already initialized.

- [ ] **`paper/refs.bib`.** Bibliography seed provided. Add entries
      as needed:
      - Roth 1953 (existing)
      - Behrend 1946 (existing)
      - Bloom-Sisask 2020/2023 (existing)
      - Kelley-Meka 2023 (existing)
      - OEIS A003002 / Cariboni b-file (existing — verify URL)
      - Tsoukalas et al. AlphaProof Nexus arXiv:2605.22763 (existing)
      - PySAT (Ignatiev-Morgado-Marques-Silva 2018) (existing)
      - CaDiCaL / Kissat (Biere) (existing)
      - drat-trim (Heule-Hunt-Biere) (existing)
      - LRAT (Cruz-Filipe et al.) (existing)
      - Lean / Mathlib (Mathlib community) (existing)
      - HiGHS (Huangfu-Hall) (existing)
      - OR-Tools / CP-SAT (Google) (existing)

- [ ] **Figures.** If the writeup currently has none, add at least:
      - The T1 → T1a / T1b / T1c funnel as a labeled flow diagram
        (tikz or a vector PDF). One figure is enough.
      - Optionally: a histogram of HiGHS dual bounds across T1
        (separates T1a's dual=inf from T1b's dual=0.0). Nice but not
        essential.

- [ ] **Algorithm boxes.** §2 describes five components; render at
      least the broad-split + AP-prefix-pruning loop as a
      `\begin{algorithm}` for readability.

- [ ] **Notation table.** Optional but appreciated by reviewers — one
      page at the front mapping `T1`, `T1a`, `T1b`, `T1c`, `N`, `K`,
      `d`, the chunk-ID encoding, etc.

---

## 3. Ancillary materials and reproducibility

arXiv accepts ancillary files but they must stay small (each file
ideally < 6 MB, total < 50 MB). The verified DRAT proofs, available
LRAT artifacts, and solver logs are huge (>100 GB combined) and do
not fit. Plan:

- [ ] **arXiv ancillary directory `anc/`.** Include only the small
      benchmark JSONL files plus the Lean encoding:
      ```
      anc/N212_K43_witness.json
      anc/N212_K44_force_endpoints.json
      anc/N212_K44_t1a25.jsonl
      anc/N212_K44_t1b_minus_t1c.jsonl
      anc/N212_K44_t1c2.jsonl
      anc/N212_K44_window100k_unknowns.jsonl
      anc/b003002.txt
      anc/lean/   (R3Base, R3_212_Witness, R3_T1c_{40959,48895})
      anc/README.md
      ```
      Total estimated size: ~20 MB.

- [x] **External hosting for the proof artifacts.** The DRAT proofs, available
      LRAT artifacts, scratch CNFs, solver logs, and SLURM scripts go on
      Zenodo at <https://doi.org/10.5281/zenodo.20463334>. Tag the upload
      as `r_3-212-campaign-v1` with the arXiv preprint ID once it assigns.
      The dataset README is provided at `zenodo/README.md`.

- [x] **Repository link in §5.5.** Add a paragraph naming the Zenodo
      DOI (or GitHub release) and the SHA256s of the top-level proof
      files. Reviewers must be able to verify the certificate claim
      end-to-end from the released artifacts.

- [ ] **Reproducibility statement.** Brief paragraph in §5.5 listing
      the OR-Tools / HiGHS / CaDiCaL / Kissat / drat-trim versions
      used. Pin the Unity Python environment (path is already
      documented in SESSION_HANDOFF.md).

---

## 4. Funding and acknowledgments

- [ ] **Cluster acknowledgment.** UMass Unity SLURM cluster, account
      `pi_ergezerm_wit_edu`. Confirm with Wentworth IT whether they
      require a specific acknowledgment text.

- [ ] **Funding.** NSF / institutional grants? Add to the
      acknowledgments block.

- [ ] **Co-author or collaborator acknowledgments.** AlphaProof Nexus
      team for the EVOLVE-BLOCK convention; whoever helped on the
      Lean side; the original OEIS A003002 maintainers.

---

## 5. Final preflight

- [ ] **Spell-check + LaTeX compile in a clean environment.**
      `latexmk -pdf paper.tex` should produce 0 errors / 0 warnings
      beyond the standard "Overfull \hbox" and "Reference XYZ
      undefined on first pass."

- [ ] **Numbers consistency sweep.** Final pass on the audited tally:
      ```
      T1a    = 25     (HiGHS 8h INFEASIBLE, dual=inf)
      T1b    = 20     (HiGHS 8h UNKNOWN, dual=0.0)
      T1b\T1c = 18    (CDCL UNSAT in first run)
      T1c    =  2     (40959, 48895; resistant to four paradigms)

      DRAT proofs emitted: 18 / 18
      drat-trim VERIFIED:  18 / 18
      ```
      Search every section for stale intermediate certificate phrasing such as
      `12 / 17`, `11 / 17`, `15 / 18`, `17 emitted`, or `verification TIMEOUT`
      and update.

- [ ] **Cross-reference checklist.** Every `§X.Y` reference resolves to
      a labeled section. Every `[citation]` resolves to a bib entry.
      Every `T1a` / `T1b` / `T1c` mention agrees with the §5.2 tier
      table.

- [ ] **Reviewer-facing reproducibility one-liner.** Each major
      empirical claim should cite either a JSONL file or a Zenodo
      artifact path. The "0 FEASIBLE rows across millions of
      subproblems" claim needs a specific reference to the aggregated
      log file.

- [ ] **PDF preview on a clean machine.** Open the compiled PDF on a
      non-author machine to check no fonts are missing, no images
      are broken, no overfull boxes mar readability.

- [ ] **Final author-internal review.** One last full read by a
      collaborator who has not been working on the campaign daily —
      they will catch the things we've stopped seeing.

---

## 6. Submission

- [ ] arXiv upload via web interface. Choose `math.CO` as primary at
      the category step.
- [ ] Once arXiv assigns the preprint ID, edit the Zenodo entry's
      "Related identifiers" field to point at the arXiv ID. The two
      become permanently cross-referenced.
- [ ] Email a copy to relevant follow-on collaborators (AlphaProof
      Nexus team if upstreaming to formal-conjectures; OEIS A003002
      maintainers).
- [ ] Post on relevant venues (Discord, Mastodon, Twitter,
      Combinatorics mailing list) once the arXiv ID is live.

---

## Notes

The submission target is the arXiv preprint, not a journal. After
preprint posting, the natural next venue is **Experimental
Mathematics** for the math-side paper and **SAT 2027** for a separate
SAT-side paper focused on the CDCL-vs-LP paradigm-invariance result.
Plan those separately; this checklist is for the arXiv stage only.
