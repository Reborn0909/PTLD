# Spatial EcoTyper Maximum Auditable Reproduction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不修改 Spatial EcoTyper 官方算法、不绕过访问控制、不自行补写未公开 Liquid EcoTyper/CytoSPACE 流程的前提下，把 Nature 2026 论文推进到官方材料允许的最高可审计复现等级，并逐图、逐数据集证明哪些计算已完成或为何无法严格完成。

**Architecture:** 以已通过最终审计的 74 个公开文件和固定官方提交为不可变基线；新增三个相互独立的清单层：论文面板层、归档内部结构层和数据集计算就绪层。所有执行决策由这三层清单连接到官方函数与目标输出；无完整输入或代码的面板保持 `BLOCKED_ACCESS`、`BLOCKED_CODE` 或 `METHOD_GAP`，不能升级为严格复现。

**Tech Stack:** Python 3、BeautifulSoup 4、PyMuPDF、R 4.4.1、SpatialEcoTyper 1.0.2、WSL2、TSV/JSON、SHA-256、GitHub REST API。

## Global Constraints

- 官方算法固定到提交 `48c2c846781d3a312771021c1a2ef5fc383700c5`，官方 `R/`、`vignettes/` 和模型参数不得修改。
- 基线下载清单固定为 74 个已验证文件、`62208522084` 实际字节；新增文件必须另建来源快照和 SHA-256 记录。
- 三个超大 10x `binned_outputs.tar.gz` 只流式列目录和读取元数据，不全量解压到 `work/`。
- Stanford 登录、GSA-Human、HTAN/Synapse 和 Vizgen 注册数据不得绕过权限；仅记录可核验证据与用户可执行的申请动作。
- 单一来源超过 100 GB 或新增下载超过 F 盘可用空间 70% 时保持容量暂停。
- `STRICT_PASS` 仅用于公开输入、官方代码、版本、参数、随机性和目标输出均可核验且本地运行成功的面板。
- 官方 API 在论文数据上的新增运行若缺少论文级预处理或目标数值，只能标为 `OFFICIAL_API_PASS` 或 `METHOD_ONLY`。
- PTLD 适配层保持独立，不能参与原文复现状态判定。

---

### Task 1: 建立逐图逐面板规范清单

**Files:**
- Create: `reproduction/spatialecotyper/scripts/extract_paper_panels.py`
- Create: `reproduction/spatialecotyper/tests/test_paper_panel_manifest.py`
- Produce: `/mnt/f/spatialecotyper_reproduction/archive/manifests/paper-figures.tsv`
- Produce: `/mnt/f/spatialecotyper_reproduction/archive/manifests/paper-panels.tsv`

**Interfaces:**
- Consumes: `archive/paper/nature-article.html` and `archive/paper/41586_2026_10452_MOESM1_ESM.pdf`.
- Produces: `extract_html_figures(path) -> list[dict]`, `extract_supplementary_figures(path) -> list[dict]`, and one panel row per explicit caption label.

- [x] **Step 1: Write the failing manifest test**

```python
assert counts == {"MAIN": 5, "EXTENDED": 12, "SUPPLEMENTARY": 9}
assert all(row["figure_id"] and row["caption"] for row in figures)
assert all(row["panel_id"] and row["panel_text"] for row in panels)
assert {row["figure_id"] for row in panels} == {row["figure_id"] for row in figures}
```

- [x] **Step 2: Run the test and confirm the missing-script failure**

Run: `python reproduction/spatialecotyper/tests/test_paper_panel_manifest.py`

Expected: FAIL because `extract_paper_panels.py` and the two manifests do not exist.

- [x] **Step 3: Implement deterministic caption extraction**

Use BeautifulSoup selectors `div[data-test="figure"]` for five main figures and `div[data-test="supp-item"][id^="Fig"]` for twelve extended figures. Use `fitz.open()` and the `Supplementary Fig. N` headings in MOESM1 for nine supplementary figures. Normalize whitespace with `re.sub(r"\s+", " ", text).strip()` and identify panel starts only with bold/heading labels matching `a` through `z`.

- [x] **Step 4: Generate and verify the two manifests**

