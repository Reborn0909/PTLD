# Spatial EcoTyper / Nature 2026 原文数据清单

生成时间（UTC）：2026-09-01T14:39:34+00:00

## 可公开获取数据

- 容量闸门通过并去重：74 个文件；已知大小合计 61211570350 字节（57.01 GiB），有界未知大小 1 个。
- 本地下载清单：74 个文件，62208522084 字节（57.94 GiB）。
- 完整性验证：74/74 通过；失败 0 个。
- 每个文件均保留原始 URL、accession、预期/实际字节数、SHA-256；上游提供 MD5 或 S3 multipart ETag 时另行校验。

### 按官方仓库汇总

| 仓库 | 文件数 | 字节数 | 易读容量 |
|---|---:|---:|---:|
| GITHUB | 1 | 996951734 | 950.77 MiB |
| NCBI_GEO | 33 | 9863802694 | 9.19 GiB |
| SPATIALRESEARCH | 2 | 22904762 | 21.84 MiB |
| TENX | 33 | 50404082517 | 46.94 GiB |
| ZENODO | 5 | 920780377 | 878.12 MiB |

## 无法直接归档的边界

- 因单一来源超过 100 GB 而暂停的已知数据：2703204515666 字节（2.46 TiB）。
- 注册、数据使用协议或受控人类数据不绕过权限，只保留可核验的 accession 与阻断原因。

| 来源记录 | accession | 访问状态 | 容量闸门 | 原因 |
|---|---|---|---|---|
| TableS1-R9 |  | REGISTRATION_REQUIRED | PASS | guest page exposes metadata but file API returned HTTP 401 |
| TableS1-R10 | HRA000437 | CONTROLLED_DUA | PASS | GSA-Human accession requires approved human-data access |
| TableS1-R16 |  | REGISTRATION_REQUIRED | PASS | guest page exposes metadata but file API returned HTTP 401 |
| TableS1-R18 |  | REGISTRATION_REQUIRED | PASS | guest page exposes metadata but file API returned HTTP 401 |
| TableS1-R19 |  | REGISTRATION_REQUIRED | PASS | Vizgen showcase download is gated by a registration form |
| TableS1-R23 |  | REGISTRATION_REQUIRED | PASS | HTAN files require portal/Synapse authentication and terms |
| TableS2-R10 |  | NOT_PUBLIC | PASS | supplementary table provides no accession or stable public file URL |
| TableS15-R6 | PRJEB23709 | PUBLIC_API | PAUSE_OVER_100GB | ENA public raw FASTQ inventory; capacity-gated because paper used processed expression |
| TableS15-R7 | PRJEB23709 | PUBLIC_API | PAUSE_OVER_100GB | ENA public raw FASTQ inventory; capacity-gated because paper used processed expression |
| TableS15-R10 |  | NOT_PUBLIC | PASS | supplementary table provides no accession or stable public file URL |
| TableS15-R11 |  | NOT_PUBLIC | PASS | supplementary table provides no accession or stable public file URL |
| TableS15-R12 | PRJEB25780 | PUBLIC_API | PAUSE_OVER_100GB | ENA public raw FASTQ inventory; capacity-gated because paper used processed expression |
| TableS15-R13 |  | NOT_PUBLIC | PASS | supplementary table provides no accession or stable public file URL |
| TableS15-R14 |  | NOT_PUBLIC | PASS | supplementary table provides no accession or stable public file URL |
| TableS15-R15 |  | NOT_PUBLIC | PASS | supplementary table provides no accession or stable public file URL |
| TableS15-R16 |  | NOT_PUBLIC | PASS | supplementary table provides no accession or stable public file URL |
| STANFORD-DOI-PM3T-CN37 | 10.25936/pm3t-cn37 | REGISTRATION_REQUIRED | PASS | Stanford DOI download is shown only after sign in |

## 已执行的原文计算

- 研究生成空间队列：17 个空间样本、15 位患者、262879 个过滤后 spot/bin。
- 输入从原始 counts 按原文重算 log2(CPM+1)，仅调用固定版本官方 `SpatialEcoTyper::DeconvoluteSE()`。
- 输出为 NonSE 与 SE1–SE9 spot/bin 分数；样本平面的加权汇总因缺失论文使用的 CytoSPACE 细胞数权重而标记为 `METHOD_GAP`。

## 第二阶段逐图板审计

- 论文图清单：26 张；显式图板：151 个。
- 74 个已验证容器流式索引为 1442 个内部成员；检查失败 0 个。
- 数据集就绪分类：BLOCKED_ACCESS=6; BLOCKED_NOT_PUBLIC=7; PARTIAL_FILES=4; PAUSED_CAPACITY=3; READY_OFFICIAL_PROCESSED=1; READY_RAW_ONLY=25。
- 图板复现分类：BLOCKED_CODE=43; METHOD_ONLY=108。
- 当前 `STRICT_PASS=0`；spot/bin级官方API输出不能替代缺失的论文预处理、派生权重和作图链。
- 官方仓库最新探测提交：`57d37cd2c31c2b0743a7d50e036c4d4a50b61eee`；Liquid EcoTyper、CytoSPACE权重和作图脚本均无解除阻塞的候选文件。

## 证据文件

- `/mnt/f/spatialecotyper_reproduction/archive/manifests/paper-downloads.tsv`
- `/mnt/f/spatialecotyper_reproduction/archive/manifests/paper-file-sha256.tsv`
- `/mnt/f/spatialecotyper_reproduction/results/reproducibility/paper-download-capacity.tsv`
- `/mnt/f/spatialecotyper_reproduction/results/reproducibility/paper-file-validation.tsv`
- `/mnt/f/spatialecotyper_reproduction/results/reproducibility/paper-container-summary.tsv`
- `/mnt/f/spatialecotyper_reproduction/results/reproducibility/paper-dataset-readiness.tsv`
- `/mnt/f/spatialecotyper_reproduction/results/reproducibility/paper-panel-audit.tsv`
- `/mnt/f/spatialecotyper_reproduction/results/reproducibility/official-material-update-report.tsv`
- `/mnt/f/spatialecotyper_reproduction/results/reproducibility/access-request-evidence.tsv`
