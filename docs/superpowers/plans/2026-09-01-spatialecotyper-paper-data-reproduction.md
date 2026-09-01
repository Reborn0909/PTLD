# Spatial EcoTyper Paper Data Reproduction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 按 Nature 原文、补充表和作者官方数据入口，完整归档可公开获得的论文输入数据，逐文件校验来源、字节数与 SHA-256，并在不修改 Spatial EcoTyper 算法的前提下尽可能完成论文级计算复现。

**Architecture:** 当前 Git 项目只保存脚本、测试、清单和小型报告；大型数据继续进入 `/mnt/f/spatialecotyper_reproduction` 的 `raw/archive/work/cache/results` 五层目录。补充表 S1、S2、S8、S12、S15、S17 是样本与队列的规范来源；作者 DOI 数据、GEO/Zenodo/Mendeley/10x/Vizgen 等公开仓库只按表中 accession 或 URL 解析。先做 HEAD/API 容量闸门，再以可续传方式下载，最后以官方代码接口验证可执行计算；登录、数据使用协议或未公开脚本造成的边界必须如实标记。

**Tech Stack:** Windows 11、WSL2 Ubuntu 24.04、PowerShell、Bash、Python 3、R 4.4.1、SpatialEcoTyper 1.0.2、curl/wget、NCBI E-utilities/GEO、Zenodo API、SHA-256、TSV/JSON。

## Global Constraints

- 原文固定为 DOI `10.1038/s41586-026-10452-4`；官方附件固定为 `MOESM1_ESM.pdf`、`MOESM2_ESM.pdf`、`MOESM3_ESM.xlsx`。
- 官方算法继续固定到提交 `48c2c846781d3a312771021c1a2ef5fc383700c5`，不得修改官方 `R/`、`vignettes/` 或统计参数。
- 数据队列只能来自原文 Data availability、Supplementary Tables S1/S2/S8/S12/S15/S17 以及它们直接引用的官方仓库。
- 优先归档作者实际用于分析的 processed/normalized 数据；原始 FASTQ 仅在补充表明确要求、公开可获得且容量闸门通过时下载。
- 所有网络文件先写 `.part`，支持断点续传，成功后原子重命名；每个文件记录 URL、accession、字节数、SHA-256、UTC 时间、HTTP ETag/Last-Modified 和下载状态。
- F盘职责边界保持不变：`raw/` 原始公开数据，`archive/` 原文附件/清单/不可变快照，`work/` 解压与计算输入，`cache/` 可重建下载缓存，`results/` 日志/验证/复现结果。
- 登录、受控访问、数据使用协议或注册要求不得绕过；这些数据写入 access ledger 并标记 `CONTROLLED` 或 `REGISTRATION_REQUIRED`。
- 任何“严格复现”必须同时满足：原文输入公开、官方代码公开、版本与参数可定位、运行成功、关键样本数和产物通过验证。
- 下载前必须记录预计总容量和 F盘余量；单个来源超过 100 GB 或预计总量超过剩余空间 70% 时暂停该来源，不影响其他来源继续。

---

### Task 1: 归档论文、附件与规范样本表

**Files:**
- Create: `reproduction/spatialecotyper/config/paper-source-lock.tsv`
- Create: `reproduction/spatialecotyper/scripts/archive_paper_sources.py`
- Create: `reproduction/spatialecotyper/tests/test_paper_source_lock.py`
- Produce: `/mnt/f/spatialecotyper_reproduction/archive/paper/`
- Produce: `/mnt/f/spatialecotyper_reproduction/archive/manifests/paper-files.tsv`

- [x] **Step 1: 写失败测试**：断言 DOI、三个附件 URL、预期字节数、固定 SHA 字段均存在，并要求附件在归档目录可读。
- [x] **Step 2: 运行测试确认因文件缺失失败**：`python reproduction/spatialecotyper/tests/test_paper_source_lock.py`。
- [x] **Step 3: 实现可续传归档脚本**：下载原文 HTML、补充 PDF、Reporting Summary 和 XLSX，写入 HTTP 元数据与 SHA-256；重复运行不得重下已验证文件。
- [x] **Step 4: 执行并验证**：三个附件预期字节数分别为 `3300403`、`3115846`、`7036608`；XLSX 已知 SHA-256 为 `d9b5bddd670cfd90ec2e60c7a28e8067eba8db5bd1a3f011959f4c4ab46cc76f`。
- [x] **Step 5: 提交**：`git commit -m "data: archive Spatial EcoTyper paper sources"`。

### Task 2: 从补充表生成论文数据 manifest

