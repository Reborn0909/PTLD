run_ptld_spatialecotyper <- function(normdata, metadata, outprefix,
                                     nfeatures = 300L, radius = 50,
                                     ncores = 2L) {
  positive_whole <- function(value) {
    is.numeric(value) && length(value) == 1L && !is.na(value) &&
      is.finite(value) && value > 0 && value == floor(value)
  }
  if (!is.character(outprefix) || length(outprefix) != 1L ||
      is.na(outprefix) || !nzchar(outprefix)) {
    stop("outprefix must be one non-empty path prefix")
  }
  if (!positive_whole(nfeatures)) {
    stop("nfeatures must be one positive integer")
  }
  if (!is.numeric(radius) || length(radius) != 1L || is.na(radius) ||
      !is.finite(radius) || radius <= 0) {
    stop("radius must be one positive finite value")
  }
  if (!positive_whole(ncores)) {
    stop("ncores must be one positive integer")
  }

  SpatialEcoTyper::SpatialEcoTyper(
    normdata, metadata,
    outprefix = outprefix,
    nfeatures = nfeatures,
    radius = radius,
    ncores = ncores
  )
}

run_ptld_by_sample <- function(normdata, metadata, output_dir,
                               prefix = "PTLD", nfeatures = 300L,
                               radius = 50, ncores = 2L) {
  if (!is.data.frame(metadata) || !"SampleID" %in% colnames(metadata)) {
    stop("metadata must contain SampleID")
  }
  if (!identical(colnames(normdata), rownames(metadata))) {
    stop("normdata columns and metadata rows must be identically ordered")
  }
  original_sample_ids <- as.character(metadata$SampleID)
  cleaned_sample_ids <- trimws(original_sample_ids)
  if (!identical(original_sample_ids, cleaned_sample_ids)) {
    stop("SampleID values must not have leading or trailing whitespace")
  }
  sample_ids <- unique(cleaned_sample_ids)
  if (anyNA(sample_ids) || any(!nzchar(sample_ids)) ||
      any(!grepl("^[A-Za-z0-9._-]+$", sample_ids))) {
    stop("SampleID values must be de-identified filename-safe tokens")
  }
  if (!is.character(output_dir) || length(output_dir) != 1L ||
      is.na(output_dir) || !nzchar(output_dir)) {
    stop("output_dir must be one non-empty path")
  }
  if (!is.character(prefix) || length(prefix) != 1L || is.na(prefix) ||
      !grepl("^[A-Za-z0-9][A-Za-z0-9._-]*$", prefix)) {
    stop("prefix must be one filename-safe token")
  }
  dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

  results <- lapply(sample_ids, function(sample_id) {
    keep <- metadata$SampleID == sample_id
    run_ptld_spatialecotyper(
      normdata = normdata[, keep, drop = FALSE],
      metadata = metadata[keep, , drop = FALSE],
      outprefix = file.path(output_dir, paste(prefix, sample_id, sep = "_")),
      nfeatures = nfeatures,
      radius = radius,
      ncores = ncores
    )
  })
  names(results) <- sample_ids
  results
}
