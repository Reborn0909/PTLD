# Spatial EcoTyper Official Reproduction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 WSL2 中建立版本固定、可审计的 Spatial EcoTyper 官方复现环境，归档 21 个教程文件和 GSE320042，依次运行 8 个官方教程，界定论文计算的严格复现边界，最后仅增加 PTLD 输入、QC 与调用接口适配层。

**Architecture:** 代码与小型清单保存在当前 Git 项目；大型数据、包缓存、中间文件和结果统一保存在 `F:\spatialecotyper_reproduction`。官方算法固定到论文日提交 `48c2c846781d3a312771021c1a2ef5fc383700c5`（SpatialEcoTyper 1.0.2），8 个官方 Rmd 保持只读；包装脚本只管理环境、下载、路径、执行顺序、日志和验证，不修改 Spatial EcoTyper 函数。

**Tech Stack:** Windows 11、WSL2 Ubuntu 24.04、micromamba、R 4.4.1、renv、SpatialEcoTyper 1.0.2、Seurat 5.1.0、Matrix 1.7-0、NMF 0.28、Bash、Rscript、SHA-256。

## Global Constraints

- 官方代码源固定为 `C:\Users\Microsoft\Documents\EBV开题\external\spatialecotyper-official` 的提交 `48c2c846781d3a312771021c1a2ef5fc383700c5`。
- 官方教程源固定为该提交中的 8 个 `vignettes/*.Rmd`；不得改写算法代码或统计参数。
- 教程文件清单必须从固定提交的 Rmd 中抽取，预期恰好为 21 个唯一的 Stanford 官方 URL。
- F盘根目录固定为 `F:\spatialecotyper_reproduction`，对应 WSL 路径 `/mnt/f/spatialecotyper_reproduction`。
- F盘一级数据层必须包含且仅以 `raw/`、`archive/`、`work/`、`cache/`、`results/` 为职责边界；日志放在 `results/logs/`。
- 所有下载先写入 `.part`，成功后原子重命名；所有归档文件生成 SHA-256、字节数、URL、UTC 下载时间和 HTTP 元数据。
- GSE320042 只从 NCBI GEO 官方目录下载：`https://ftp.ncbi.nlm.nih.gov/geo/series/GSE320nnn/GSE320042/suppl/`。
- 严格复现、教程级复现、方法级复现和不可复现必须分开标记；不得把缺失的 Liquid EcoTyper PyTorch、论文完整作图脚本或未公开预处理代码标为已复现。
- PTLD 阶段只允许输入格式、QC、细胞类型映射、批量调用和结果整理；不得修改 `R/` 下的官方算法。
- 当前官方材料没有提供 `renv.lock`；环境采用官方 HTML `sessionInfo()` 重建并显式记录这一证据缺口。

---

### Task 1: 固化官方来源、教程顺序与环境证据

**Files:**
- Create: `reproduction/spatialecotyper/config/source-lock.tsv`
- Create: `reproduction/spatialecotyper/config/tutorial-order.tsv`
- Create: `reproduction/spatialecotyper/scripts/extract_official_manifest.R`
- Create: `reproduction/spatialecotyper/tests/test_source_lock.R`

**Interfaces:**
- Consumes: 固定提交中的 `DESCRIPTION`、`vignettes/*.Rmd`、`docs/articles/*.html`。
- Produces: `source-lock.tsv`、`tutorial-order.tsv`、F盘 `archive/manifests/tutorial-files.tsv` 和 `archive/manifests/official-session-packages.tsv`。

- [ ] **Step 1: 写入来源锁和教程顺序测试**

```r
source_lock <- read.delim("reproduction/spatialecotyper/config/source-lock.tsv", check.names = FALSE)
stopifnot(source_lock$value[source_lock$key == "git_commit"] ==
            "48c2c846781d3a312771021c1a2ef5fc383700c5")
stopifnot(source_lock$value[source_lock$key == "package_version"] == "1.0.2")

order <- read.delim("reproduction/spatialecotyper/config/tutorial-order.tsv")
stopifnot(identical(order$order, 1:8))
stopifnot(identical(order$rmd, c(
  "SingleSample.Rmd", "Integration.Rmd", "TrainRecoveryModel.Rmd",
  "Discovery_SE_CellStates.Rmd", "Recovery_scST.Rmd",
  "Recovery_scRNA.Rmd", "TrainDeconvModel.Rmd", "Recovery_Bulk.Rmd"
)))
```

