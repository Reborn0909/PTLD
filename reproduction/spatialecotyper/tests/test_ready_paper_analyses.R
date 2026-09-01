full_args <- commandArgs(trailingOnly = FALSE)
script_arg <- grep("^--file=", full_args, value = TRUE)
stopifnot(length(script_arg) == 1L)
test_path <- normalizePath(sub("^--file=", "", script_arg), mustWork = TRUE)
repo_root <- normalizePath(file.path(dirname(test_path), "../../.."), mustWork = TRUE)
script <- file.path(
  repo_root, "reproduction", "spatialecotyper", "scripts", "run_ready_paper_analyses.R"
)
stopifnot(file.exists(script))
source(script, local = TRUE)

ready <- data.frame(
  source_record_id = "GENERATED-GSE320042",
  readiness_class = "READY_OFFICIAL_PROCESSED",
  expression_status = "AVAILABLE",
  spatial_status = "AVAILABLE",
  stringsAsFactors = FALSE
)
panel <- data.frame(
  panel_id = "TEST:a",
  input_records = "GENERATED-GSE320042",
  official_entrypoint = "SpatialEcoTyper::DeconvoluteSE",
  expected_output = "test output",
  observed_output = "",
  status = "METHOD_ONLY",
  limitation = "contract fixture",
  stringsAsFactors = FALSE
)

ok <- validate_dispatch_row(panel[1, ], ready, namespace_exports = "DeconvoluteSE")
stopifnot(ok$eligible, ok$reason == "ELIGIBLE")

raw_only <- ready
raw_only$readiness_class <- "READY_RAW_ONLY"
stopifnot(!validate_dispatch_row(panel[1, ], raw_only, "DeconvoluteSE")$eligible)

blocked <- ready
blocked$readiness_class <- "BLOCKED_ACCESS"
stopifnot(!validate_dispatch_row(panel[1, ], blocked, "DeconvoluteSE")$eligible)

no_coordinates <- ready
no_coordinates$spatial_status <- "MISSING"
stopifnot(!validate_dispatch_row(panel[1, ], no_coordinates, "DeconvoluteSE")$eligible)

unknown <- panel
unknown$official_entrypoint <- "SpatialEcoTyper::InventedFunction"
stopifnot(!validate_dispatch_row(unknown[1, ], ready, "DeconvoluteSE")$eligible)

empty <- panel
empty$official_entrypoint <- ""
stopifnot(!validate_dispatch_row(empty[1, ], ready, "DeconvoluteSE")$eligible)

cat("ready paper analysis execution gate test: PASS\n")
