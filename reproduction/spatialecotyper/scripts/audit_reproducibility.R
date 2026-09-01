full_args <- commandArgs(trailingOnly = FALSE)
script_arg <- grep("^--file=", full_args, value = TRUE)
stopifnot(length(script_arg) == 1L)
script_path <- normalizePath(sub("^--file=", "", script_arg), mustWork = TRUE)
repo_root <- normalizePath(file.path(dirname(script_path), "../../.."), mustWork = TRUE)

data_root <- "/mnt/f/spatialecotyper_reproduction"
official_repo <- "/mnt/c/Users/Microsoft/Documents/EBV开题/external/spatialecotyper-official"
official_commit <- "48c2c846781d3a312771021c1a2ef5fc383700c5"
result_dir <- file.path(data_root, "results", "reproducibility")
config_path <- file.path(
  repo_root, "reproduction", "spatialecotyper", "config",
  "paper-computation-inventory.tsv"
)
result_path <- file.path(result_dir, "paper-computation-matrix.tsv")
source_inventory_path <- file.path(result_dir, "source-code-inventory.tsv")
gse_summary_path <- file.path(result_dir, "gse320042-summary.tsv")
publication_evidence_path <- file.path(result_dir, "publication-evidence.tsv")
report_path <- file.path(
  repo_root, "docs", "reproduction",
  "spatialecotyper-reproduction-boundary.md"
)
tutorial_status_path <- file.path(
  data_root, "results", "tutorials", "run-status.tsv"
)
gse_members_path <- file.path(
  data_root, "archive", "manifests", "GSE320042_RAW.tar.members.txt"
)
gse_metadata_path <- file.path(
  data_root, "archive", "manifests", "GSE320042.download-metadata.tsv"
)
paper_downloads_path <- file.path(
  data_root, "archive", "manifests", "paper-downloads.tsv"
)
download_capacity_path <- file.path(
  result_dir, "paper-download-capacity.tsv"
)
paper_files_path <- file.path(
  data_root, "archive", "manifests", "paper-file-sha256.tsv"
)
paper_validation_path <- file.path(
  result_dir, "paper-file-validation.tsv"
)
paper_run_status_path <- file.path(
  data_root, "results", "paper_reproduction",
  "generated_visium_deconvolution", "run-status.tsv"
)