Run: `python reproduction/spatialecotyper/scripts/extract_paper_panels.py --root /mnt/f/spatialecotyper_reproduction`

Expected: `paper panel manifest: PASS figures=26` followed by the number of extracted panel rows.

- [x] **Step 5: Commit**

```bash
git add reproduction/spatialecotyper/scripts/extract_paper_panels.py reproduction/spatialecotyper/tests/test_paper_panel_manifest.py
git commit -m "data: index every paper figure panel"
```

### Task 2: 流式索引 74 个归档文件的内部结构

**Files:**
- Create: `reproduction/spatialecotyper/scripts/index_paper_archives.py`
- Create: `reproduction/spatialecotyper/tests/test_paper_archive_index.py`
- Produce: `/mnt/f/spatialecotyper_reproduction/results/reproducibility/paper-archive-members.tsv`
- Produce: `/mnt/f/spatialecotyper_reproduction/results/reproducibility/paper-container-summary.tsv`

**Interfaces:**
- Consumes: `paper-file-sha256.tsv` with exactly 74 verified local paths.
- Produces: `inspect_container(path: Path) -> Iterable[MemberRecord]` where `MemberRecord` contains `local_path`, `member_path`, `member_bytes`, `container_type`, `content_role`, and `inspection_status`.

- [x] **Step 1: Write fixtures for tar, tar.gz, zip, gzip, HDF5 and plain files**

The test must assert member names and sizes, prevent path extraction, and reject any manifest row whose file is missing or not present in the 74-row validation table.

- [x] **Step 2: Run the test and confirm failure**

Run: `python reproduction/spatialecotyper/tests/test_paper_archive_index.py`

Expected: FAIL because the archive indexer does not exist.

- [x] **Step 3: Implement read-only streaming inspection**

Use `tarfile.open(..., "r|*")`, `zipfile.ZipFile.infolist()`, `gzip.GzipFile.peek(1)`, and `h5py.File.visititems()`. Never call `extract`, `extractall`, or write archive members to disk. Classify paths with fixed roles: `expression`, `barcode`, `feature`, `coordinate`, `image`, `segmentation`, `metadata`, `model`, or `other`.

- [x] **Step 4: Run the full index and contract test**

Run: `python reproduction/spatialecotyper/scripts/index_paper_archives.py --root /mnt/f/spatialecotyper_reproduction`

Expected: 74 containers, zero `INSPECTION_FAIL`, and no growth of `work/` attributable to archive extraction.

- [x] **Step 5: Commit**

```bash
git add reproduction/spatialecotyper/scripts/index_paper_archives.py reproduction/spatialecotyper/tests/test_paper_archive_index.py
git commit -m "repro: index archived paper data without extraction"
```

### Task 3: 生成逐数据集计算就绪矩阵

**Files:**
- Create: `reproduction/spatialecotyper/scripts/classify_paper_dataset_readiness.py`
- Create: `reproduction/spatialecotyper/tests/test_paper_dataset_readiness.py`
- Produce: `/mnt/f/spatialecotyper_reproduction/results/reproducibility/paper-dataset-readiness.tsv`

**Interfaces:**
- Consumes: paper datasets, downloads, file validation, sample availability, archive members and access ledger.
- Produces: one row per `source_record_id` with `expression_status`, `metadata_status`, `spatial_status`, `official_preprocessing_status`, `readiness_class`, and `blocking_evidence`.

- [x] **Step 1: Write classification tests**

Test all allowed classes: `READY_OFFICIAL_PROCESSED`, `READY_RAW_ONLY`, `PARTIAL_FILES`, `PAUSED_CAPACITY`, `BLOCKED_ACCESS`, `BLOCKED_NOT_PUBLIC`, and `METHOD_GAP`. Assert that registration or controlled rows can never become `READY_*` without a verified file manifest row.

- [x] **Step 2: Run the test and confirm failure**

Run: `python reproduction/spatialecotyper/tests/test_paper_dataset_readiness.py`

Expected: FAIL because the classifier is absent.

- [x] **Step 3: Implement deterministic joins and conservative rules**

Require verified expression plus metadata/coordinates for `READY_OFFICIAL_PROCESSED`; classify expression without complete paper preprocessing as `READY_RAW_ONLY`; carry access and capacity states directly from the ledger. Every non-ready row must contain a concrete URL, accession, missing role, or unpublished-method statement.

