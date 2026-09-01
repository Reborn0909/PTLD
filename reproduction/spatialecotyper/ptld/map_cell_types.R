map_ptld_cell_types <- function(metadata, mapping) {
  if (!is.data.frame(metadata) || !"CellType" %in% colnames(metadata)) {
    stop("metadata must be a data frame with a CellType column")
  }
  if (!is.data.frame(mapping) || !all(c("source", "target") %in% colnames(mapping))) {
    stop("mapping must contain source and target columns")
  }
  if ("OriginalCellType" %in% colnames(metadata)) {
    stop("metadata already contains OriginalCellType; refusing to overwrite it")
  }

  source <- trimws(as.character(mapping$source))
  target <- trimws(as.character(mapping$target))
  if (anyNA(source) || anyNA(target) || any(!nzchar(source)) || any(!nzchar(target))) {
    stop("mapping source and target values must be non-empty")
  }
  if (anyDuplicated(source)) {
    stop("mapping contains duplicate source cell types")
  }
  if (any(grepl(".", target, fixed = TRUE))) {
    stop(
      "mapping targets must not contain '.' because the official algorithm ",
      "reserves it as a delimiter"
    )
  }

  observed <- trimws(as.character(metadata$CellType))
  unknown <- setdiff(unique(observed), source)
  if (length(unknown)) {
    stop("unknown cell types without an explicit mapping: ", paste(unknown, collapse = ", "))
  }

  metadata$OriginalCellType <- observed
  metadata$CellType <- unname(target[match(observed, source)])
  metadata
}
