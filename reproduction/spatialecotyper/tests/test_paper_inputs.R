full_args <- commandArgs(trailingOnly = FALSE)
script_arg <- grep("^--file=", full_args, value = TRUE)
stopifnot(length(script_arg) == 1L)
test_path <- normalizePath(sub("^--file=", "", script_arg), mustWork = TRUE)
repo_root <- normalizePath(file.path(dirname(test_path), "../../.."), mustWork = TRUE)
script <- file.path(
  repo_root, "reproduction", "spatialecotyper", "scripts", "prepare_paper_inputs.R"
)
stopifnot(file.exists(script))
source(script, local = TRUE)

contract <- paper_method_contract()
public_hd <- contract[contract$input_class == "public_s8_visium_hd", , drop = FALSE]
paired_hd <- contract[contract$input_class == "generated_paired_visium_hd", , drop = FALSE]
standard <- contract[contract$input_class == "standard_visium", , drop = FALSE]
stopifnot(
  nrow(public_hd) == 1L,
  public_hd$bin_width_um == 8,
  public_hd$min_detected_genes == 20,
  public_hd$max_mito_fraction == 0.10,
  nrow(paired_hd) == 1L,
  paired_hd$bin_width_um == 16,
  paired_hd$min_detected_genes == 20,
  paired_hd$max_mito_fraction == 0.10,
  nrow(standard) == 1L,
  standard$min_detected_genes == 50,
  standard$normalization == "log2_CPM"
)

members <- c(
  "GSM1_A_tumor_scrna_cells.tsv.gz",
  "GSM1_A_tumor_scrna_counts.mtx.gz",
  "GSM1_A_tumor_scrna_genes.tsv.gz",
  "GSM1_A_tumor_scrna_logcpm.mtx.gz",
  "GSM1_A_tumor_scrna_metadata.tsv.gz",
  "GSM2_B_HD_016um_filtered_feature_bc_matrix.h5",
  "GSM2_B_HD_016um_tissue_positions.parquet.gz"
)
inventory <- build_gse_inventory(members, validate_expected = FALSE)
stopifnot(
  nrow(inventory) == length(members),
  all(inventory$modality[seq_len(5)] == "scrna"),
  all(inventory$sample_id[seq_len(5)] == "GSM1_A"),
  all(inventory$modality[6:7] == "visium_hd"),
  all(inventory$resolution_um[6:7] == 16),
  inventory$role[[2]] == "raw_counts",
  inventory$role[[4]] == "log2_cpm",
  inventory$role[[6]] == "expression_h5",
  inventory$role[[7]] == "coordinates"
)

cat("paper input contract test: PASS\n")