- [x] **Step 4: Generate the matrix and verify conservation**

Run: `python reproduction/spatialecotyper/scripts/classify_paper_dataset_readiness.py --root /mnt/f/spatialecotyper_reproduction`

Expected: every canonical `source_record_id` appears exactly once and the class counts sum to the input record count.

- [x] **Step 5: Commit**

```bash
git add reproduction/spatialecotyper/scripts/classify_paper_dataset_readiness.py reproduction/spatialecotyper/tests/test_paper_dataset_readiness.py
git commit -m "repro: classify paper dataset computation readiness"
```

### Task 4: 将每个论文面板连接到输入、代码和目标输出

**Files:**
- Create: `reproduction/spatialecotyper/config/paper-panel-reproduction.tsv`
- Create: `reproduction/spatialecotyper/scripts/audit_paper_panels.py`
- Create: `reproduction/spatialecotyper/tests/test_paper_panel_reproduction.py`
- Produce: `/mnt/f/spatialecotyper_reproduction/results/reproducibility/paper-panel-audit.tsv`

**Interfaces:**
- Consumes: `paper-panels.tsv`, dataset readiness, `paper-computation-inventory.tsv`, supplementary tables and fixed official source inventory.
- Produces: exactly one audit row per extracted panel with `input_records`, `official_entrypoint`, `expected_output`, `observed_output`, `status`, and `limitation`.

- [x] **Step 1: Write coverage and status tests**

Assert that no panel is missing or duplicated and only `STRICT_PASS`, `OFFICIAL_API_PASS`, `TUTORIAL_REPRODUCED`, `METHOD_ONLY`, `METHOD_GAP`, `BLOCKED_ACCESS`, or `BLOCKED_CODE` are accepted. `STRICT_PASS` must point to an existing observed-output file and a callable official entry point.

- [x] **Step 2: Run the test and confirm failure**

Run: `python reproduction/spatialecotyper/tests/test_paper_panel_reproduction.py`

Expected: FAIL because the panel mapping is absent.

- [x] **Step 3: Curate the mapping exclusively from captions, Methods and Supplementary Tables 1–28**

Record figure-level diagrams as `METHOD_ONLY`; map generated tumour spatial panels to GSE320042 and `SpatialEcoTyper::DeconvoluteSE`; map Liquid EcoTyper panels to `BLOCKED_CODE`; map protected clinical cohorts to `BLOCKED_ACCESS`; do not infer an entry point that is not present in the fixed repository.

- [x] **Step 4: Generate the audit and verify full panel coverage**

Run: `python reproduction/spatialecotyper/scripts/audit_paper_panels.py --root /mnt/f/spatialecotyper_reproduction`

Expected: audit row count equals `paper-panels.tsv`; no empty `status` or `limitation` fields.

- [x] **Step 5: Commit**

```bash
git add reproduction/spatialecotyper/config/paper-panel-reproduction.tsv reproduction/spatialecotyper/scripts/audit_paper_panels.py reproduction/spatialecotyper/tests/test_paper_panel_reproduction.py
git commit -m "repro: map every paper panel to reproducibility evidence"
```

### Task 5: 执行新增的严格或官方 API 可运行项

**Files:**
- Create: `reproduction/spatialecotyper/scripts/run_ready_paper_analyses.R`
- Create: `reproduction/spatialecotyper/tests/test_ready_paper_analyses.R`
- Produce: `/mnt/f/spatialecotyper_reproduction/results/paper_reproduction/ready_analyses/`

**Interfaces:**
- Consumes: only `READY_OFFICIAL_PROCESSED` datasets and panel rows with a fixed-repository entry point.
- Produces: per-run provenance containing input SHA-256, official function, arguments, random seed, package version, output dimensions, runtime and status.

- [x] **Step 1: Write the execution gate test**

The test must reject `READY_RAW_ONLY`, access-blocked rows, missing coordinates and any function not exported by the installed SpatialEcoTyper 1.0.2 namespace.

- [x] **Step 2: Run the test and confirm failure**

