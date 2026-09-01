args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2L) {
  stop("Usage: record_environment.R OFFICIAL_REPO DATA_ROOT")
}

official_repo <- normalizePath(args[[1]], mustWork = TRUE)
data_root <- normalizePath(args[[2]], mustWork = TRUE)
environment_dir <- file.path(data_root, "results", "environment")
manifest_dir <- file.path(data_root, "archive", "manifests")
renv_cache <- file.path(data_root, "cache", "renv")
download_cache <- file.path(data_root, "cache", "downloads")
dir.create(environment_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(manifest_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(renv_cache, recursive = TRUE, showWarnings = FALSE)
dir.create(download_cache, recursive = TRUE, showWarnings = FALSE)
Sys.setenv(RENV_PATHS_CACHE = renv_cache)

expected_commit <- "48c2c846781d3a312771021c1a2ef5fc383700c5"
observed_commit <- system2(
  "git", c("-C", shQuote(official_repo), "rev-parse", "HEAD"), stdout = TRUE
)
stopifnot(identical(observed_commit, expected_commit))
stopifnot(getRversion() == "4.4.1")

if (!requireNamespace("remotes", quietly = TRUE)) {
  stop("The fixed environment is missing remotes")
}

install_cran_exact <- function(package, version, dependencies = FALSE) {
  installed <- requireNamespace(package, quietly = TRUE)
  correct <- installed &&
    utils::packageVersion(package) == package_version(version)
  if (!correct) {
    remotes::install_version(
      package,
      version = version,
      repos = "https://cloud.r-project.org",
      upgrade = "never",
      dependencies = dependencies,
      force = TRUE
    )
  }
}

# These exact historical builds are absent from the current conda index.
# Install their official CRAN/Bioconductor sources on top of the binary base.
install_cran_exact("Matrix", "1.7-0")
install_cran_exact("data.table", "1.16.0")
# The conda build rewrites this R package version as 1.0.13-1; restore the
# exact CRAN DESCRIPTION version recorded by every official tutorial.
install_cran_exact("Rcpp", "1.0.13")
# glmGamPoi 1.16.0 declares C++11. RcppArmadillo 15 switched its bundled
# Armadillo headers to C++14, so use the last 2024-era release compatible
# with the tutorial's R 4.4.1 / Bioconductor 3.19 stack.
install_cran_exact("RcppArmadillo", "14.0.2-1")
# All eight official tutorial sessionInfo blocks record patchwork 1.2.0.
# Newer patchwork releases import ggplot2::is_ggplot, which is absent from
# the tutorial's fixed ggplot2 3.5.1.
install_cran_exact("patchwork", "1.2.0")

if (!requireNamespace("BiocManager", quietly = TRUE)) {
  stop("The fixed environment is missing BiocManager")
}
BiocManager::install(version = "3.19", ask = FALSE, update = FALSE)
for (package in c("ComplexHeatmap", "glmGamPoi")) {
  if (!requireNamespace(package, quietly = TRUE)) {
    BiocManager::install(
      package,
      version = "3.19",
      ask = FALSE,
      update = FALSE
    )
  }
}

# NMF imports Biobase, so install it only after the Bioconductor 3.19
# dependency layer has been established above.
install_cran_exact("NMF", "0.28", dependencies = NA)

presto_sha <- "7636b3d0465c468c35853f82f1717d3a64b3c8f6"
presto_ok <- requireNamespace("presto", quietly = TRUE) &&
  as.character(utils::packageVersion("presto")) == "1.0.0"
if (!presto_ok) {
  presto_archive <- file.path(
    download_cache,
    sprintf("presto-%s.tar.gz", presto_sha)
  )
  if (!file.exists(presto_archive)) {
    status <- system2(
      "curl",
      c(
        "--fail", "--location", "--retry", "5", "--retry-all-errors",
        "--output", shQuote(paste0(presto_archive, ".part")),
        shQuote(sprintf(
          "https://codeload.github.com/immunogenomics/presto/tar.gz/%s",
          presto_sha
        ))
      )
    )
    if (!identical(status, 0L)) {
      stop("Failed to download the pinned presto source archive")
    }
    file.rename(paste0(presto_archive, ".part"), presto_archive)
  }
  remotes::install_local(
    presto_archive,
    upgrade = "never",
    dependencies = FALSE
  )
}

spatial_ok <- requireNamespace("SpatialEcoTyper", quietly = TRUE) &&
  as.character(utils::packageVersion("SpatialEcoTyper")) == "1.0.2"
if (!spatial_ok) {
  remotes::install_local(
    official_repo,
    upgrade = "never",
    dependencies = FALSE,
    force = TRUE
  )
}

required_versions <- c(
  SpatialEcoTyper = "1.0.2",
  presto = "1.0.0",
  Seurat = "5.1.0",
  SeuratObject = "5.0.2",
  Matrix = "1.7.0",
  RcppArmadillo = "14.0.2.1",
  patchwork = "1.2.0",
  NMF = "0.28",
  data.table = "1.16.0",
  dplyr = "1.1.4",
  tidyr = "1.3.1",
  ggplot2 = "3.5.1",
  Rcpp = "1.0.13",
  RANN = "2.6.2",
  pals = "1.9",
  R.utils = "2.12.3",
  hdf5r = "1.3.11",
  ComplexHeatmap = "2.20.0",
  glmGamPoi = "1.16.0"
)
observed_versions <- vapply(
  names(required_versions),
  function(package) as.character(utils::packageVersion(package)),
  character(1)
)
bad <- names(required_versions)[observed_versions != required_versions]
if (length(bad)) {
  stop(sprintf(
    "Version mismatch: %s",
    paste(sprintf(
      "%s expected %s observed %s",
      bad, required_versions[bad], observed_versions[bad]
    ), collapse = "; ")
  ))
}

writeLines(
  capture.output(utils::sessionInfo()),
  file.path(environment_dir, "sessionInfo.txt")
)

installed <- as.data.frame(utils::installed.packages(), stringsAsFactors = FALSE)
installed$Package <- rownames(installed)
inventory_fields <- c(
  "Package", "Version", "LibPath", "Priority", "Depends", "Imports",
  "LinkingTo", "Repository"
)
for (field in setdiff(inventory_fields, names(installed))) {
  installed[[field]] <- NA_character_
}
installed <- installed[, inventory_fields]
write.table(
  installed,
  file.path(manifest_dir, "installed-packages.tsv"),
  sep = "\t",
  row.names = FALSE,
  quote = FALSE,
  na = ""
)

provenance <- data.frame(
  component = c("SpatialEcoTyper", "presto"),
  version = c("1.0.2", "1.0.0"),
  git_commit = c(expected_commit, presto_sha),
  source = c(
    "local full-history official repository",
    "official immunogenomics/presto tag 1.0.0"
  )
)
write.table(
  provenance,
  file.path(manifest_dir, "source-provenance.tsv"),
  sep = "\t",
  row.names = FALSE,
  quote = FALSE
)

lock_project <- file.path(data_root, "work", "environment-lock")
dir.create(lock_project, recursive = TRUE, showWarnings = FALSE)
if (!file.exists(file.path(lock_project, "renv.lock"))) {
  renv::init(project = lock_project, bare = TRUE, restart = FALSE)
}
renv::settings$bioconductor.version("3.19", project = lock_project)
renv::snapshot(
  project = lock_project,
  lockfile = file.path(manifest_dir, "renv.lock"),
  library = unique(installed$LibPath),
  type = "all",
  packages = installed$Package,
  repos = BiocManager::repositories(version = "3.19"),
  prompt = FALSE,
  # The official tutorial session itself records units 1.0-1 alongside
  # Rcpp 1.0.13 even though units now declares Rcpp >= 1.1.0. Preserve that
  # historical state and let the execution tests decide runtime compatibility.
  force = TRUE
)

message("fixed official R environment: PASS")
