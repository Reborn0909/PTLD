source_lock <- read.delim(
  "reproduction/spatialecotyper/config/source-lock.tsv",
  check.names = FALSE,
  stringsAsFactors = FALSE
)

value_for <- function(key) {
  values <- source_lock$value[source_lock$key == key]
  stopifnot(length(values) == 1L)
  values
}

stopifnot(
  value_for("git_commit") ==
    "48c2c846781d3a312771021c1a2ef5fc383700c5",
  value_for("package_version") == "1.0.2",
  value_for("r_version") == "4.4.1",
  value_for("seurat_version") == "5.1.0",
  value_for("matrix_version") == "1.7-0",
  value_for("nmf_version") == "0.28",
  value_for("geo_accession") == "GSE320042"
)

tutorial_order <- read.delim(
  "reproduction/spatialecotyper/config/tutorial-order.tsv",
  stringsAsFactors = FALSE
)
stopifnot(identical(tutorial_order$order, 1:8))
stopifnot(identical(
  tutorial_order$rmd,
  c(
    "SingleSample.Rmd",
    "Integration.Rmd",
    "TrainRecoveryModel.Rmd",
    "Discovery_SE_CellStates.Rmd",
    "Recovery_scST.Rmd",
    "Recovery_scRNA.Rmd",
    "TrainDeconvModel.Rmd",
    "Recovery_Bulk.Rmd"
  )
))

message("source lock and tutorial order: PASS")