Run in the fixed environment: `Rscript reproduction/spatialecotyper/tests/test_ready_paper_analyses.R`

Expected: FAIL because the gated runner is absent.

- [x] **Step 3: Implement the official-function dispatcher**

Allow only the explicit function names already present in `paper-panel-reproduction.tsv`; set `set.seed()` from the table; write `.part` followed by atomic rename; validate existing outputs before reuse. Never implement a Liquid EcoTyper substitute.

- [x] **Step 4: Run all eligible rows and update panel audit evidence**

Run: `Rscript reproduction/spatialecotyper/scripts/run_ready_paper_analyses.R`

Expected: every eligible row is `PASS` or the run exits non-zero with a sample-specific error; ineligible rows are reported but never executed.

Observed on 2026-09-01: all 151 panel rows were ineligible because the fixed official repository exposes no panel-linked entrypoint in the curated mapping. The atomic gate and summary report `eligible=0`; no computation was dispatched or status upgraded.

- [x] **Step 5: Commit**

```bash
git add reproduction/spatialecotyper/scripts/run_ready_paper_analyses.R reproduction/spatialecotyper/tests/test_ready_paper_analyses.R
git commit -m "repro: run all eligible official paper analyses"
```

### Task 6: 监测官方材料更新并刷新阻塞证据

**Files:**
- Create: `reproduction/spatialecotyper/scripts/probe_official_material_updates.py`
- Create: `reproduction/spatialecotyper/tests/test_official_material_probe.py`
- Produce: `/mnt/f/spatialecotyper_reproduction/archive/manifests/official-material-snapshots.tsv`
- Produce: `/mnt/f/spatialecotyper_reproduction/results/reproducibility/official-material-update-report.tsv`

**Interfaces:**
- Consumes: official GitHub repository metadata, Nature data/code availability URLs and Stanford DOI metadata.
- Produces: immutable observations with URL, HTTP status, ETag/commit, observed UTC, artifact type and whether it changes a current blocker.

- [ ] **Step 1: Write mocked API and idempotency tests**

Assert identical observations do not create duplicate snapshots; a new official commit is archived separately and never silently replaces the fixed paper commit; authentication pages remain `REGISTRATION_REQUIRED`.

- [ ] **Step 2: Run the test and confirm failure**

Run: `python reproduction/spatialecotyper/tests/test_official_material_probe.py`

Expected: FAIL because the probe does not exist.

- [ ] **Step 3: Implement read-only official endpoint probes**

Use conditional HTTP requests and GitHub commit/release APIs. Record discovery of Python files, checkpoints, CytoSPACE weights or figure scripts as candidate unblockers, but require local archive and validation before changing a panel status.

- [ ] **Step 4: Run once and archive the baseline observation**

Run: `python reproduction/spatialecotyper/scripts/probe_official_material_updates.py --root /mnt/f/spatialecotyper_reproduction`

Expected: one current snapshot per official endpoint and a report explicitly stating whether any of the three `BLOCKED_CODE` components changed.

- [ ] **Step 5: Commit**

```bash
git add reproduction/spatialecotyper/scripts/probe_official_material_updates.py reproduction/spatialecotyper/tests/test_official_material_probe.py
git commit -m "repro: monitor official material release gaps"
```

### Task 7: 生成数据访问与作者材料申请包

**Files:**
- Create: `docs/reproduction/spatialecotyper-access-request-checklist.md`
- Create: `reproduction/spatialecotyper/scripts/write_access_request_evidence.py`
- Create: `reproduction/spatialecotyper/tests/test_access_request_evidence.py`
- Produce: `/mnt/f/spatialecotyper_reproduction/results/reproducibility/access-request-evidence.tsv`

**Interfaces:**
- Consumes: access ledger and panel audit.
- Produces: grouped, non-duplicated requests for Stanford normalized data, CytoSPACE spot-cell weights, Liquid EcoTyper code/checkpoints and figure scripts; no message is sent automatically.

- [ ] **Step 1: Write the request-evidence contract test**

```python
assert {row["request_type"] for row in rows} == {
    "STANFORD_NORMALIZED_DATA", "CYTOSPACE_WEIGHTS",
    "LIQUID_ECOTYPER_CODE_WEIGHTS", "FIGURE_SCRIPTS"
}
assert all(row["blocked_panel_ids"] and row["official_evidence"] for row in rows)
assert all("@" not in row["recipient"] for row in rows)
```

