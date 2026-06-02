# Makefile — build the arXiv submission tarball.
#
# Usage:
#   make            — build the PDF
#   make body       — regenerate paper.body.tex from the markdown sections
#   make arxiv      — produce arxiv-submission.tar.gz ready for upload
#   make clean      — drop build artifacts (keeps paper.body.tex)
#   make distclean  — drop everything regeneratable
#
# Requires: pandoc, latexmk, bibtex, tar.

PAPER       := paper
BODY_MD     := sections-concatenated.md
BODY_TEX    := paper.body.tex
ANCDIR      := anc
ARXIV_TAR   := arxiv-submission.tar.gz

# Source section files in the parent directory.
SECTION_MDS := \
  ../WRITEUP_SECTION_1.md \
  ../WRITEUP_SECTION_2.md \
  ../WRITEUP_SECTION_3.md \
  ../WRITEUP_SECTION_4.md \
  ../WRITEUP_SECTION_5.md \
  ../WRITEUP_SECTION_6.md

.PHONY: all body arxiv clean distclean

all: $(PAPER).pdf

# Concatenate the section markdown files; pandoc to LaTeX body.
$(BODY_MD): $(SECTION_MDS)
	awk 'FNR==1 && NR!=1 { print "" } { print }' $^ > $@

$(BODY_TEX): $(BODY_MD)
	pandoc $< -o $@ \
	  --from=markdown+pipe_tables+raw_tex \
	  --to=latex \
	  --top-level-division=section \
	  --wrap=preserve
	@echo "WARNING: hand-edit $(BODY_TEX) — see ARXIV_SUBMISSION.md §2 for the"
	@echo "         specific markdown→LaTeX fixups (math typography, cross-refs, etc.)."

body: $(BODY_TEX)

$(PAPER).pdf: $(PAPER).tex $(BODY_TEX) refs.bib
	latexmk -pdf -interaction=nonstopmode $(PAPER).tex

# Pack the arXiv tarball: sources + ancillary files.
arxiv: $(PAPER).pdf
	@mkdir -p $(ANCDIR)
	@echo "==> assembling ancillary files in $(ANCDIR)/"
	@cp -f ../results/N212_K43_witness.json $(ANCDIR)/ 2>/dev/null || true
	@cp -f ../results/N212_K44_force_endpoints.json $(ANCDIR)/ 2>/dev/null || true
	@cp -f ../results/N212_K44_t1a25.jsonl $(ANCDIR)/ 2>/dev/null || true
	@cp -f ../results/N212_K44_t1b_minus_t1c.jsonl $(ANCDIR)/ 2>/dev/null || true
	@cp -f ../results/N212_K44_t1c2.jsonl $(ANCDIR)/ 2>/dev/null || true
	@cp -f ../results/N212_K44_window100k_unknowns.jsonl $(ANCDIR)/ 2>/dev/null || true
	@cp -f ../results/b003002.txt $(ANCDIR)/ 2>/dev/null || true
	@mkdir -p $(ANCDIR)/lean
	@cp -f ../lean/R3Base.lean $(ANCDIR)/lean/
	@cp -f ../lean/R3_212_Witness.lean $(ANCDIR)/lean/
	@cp -f ../lean/R3_T1c_40959.lean $(ANCDIR)/lean/
	@cp -f ../lean/R3_T1c_48895.lean $(ANCDIR)/lean/
	@cp -f ../lean/README.md $(ANCDIR)/lean/
	@du -sh $(ANCDIR)/
	tar czf $(ARXIV_TAR) \
	  $(PAPER).tex $(BODY_TEX) refs.bib \
	  figures/ \
	  $(ANCDIR)/
	@echo "==> wrote $(ARXIV_TAR)"
	@ls -lh $(ARXIV_TAR)

clean:
	latexmk -C $(PAPER).tex 2>/dev/null || true
	rm -f $(PAPER).aux $(PAPER).log $(PAPER).out $(PAPER).bbl $(PAPER).blg
	rm -f $(PAPER).fls $(PAPER).fdb_latexmk $(PAPER).toc

distclean: clean
	rm -f $(BODY_MD) $(BODY_TEX) $(PAPER).pdf $(ARXIV_TAR)
	rm -rf $(ANCDIR)
