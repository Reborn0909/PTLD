full_args <- commandArgs(trailingOnly = FALSE)
script_arg <- grep("^--file=", full_args, value = TRUE)
stopifnot(length(script_arg) == 1L)
test_path <- normalizePath(sub("^--file=", "", script_arg), mustWork = TRUE)
repo_root <- normalizePath(file.path(dirname(test_path), "../../.."), mustWork = TRUE)
script <- file.path(
  repo_root, "reproduction", "spatialecotyper", "scripts", "audit_gse320042_objects.R"
)
stopifnot(file.exists(script), requireNamespace("SeuratObject", quietly = TRUE))
source(script, local = TRUE)

counts <- matrix(
  c(1, 2, 1, 1, 1, 1), nrow = 3,
  dimnames = list(c("A", "B", "MT-C"), c("bin1", "bin2"))
)
object <- SeuratObject::CreateSeuratObject(counts = counts, assay = "Spatial")
object[["row"]] <- c(1, 2)
object[["col"]] <- c(3, 4)
object[["X"]] <- c(10, 20)
object[["Y"]] <- c(30, 40)
object[["percent.mt"]] <- c(5, 9)
summary <- summarize_seurat_object(
  object, "GSM1_A_HD_016um_seuratobj.rds", min_genes = 2,
  max_mito_percent = 10, compute_sha = FALSE
)
stopifnot(
  summary$sample_id == "GSM1_A",
  summary$modality == "visium_hd",
  summary$resolution_um == 16,
  summary$genes == 3,
  summary$locations == 2,
  summary$below_gene_threshold == 0,
  summary$above_mito_threshold == 0,
  summary$qc_contract == "PASS",
  grepl("counts", summary$layers, fixed = TRUE)
)

cat("GSE object audit test: PASS\n")