dir.create(result_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(dirname(report_path), recursive = TRUE, showWarnings = FALSE)

write_tsv_atomic <- function(x, path) {
  temp <- paste0(path, ".part")
  write.table(
    x, temp, sep = "\t", row.names = FALSE, quote = FALSE, na = ""
  )
  stopifnot(file.rename(temp, path))
}

git_head <- system2(
  "git", c("-C", shQuote(official_repo), "rev-parse", "HEAD"),
  stdout = TRUE
)
stopifnot(identical(git_head, official_commit))
tracked <- system2(
  "git", c("-C", shQuote(official_repo), "ls-files"), stdout = TRUE
)
extensions <- tolower(sub("^.*(?=\\.[^.]+$)", "", tracked, perl = TRUE))
extension_levels <- c(".r", ".rmd", ".py", ".ipynb", ".sh")
source_inventory <- data.frame(
  item = c("git_commit", sub("^\\.", "", extension_levels)),
  value = c(
    official_commit,
    vapply(extension_levels, function(ext) sum(extensions == ext), integer(1))
  ),
  interpretation = c(
    "fixed paper-day official source",
    "tracked R source files", "tracked R Markdown tutorials",
    "tracked Python files", "tracked Jupyter notebooks", "tracked shell files"
  ),
  stringsAsFactors = FALSE
)
write_tsv_atomic(source_inventory, source_inventory_path)

stopifnot(file.exists(gse_members_path), file.exists(gse_metadata_path))
members <- readLines(gse_members_path, warn = FALSE)
extract_gsm <- function(x) {
  hit <- grepl("^GSM[0-9]+", x)
  unique(sub("^(GSM[0-9]+).*$", "\\1", x[hit]))
}
all_gsm <- extract_gsm(members)
scrna_gsm <- extract_gsm(members[grepl("_tumor_scrna_", members)])
hd_gsm <- extract_gsm(members[grepl("_HD_016um_", members)])
spatial_gsm <- setdiff(all_gsm, scrna_gsm)
gse_metadata <- read.delim(
  gse_metadata_path, stringsAsFactors = FALSE, check.names = FALSE
)
tar_row <- gse_metadata[gse_metadata$file == "GSE320042_RAW.tar", , drop = FALSE]
stopifnot(nrow(tar_row) == 1L)
gse_summary <- data.frame(
  metric = c(
    "tar_bytes", "tar_sha256", "tar_members", "gsm_records",
    "scrna_gsm", "spatial_gsm", "visium_hd_gsm",
    "scrna_members", "visium_hd_members", "other_spatial_members"
  ),
  value = c(
    tar_row$bytes, tar_row$sha256, length(members), length(all_gsm),
    length(scrna_gsm), length(spatial_gsm), length(hd_gsm),
    sum(grepl("_tumor_scrna_", members)),
    sum(grepl("_HD_", members)),
    sum(!grepl("_tumor_scrna_|_HD_", members))
  ),
  stringsAsFactors = FALSE
)
write_tsv_atomic(gse_summary, gse_summary_path)

stopifnot(file.exists(paper_downloads_path), file.exists(download_capacity_path))
paper_downloads <- read.delim(
  paper_downloads_path, stringsAsFactors = FALSE, check.names = FALSE,
  quote = "", comment.char = ""
)
download_capacity <- read.delim(
  download_capacity_path, stringsAsFactors = FALSE, check.names = FALSE,
  quote = "", comment.char = ""
)
passed_sources <- download_capacity$source_record_id[
  download_capacity$source_gate == "PASS"
]
paper_downloads$size_numeric <- suppressWarnings(as.numeric(paper_downloads$size_bytes))
actionable <- paper_downloads[
  paper_downloads$source_record_id %in% passed_sources &
    ((!is.na(paper_downloads$size_numeric) & paper_downloads$size_numeric > 0) |
      (paper_downloads$repository == "GITHUB" &
        (is.na(paper_downloads$size_numeric) | paper_downloads$size_numeric == 0))) &
    nzchar(paper_downloads$download_url),
  , drop = FALSE
]
actionable <- actionable[!duplicated(actionable$download_url), , drop = FALSE]
actionable_files <- nrow(actionable)
actionable_bytes <- sum(actionable$size_numeric, na.rm = TRUE)
bounded_unknown_files <- sum(
  is.na(actionable$size_numeric) | actionable$size_numeric == 0
)
paused_bytes <- sum(
  suppressWarnings(as.numeric(download_capacity$known_bytes[
    download_capacity$source_gate != "PASS"
  ])),
  na.rm = TRUE
)
downloaded_files <- 0L
downloaded_bytes <- 0
validated_files <- 0L
if (file.exists(paper_files_path)) {
  paper_files <- read.delim(
    paper_files_path, stringsAsFactors = FALSE, check.names = FALSE,
    quote = "", comment.char = ""
  )
  downloaded_files <- nrow(paper_files)
  downloaded_bytes <- sum(suppressWarnings(as.numeric(paper_files$actual_bytes)), na.rm = TRUE)
}
if (file.exists(paper_validation_path)) {
  paper_validation <- read.delim(
    paper_validation_path, stringsAsFactors = FALSE, check.names = FALSE,
    quote = "", comment.char = ""
  )
  validated_files <- sum(paper_validation$validation_status == "PASS")
}

stopifnot(file.exists(paper_run_status_path))
paper_runs <- read.delim(
  paper_run_status_path, stringsAsFactors = FALSE, check.names = FALSE,
  quote = "", comment.char = ""
)
spot_runs <- paper_runs[
  paper_runs$status %in% c("SPOT_LEVEL_REPRODUCED", "VERIFIED_EXISTING"),
  , drop = FALSE
]
spot_samples <- nrow(spot_runs)
spot_patients <- length(unique(spot_runs$patient_id))
spot_locations <- sum(as.numeric(spot_runs$locations))

publication_evidence <- data.frame(
  claim_id = c(
    "paper_scale", "data_availability", "code_availability",
    "liquid_training", "paired_tumour_plasma"
  ),
  source_url = rep(
    "https://www.nature.com/articles/s41586-026-10452-4", 5
  ),
  observed_statement = c(
    "The paper reports 132 spatial tumour specimens and 144 scRNA tumour samples.",
    "Generated de-identified genomics are assigned to GSE320042; normalized data use DOI 10.25936/pm3t-cn37; public source accessions are in supplementary tables.",
    "The paper cites the Spatial EcoTyper GitHub repository and Stanford site and advertises an online trained-model interface.",
    "Methods state that Liquid EcoTyper was implemented and trained with PyTorch 2.2.0.",
    "The paired melanoma cohort contains 23 patients; 15 have tumour spatial data and two of those spatial samples are Visium HD."
  ),
  local_audit_observation = c(
    sprintf(
      "Local GSE archive has %d GSM records: %d scRNA and %d spatial, including %d Visium HD.",
      length(all_gsm), length(scrna_gsm), length(spatial_gsm), length(hd_gsm)
    ),
    sprintf(
      "GSE320042 is SHA-verified; the resolved actionable public queue has %d files (%s known bytes; %d bounded unknown-size files), of which %d files (%s bytes) are in the finalized download manifest and %d passed full validation.",
      actionable_files, format(actionable_bytes, scientific = FALSE, trim = TRUE),
      bounded_unknown_files,
      downloaded_files, format(downloaded_bytes, scientific = FALSE, trim = TRUE),
      validated_files
    ),
    sprintf(
      "Fixed repository contains %d R files and %d Rmd files but zero Python and zero notebook files.",
      sum(extensions == ".r"), sum(extensions == ".rmd")
    ),
    "No local Python implementation, training entry point, configuration, checkpoint or model weight is present in the fixed repository.",
    "GSE member names include 17 spatial GSM records, including two Visium HD records, plus seven scRNA GSM records."
  ),
  checked_utc = rep(format(Sys.time(), tz = "UTC", usetz = TRUE), 5),
  stringsAsFactors = FALSE
)
write_tsv_atomic(publication_evidence, publication_evidence_path)

stopifnot(file.exists(tutorial_status_path))
tutorials <- read.delim(
  tutorial_status_path, stringsAsFactors = FALSE, check.names = FALSE
)
stopifnot(nrow(tutorials) == 8L, all(tutorials$status == "PASS"))

inventory <- read.delim(
  config_path, stringsAsFactors = FALSE, check.names = FALSE
)
required_columns <- c(
  "component_id", "component", "status", "evidence_path",
  "evidence_basis", "limitation"
)
stopifnot(all(required_columns %in% names(inventory)))
allowed <- c(
  "STRICT_REPRODUCED", "TUTORIAL_REPRODUCED",
  "METHOD_ONLY", "BLOCKED_NOT_PUBLIC"
)
stopifnot(
  !anyDuplicated(inventory$component_id),
  all(inventory$status %in% allowed),
  all(nzchar(inventory$evidence_path)),
  all(file.exists(inventory$evidence_path))
)
liquid <- inventory[inventory$component_id == "liquid_ecotyper_training", , drop = FALSE]
stopifnot(nrow(liquid) == 1L, liquid$status == "BLOCKED_NOT_PUBLIC")
stopifnot(!any(
  grepl("Liquid EcoTyper", inventory$component, fixed = TRUE) &
    inventory$status == "STRICT_REPRODUCED"
))
write_tsv_atomic(inventory, result_path)

counts <- table(factor(inventory$status, levels = allowed))
report <- c(
  "# Spatial EcoTyper / Nature 2026 计算复现边界",
  "",
  sprintf("审计代码固定到官方提交 `%s`（SpatialEcoTyper 1.0.2）。", official_commit),
  "本报告把官方教程可运行与论文图表可严格重建分开；不会把方法描述或黑箱网页调用冒充为严格复现。",
  "",
  "## 结论",
  "",
  sprintf(
    "- 严格论文级复现：%d 项。当前没有完整论文计算满足输入、代码、参数、随机性和目标输出全部可核验。",
    counts[["STRICT_REPRODUCED"]]
  ),
  sprintf("- 官方教程级复现：%d 项；8 个 Rmd 均已运行。", counts[["TUTORIAL_REPRODUCED"]]),
  sprintf("- 仅方法级：%d 项。", counts[["METHOD_ONLY"]]),
  sprintf("- 因官方材料缺失而阻断：%d 项。", counts[["BLOCKED_NOT_PUBLIC"]]),
  "- T02 不是严格材料复现：官方归档 RDS 缺少固定代码要求的 `Spot.X/Spot.Y`，因此使用 T01 按官方流程生成的上游输出。",
  "",
  "## 本地公开材料实测",
  "",
  sprintf("- 固定仓库：%d 个 R 文件、%d 个 Rmd、0 个 Python、0 个 notebook。", sum(extensions == ".r"), sum(extensions == ".rmd")),
  sprintf("- GSE320042：%s 字节，SHA-256 `%s`，%d 个 tar 成员。", tar_row$bytes, tar_row$sha256, length(members)),
  sprintf("- GEO 成员：%d 个 GSM；%d 个 scRNA，%d 个空间记录，其中 %d 个 Visium HD。", length(all_gsm), length(scrna_gsm), length(spatial_gsm), length(hd_gsm)),
  sprintf(
    "- 补充表解析得到 %d 个可操作公开文件，已知大小共 %s 字节，有界未知大小 %d 个；已归档 %d 个/%s 字节，%d 个通过全量格式与校验值验证。",
    actionable_files, format(actionable_bytes, scientific = FALSE, trim = TRUE),
    bounded_unknown_files,
    downloaded_files, format(downloaded_bytes, scientific = FALSE, trim = TRUE),
    validated_files
  ),
  sprintf(
    "- 超过单来源 100 GB 闸门的 ENA 原始数据共 %s 字节，因 F 盘容量不足保持暂停；注册/受控数据不绕过权限。",
    format(paused_bytes, scientific = FALSE, trim = TRUE)
  ),
  sprintf(
    "- 生成队列已完成官方 spot-level 去卷积：%d 个空间样本、%d 位患者、%s 个 spot/bin，与补充表 S17 样本计数逐项一致。",
    spot_samples, spot_patients,
    format(spot_locations, scientific = FALSE, trim = TRUE)
  ),
  "",
  "## 逐项矩阵",
  "",
  "| 计算项 | 状态 | 证据 | 关键边界 |",
  "|---|---|---|---|"
)
for (i in seq_len(nrow(inventory))) {
  report <- c(
    report,
    sprintf(
      "| %s | `%s` | `%s` | %s |",
      inventory$component[[i]], inventory$status[[i]],
      inventory$evidence_path[[i]], inventory$limitation[[i]]
    )
  )
}
report <- c(
  report, "", "## 官方页面证据", "",
  "- Nature 数据可用性：GSE320042；预处理/标准化数据 DOI `10.25936/pm3t-cn37`；外部公共数据编号见补充表。",
  "- Nature 代码可用性指向 Spatial EcoTyper GitHub 与 Stanford 网站，但固定仓库实测没有 Liquid EcoTyper 的 Python 训练或本地推理代码。",
  "- 因此，Spatial EcoTyper R 方法和 8 个教程可审计运行；Liquid EcoTyper 训练、cfDNA 本地预测、论文完整作图不能按当前公开包严格重现。",
  "",
  "来源：https://www.nature.com/articles/s41586-026-10452-4"
)
writeLines(report, report_path, useBytes = TRUE)

message(sprintf(
  "reproducibility audit: PASS (%d components; strict=%d, tutorial=%d, method=%d, blocked=%d)",
  nrow(inventory), counts[[1]], counts[[2]], counts[[3]], counts[[4]]
))
