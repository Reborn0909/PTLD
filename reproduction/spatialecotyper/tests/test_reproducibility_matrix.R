repo_root <- normalizePath(".", mustWork = TRUE)
data_root <- "/mnt/f/spatialecotyper_reproduction"
config_path <- file.path(
  repo_root, "reproduction", "spatialecotyper", "config",
  "paper-computation-inventory.tsv"
)
result_path <- file.path(
  data_root, "results", "reproducibility", "paper-computation-matrix.tsv"
)
report_path <- file.path(
  repo_root, "docs", "reproduction",
  "spatialecotyper-reproduction-boundary.md"
)

stopifnot(file.exists(config_path), file.exists(result_path), file.exists(report_path))
config <- read.delim(config_path, stringsAsFactors = FALSE, check.names = FALSE)
x <- read.delim(result_path, stringsAsFactors = FALSE, check.names = FALSE)
required_columns <- c(
  "component_id", "component", "status", "evidence_path",
  "evidence_basis", "limitation"
)
stopifnot(all(required_columns %in% names(config)))
stopifnot(identical(config$component_id, x$component_id))
stopifnot(!anyDuplicated(x$component_id))
stopifnot(all(nzchar(x$component)), all(nzchar(x$evidence_path)))
stopifnot(all(nzchar(x$evidence_basis)), all(nzchar(x$limitation)))

allowed <- c(
  "STRICT_REPRODUCED", "TUTORIAL_REPRODUCED",
  "METHOD_ONLY", "BLOCKED_NOT_PUBLIC"
)
stopifnot(all(x$status %in% allowed))
stopifnot(all(file.exists(x$evidence_path)))

required_components <- c(
  "single_sample_discovery", "multi_sample_integration",
  "recovery_model_training", "se_specific_cell_states",
  "scst_recovery", "scrna_recovery", "bulk_deconv_training",
  "bulk_recovery", "cytospace_preprocessing", "paper_figure_generation",
  "tcga_ici_statistics", "liquid_ecotyper_training", "cfdna_prediction"
)
stopifnot(all(required_components %in% x$component_id))

liquid <- x[x$component_id == "liquid_ecotyper_training", , drop = FALSE]
stopifnot(nrow(liquid) == 1L, liquid$status == "BLOCKED_NOT_PUBLIC")
stopifnot(!any(grepl("Liquid EcoTyper", x$component, fixed = TRUE) &
                x$status == "STRICT_REPRODUCED"))
stopifnot(x$status[x$component_id == "multi_sample_integration"] ==
            "TUTORIAL_REPRODUCED")
stopifnot(grepl(
  "Spot.X/Spot.Y", x$limitation[x$component_id == "multi_sample_integration"],
  fixed = TRUE
))

message("paper reproducibility matrix: PASS")
