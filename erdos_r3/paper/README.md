# Paper build directory

LaTeX source for the arXiv preprint.

Submission snapshot: [`mpc-submission-v1.2`](https://github.com/memoatwit/erdos_1194/tree/mpc-submission-v1.2/erdos_r3/paper)

## Contents

```
paper.tex      driver: preamble, frontmatter, \input{paper.body.tex},
               bibliography setup
refs.bib       bibliography (seed; verify entries before submission)
Makefile       build rules: PDF, body regen from markdown, arXiv tarball
README.md      this file
anc/           arXiv ancillary files (populated by `make arxiv`)
```

`paper.body.tex` is the maintained manuscript source. The Markdown section
files are retained as drafting history and no longer reproduce all later
LaTeX edits. `make body` writes `paper.body.generated.tex` for comparison and
does not overwrite the maintained body.

## Build

Quick check that the toolchain is available:

```bash
which pandoc latexmk bibtex tar
```

Full build:

```bash
make              # compile the maintained LaTeX source

# Optional drafting comparison only:
make body         # markdown -> paper.body.generated.tex
```

To produce the arXiv submission tarball:

```bash
make arxiv
# -> arxiv-submission.tar.gz
```

## arXiv ancillary files

`make arxiv` populates `anc/` with:

- The verified 43-element witness and endpoint-forcing JSONs.
- The four tiered-benchmark JSONLs (T1a, T1b ∖ T1c, T1c, T2).
- The OEIS A003002 b-file used for window-cardinality bounds.
- The Lean encoding (R3Base.lean, R3_212_Witness.lean,
  R3_T1c_{40959,48895}.lean, README.md).

The DRAT/LRAT proofs (~100 GB combined) are too large for arXiv
ancillary; they are released separately. See `ARXIV_SUBMISSION.md` §3
for the Zenodo plan.

## Pre-submission checklist

See `../ARXIV_SUBMISSION.md` for the full checklist. The high-leverage
items:

1. Hand-edit `paper.body.tex` for math typography (`$r_3(N)$` etc.),
   pandoc-emitted longtable → tabularx where appropriate, and
   cross-reference labels.
2. Verify every bib entry against the actual source (years, DOIs,
   arXiv IDs).
3. Add a figure for the T1 → T1a / T1b / T1c funnel.
4. Final numbers consistency sweep — make sure no stale 12/17 or
   11/17 verification counts survive; the audited final is 18/18.
5. Confirm author list, affiliations, ORCIDs, funding statement.
6. Test the tarball on a clean machine.

## Notes

- We use `amsart` (not `article`) since the natural venue family is
  math.CO. Switch to `article` only if a journal requires it later.
- `unicode-math` lets us write `≥` and `∖` literally in source; if
  pandoc emits them as Unicode, they should compile under LuaLaTeX or
  XeLaTeX. If staying on pdflatex, replace with `\geq` and
  `\setminus`.
- The `T1a`, `T1b`, `T1c` macros (`\Tonea` etc.) are defined in
  `paper.tex` so the tier names render consistently throughout.
