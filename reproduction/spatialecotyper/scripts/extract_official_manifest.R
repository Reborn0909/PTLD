args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2L) {
  stop("Usage: extract_official_manifest.R OFFICIAL_REPO OUTPUT_DIRECTORY")
}

repo <- normalizePath(args[[1]], mustWork = TRUE)
out <- args[[2]]
dir.create(out, recursive = TRUE, showWarnings = FALSE)
out <- normalizePath(out, mustWork = TRUE)

expected_commit <- "48c2c846781d3a312771021c1a2ef5fc383700c5"
observed_commit <- system2(
  "git",
  c("-C", shQuote(repo), "rev-parse", "HEAD"),
  stdout = TRUE
)
stopifnot(length(observed_commit) == 1L, observed_commit == expected_commit)

order_path <- file.path(
  "reproduction", "spatialecotyper", "config", "tutorial-order.tsv"
)
tutorial_order <- read.delim(order_path, stringsAsFactors = FALSE)
rmd_paths <- file.path(repo, "vignettes", tutorial_order$rmd)
stopifnot(all(file.exists(rmd_paths)))

stanford_pattern <- paste0(
  "https://spatialecotyper\\.stanford\\.edu/inc/",
  "inc\\.public\\.vignettes\\.php\\?file=[^\\\"') ]+"
)

manifest_rows <- lapply(seq_along(rmd_paths), function(i) {
  lines <- readLines(rmd_paths[[i]], warn = FALSE)
  hits <- unlist(regmatches(
    lines,
    gregexpr(stanford_pattern, lines, perl = TRUE)
  ))
  hits <- sort(unique(hits[nzchar(hits)]))
  if (!length(hits)) {
    return(NULL)
  }
  data.frame(
    file = sub("^.*[?]file=", "", hits),
    url = hits,
    tutorial_id = tutorial_order$tutorial_id[[i]],
    rmd = tutorial_order$rmd[[i]],
    stringsAsFactors = FALSE
  )
})
manifest_long <- do.call(rbind, manifest_rows)

files <- sort(unique(manifest_long$file))
stopifnot(length(files) == 21L)
manifest <- do.call(rbind, lapply(files, function(filename) {
  rows <- manifest_long[manifest_long$file == filename, , drop = FALSE]
  stopifnot(length(unique(rows$url)) == 1L)
  data.frame(
    file = filename,
    url = rows$url[[1]],
    used_by = paste(rows$tutorial_id, collapse = ","),
    source_commit = expected_commit,
    stringsAsFactors = FALSE
  )
}))
write.table(
  manifest,
  file.path(out, "tutorial-files.tsv"),
  sep = "\t",
  row.names = FALSE,
  quote = FALSE
)

strip_html <- function(x) {
  x <- gsub("<[^>]+>", "", x)
  x <- gsub("&gt;", ">", x, fixed = TRUE)
  x <- gsub("&lt;", "<", x, fixed = TRUE)
  x <- gsub("&amp;", "&", x, fixed = TRUE)
  x
}

package_pattern <- "([A-Za-z][A-Za-z0-9.]*)_([0-9][A-Za-z0-9.-]*)"
session_rows <- lapply(seq_len(nrow(tutorial_order)), function(i) {
  html_name <- sub("\\.Rmd$", ".html", tutorial_order$rmd[[i]])
  html_path <- file.path(repo, "docs", "articles", html_name)
  stopifnot(file.exists(html_path))
  text <- strip_html(readLines(html_path, warn = FALSE))
  start <- grep("other attached packages:", text, fixed = TRUE)
  end <- grep("loaded via a namespace", text, fixed = TRUE)
  stopifnot(length(start) == 1L, length(end) >= 1L)
  end <- end[end > start][[1]]
  section <- text[seq.int(start + 1L, end - 1L)]
  tokens <- unlist(regmatches(
    section,
    gregexpr(package_pattern, section, perl = TRUE)
  ))
  tokens <- unique(tokens[nzchar(tokens)])
  matches <- regexec(package_pattern, tokens, perl = TRUE)
  parts <- regmatches(tokens, matches)
  data.frame(
    tutorial_id = tutorial_order$tutorial_id[[i]],
    rmd = tutorial_order$rmd[[i]],
    package = vapply(parts, `[[`, character(1), 2L),
    version = vapply(parts, `[[`, character(1), 3L),
    source_commit = expected_commit,
    stringsAsFactors = FALSE
  )
})
session_packages <- do.call(rbind, session_rows)
stopifnot(any(
  session_packages$package == "SpatialEcoTyper" &
    session_packages$version == "1.0.2"
))
stopifnot(any(
  session_packages$package == "Seurat" &
    session_packages$version == "5.1.0"
))
write.table(
  session_packages,
  file.path(out, "official-session-packages.tsv"),
  sep = "\t",
  row.names = FALSE,
  quote = FALSE
)

message(sprintf(
  "official manifest: PASS (%d files, %d attached-package records)",
  nrow(manifest),
  nrow(session_packages)
))
