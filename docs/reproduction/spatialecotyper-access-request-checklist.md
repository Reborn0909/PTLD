# Spatial EcoTyper 缺失材料与访问申请清单

本清单只生成证据充分的申请内容，**不会自动发送**。This package is **not sent automatically**.

固定论文代码提交：`48c2c846781d3a312771021c1a2ef5fc383700c5`。任何新收到的材料都应单独归档、计算 SHA-256，并在改变复现状态前完成本地验证。

## 1. STANFORD_NORMALIZED_DATA

- 建议渠道：Stanford Spatial EcoTyper portal data-access channel
- 请求材料：preprocessed and normalized paper data under DOI 10.25936/pm3t-cn37; file manifest; sample-to-file map; preprocessing metadata
- 版本范围：paper release associated with Nature DOI 10.1038/s41586-026-10452-4
- 关联图板：108 个；完整 ID 见 `access-request-evidence.tsv`。
- 官方证据：https://doi.org/10.25936/pm3t-cn37;F:\spatialecotyper_reproduction\archive\manifests\official-material-snapshots.tsv;F:\spatialecotyper_reproduction\archive\manifests\paper-access-ledger.tsv
- 边界：Request portal access; do not bypass sign-in, DUA or cohort restrictions.
- 当前状态：`NOT_SENT`

## 2. CYTOSPACE_WEIGHTS

- 建议渠道：Corresponding authors through the Nature article contact channel
- 请求材料：paper-specific CytoSPACE spot-to-cell assignments or per-spot cell-count weights; sample identifiers; CytoSPACE version; parameters and random seeds
- 版本范围：exact objects used for the published 132-sample atlas and GSE320042 cohort
- 关联图板：26 个；完整 ID 见 `access-request-evidence.tsv`。
- 官方证据：https://www.nature.com/articles/s41586-026-10452-4;F:\spatialecotyper_reproduction\results\reproducibility\paper-panel-audit.tsv
- 边界：Ask for shareable derived weights only; raw human data remain subject to DUA/IRB.
- 当前状态：`NOT_SENT`

## 3. LIQUID_ECOTYPER_CODE_WEIGHTS

- 建议渠道：Corresponding authors through the Nature article contact channel
- 请求材料：Liquid EcoTyper PyTorch 2.2.0 source; training and inference entrypoints; configuration; CpG preprocessing; checkpoints; model weights; seeds
- 版本范围：exact version used for the 2026 Nature paper
- 关联图板：43 个；完整 ID 见 `access-request-evidence.tsv`。
- 官方证据：https://github.com/digitalcytometry/spatialecotyper;F:\spatialecotyper_reproduction\results\reproducibility\official-material-update-report.tsv;F:\spatialecotyper_reproduction\results\reproducibility\source-code-inventory.tsv
- 边界：Request official code and weights; do not substitute a newly designed model.
- 当前状态：`NOT_SENT`

## 4. FIGURE_SCRIPTS

- 建议渠道：Corresponding authors through the Nature article contact channel
- 请求材料：figure-generation scripts for main, extended and supplementary figures; intermediate tables; package lockfiles; command order; random seeds
- 版本范围：scripts and intermediate values used for the final published figures
- 关联图板：151 个；完整 ID 见 `access-request-evidence.tsv`。
- 官方证据：https://www.nature.com/articles/s41586-026-10452-4;F:\spatialecotyper_reproduction\results\reproducibility\official-material-update-report.tsv;F:\spatialecotyper_reproduction\results\reproducibility\paper-panel-audit.tsv
- 边界：Request non-identifying scripts and derived values; no automatic contact is made.
- 当前状态：`NOT_SENT`

## 收到材料后的验证顺序

1. 保存原始下载文件、来源 URL、访问日期、许可条款和 SHA-256。
2. 检查样本映射、软件版本、参数、随机种子及权重是否齐全。
3. 在独立 `work/` 目录调用官方算法，不修改 Spatial EcoTyper。
4. 只有目标图板输出与论文值可核验一致时，才考虑升级复现状态。