**Files:**
- Create: `reproduction/spatialecotyper/scripts/extract_paper_data_manifest.py`
- Create: `reproduction/spatialecotyper/tests/test_paper_data_manifest.py`
- Produce: `/mnt/f/spatialecotyper_reproduction/archive/manifests/paper-datasets.tsv`
- Produce: `/mnt/f/spatialecotyper_reproduction/archive/manifests/paper-samples.tsv`
- Produce: `/mnt/f/spatialecotyper_reproduction/archive/manifests/paper-access-ledger.tsv`

- [x] **Step 1: 写失败测试**：要求完整读取 S1/S2/S8/S12/S15/S17，保留每行原始字段与 sheet/row provenance；校验 S1 有 18 个队列数据行（Excel 总 48 行）、S2 有 14 个队列数据行（Excel 总 18 行）、S8 有 31 个样本数据行（Excel 总 42 行）。
- [x] **Step 2: 运行测试确认失败**：`python reproduction/spatialecotyper/tests/test_paper_data_manifest.py`。
- [x] **Step 3: 实现抽取与规范化**：统一 accession、portal、modality、platform、cancer type、reported sample count、publication URL；不得把同一 accession 的不同样本静默合并。
- [x] **Step 4: 标注访问层级**：生成待解析的 access ledger；具体层级由 Task 3 的仓库探测证据写回。
- [x] **Step 5: 运行测试和人工审计**：生成逐 sheet 行数、唯一 accession 数、报告样本数总和与重复项报告。
- [x] **Step 6: 提交**：`git commit -m "data: derive canonical paper dataset manifest"`。

### Task 3: 解析下载 URL、许可证与容量闸门

**Files:**
- Create: `reproduction/spatialecotyper/scripts/resolve_paper_downloads.py`
- Create: `reproduction/spatialecotyper/tests/test_paper_download_resolution.py`
- Produce: `/mnt/f/spatialecotyper_reproduction/archive/manifests/paper-downloads.tsv`
- Produce: `/mnt/f/spatialecotyper_reproduction/results/reproducibility/paper-download-capacity.tsv`

- [x] **Step 1: 写解析器契约测试**：每个公开数据集必须得到直接文件 URL/API 文件列表或明确失败原因；未知大小不得自动进入批量下载。
- [x] **Step 2: 实现官方仓库解析器**：覆盖 Stanford DOI、NCBI GEO、Zenodo、Mendeley Data、10x Genomics、Vizgen、HRA/GSA、ENA 和补充表中的 GitHub/SpatialResearch 链接；无公开文件 API 的来源写入明确阻塞证据。
- [x] **Step 3: 仅做元数据探测**：HEAD/API 获取文件名、大小、校验值、许可证和访问状态，不下载大文件。
- [x] **Step 4: 容量审计**：记录逐来源与总字节数、F盘可用空间、是否通过 100 GB/70% 闸门；约 1.94 TB ENA raw FASTQ 被来源闸门暂停，可执行下载量约 60.29 GB。
- [x] **Step 5: 提交**：`git commit -m "data: resolve paper download inventory"`。

### Task 4: 下载作者生成数据与公开处理后数据

**Files:**
- Create: `reproduction/spatialecotyper/scripts/download_paper_data.sh`
- Create: `reproduction/spatialecotyper/tests/test_paper_download_archive.sh`
- Produce: `/mnt/f/spatialecotyper_reproduction/raw/paper_generated/`
- Produce: `/mnt/f/spatialecotyper_reproduction/archive/manifests/paper-file-sha256.tsv`

- [ ] **Step 1: 写幂等/损坏检测测试**：验证 `.part`、断点续传、大小检查、SHA 校验、原子重命名和重复运行跳过。
- [ ] **Step 2: 下载 Stanford DOI 可直接公开的 processed/normalized 文件**；若网页强制登录，则只标记 `REGISTRATION_REQUIRED`，不创建账户、不猜测直链。
- [ ] **Step 3: 对 GSE320042 已下载归档做去重登记**：引用已有 4.6 GB tar 与 SHA，不重复下载。
- [ ] **Step 4: 下载其它作者生成、无需协议的处理后数据**，逐文件写 manifest 和日志。
- [ ] **Step 5: 验证文件完整性并提交脚本/清单定义**：`git commit -m "data: archive public paper-generated datasets"`。

### Task 5: 下载公开空间转录组和单细胞参考队列

**Files:**
- Modify: `reproduction/spatialecotyper/scripts/download_paper_data.sh`
- Create: `reproduction/spatialecotyper/scripts/validate_paper_samples.py`
- Create: `reproduction/spatialecotyper/tests/test_paper_sample_validation.py`
- Produce: `/mnt/f/spatialecotyper_reproduction/raw/public_spatial/`
- Produce: `/mnt/f/spatialecotyper_reproduction/raw/public_scrna/`