- [ ] **Step 2: 运行测试并确认在文件创建前失败**

Run:

```bash
wsl.exe -d Ubuntu -- bash -lc 'cd /mnt/c/Users/Microsoft/Documents/EBV开题 && Rscript reproduction/spatialecotyper/tests/test_source_lock.R'
```

Expected: FAIL，原因是 `source-lock.tsv` 或 `tutorial-order.tsv` 尚不存在。

- [ ] **Step 3: 写入固定来源清单**

`source-lock.tsv` 必须包含：`git_commit`、`package_version`、`r_version`、`seurat_version`、`matrix_version`、`nmf_version`、`geo_accession`、`geo_raw_url`。对应值分别为 `48c2c846...`、`1.0.2`、`4.4.1`、`5.1.0`、`1.7-0`、`0.28`、`GSE320042`、`https://ftp.ncbi.nlm.nih.gov/geo/series/GSE320nnn/GSE320042/suppl/GSE320042_RAW.tar`。

- [ ] **Step 4: 实现官方清单抽取脚本**

脚本必须：

```r
repo <- normalizePath(commandArgs(trailingOnly = TRUE)[1], mustWork = TRUE)
out <- commandArgs(trailingOnly = TRUE)[2]
rmd <- list.files(file.path(repo, "vignettes"), "\\.Rmd$", full.names = TRUE)
text <- unlist(lapply(rmd, readLines, warn = FALSE), use.names = FALSE)
pattern <- "https://spatialecotyper\\.stanford\\.edu/inc/inc\\.public\\.vignettes\\.php\\?file=[^\\\"') ]+"
urls <- sort(unique(unlist(regmatches(text, gregexpr(pattern, text, perl = TRUE)))))
stopifnot(length(urls) == 21L)
manifest <- data.frame(
  file = sub("^.*[?]file=", "", urls),
  url = urls,
  source_commit = "48c2c846781d3a312771021c1a2ef5fc383700c5"
)
write.table(manifest, file.path(out, "tutorial-files.tsv"), sep = "\t",
            row.names = FALSE, quote = FALSE)
```

并从 8 个本地官方 HTML 的 `sessionInfo()` 输出抽取包名与版本；相同包出现多个版本时保留教程名和版本，不静默合并。

- [ ] **Step 5: 运行测试与清单抽取**

Run:

```bash
Rscript reproduction/spatialecotyper/tests/test_source_lock.R
Rscript reproduction/spatialecotyper/scripts/extract_official_manifest.R \
  external/spatialecotyper-official \
  /mnt/f/spatialecotyper_reproduction/archive/manifests
```

Expected: 测试 PASS；`tutorial-files.tsv` 恰好 21 行数据；关键包版本与官方 HTML 一致。

- [ ] **Step 6: 提交 Task 1**

```bash
git add reproduction/spatialecotyper/config reproduction/spatialecotyper/scripts/extract_official_manifest.R reproduction/spatialecotyper/tests/test_source_lock.R
git commit -m "chore: lock Spatial EcoTyper official sources"
```

### Task 2: 建立 F 盘五层目录与可重复 WSL 环境

**Files:**
- Create: `reproduction/spatialecotyper/config/environment.yml`
- Create: `reproduction/spatialecotyper/scripts/bootstrap_wsl.sh`
- Create: `reproduction/spatialecotyper/scripts/record_environment.R`
- Create: `reproduction/spatialecotyper/tests/test_layout.sh`

**Interfaces:**
- Consumes: Task 1 的版本锁。
- Produces: `/mnt/f/spatialecotyper_reproduction` 五层目录、micromamba 环境 `spatialecotyper-1.0.2`、`results/environment/sessionInfo.txt`。

- [ ] **Step 1: 写入目录测试**

```bash
#!/usr/bin/env bash
set -euo pipefail
root=/mnt/f/spatialecotyper_reproduction
for d in raw archive work cache results; do
  test -d "$root/$d"
done
test -d "$root/results/logs"
test -d "$root/archive/manifests"
test -d "$root/raw/tutorial"
test -d "$root/raw/gse320042"
```

- [ ] **Step 2: 运行目录测试并确认失败**

Run: `bash reproduction/spatialecotyper/tests/test_layout.sh`

