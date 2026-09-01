full_args <- commandArgs(trailingOnly = FALSE)
script_arg <- grep("^--file=", full_args, value = TRUE)
stopifnot(length(script_arg) == 1L)
test_path <- normalizePath(sub("^--file=", "", script_arg), mustWork = TRUE)
repo_root <- normalizePath(file.path(dirname(test_path), "../../.."), mustWork = TRUE)
script <- file.path(
  repo_root, "reproduction", "spatialecotyper", "scripts", "run_paper_reproduction.R"
)
stopifnot(file.exists(script), requireNamespace("Matrix", quietly = TRUE))
source(script, local = TRUE)

counts <- Matrix::Matrix(
  matrix(c(1, 3, 0, 2), nrow = 2,
         dimnames = list(c("A", "B"), c("spot1", "spot2"))),
  sparse = TRUE
)
observed <- normalize_log2_cpm(counts)
expected <- log2(sweep(as.matrix(counts), 2, Matrix::colSums(counts), "/") * 1e6 + 1)
stopifnot(
  inherits(observed, "sparseMatrix"),
  identical(dimnames(observed), dimnames(counts)),
  max(abs(as.matrix(observed) - expected)) < 1e-10
)

fractions <- matrix(
  c(0.2, 0.8, 0.6, 0.4), nrow = 2, byrow = TRUE,
  dimnames = list(c("spot1", "spot2"), c("SE1", "SE2"))
)
weighted <- aggregate_se_weighted(fractions, c(spot1 = 1, spot2 = 3))
stopifnot(max(abs(weighted - c(SE1 = 0.5, SE2 = 0.5))) < 1e-12)
gap <- aggregation_contract(NULL)
stopifnot(gap$status == "METHOD_GAP", grepl("CytoSPACE", gap$reason, fixed = TRUE))
stopifnot(
  paper_patient_id("GSM9532657_WU1384_1") == "WU1384",
  paper_patient_id("GSM9532667_YUADD") == "YUADD"
)

body_text <- paste(deparse(body(run_one_sample)), collapse = "\n")
stopifnot(grepl("SpatialEcoTyper::DeconvoluteSE", body_text, fixed = TRUE))

cat("paper reproduction contract test: PASS\n")