- [ ] **Step 1: 按容量闸门通过顺序下载 S1 空间队列**：processed matrices、coordinates、images/segmentation metadata 优先；每个 accession 独立日志和 SHA。
- [ ] **Step 2: 下载 S2 单细胞参考队列**：优先论文使用的 count matrix/metadata，不用替代版本；受控来源保留 ledger。
- [ ] **Step 3: 验证 S8 单细胞尺度空间样本**：平台、癌种、发现/验证分组、纳入/排除标记与补充表逐行一致。
- [ ] **Step 4: 运行样本审计**：报告 `expected/available/downloaded/verified/blocked`，任何数目差异必须列出确切样本 ID。
- [ ] **Step 5: 提交**：`git commit -m "data: archive public spatial and single-cell cohorts"`。

### Task 6: 构建原文计算输入，不改变算法

**Files:**
- Create: `reproduction/spatialecotyper/scripts/prepare_paper_inputs.R`
- Create: `reproduction/spatialecotyper/tests/test_paper_inputs.R`
- Produce: `/mnt/f/spatialecotyper_reproduction/work/paper_inputs/`

- [ ] **Step 1: 写输入契约测试**：只接受补充方法明确的矩阵、metadata、coordinates 和平台字段；禁止推测缺失标签。
- [ ] **Step 2: 实现原文预处理接口**：Visium 使用 Space Ranger/Seurat 原文阈值，Visium HD 使用 16 µm bins 与 `<20 genes` 过滤；无法由公开材料确定的步骤停止在 `METHOD_GAP`。
- [ ] **Step 3: 构建 discovery/reference/recovery 输入**：记录每一步输入文件 SHA、参数、软件版本、随机种子和输出维度。
- [ ] **Step 4: 验证样本数与矩阵尺寸**：与 S1/S2/S8 和原文 Methods 交叉核对。
- [ ] **Step 5: 提交**：`git commit -m "repro: prepare paper-derived Spatial EcoTyper inputs"`。

### Task 7: 执行论文级计算复现与定量比对

**Files:**
- Create: `reproduction/spatialecotyper/scripts/run_paper_reproduction.R`
- Create: `reproduction/spatialecotyper/scripts/compare_paper_outputs.R`
- Create: `reproduction/spatialecotyper/tests/test_paper_reproduction.R`
- Modify: `reproduction/spatialecotyper/config/paper-computation-inventory.tsv`
- Produce: `/mnt/f/spatialecotyper_reproduction/results/paper_reproduction/`

- [ ] **Step 1: 将正文/扩展数据每项计算映射到输入、官方函数和预期输出**，继续区分 strict/tutorial/method-only/blocked。
- [ ] **Step 2: 运行官方 Spatial EcoTyper 发现、恢复、整合流程**：只调用固定提交中的官方 API；不补写 Liquid EcoTyper 深度学习代码。
- [ ] **Step 3: 比对定量结果**：cell state/SE 数目、样本分组、相关性/效应方向、可获得的表格数值；设置明确容差并输出 diff。
- [ ] **Step 4: 对缺失代码、受控数据和认证数据生成阻塞证据**，不得用教程成功替代论文成功。
- [ ] **Step 5: 提交**：`git commit -m "repro: run paper-level Spatial EcoTyper analyses"`。

### Task 8: 最终下载与复现审计

**Files:**
- Modify: `reproduction/spatialecotyper/scripts/final_audit.sh`
- Modify: `docs/reproduction/spatialecotyper-reproduction-boundary.md`
- Create: `docs/reproduction/spatialecotyper-paper-data-inventory.md`
- Produce: `/mnt/f/spatialecotyper_reproduction/results/reproducibility/paper-final-audit.txt`

- [ ] **Step 1: 运行所有单元、清单、SHA、样本数和官方教程回归测试**。
- [ ] **Step 2: 生成完整磁盘清单**：逐层字节数、文件数、最大文件、重复文件和未完成 `.part`。
- [ ] **Step 3: 更新复现边界**：逐正文图/扩展图列出 `STRICT_PASS`、`PARTIAL_PASS`、`METHOD_ONLY`、`BLOCKED_ACCESS`、`BLOCKED_CODE`。
- [ ] **Step 4: 运行最终审计**：要求零损坏文件、零不明来源文件、零算法改动；保留所有受控/认证阻塞项。
- [ ] **Step 5: 提交并推送当前 PR 分支**：`git commit -m "docs: report paper data and reproduction audit"`。