Expected: FAIL，因为F盘结构尚不存在。

- [ ] **Step 3: 实现幂等目录建立**

`bootstrap_wsl.sh` 使用一个固定数组创建：

```bash
root=/mnt/f/spatialecotyper_reproduction
mkdir -p \
  "$root/raw/tutorial" "$root/raw/gse320042" \
  "$root/archive/source" "$root/archive/manifests" \
  "$root/work/tutorials" "$root/work/gse320042" \
  "$root/cache/micromamba" "$root/cache/renv" "$root/cache/downloads" \
  "$root/results/tutorials" "$root/results/reproducibility" \
  "$root/results/ptld_adapter" "$root/results/environment" "$root/results/logs"
```

- [ ] **Step 4: 创建官方推荐的 Conda 路线环境**

`environment.yml` 固定核心版本：

```yaml
name: spatialecotyper-1.0.2
channels:
  - conda-forge
  - bioconda
dependencies:
  - r-base=4.4.1
  - r-seurat=5.1.0
  - r-matrix=1.7_0
  - r-nmf=0.28
  - bioconductor-complexheatmap=2.20.0
  - r-data.table=1.16.0
  - r-hdf5r=1.3.11
  - r-remotes
  - r-renv
  - r-rmarkdown
  - r-knitr
```

若 conda build 字符串导致求解失败，只允许放宽 build 字符串，不允许放宽上述版本；失败信息进入 `results/logs/environment-solve.log`。

- [ ] **Step 5: 安装固定提交并记录完整环境**

在环境内执行：

```r
options(repos = c(CRAN = "https://cloud.r-project.org"))
BiocManager::install(version = "3.19", ask = FALSE, update = FALSE)
remotes::install_github("immunogenomics/presto", upgrade = "never")
remotes::install_local(
  "/mnt/c/Users/Microsoft/Documents/EBV开题/external/spatialecotyper-official",
  upgrade = "never", dependencies = FALSE
)
stopifnot(as.character(packageVersion("SpatialEcoTyper")) == "1.0.2")
writeLines(capture.output(sessionInfo()),
           "/mnt/f/spatialecotyper_reproduction/results/environment/sessionInfo.txt")
```

同时生成 `explicit-conda-spec.txt`、`installed-packages.tsv` 和 `renv.lock`。`presto` 只有版本号而无论文日提交证据时，必须在环境报告中标为 `source_commit_unresolved`。

- [ ] **Step 6: 验证环境**

Run:

```bash
bash reproduction/spatialecotyper/tests/test_layout.sh
micromamba run -n spatialecotyper-1.0.2 Rscript -e \
  'stopifnot(getRversion()=="4.4.1", packageVersion("SpatialEcoTyper")=="1.0.2", packageVersion("Seurat")=="5.1.0")'
```

Expected: PASS，且 `sessionInfo.txt` 存在。

- [ ] **Step 7: 提交 Task 2**

```bash
git add reproduction/spatialecotyper/config/environment.yml reproduction/spatialecotyper/scripts/bootstrap_wsl.sh reproduction/spatialecotyper/scripts/record_environment.R reproduction/spatialecotyper/tests/test_layout.sh
git commit -m "build: add fixed WSL reproduction environment"
```

### Task 3: 下载并校验21个官方教程文件

**Files:**
- Create: `reproduction/spatialecotyper/scripts/download_manifest.sh`
- Create: `reproduction/spatialecotyper/scripts/verify_sha256.sh`
- Create: `reproduction/spatialecotyper/tests/test_tutorial_archive.sh`

**Interfaces:**
- Consumes: `archive/manifests/tutorial-files.tsv`。
- Produces: `raw/tutorial/*`、`archive/manifests/tutorial-files.downloaded.tsv`、`archive/manifests/tutorial-files.sha256`。

- [ ] **Step 1: 写入失败优先的归档测试**

测试必须断言：清单为21行；21个文件均为非零字节；下载清单每行都有64位小写SHA-256；`sha256sum --check` 全部通过；不存在 `.part`。

- [ ] **Step 2: 运行测试并确认失败**

Run: `bash reproduction/spatialecotyper/tests/test_tutorial_archive.sh`

Expected: FAIL，因为文件未下载。

- [ ] **Step 3: 实现断点续传、原子落盘和元数据记录**

核心下载命令：

