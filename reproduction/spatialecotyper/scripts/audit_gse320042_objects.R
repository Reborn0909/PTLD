object_sample_id <- function(path) {
  name <- basename(path)
  name <- sub("_HD_016um_seuratobj[.]rds$", "", name)
  sub("_visium_seuratobj[.]rds$", "", name)
}

sha256_file <- function(path) {
  output <- system2("sha256sum", shQuote(path), stdout = TRUE, stderr = TRUE)
  status <- attr(output, "status")
  if (!is.null(status) && status != 0L) stop(paste(output, collapse = "\n"))
  sub("[[:space:]].*$", "", output[[1]])
}

summarize_seurat_object <- function(object, path, min_genes, max_mito_percent,
                                    compute_sha = TRUE) {
  stopifnot(inherits(object, "Seurat"), "Spatial" %in% names(object@assays))
  metadata <- object@meta.data
  required <- c("nCount_Spatial", "nFeature_Spatial", "percent.mt")
  missing <- setdiff(required, colnames(metadata))
  if (length(missing)) stop("missing metadata fields: ", paste(missing, collapse = ","))
  if (all(c("row", "col", "X", "Y") %in% colnames(metadata))) {
    coordinate_schema <- "metadata_row_col_X_Y"
  } else if (all(c("array_row", "array_col") %in% colnames(metadata)) && length(object@images)) {
    coordinates <- SeuratObject::GetTissueCoordinates(object)
    if (!all(c("x", "y") %in% colnames(coordinates))) {
      stop("Seurat image lacks x/y tissue coordinates: ", basename(path))
    }
    coordinate_schema <- "metadata_array_row_col+image_x_y"
  } else {
    stop("no supported spatial coordinate schema: ", basename(path))
  }
  features <- metadata[["nFeature_Spatial"]]
  mito <- metadata[["percent.mt"]]
  is_hd <- grepl("_HD_016um_", basename(path), fixed = TRUE)
  below <- sum(features < min_genes)
  above <- sum(mito > max_mito_percent)
  data.frame(
    file = basename(path),
    sample_id = object_sample_id(path),
    modality = if (is_hd) "visium_hd" else "visium",
    resolution_um = if (is_hd) 16 else 55,
    genes = nrow(object),
    locations = ncol(object),
    min_detected_genes = min(features),
    max_mito_percent = max(mito),
    below_gene_threshold = below,
    above_mito_threshold = above,
    layers = paste(SeuratObject::Layers(object[["Spatial"]]), collapse = ";"),
    metadata_fields = paste(colnames(metadata), collapse = ";"),
    coordinate_schema = coordinate_schema,
    qc_contract = if (below == 0L && above == 0L) "PASS" else "FAIL",
    bytes = if (file.exists(path)) file.info(path)$size else NA_real_,
    sha256 = if (compute_sha) sha256_file(path) else "",
    stringsAsFactors = FALSE
  )
}

write_tsv <- function(value, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  write.table(value, path, sep = "\t", quote = FALSE, row.names = FALSE, na = "")
}

main <- function() {
  args <- commandArgs(trailingOnly = TRUE)
  data_root <- if (length(args)) args[[1]] else "/mnt/f/spatialecotyper_reproduction"
  object_dir <- file.path(data_root, "work", "paper_inputs", "gse320042_objects")
  paths <- sort(list.files(object_dir, pattern = "_seuratobj[.]rds$", full.names = TRUE))
  stopifnot(length(paths) == 17L)
  rows <- lapply(paths, function(path) {
    is_hd <- grepl("_HD_016um_", basename(path), fixed = TRUE)
    object <- readRDS(path)
    summarize_seurat_object(
      object, path, min_genes = if (is_hd) 20 else 50,
      max_mito_percent = 10, compute_sha = TRUE
    )
  })
  audit <- do.call(rbind, rows)
  stopifnot(nrow(audit) == 17L, sum(audit$modality == "visium_hd") == 2L)
  output <- file.path(data_root, "results", "reproducibility", "gse320042-object-qc.tsv")
  write_tsv(audit, output)
  cat(sprintf(
    "GSE320042 object audit: samples=%d hd16=%d qc_pass=%d output=%s\n",
    nrow(audit), sum(audit$modality == "visium_hd"),
    sum(audit$qc_contract == "PASS"), output
  ))
}

if (sys.nframe() == 0L) main()
