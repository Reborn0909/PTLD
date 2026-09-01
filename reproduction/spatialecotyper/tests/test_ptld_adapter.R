source("reproduction/spatialecotyper/ptld/validate_input.R")
source("reproduction/spatialecotyper/ptld/map_cell_types.R")
source("reproduction/spatialecotyper/ptld/run_official_api.R")

expect_error <- function(expr, pattern = NULL) {
  error <- tryCatch(
    {
      force(expr)
      NULL
    },
    error = identity
  )
  stopifnot(inherits(error, "error"))
  if (!is.null(pattern)) {
    stopifnot(grepl(pattern, conditionMessage(error), ignore.case = TRUE))
  }
  invisible(error)
}

counts <- matrix(
  c(
    1, 0, 3, 2, 1, 4,
    0, 2, 1, 0, 2, 3,
    5, 1, 0, 3, 1, 0
  ),
  nrow = 3,
  dimnames = list(
    c("EBER1", "CD3D", "MS4A1"),
    paste0("cell", 1:6)
  )
)
metadata <- data.frame(
  X = c(0, 10, 20, 0, 10, 20),
  Y = c(0, 0, 0, 10, 10, 10),
  CellType = c("T_raw", "T_raw", "B_raw", "B_raw", "T_raw", "B_raw"),
  SampleID = rep(c("PTLD01", "CTRL01"), each = 3),
  row.names = colnames(counts),
  stringsAsFactors = FALSE
)

valid <- validate_ptld_input(counts, metadata, min_cells_per_sample = 2L)
stopifnot(identical(valid$counts, counts))
stopifnot(identical(rownames(valid$metadata), colnames(counts)))
stopifnot(identical(valid$metadata$X, metadata$X))
stopifnot(nrow(valid$qc$sample_summary) == 2L)
stopifnot(valid$qc$n_cells == 6L, valid$qc$n_genes == 3L)

sparse_counts <- Matrix::Matrix(counts, sparse = TRUE)
sparse_valid <- validate_ptld_input(
  sparse_counts, metadata, min_cells_per_sample = 2L
)
stopifnot(identical(sparse_valid$counts, sparse_counts))
stopifnot(identical(
  sparse_valid$qc$cell_qc$library_size,
  unname(as.numeric(colSums(counts)))
))

logical_sparse <- sparse_counts > 0
expect_error(
  validate_ptld_input(logical_sparse, metadata, min_cells_per_sample = 2L),
  "numeric or integer"
)
pattern_sparse <- methods::as(logical_sparse, "nMatrix")
expect_error(
  validate_ptld_input(pattern_sparse, metadata, min_cells_per_sample = 2L),
  "numeric or integer"
)

duplicate_counts <- counts
colnames(duplicate_counts)[[2]] <- colnames(duplicate_counts)[[1]]
expect_error(
  validate_ptld_input(duplicate_counts, metadata, min_cells_per_sample = 2L),
  "duplicate"
)

duplicate_genes <- counts
rownames(duplicate_genes)[[2]] <- rownames(duplicate_genes)[[1]]
expect_error(
  validate_ptld_input(duplicate_genes, metadata, min_cells_per_sample = 2L),
  "duplicate gene"
)

mismatch_metadata <- metadata[-1, , drop = FALSE]
expect_error(
  validate_ptld_input(counts, mismatch_metadata, min_cells_per_sample = 2L),
  "identical cell IDs"
)

duplicate_metadata <- metadata
attr(duplicate_metadata, "row.names") <- c(
  "cell1", "cell1", "cell3", "cell4", "cell5", "cell6"
)
expect_error(
  validate_ptld_input(counts, duplicate_metadata, min_cells_per_sample = 2L),
  "duplicate cell"
)

bad_coordinate <- metadata
bad_coordinate$X[[1]] <- Inf
expect_error(
  validate_ptld_input(counts, bad_coordinate, min_cells_per_sample = 2L),
  "finite"
)

negative_counts <- counts
negative_counts[[1]] <- -1
expect_error(
  validate_ptld_input(negative_counts, metadata, min_cells_per_sample = 2L),
  "negative"
)

nonfinite_counts <- counts
nonfinite_counts[[1]] <- Inf
expect_error(
  validate_ptld_input(nonfinite_counts, metadata, min_cells_per_sample = 2L),
  "non-finite"
)

empty_celltype <- metadata
empty_celltype$CellType[[1]] <- ""
expect_error(
  validate_ptld_input(counts, empty_celltype, min_cells_per_sample = 2L),
  "CellType"
)

empty_sample <- metadata
empty_sample$SampleID[[1]] <- ""
expect_error(
  validate_ptld_input(counts, empty_sample, min_cells_per_sample = 2L),
  "SampleID"
)

