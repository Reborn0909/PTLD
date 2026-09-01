allowed_entrypoint_pattern <- "^SpatialEcoTyper::[A-Za-z][A-Za-z0-9._]*$"

split_input_records <- function(value) {
  values <- trimws(unlist(strsplit(value, "[;,]", perl = TRUE)))
  values[nzchar(values)]
}

entrypoint_function <- function(value) {
  if (!grepl(allowed_entrypoint_pattern, value)) return("")
  sub("^SpatialEcoTyper::", "", value)
}

validate_dispatch_row <- function(panel_row, readiness, namespace_exports = NULL) {
  entrypoint <- as.character(panel_row$official_entrypoint[[1]])
  function_name <- entrypoint_function(entrypoint)
  if (!nzchar(function_name)) {
    return(list(eligible = FALSE, reason = "NO_OFFICIAL_ENTRYPOINT"))
  }
  if (is.null(namespace_exports)) {
    if (!requireNamespace("SpatialEcoTyper", quietly = TRUE)) {
      return(list(eligible = FALSE, reason = "PACKAGE_NOT_INSTALLED"))
    }
    namespace_exports <- getNamespaceExports("SpatialEcoTyper")
  }
  if (!function_name %in% namespace_exports) {
    return(list(eligible = FALSE, reason = "ENTRYPOINT_NOT_EXPORTED"))
  }

  input_ids <- split_input_records(as.character(panel_row$input_records[[1]]))
  if (!length(input_ids)) {
    return(list(eligible = FALSE, reason = "NO_CANONICAL_INPUT_RECORD"))
  }
  matched <- readiness[readiness$source_record_id %in% input_ids, , drop = FALSE]
  if (nrow(matched) != length(unique(input_ids))) {
    return(list(eligible = FALSE, reason = "INPUT_RECORD_NOT_CANONICAL"))
  }
  if (any(matched$readiness_class != "READY_OFFICIAL_PROCESSED")) {
    return(list(eligible = FALSE, reason = "INPUT_NOT_OFFICIAL_PROCESSED"))
  }
  if (any(matched$expression_status != "AVAILABLE")) {
    return(list(eligible = FALSE, reason = "EXPRESSION_MISSING"))
  }
  if ("spatial_status" %in% names(matched) && any(matched$spatial_status == "MISSING")) {
    return(list(eligible = FALSE, reason = "SPATIAL_COORDINATES_MISSING"))
  }
  list(eligible = TRUE, reason = "ELIGIBLE")
}

atomic_write_tsv <- function(value, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  part <- paste0(path, ".part")
  utils::write.table(
    value, part, sep = "\t", quote = FALSE, row.names = FALSE, na = ""
  )
  if (!file.rename(part, path)) stop("failed atomic output rename: ", path)
}

build_execution_gate <- function(root) {
  panel_path <- file.path(root, "results", "reproducibility", "paper-panel-audit.tsv")
  readiness_path <- file.path(root, "results", "reproducibility", "paper-dataset-readiness.tsv")
  stopifnot(file.exists(panel_path), file.exists(readiness_path))
  panels <- utils::read.delim(panel_path, check.names = FALSE, stringsAsFactors = FALSE)
  readiness <- utils::read.delim(readiness_path, check.names = FALSE, stringsAsFactors = FALSE)
  exports <- getNamespaceExports("SpatialEcoTyper")
  decisions <- lapply(seq_len(nrow(panels)), function(index) {
    decision <- validate_dispatch_row(panels[index, , drop = FALSE], readiness, exports)
    data.frame(
      panel_id = panels$panel_id[[index]],
      input_records = panels$input_records[[index]],
      official_entrypoint = panels$official_entrypoint[[index]],
      eligible = decision$eligible,
      gate_reason = decision$reason,
      stringsAsFactors = FALSE
    )
  })
  do.call(rbind, decisions)
}

parse_args <- function(args) {
  result <- list(root = "/mnt/f/spatialecotyper_reproduction")
  index <- 1L
  while (index <= length(args)) {
    if (args[[index]] != "--root" || index == length(args)) {
      stop("invalid argument: ", args[[index]])
    }
    result$root <- args[[index + 1L]]
    index <- index + 2L
  }
  result
}

main <- function() {
  args <- parse_args(commandArgs(trailingOnly = TRUE))
  stopifnot(
    as.character(getRversion()) == "4.4.1",
    requireNamespace("SpatialEcoTyper", quietly = TRUE),
    as.character(utils::packageVersion("SpatialEcoTyper")) == "1.0.2"
  )
  gate <- build_execution_gate(args$root)
  output_dir <- file.path(
    args$root, "results", "paper_reproduction", "ready_analyses"
  )
  gate_path <- file.path(output_dir, "execution-gate.tsv")
  atomic_write_tsv(gate, gate_path)
  eligible <- gate[gate$eligible, , drop = FALSE]
  if (nrow(eligible)) {
    stop(
      "eligible rows require an explicit, reviewed argument recipe before execution: ",
      paste(eligible$panel_id, collapse = ",")
    )
  }
  summary <- data.frame(
    status = "PASS_NO_ELIGIBLE_PANELS",
    panel_rows = nrow(gate),
    eligible_rows = 0L,
    package = "SpatialEcoTyper",
    package_version = as.character(utils::packageVersion("SpatialEcoTyper")),
    official_commit = "48c2c846781d3a312771021c1a2ef5fc383700c5",
    limitation = paste(
      "No paper panel currently has both READY_OFFICIAL_PROCESSED canonical inputs",
      "and an explicit fixed-repository entrypoint; no analysis was dispatched."
    ),
    stringsAsFactors = FALSE
  )
  summary_path <- file.path(output_dir, "execution-summary.tsv")
  atomic_write_tsv(summary, summary_path)
  cat(sprintf(
    "ready paper analysis gate: PASS panels=%d eligible=0 output=%s\n",
    nrow(gate), gate_path
  ))
}

if (sys.nframe() == 0L) main()
