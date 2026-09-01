expected <- c(
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

stopifnot(getRversion() == "4.4.1")
observed <- vapply(
  names(expected),
  function(package) as.character(utils::packageVersion(package)),
  character(1)
)
stopifnot(identical(unname(observed), unname(expected)))
message(sprintf("fixed R environment: PASS (%d packages)", length(expected)))