```bash
curl --fail --location --retry 5 --retry-all-errors \
  --continue-at - --output "$dest.part" "$url"
mv -- "$dest.part" "$dest"
sha256sum "$dest"
stat --printf='%s' "$dest"
```

脚本必须保留 URL、HTTP `ETag`/`Last-Modified`（若服务端返回）、字节数、SHA-256和UTC时间。

- [ ] **Step 4: 下载21个文件并验证**

Run:

```bash
bash reproduction/spatialecotyper/scripts/download_manifest.sh
bash reproduction/spatialecotyper/tests/test_tutorial_archive.sh
```

Expected: 21/21 下载成功，SHA-256检查 21/21 OK。

- [ ] **Step 5: 提交 Task 3**

```bash
git add reproduction/spatialecotyper/scripts/download_manifest.sh reproduction/spatialecotyper/scripts/verify_sha256.sh reproduction/spatialecotyper/tests/test_tutorial_archive.sh
git commit -m "feat: archive official Spatial EcoTyper tutorial data"
```

### Task 4: 按官方顺序运行8个教程

**Files:**
- Create: `reproduction/spatialecotyper/scripts/run_tutorials.R`
- Create: `reproduction/spatialecotyper/tests/test_tutorial_runs.R`

**Interfaces:**
- Consumes: 固定提交中的8个Rmd、锁定环境、21文件归档。
- Produces: `results/tutorials/T01` 至 `T08`、逐教程日志、状态表 `results/tutorials/run-status.tsv`。

- [ ] **Step 1: 写入运行状态测试**

```r
x <- read.delim("/mnt/f/spatialecotyper_reproduction/results/tutorials/run-status.tsv")
stopifnot(nrow(x) == 8L)
stopifnot(identical(x$order, 1:8))
stopifnot(all(x$status == "PASS"))
stopifnot(all(file.exists(x$rendered_html)))
```

- [ ] **Step 2: 运行测试并确认失败**

Run: `Rscript reproduction/spatialecotyper/tests/test_tutorial_runs.R`

Expected: FAIL，因为状态表不存在。

- [ ] **Step 3: 实现只读官方Rmd运行器**

运行器验证源Rmd的SHA-256后，逐个调用：

```r
rmarkdown::render(
  input = official_rmd,
  output_file = paste0(tools::file_path_sans_ext(basename(official_rmd)), ".html"),
  output_dir = result_dir,
  knit_root_dir = work_dir,
  clean = FALSE,
  envir = new.env(parent = globalenv()),
  quiet = FALSE
)
```

每个教程分别记录开始/结束UTC、耗时、峰值内存（若 `/usr/bin/time -v` 可用）、退出码、Rmd SHA-256、环境锁SHA-256、HTML路径。失败即停止后续教程，不伪造PASS。

- [ ] **Step 4: 依次运行并验证8个教程**

Run:

```bash
micromamba run -n spatialecotyper-1.0.2 Rscript \
  reproduction/spatialecotyper/scripts/run_tutorials.R
micromamba run -n spatialecotyper-1.0.2 Rscript \
  reproduction/spatialecotyper/tests/test_tutorial_runs.R
```

Expected: 8/8 PASS；若任一失败，保存日志并进入调试，不继续GEO阶段。

- [ ] **Step 5: 提交 Task 4**

```bash
git add reproduction/spatialecotyper/scripts/run_tutorials.R reproduction/spatialecotyper/tests/test_tutorial_runs.R
git commit -m "test: run eight official Spatial EcoTyper tutorials"
```

### Task 5: 下载并归档 GSE320042

**Files:**
- Create: `reproduction/spatialecotyper/scripts/download_gse320042.sh`
- Create: `reproduction/spatialecotyper/tests/test_gse320042_archive.sh`

**Interfaces:**
- Consumes: NCBI GEO 官方 `GSE320042_RAW.tar` 与 `filelist.txt`。
- Produces: `raw/gse320042/GSE320042_RAW.tar`、`raw/gse320042/filelist.txt`、SHA-256与tar成员清单。

- [ ] **Step 1: 写入GEO归档测试**

测试断言：tar大于4,500,000,000字节；`tar -tf` 成功；无绝对路径和 `..` 路径成员；SHA-256文件可验证；官方 `filelist.txt` 已保存。

- [ ] **Step 2: 运行测试并确认失败**

