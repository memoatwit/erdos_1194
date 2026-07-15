# Makefile — build the arXiv submission tarball.
#
# Usage:
#   make            — build the PDF
#   make body       — regenerate a comparison draft from the markdown sections
#   make arxiv      — produce arxiv-submission.tar.gz ready for upload
#   make clean      — drop build artifacts (keeps paper.body.tex)
#   make distclean  — drop everything regeneratable
#
# Requires: pandoc, latexmk, bibtex, tar.

PAPER       := paper
BODY_MD     := sections-concatenated.md
BODY_TEX    := paper.body.tex
GENERATED_BODY := paper.body.generated.tex
ANCDIR      := anc
ARXIV_TAR   := arxiv-submission.tar.gz
FIGURES     := figures/t1_funnel.tex \
  figures/t2_portfolio_cactus.pdf \
  figures/split_policy_ablation.pdf

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

$(GENERATED_BODY): $(BODY_MD)
	pandoc $< -o $@ \
	  --from=markdown+pipe_tables+raw_tex \
	  --to=latex \
	  --top-level-division=section \
	  --wrap=preserve
	@echo "==> wrote $(GENERATED_BODY) for comparison only"
	@echo "    $(BODY_TEX) is the maintained manuscript source and is not overwritten."

body: $(GENERATED_BODY)

$(PAPER).pdf: $(PAPER).tex $(BODY_TEX) refs.bib $(FIGURES)
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
	@cp -f ../results/N212_K44_model_audit.json $(ANCDIR)/ 2>/dev/null || true
	@cp -f ../results/split_policy_ablation_summary.json $(ANCDIR)/ 2>/dev/null || true
	@cp -f ../results/global_degree_survivor_sample100.jsonl $(ANCDIR)/ 2>/dev/null || true
	@cp -f ../results/global_degree_survivor_sample100_summary.json $(ANCDIR)/ 2>/dev/null || true
	@cp -f ../r3_model_audit.py $(ANCDIR)/ 2>/dev/null || true
	@cp -f ../ARTIFACT_REPRODUCIBILITY.md $(ANCDIR)/ 2>/dev/null || true
	@cp -f ../environment.yml $(ANCDIR)/ 2>/dev/null || true
	@cp -f ../requirements-campaign.txt $(ANCDIR)/ 2>/dev/null || true
	@mkdir -p $(ANCDIR)/known_exact_certified
	@cp -Rf ../results/baselines/known_exact_certified/N80 $(ANCDIR)/known_exact_certified/ 2>/dev/null || true
	@cp -Rf ../results/baselines/known_exact_certified/N90 $(ANCDIR)/known_exact_certified/ 2>/dev/null || true
	@cp -Rf ../results/baselines/known_exact_certified/N100 $(ANCDIR)/known_exact_certified/ 2>/dev/null || true
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
	rm -f $(BODY_MD) $(GENERATED_BODY) $(PAPER).pdf $(ARXIV_TAR)
	rm -rf $(ANCDIR)