small_sample <- metadata
small_sample$SampleID <- c("TOO_SMALL", rep("OTHER", 5))
expect_error(
  validate_ptld_input(counts, small_sample, min_cells_per_sample = 2L),
  "minimum"
)

mapping <- data.frame(
  source = c("T_raw", "B_raw"),
  target = c("CD3 T", "B"),
  stringsAsFactors = FALSE
)
mapped <- map_ptld_cell_types(valid$metadata, mapping)
stopifnot(identical(mapped$OriginalCellType, metadata$CellType))
stopifnot(identical(unique(mapped$CellType), c("CD3 T", "B")))

incomplete_mapping <- mapping[1, , drop = FALSE]
expect_error(
  map_ptld_cell_types(valid$metadata, incomplete_mapping),
  "unknown"
)

duplicate_mapping <- rbind(mapping, mapping[1, , drop = FALSE])
expect_error(
  map_ptld_cell_types(valid$metadata, duplicate_mapping),
  "duplicate source"
)

period_mapping <- mapping
period_mapping$target[[1]] <- "CD4.T"
expect_error(
  map_ptld_cell_types(valid$metadata, period_mapping),
  "must not contain"
)

wrapper_formals <- formals(run_ptld_spatialecotyper)
stopifnot(
  identical(wrapper_formals$nfeatures, 300L),
  identical(wrapper_formals$radius, 50),
  identical(wrapper_formals$ncores, 2L)
)
wrapper_body <- paste(deparse(body(run_ptld_spatialecotyper)), collapse = "\n")
stopifnot(grepl("SpatialEcoTyper::SpatialEcoTyper", wrapper_body, fixed = TRUE))
stopifnot(grepl("nfeatures = nfeatures", wrapper_body, fixed = TRUE))
stopifnot(grepl("radius = radius", wrapper_body, fixed = TRUE))
stopifnot(grepl("ncores = ncores", wrapper_body, fixed = TRUE))

expect_error(
  run_ptld_spatialecotyper(counts, metadata, "unused", nfeatures = NA_real_),
  "nfeatures"
)
expect_error(
  run_ptld_spatialecotyper(counts, metadata, "unused", radius = "50"),
  "radius"
)
expect_error(
  run_ptld_spatialecotyper(counts, metadata, "unused", ncores = NA_integer_),
  "ncores"
)

unsafe_output <- tempfile("ptld-unsafe-prefix-")
expect_error(
  run_ptld_by_sample(counts, metadata, unsafe_output, prefix = "../escape"),
  "prefix"
)
stopifnot(!dir.exists(unsafe_output))

spaced_sample <- metadata
spaced_sample$SampleID[[1]] <- " PTLD01 "
expect_error(
  run_ptld_by_sample(counts, spaced_sample, tempfile("ptld-spaced-sample-")),
  "whitespace"
)

local({
  calls <- list()
  official_runner <- run_ptld_spatialecotyper
  on.exit(
    assign(
      "run_ptld_spatialecotyper", official_runner,
      envir = .GlobalEnv
    )
  )
  assign(
    "run_ptld_spatialecotyper",
    function(normdata, metadata, outprefix, nfeatures, radius, ncores) {
      calls[[length(calls) + 1L]] <<- list(
        normdata = normdata,
        metadata = metadata,
        outprefix = outprefix,
        nfeatures = nfeatures,
        radius = radius,
        ncores = ncores
      )
      list(sample_id = unique(metadata$SampleID))
    },
    envir = .GlobalEnv
  )

  batch_dir <- tempfile("ptld-batch-")
  on.exit(unlink(batch_dir, recursive = TRUE), add = TRUE)
  batch <- run_ptld_by_sample(counts, metadata, batch_dir)
  stopifnot(identical(names(batch), c("PTLD01", "CTRL01")))
  stopifnot(length(calls) == 2L)
  stopifnot(identical(
    colnames(calls[[1]]$normdata), rownames(calls[[1]]$metadata)
  ))
  stopifnot(basename(calls[[1]]$outprefix) == "PTLD_PTLD01")
  stopifnot(dirname(calls[[1]]$outprefix) == batch_dir)
  stopifnot(
    identical(calls[[1]]$nfeatures, 300L),
    identical(calls[[1]]$radius, 50),
    identical(calls[[1]]$ncores, 2L)
  )
})

config_path <- file.path(
  "reproduction", "spatialecotyper", "ptld",
  "ptld-run-config.example.tsv"
)
stopifnot(file.exists(config_path))
config <- utils::read.delim(config_path, stringsAsFactors = FALSE)
stopifnot(
  all(c("key", "value", "note") %in% colnames(config)),
  config$value[config$key == "source_commit"] ==
    "48c2c846781d3a312771021c1a2ef5fc383700c5",
  config$value[config$key == "nfeatures"] == "300",
  config$value[config$key == "radius"] == "50",
  config$value[config$key == "ncores"] == "2"
)

message("PTLD adapter: PASS")
