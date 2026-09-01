json_scalar <- function(text, key) {
  escaped <- gsub("([][{}()+*^$|\\?.])", "\\\\\\1", key)
  pattern <- paste0('"', escaped, '"[[:space:]]*:[[:space:]]*("[^"]*"|[0-9]+)')
  matched <- regmatches(text, regexpr(pattern, text))
  if (!nzchar(matched)) stop("missing JSON scalar: ", key)
  value <- sub("^[^:]*:[[:space:]]*", "", matched)
  sub('^"(.*)"$', "\\1", value)
}

compare_s17_spatial <- function(samples, actual) {
  expected <- samples[
    samples$sheet == "Table S17" & samples$platform %in% c("Visium", "Visium HD"),
    , drop = FALSE
  ]
  replicate_id <- vapply(expected$raw_json, json_scalar, character(1), key = "Replicate #")
  expected_key <- ifelse(
    grepl("^[0-9]+$", replicate_id),
    paste(expected$sample_id, replicate_id, sep = "_"),
    expected$sample_id
  )
  expected_locations <- as.integer(vapply(
    expected$raw_json, json_scalar, character(1),
    key = "Number of spots/bins (filtered)"
  ))
  actual_key <- sub("^GSM[0-9]+_", "", actual$sample_id)
  matched <- match(expected_key, actual_key)
  observed_locations <- actual$locations[matched]
  observed_modality <- actual$modality[matched]
  expected_modality <- ifelse(expected$platform == "Visium HD", "visium_hd_16um", "visium")
  comparison_status <- ifelse(
    is.na(matched), "MISSING",
    ifelse(
      observed_locations != expected_locations, "LOCATION_MISMATCH",
      ifelse(observed_modality != expected_modality, "PLATFORM_MISMATCH", "PASS")
    )
  )
  data.frame(
    source_record_id = expected$source_record_id,
    patient_id = expected$sample_id,
    replicate = replicate_id,
    platform = expected$platform,
    expected_sample_key = expected_key,
    actual_sample_id = ifelse(is.na(matched), "", actual$sample_id[matched]),
    expected_locations = expected_locations,
    observed_locations = ifelse(is.na(matched), NA_integer_, observed_locations),
    expected_modality = expected_modality,
    observed_modality = ifelse(is.na(matched), "", observed_modality),
    comparison_status = comparison_status,
    stringsAsFactors = FALSE
  )
}

main <- function() {
  args <- commandArgs(trailingOnly = TRUE)
  data_root <- if (length(args)) args[[1]] else "/mnt/f/spatialecotyper_reproduction"
  samples <- read.delim(
    file.path(data_root, "archive", "manifests", "paper-samples.tsv"),
    stringsAsFactors = FALSE, check.names = FALSE
  )
  actual <- read.delim(
    file.path(
      data_root, "results", "paper_reproduction", "generated_visium_deconvolution",
      "run-status.tsv"
    ),
    stringsAsFactors = FALSE, check.names = FALSE
  )
  comparison <- compare_s17_spatial(samples, actual)
  stopifnot(
    nrow(comparison) == 17L,
    length(unique(comparison$patient_id)) == 15L,
    sum(comparison$expected_locations) == 262879L,
    all(comparison$comparison_status == "PASS")
  )
  output <- file.path(
    data_root, "results", "paper_reproduction", "generated_visium_deconvolution",
    "supplementary-table-s17-comparison.tsv"
  )
  write.table(comparison, output, sep = "\t", quote = FALSE, row.names = FALSE, na = "")
  cat(sprintf(
    "paper S17 comparison: PASS samples=%d patients=%d locations=%d output=%s\n",
    nrow(comparison), length(unique(comparison$patient_id)),
    sum(comparison$expected_locations), output
  ))
}

if (sys.nframe() == 0L) main()
