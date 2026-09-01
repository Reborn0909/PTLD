full_args <- commandArgs(trailingOnly = FALSE)
script_arg <- grep("^--file=", full_args, value = TRUE)
stopifnot(length(script_arg) == 1L)
test_path <- normalizePath(sub("^--file=", "", script_arg), mustWork = TRUE)
repo_root <- normalizePath(file.path(dirname(test_path), "../../.."), mustWork = TRUE)
script <- file.path(
  repo_root, "reproduction", "spatialecotyper", "scripts", "compare_paper_outputs.R"
)
stopifnot(file.exists(script))
source(script, local = TRUE)

samples <- data.frame(
  source_record_id = c("TableS17-R1", "TableS17-R2"),
  sheet = c("Table S17", "Table S17"),
  sample_id = c("WU1", "WU2"),
  platform = c("Visium", "Visium HD"),
  raw_json = c(
    '{"Number of spots/bins (filtered)": 12, "Patient ID": "WU1", "Replicate #": 2}',
    '{"Number of spots/bins (filtered)": 34, "Patient ID": "WU2", "Replicate #": "N/A"}'
  ),
  stringsAsFactors = FALSE
)
actual <- data.frame(
  sample_id = c("GSM1_WU1_2", "GSM2_WU2"),
  patient_id = c("WU1", "WU2"),
  modality = c("visium", "visium_hd_16um"),
  locations = c(12, 34),
  status = c("SPOT_LEVEL_REPRODUCED", "SPOT_LEVEL_REPRODUCED"),
  stringsAsFactors = FALSE
)
comparison <- compare_s17_spatial(samples, actual)
stopifnot(
  nrow(comparison) == 2L,
  identical(comparison$expected_sample_key, c("WU1_2", "WU2")),
  all(comparison$comparison_status == "PASS")
)

cat("paper output comparison test: PASS\n")