Run: `bash reproduction/spatialecotyper/tests/test_gse320042_archive.sh`

Expected: FAIL，因为GEO文件不存在。

- [ ] **Step 3: 实现断点续传与归档审计**

使用：

```bash
curl --fail --location --retry 8 --retry-all-errors --continue-at - \
  --output GSE320042_RAW.tar.part \
  https://ftp.ncbi.nlm.nih.gov/geo/series/GSE320nnn/GSE320042/suppl/GSE320042_RAW.tar
mv GSE320042_RAW.tar.part GSE320042_RAW.tar
sha256sum GSE320042_RAW.tar > ../../archive/manifests/GSE320042_RAW.tar.sha256
tar -tf GSE320042_RAW.tar > ../../archive/manifests/GSE320042_RAW.tar.members.txt
```

- [ ] **Step 4: 下载并验证**

Run:

```bash
bash reproduction/spatialecotyper/scripts/download_gse320042.sh
bash reproduction/spatialecotyper/tests/test_gse320042_archive.sh
```

Expected: 下载约4.6GB；SHA-256通过；tar结构安全可读。

- [ ] **Step 5: 提交 Task 5**

```bash
git add reproduction/spatialecotyper/scripts/download_gse320042.sh reproduction/spatialecotyper/tests/test_gse320042_archive.sh
git commit -m "feat: archive GSE320042 with integrity metadata"
```

### Task 6: 建立论文计算复现边界矩阵

**Files:**
- Create: `reproduction/spatialecotyper/scripts/audit_reproducibility.R`
- Create: `reproduction/spatialecotyper/config/paper-computation-inventory.tsv`
- Create: `reproduction/spatialecotyper/tests/test_reproducibility_matrix.R`
- Create: `docs/reproduction/spatialecotyper-reproduction-boundary.md`

**Interfaces:**
- Consumes: 8教程结果、GSE清单、官方代码审计、论文方法与数据可用性说明。
- Produces: 可机器读取的复现矩阵和中文审计报告。

- [ ] **Step 1: 定义四级状态并写测试**

合法状态只能是：`STRICT_REPRODUCED`、`TUTORIAL_REPRODUCED`、`METHOD_ONLY`、`BLOCKED_NOT_PUBLIC`。测试必须拒绝空状态、无证据路径或把 Liquid EcoTyper 训练代码标为严格复现。

- [ ] **Step 2: 运行测试并确认失败**

Run: `Rscript reproduction/spatialecotyper/tests/test_reproducibility_matrix.R`

Expected: FAIL，因为矩阵尚未生成。

- [ ] **Step 3: 实现证据驱动审计**

矩阵至少逐项覆盖：单样本发现、多样本整合、恢复模型训练、SE特异细胞状态、scST恢复、scRNA恢复、bulk解卷积模型、bulk恢复、CytoSPACE上游预处理、完整论文作图、TCGA/ICI统计、Liquid EcoTyper PyTorch训练、cfDNA预测。

- [ ] **Step 4: 运行审计和测试**

Run:

```bash
Rscript reproduction/spatialecotyper/scripts/audit_reproducibility.R
Rscript reproduction/spatialecotyper/tests/test_reproducibility_matrix.R
```

Expected: 所有状态均有本地证据路径或官方缺失证据；报告明确区分算法教程复现与整篇Nature论文复现。

- [ ] **Step 5: 提交 Task 6**

```bash
git add reproduction/spatialecotyper/config/paper-computation-inventory.tsv reproduction/spatialecotyper/scripts/audit_reproducibility.R reproduction/spatialecotyper/tests/test_reproducibility_matrix.R docs/reproduction/spatialecotyper-reproduction-boundary.md
git commit -m "docs: define Spatial EcoTyper reproduction boundaries"
```

### Task 7: 增加不改算法的PTLD输入、QC与调用适配层

**Files:**
- Create: `reproduction/spatialecotyper/ptld/validate_input.R`
- Create: `reproduction/spatialecotyper/ptld/map_cell_types.R`
- Create: `reproduction/spatialecotyper/ptld/run_official_api.R`
- Create: `reproduction/spatialecotyper/ptld/README.md`
- Create: `reproduction/spatialecotyper/tests/test_ptld_adapter.R`

