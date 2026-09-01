validate_ptld_input <- function(counts, metadata, min_cells_per_sample = 20L) {
  matrix_like <- is.matrix(counts) || inherits(counts, "Matrix")
  if (!matrix_like || length(dim(counts)) != 2L) {
    stop("counts must be a numeric matrix or Matrix sparse matrix")
  }
  values <- if (inherits(counts, "Matrix")) {
    if (!"x" %in% methods::slotNames(counts)) {
      stop("counts Matrix must store numeric or integer values")
    }
    methods::slot(counts, "x")
  } else {
    as.vector(counts)
  }
  if (!typeof(values) %in% c("double", "integer")) {
    stop("counts must store numeric or integer values")
  }
  if (nrow(counts) < 1L || ncol(counts) < 1L) {
    stop("counts must contain at least one gene and one cell")
  }

  gene_ids <- rownames(counts)
  cell_ids <- colnames(counts)
  if (is.null(gene_ids) || anyNA(gene_ids) || any(!nzchar(gene_ids))) {
    stop("counts must have non-empty gene row names")
  }
  if (anyDuplicated(gene_ids)) {
    stop("counts contain duplicate gene IDs")
  }
  if (is.null(cell_ids) || anyNA(cell_ids) || any(!nzchar(cell_ids))) {
    stop("counts must have non-empty cell column names")
  }
  if (anyDuplicated(cell_ids)) {
    stop("counts contain duplicate cell IDs")
  }

  if (any(!is.finite(values))) {
    stop("counts contain non-finite values")
  }
  if (any(values < 0)) {
    stop("counts contain negative values")
  }

  if (!is.data.frame(metadata)) {
    stop("metadata must be a data frame")
  }
  metadata_ids <- rownames(metadata)
  if (is.null(metadata_ids) || anyNA(metadata_ids) || any(!nzchar(metadata_ids))) {
    stop("metadata must have non-empty cell row names")
  }
  if (anyDuplicated(metadata_ids)) {
    stop("metadata contain duplicate cell IDs")
  }
  if (!setequal(cell_ids, metadata_ids) || length(cell_ids) != length(metadata_ids)) {
    stop("counts and metadata must contain identical cell IDs")
  }
  metadata <- metadata[cell_ids, , drop = FALSE]

  required <- c("X", "Y", "CellType", "SampleID")
  missing_columns <- setdiff(required, colnames(metadata))
  if (length(missing_columns)) {
    stop("metadata missing required columns: ", paste(missing_columns, collapse = ", "))
  }
  for (coordinate in c("X", "Y")) {
    if (!is.numeric(metadata[[coordinate]])) {
      stop(coordinate, " coordinates must be numeric")
    }
    if (any(!is.finite(metadata[[coordinate]]))) {
      stop(coordinate, " coordinates must be finite")
    }
  }

  metadata$CellType <- trimws(as.character(metadata$CellType))
  metadata$SampleID <- trimws(as.character(metadata$SampleID))
  if (anyNA(metadata$CellType) || any(!nzchar(metadata$CellType))) {
    stop("CellType must not contain missing or empty values")
  }
  if (anyNA(metadata$SampleID) || any(!nzchar(metadata$SampleID))) {
    stop("SampleID must not contain missing or empty values")
  }
  if (length(min_cells_per_sample) != 1L || !is.finite(min_cells_per_sample) ||
      min_cells_per_sample < 1 || min_cells_per_sample != as.integer(min_cells_per_sample)) {
    stop("min_cells_per_sample must be one positive integer")
  }
  min_cells_per_sample <- as.integer(min_cells_per_sample)

  sample_sizes <- table(metadata$SampleID)
  if (any(sample_sizes < min_cells_per_sample)) {
    too_small <- names(sample_sizes)[sample_sizes < min_cells_per_sample]
    stop(
      "samples below minimum cell count (", min_cells_per_sample, "): ",
      paste(too_small, collapse = ", ")
    )
  }

  column_sums <- function(x) {
    if (inherits(x, "Matrix")) Matrix::colSums(x) else base::colSums(x)
  }
  library_size <- as.numeric(column_sums(counts))
  detected_genes <- as.numeric(column_sums(counts > 0))
  sample_summary <- data.frame(
    SampleID = names(sample_sizes),
    n_cells = as.integer(sample_sizes),
    n_cell_types = vapply(
      names(sample_sizes),
      function(sample_id) {
        length(unique(metadata$CellType[metadata$SampleID == sample_id]))
      },
      integer(1)
    ),
    median_library_size = vapply(
      names(sample_sizes),
      function(sample_id) {
        stats::median(library_size[metadata$SampleID == sample_id])
      },
      numeric(1)
    ),
    median_detected_genes = vapply(
      names(sample_sizes),
      function(sample_id) {
        stats::median(detected_genes[metadata$SampleID == sample_id])
      },
      numeric(1)
    ),
    stringsAsFactors = FALSE
  )
  cell_qc <- data.frame(
    CellID = cell_ids,
    SampleID = metadata$SampleID,
    library_size = library_size,
    detected_genes = detected_genes,
    zero_library = library_size == 0,
    stringsAsFactors = FALSE,
    row.names = cell_ids
  )

  list(
    counts = counts,
    metadata = metadata,
    qc = list(
      n_genes = nrow(counts),
      n_cells = ncol(counts),
      n_samples = length(sample_sizes),
      n_cell_types = length(unique(metadata$CellType)),
      min_cells_per_sample = min_cells_per_sample,
      sample_summary = sample_summary,
      cell_qc = cell_qc
    )
  )
}
