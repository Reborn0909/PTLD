status_path <- file.path(
  "/mnt/f/spatialecotyper_reproduction",
  "results", "tutorials", "run-status.tsv"
)
stopifnot(file.exists(status_path))
x <- read.delim(status_path, stringsAsFactors = FALSE, check.names = FALSE)
stopifnot(nrow(x) == 8L)
stopifnot(identical(x$order, 1:8))
stopifnot(identical(x$tutorial_id, sprintf("T%02d", 1:8)))
stopifnot(all(x$status == "PASS"))
stopifnot(all(x$exit_code == 0L))
stopifnot(all(is.finite(x$duration_seconds)), all(x$duration_seconds > 0))
stopifnot(all(is.finite(x$peak_rss_kb)), all(x$peak_rss_kb > 0))
stopifnot(all(file.exists(x$rendered_html)))
stopifnot(all(file.info(x$rendered_html)$size > 0))
stopifnot(all(file.exists(x$log)))
stopifnot(all(grepl("^[0-9a-f]{64}$", x$original_rmd_sha256)))
stopifnot(all(grepl("^[0-9a-f]{64}$", x$runtime_rmd_sha256)))
stopifnot(all(grepl("^[0-9a-f]{64}$", x$environment_lock_sha256)))
stopifnot(all(startsWith(
  x$input_adapter,
  "official_urls_to_sha256_verified_local_archive"
)))
stopifnot(x$strict_material_status[x$tutorial_id == "T02"] ==
  "FAIL_INPUT_SCHEMA_WITH_OFFICIAL_UPSTREAM_FALLBACK")
stopifnot(all(x$strict_material_status[x$tutorial_id != "T02"] == "PASS"))
message("official tutorial runs: PASS (8/8)")
