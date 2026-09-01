paper_method_contract <- function() {
  data.frame(
    input_class = c(
      "standard_visium", "public_s8_visium_hd", "generated_paired_visium_hd",
      "public_xenium"
    ),
    bin_width_um = c(55, 8, 16, NA_real_),
    min_detected_genes = c(50L, 20L, 20L, 20L),
    max_mito_fraction = c(0.10, 0.10, 0.10, 0.10),
    normalization = c("log2_CPM", "paper_Seurat_workflow", "log2_CPM", "paper_Seurat_workflow"),
    method_scope = c(
      "bulk ST and paired tumour analyses",
      "public single-cell-scale validation and colocalization",
      "study-generated tumour-plasma paired deconvolution",
      "public single-cell validation"
    ),
    stringsAsFactors = FALSE
  )
}

member_role <- function(member) {
  patterns <- c(
    "_tumor_scrna_cells.tsv.gz$" = "cell_ids",
    "_tumor_scrna_counts.mtx.gz$" = "raw_counts",
    "_tumor_scrna_genes.tsv.gz$" = "gene_ids",
    "_tumor_scrna_logcpm.mtx.gz$" = "log2_cpm",
    "_tumor_scrna_metadata.tsv.gz$" = "cell_metadata",
    "_filtered_feature_bc_matrix.h5$" = "expression_h5",
    "_visium_seuratobj.rds$" = "seurat_object",
    "_HD_016um_seuratobj.rds$" = "seurat_object",
    "_tissue_positions.csv.gz$" = "coordinates",
    "_tissue_positions.parquet.gz$" = "coordinates",
    "_scalefactors_json.json.gz$" = "scale_factors",
    "_aligned_fiducials.jpg.gz$" = "fiducial_image",
    "_tissue_hires_image.png.gz$" = "hires_image",
    "_tissue_lowres_image.png.gz$" = "lowres_image"
  )
  result <- rep("UNKNOWN", length(member))
  for (pattern in names(patterns)) {
    result[grepl(pattern, member)] <- unname(patterns[[pattern]])
  }
  result
}

member_sample_id <- function(member) {
  result <- sub("_tumor_scrna_.*$", "", member)
  result <- sub("_HD_016um_.*$", "", result)
  result <- sub(
    "_(aligned_fiducials|filtered_feature_bc_matrix|scalefactors_json|tissue_hires_image|tissue_lowres_image|tissue_positions|visium_seuratobj).*$",
    "", result
  )
  result
}

build_gse_inventory <- function(members, validate_expected = TRUE) {
  stopifnot(length(members) > 0L, !anyDuplicated(members))
  modality <- ifelse(
    grepl("_tumor_scrna_", members), "scrna",
    ifelse(grepl("_HD_016um_", members), "visium_hd", "visium")
  )
  inventory <- data.frame(
    member = members,
    sample_id = member_sample_id(members),
    modality = modality,
    resolution_um = ifelse(modality == "visium_hd", 16, NA_real_),
    role = member_role(members),
    stringsAsFactors = FALSE
  )
  if (validate_expected) {
    spatial_ids <- unique(inventory$sample_id[inventory$modality %in% c("visium", "visium_hd")])
    scrna_ids <- unique(inventory$sample_id[inventory$modality == "scrna"])
    hd_ids <- unique(inventory$sample_id[inventory$modality == "visium_hd"])
    stopifnot(
      nrow(inventory) == 154L,
      length(scrna_ids) == 7L,
      length(spatial_ids) == 17L,
      length(hd_ids) == 2L,
      !any(inventory$role == "UNKNOWN")
    )
  }
  inventory
}

sha256_file <- function(path) {
  output <- system2("sha256sum", shQuote(path), stdout = TRUE, stderr = TRUE)
  status <- attr(output, "status")
  if (!is.null(status) && status != 0L) stop(paste(output, collapse = "\n"))
  sub("[[:space:]].*$", "", output[[1]])
}

write_tsv <- function(value, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  write.table(value, path, sep = "\t", quote = FALSE, row.names = FALSE, na = "")
}

main <- function() {
  args <- commandArgs(trailingOnly = TRUE)
  data_root <- if (length(args)) args[[1]] else "/mnt/f/spatialecotyper_reproduction"
  archive <- file.path(data_root, "raw", "gse320042", "GSE320042_RAW.tar")
  stopifnot(file.exists(archive), file.info(archive)$size == 4936970240)
  members <- system2("tar", c("-tf", shQuote(archive)), stdout = TRUE, stderr = TRUE)
  status <- attr(members, "status")
  if (!is.null(status) && status != 0L) stop(paste(members, collapse = "\n"))
  inventory <- build_gse_inventory(members, validate_expected = TRUE)
  inventory$source_archive <- archive
  inventory$source_tar_sha256 <- sha256_file(archive)
  result_dir <- file.path(data_root, "work", "paper_inputs")
  write_tsv(inventory, file.path(result_dir, "gse320042-input-files.tsv"))
  write_tsv(paper_method_contract(), file.path(result_dir, "paper-method-contract.tsv"))
  cat(sprintf(
    "paper input inventory: PASS members=%d scrna_samples=%d spatial_samples=%d hd16_samples=%d\n",
    nrow(inventory),
    length(unique(inventory$sample_id[inventory$modality == "scrna"])),
    length(unique(inventory$sample_id[inventory$modality %in% c("visium", "visium_hd")])),
    length(unique(inventory$sample_id[inventory$modality == "visium_hd"]))
  ))
}

if (sys.nframe() == 0L) main()