- [ ] **Step 2: Run the test and confirm failure**

Run: `python reproduction/spatialecotyper/tests/test_access_request_evidence.py`

Expected: FAIL because the evidence writer and request checklist do not exist.

- [ ] **Step 3: Generate the evidence table and bilingual checklist**

Run: `python reproduction/spatialecotyper/scripts/write_access_request_evidence.py --root /mnt/f/spatialecotyper_reproduction --output docs/reproduction/spatialecotyper-access-request-checklist.md`

The generated checklist must ask for exact file classes, versions and panel linkage; it must not invent an email address or claim that approval has been obtained.

- [ ] **Step 4: Verify controlled-data boundaries**

Run: `python reproduction/spatialecotyper/tests/test_access_request_evidence.py`

Expected: PASS and every GSA-Human/HTAN/registered cohort remains `BLOCKED_ACCESS` pending its own DUA/IRB process.

- [ ] **Step 5: Commit**

```bash
git add docs/reproduction/spatialecotyper-access-request-checklist.md reproduction/spatialecotyper/scripts/write_access_request_evidence.py reproduction/spatialecotyper/tests/test_access_request_evidence.py
git commit -m "docs: prepare missing-material access evidence"
```

### Task 8: 扩展最终审计并发布第二阶段报告

**Files:**
- Modify: `reproduction/spatialecotyper/scripts/final_audit.sh`
- Create: `docs/reproduction/spatialecotyper-panel-level-reproduction.md`
- Modify: `docs/reproduction/spatialecotyper-paper-data-inventory.md`
- Test: all tests under `reproduction/spatialecotyper/tests/`

**Interfaces:**
- Consumes: all Task 1–7 outputs.
- Produces: a final panel-level report and non-zero audit failure for missing panels, stale inputs, invalid status upgrades, corrupt files or algorithm modifications.

- [ ] **Step 1: Add explicit final-audit assertions**

Require `figures=26`, archive container rows `=74`, zero unknown dataset classes, full panel coverage, zero invalid `STRICT_PASS`, zero failed eligible runs and zero `.part/.aria2` files.

- [ ] **Step 2: Extend and run the shell audit**

Run: `bash reproduction/spatialecotyper/scripts/final_audit.sh`

Expected: non-zero until every new manifest and test passes; after implementation, the last line must be `FINAL_AUDIT\tPASS`.

- [ ] **Step 3: Generate the Chinese panel-level report**

The report must tabulate every figure and panel, status counts, exact evidence paths, remaining blocker classes and the user action required for access-controlled materials.

- [ ] **Step 4: Run fresh independent assertions**

```bash
test "$(awk 'END{print NR-1}' paper-figures.tsv)" -eq 26
test "$(awk 'END{print NR-1}' paper-file-sha256.tsv)" -eq 74
test -z "$(find /mnt/f/spatialecotyper_reproduction/raw /mnt/f/spatialecotyper_reproduction/archive -type f \( -name '*.part' -o -name '*.aria2' \) -print -quit)"
```

- [ ] **Step 5: Commit and push**

```bash
git add reproduction/spatialecotyper/scripts/final_audit.sh docs/reproduction/spatialecotyper-panel-level-reproduction.md docs/reproduction/spatialecotyper-paper-data-inventory.md
git commit -m "docs: publish maximum paper reproduction audit"
git push origin codex/spatialecotyper-reproduction
```

## Self-Review

- Spec coverage: the plan covers every figure family, every downloaded container, dataset readiness, all executable official functions, changing official releases, access-only blockers and final verification.
- Placeholder scan: no placeholder text, guessed contact, guessed preprocessing parameter or unimplemented algorithm is permitted.
- Type consistency: `source_record_id`, `figure_id`, `panel_id`, `readiness_class` and the allowed reproduction statuses are stable across Tasks 1–8.
- Boundary: completion of this plan means maximum auditable reproduction under available official materials; it does not relabel unpublished Liquid EcoTyper or CytoSPACE computations as reproduced.
