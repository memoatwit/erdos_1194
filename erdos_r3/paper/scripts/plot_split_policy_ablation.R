#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2) {
  stop("usage: plot_split_policy_ablation.R SUMMARY_JSON OUTPUT_PDF")
}

data <- jsonlite::fromJSON(args[[1]], simplifyVector = FALSE)
summaries <- data$policy_summaries
keys <- c(
  "deployed_witness_numeric",
  "witness_degree",
  "witness_random",
  "global_degree",
  "global_random"
)
labels <- c("W-num", "W-deg", "W-rand", "G-deg", "G-rand")

survivors <- vapply(
  keys,
  function(key) summaries[[key]]$exact_prefix_enumeration$survivors,
  numeric(1)
)
statuses <- c("PRUNED_PREFIX_AP", "INFEASIBLE", "UNKNOWN")
outcomes <- vapply(
  keys,
  function(key) {
    counts <- summaries[[key]]$statuses
    vapply(statuses, function(status) {
      value <- counts[[status]]
      if (is.null(value)) 0 else value
    }, numeric(1))
  },
  numeric(length(statuses))
)

pdf(args[[2]], width = 7.0, height = 3.0, family = "serif", useDingbats = FALSE)
layout(matrix(c(1, 2, 3, 3), nrow = 2, byrow = TRUE), heights = c(5.4, 0.7))
par(mar = c(3.2, 4.2, 2.1, 0.7), mgp = c(2.3, 0.7, 0), tcl = -0.25)

mids <- barplot(
  survivors,
  names.arg = rep("", length(labels)),
  log = "y",
  ylim = c(5e4, 4e7),
  col = "#4C78A8",
  border = NA,
  ylab = "Exact surviving cubes (log scale)",
  main = "(a) Complete depth-24 cover",
  axes = FALSE,
  cex.names = 0.78,
  cex.axis = 0.8,
  cex.lab = 0.85,
  cex.main = 0.9
)
axis(2, at = c(1e5, 1e6, 1e7), labels = c("100k", "1m", "10m"), las = 1, cex.axis = 0.8)
abline(h = c(1e5, 1e6, 1e7), col = "#D9D9D9", lwd = 0.6)
axis(1, at = mids, labels = labels, tick = FALSE, cex.axis = 0.75)
text(mids, survivors * 1.13, format(survivors, big.mark = ",", scientific = FALSE), cex = 0.58)
box(bty = "l")

par(mar = c(3.2, 4.2, 2.1, 0.7), mgp = c(2.3, 0.7, 0), tcl = -0.25)
mids2 <- barplot(
  outcomes / 5,
  names.arg = rep("", length(labels)),
  ylim = c(0, 100),
  col = c("#4C78A8", "#59A14F", "#E15759"),
  border = NA,
  ylab = "Matched raw assignments (%)",
  main = "(b) Matched sample (n = 500)",
  axes = FALSE,
  cex.names = 0.78,
  cex.axis = 0.8,
  cex.lab = 0.85,
  cex.main = 0.9
)
axis(2, at = seq(0, 100, 20), labels = paste0(seq(0, 100, 20), "%"), las = 1, cex.axis = 0.8)
abline(h = seq(0, 100, 20), col = "#D9D9D9", lwd = 0.6)
axis(1, at = mids2, labels = labels, tick = FALSE, cex.axis = 0.75)
box(bty = "l")

par(mar = c(0, 0, 0, 0))
plot.new()
legend(
  "center",
  horiz = TRUE,
  bty = "n",
  fill = c("#4C78A8", "#59A14F", "#E15759"),
  legend = c("Prefix-pruned", "CP-SAT infeasible", "CP-SAT unknown"),
  cex = 0.76
)

dev.off()