**Interfaces:**
- Consumes: genes×cells计数矩阵；行名与细胞ID一致且至少含 `X`、`Y`、`CellType`、`SampleID` 的元数据；显式细胞类型映射表。
- Produces: QC报告、官方API可直接接收的矩阵/元数据、逐样本官方 `SpatialEcoTyper()` 结果；不修改官方包。

- [ ] **Step 1: 写PTLD适配器失败测试**

测试覆盖：重复细胞ID、矩阵/元数据ID不一致、非有限坐标、负计数、空细胞类型、未知映射、样本内细胞不足；同时用一个最小合法示例验证返回对象只包含标准化输入和QC，不改变表达值。

- [ ] **Step 2: 运行测试并确认失败**

Run: `Rscript reproduction/spatialecotyper/tests/test_ptld_adapter.R`

Expected: FAIL，因为适配函数尚不存在。

- [ ] **Step 3: 实现输入验证和显式映射**

`validate_ptld_input(counts, metadata)` 返回 `list(counts, metadata, qc)`；`map_ptld_cell_types(metadata, mapping)` 对未知类型直接报错，不允许自动猜测。

- [ ] **Step 4: 实现官方API薄包装**

```r
run_ptld_spatialecotyper <- function(normdata, metadata, outprefix,
                                     nfeatures = 300L, radius = 50,
                                     ncores = 2L) {
  SpatialEcoTyper::SpatialEcoTyper(
    normdata, metadata,
    outprefix = outprefix,
    nfeatures = nfeatures,
    radius = radius,
    ncores = ncores
  )
}
```

默认值逐字沿用官方 Tutorial 1；任何PTLD参数变化必须由单独配置文件明确记录，包装函数不得复制或改写官方内部函数。

- [ ] **Step 5: 运行PTLD适配器测试**

Run: `Rscript reproduction/spatialecotyper/tests/test_ptld_adapter.R`

Expected: PASS；官方包源码目录的 `git status --short` 为空；固定提交仍为 `48c2c846...`。

- [ ] **Step 6: 提交 Task 7**

```bash
git add reproduction/spatialecotyper/ptld reproduction/spatialecotyper/tests/test_ptld_adapter.R
git commit -m "feat: add non-invasive PTLD adapter for official API"
```

### Task 8: 全链路验收与空间审计

**Files:**
- Create: `reproduction/spatialecotyper/scripts/final_audit.sh`
- Create: `docs/reproduction/spatialecotyper-runbook.md`

**Interfaces:**
- Consumes: Tasks 1–7 的全部清单、日志、结果和测试。
- Produces: `results/reproducibility/final-audit.txt`、磁盘占用表、失败恢复说明和用户操作手册。

- [ ] **Step 1: 实现全链路验收**

验收脚本必须检查：源提交和源码工作树、环境版本、F盘五层目录、21文件SHA、8教程状态、GSE SHA与tar成员、复现矩阵合法性、PTLD适配器测试、F盘各层字节数。

- [ ] **Step 2: 运行全部验证**

Run:

```bash
bash reproduction/spatialecotyper/scripts/final_audit.sh
```

Expected: 每项输出 `PASS` 或明确 `BLOCKED_NOT_PUBLIC`；不得用 `SKIP` 掩盖失败。

- [ ] **Step 3: 编写运行手册**

手册给出：首次建立、断点续传、单教程重跑、全部教程重跑、GEO校验、日志定位、清缓存而不删raw/archive、PTLD输入示例和复现状态解释。

- [ ] **Step 4: 提交 Task 8**

```bash
git add reproduction/spatialecotyper/scripts/final_audit.sh docs/reproduction/spatialecotyper-runbook.md
git commit -m "docs: add audited Spatial EcoTyper reproduction runbook"
```

## Self-Review

- Spec coverage: WSL独立环境、F盘五层目录、21文件与SHA、8教程、GSE320042、论文复现边界、PTLD薄适配均有独立任务和验收。
- Completeness scan: 每个任务都有具体文件、命令、预期结果和提交点，不含待补内容。
- Type consistency: 教程顺序由同一个 `tutorial-order.tsv` 驱动；下载清单由同一个抽取脚本产生；所有路径统一使用 `/mnt/f/spatialecotyper_reproduction`。
- Known evidence gap: 官方未提供 `renv.lock`，且 `presto 1.0.0` 的论文日Git SHA不能由 `sessionInfo()`恢复；计划要求显式记录而非伪造严格一致。

