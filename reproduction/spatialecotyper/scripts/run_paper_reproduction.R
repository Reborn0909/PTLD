normalize_log2_cpm <- function(counts) {
  stopifnot(inherits(counts, "Matrix"), nrow(counts) > 0L, ncol(counts) > 0L)
  libraries <- Matrix::colSums(counts)
  if (any(!is.finite(libraries)) || any(libraries <= 0)) {
    stop("all spatial locations must have positive finite library sizes")
  }
  original_dimnames <- dimnames(counts)
  normalized <- counts %*% Matrix::Diagonal(x = 1e6 / libraries)
  dimnames(normalized) <- original_dimnames
  normalized@x <- log2(normalized@x + 1)
  normalized
}

paper_patient_id <- function(sample_id) {
  value <- sub("^GSM[0-9]+_", "", sample_id)
  sub("_[12]$", "", value)
}

aggregate_se_weighted <- function(fractions, cell_counts) {
  stopifnot(is.matrix(fractions), !is.null(rownames(fractions)))
  stopifnot(!is.null(names(cell_counts)), all(rownames(fractions) %in% names(cell_counts)))
  weights <- as.numeric(cell_counts[rownames(fractions)])
  stopifnot(all(is.finite(weights)), all(weights >= 0), sum(weights) > 0)
  result <- colSums(fractions * weights) / sum(weights)
  result / sum(result)
}

aggregation_contract <- function(cytospace_cell_counts) {
  if (is.null(cytospace_cell_counts)) {
    return(list(
      status = "METHOD_GAP",
      reason = paste(
        "Paper sample-level SE values require CytoSPACE-estimated cell counts per spot;",
        "those count estimates are not present in GSE320042 or the fixed official repository."
      )
    ))
  }
  list(status = "READY", reason = "CytoSPACE cell-count weights supplied")
}

sha256_file <- function(path) {
  output <- system2("sha256sum", shQuote(path), stdout = TRUE, stderr = TRUE)
  status <- attr(output, "status")
  if (!is.null(status) && status != 0L) stop(paste(output, collapse = "\n"))
  sub("[[:space:]].*$", "", output[[1]])
}

sample_id_from_path <- function(path) {
  value <- basename(path)
  value <- sub("_HD_016um_seuratobj[.]rds$", "", value)
  sub("_visium_seuratobj[.]rds$", "", value)
}

validate_deconvolution <- function(result, expected_locations) {
  expected_states <- c("NonSE", paste0("SE", 1:9))
  stopifnot(
    is.matrix(result), nrow(result) == expected_locations,
    identical(colnames(result), expected_states),
    max(abs(rowSums(result) - 1)) < 1e-8,
    all(is.finite(result)), all(result >= 0)
  )
  invisible(TRUE)
}

run_one_sample <- function(path, output_dir, ncores = 8L) {
  sample_id <- sample_id_from_path(path)
  output <- file.path(output_dir, paste0(sample_id, "_spot_SE_fractions.rds"))
  started <- Sys.time()
  status <- "VERIFIED_EXISTING"
  if (file.exists(output)) {
    object <- readRDS(path)
    result <- readRDS(output)
    validate_deconvolution(result, ncol(object))
    genes <- nrow(object)
    locations <- ncol(object)
  } else {
    part <- paste0(output, ".part")
    if (file.exists(part)) stop("unfinished output requires audit before retry: ", part)
    object <- readRDS(path)
    counts <- SeuratObject::LayerData(object, assay = "Spatial", layer = "counts")
    genes <- nrow(counts)
    locations <- ncol(counts)
    expression <- normalize_log2_cpm(counts)
    set.seed(1L)
    result <- SpatialEcoTyper::DeconvoluteSE(
      expression, scale = TRUE, nsample.per.run = 500,
      sum2one = TRUE, ncores = as.integer(ncores)
    )
    validate_deconvolution(result, locations)
    saveRDS(result, part, compress = "gzip")
    if (!file.rename(part, output)) stop("failed atomic output rename: ", output)
    status <- "SPOT_LEVEL_REPRODUCED"
  }
  data.frame(
    sample_id = sample_id,
    patient_id = paper_patient_id(sample_id),
    modality = if (grepl("_HD_016um_", basename(path), fixed = TRUE)) "visium_hd_16um" else "visium",
    genes = genes,
    locations = locations,
    states = ncol(result),
    row_sum_max_error = max(abs(rowSums(result) - 1)),
    input_path = path,
    input_sha256 = sha256_file(path),
    output_path = output,
    output_sha256 = sha256_file(output),
    status = status,
    aggregation_status = aggregation_contract(NULL)$status,
    aggregation_limitation = aggregation_contract(NULL)$reason,
    elapsed_seconds = as.numeric(difftime(Sys.time(), started, units = "secs")),
    stringsAsFactors = FALSE
  )
}

parse_args <- function(args) {
  result <- list(root = "/mnt/f/spatialecotyper_reproduction", sample = "", ncores = 8L)
  index <- 1L
  while (index <= length(args)) {
    key <- args[[index]]
    if (!key %in% c("--root", "--sample", "--ncores") || index == length(args)) {
      stop("invalid argument: ", key)
    }
    value <- args[[index + 1L]]
    if (key == "--root") result$root <- value
    if (key == "--sample") result$sample <- value
    if (key == "--ncores") result$ncores <- as.integer(value)
    index <- index + 2L
  }
  stopifnot(is.finite(result$ncores), result$ncores >= 1L)
  result
}

main <- function() {
  args <- parse_args(commandArgs(trailingOnly = TRUE))
  stopifnot(
    as.character(utils::packageVersion("SpatialEcoTyper")) == "1.0.2",
    as.character(getRversion()) == "4.4.1"
  )
  object_dir <- file.path(args$root, "work", "paper_inputs", "gse320042_objects")
  paths <- sort(list.files(object_dir, pattern = "_seuratobj[.]rds$", full.names = TRUE))
  stopifnot(length(paths) == 17L)
  if (nzchar(args$sample)) {
    paths <- paths[vapply(paths, function(path) sample_id_from_path(path) == args$sample, logical(1))]
    if (length(paths) != 1L) stop("sample must match exactly one generated spatial object")
  }
  output_dir <- file.path(args$root, "results", "paper_reproduction", "generated_visium_deconvolution")
  dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
  rows <- lapply(paths, run_one_sample, output_dir = output_dir, ncores = args$ncores)
  status <- do.call(rbind, rows)
  status_path <- file.path(output_dir, "run-status.tsv")
  write.table(status, status_path, sep = "\t", quote = FALSE, row.names = FALSE)
  cat(sprintf(
    "paper generated Visium deconvolution: samples=%d locations=%d aggregation=%s output=%s\n",
    nrow(status), sum(status$locations), unique(status$aggregation_status), status_path
  ))
}

if (sys.nframe() == 0L) main()
