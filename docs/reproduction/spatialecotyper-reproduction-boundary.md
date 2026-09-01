# Spatial EcoTyper / Nature 2026 计算复现边界

审计代码固定到官方提交 `48c2c846781d3a312771021c1a2ef5fc383700c5`（SpatialEcoTyper 1.0.2）。
本报告把官方教程可运行与论文图表可严格重建分开；不会把方法描述或黑箱网页调用冒充为严格复现。

## 结论

- 严格论文级复现：0 项。当前没有完整论文计算满足输入、代码、参数、随机性和目标输出全部可核验。
- 官方教程级复现：8 项；8 个 Rmd 均已运行。
- 仅方法级：8 项。
- 因官方材料缺失而阻断：3 项。
- T02 不是严格材料复现：官方归档 RDS 缺少固定代码要求的 `Spot.X/Spot.Y`，因此使用 T01 按官方流程生成的上游输出。

## 本地公开材料实测

- 固定仓库：29 个 R 文件、8 个 Rmd、0 个 Python、0 个 notebook。
- GSE320042：4936970240 字节，SHA-256 `f4d31a629a2c42d7d21c1fd6cf43cd71d115a04bdd6d3f3730cf91d37f9335b3`，154 个 tar 成员。
- GEO 成员：24 个 GSM；7 个 scRNA，17 个空间记录，其中 2 个 Visium HD。
- 补充表解析得到 74 个可操作公开文件，已知大小共 61211570350 字节，有界未知大小 1 个；已归档 74 个/62208522084 字节，74 个通过全量格式与校验值验证。
- 超过单来源 100 GB 闸门的 ENA 原始数据共 2703204515666 字节，因 F 盘容量不足保持暂停；注册/受控数据不绕过权限。
- 生成队列已完成官方 spot-level 去卷积：17 个空间样本、15 位患者、262879 个 spot/bin，与补充表 S17 样本计数逐项一致。

## 逐项矩阵

| 计算项 | 状态 | 证据 | 关键边界 |
|---|---|---|---|
| Spatial EcoTyper single-sample discovery | `TUTORIAL_REPRODUCED` | `/mnt/f/spatialecotyper_reproduction/results/tutorials/run-status.tsv` | Demonstration melanoma subset only; not the paper-scale discovery cohort or an exact paper figure |
| Spatial EcoTyper multi-sample integration | `TUTORIAL_REPRODUCED` | `/mnt/f/spatialecotyper_reproduction/results/tutorials/run-status.tsv` | Archived T02 RDS lacks Spot.X/Spot.Y required by the fixed code; official T01 output was used and strict material reproduction failed |
| SE recovery-model training | `TUTORIAL_REPRODUCED` | `/mnt/f/spatialecotyper_reproduction/results/tutorials/run-status.tsv` | Tutorial-scale model only; paper cohort model training inputs and exact stochastic seeds are not supplied as one executable workflow |
| SE-specific cell-state LOOCV | `TUTORIAL_REPRODUCED` | `/mnt/f/spatialecotyper_reproduction/results/tutorials/run-status.tsv` | Two-sample demonstration only; not the paper discovery cohort or its repeated cross-validation jobs |
| Single-cell spatial transcriptomics SE recovery | `TUTORIAL_REPRODUCED` | `/mnt/f/spatialecotyper_reproduction/results/tutorials/run-status.tsv` | Tutorial validation subset only; does not recreate every cross-platform paper panel |
| scRNA-seq SE recovery | `TUTORIAL_REPRODUCED` | `/mnt/f/spatialecotyper_reproduction/results/tutorials/run-status.tsv` | Tutorial dataset only; the 144-tumour paper atlas and complete preprocessing are not included |
| Bulk SE deconvolution-model training | `TUTORIAL_REPRODUCED` | `/mnt/f/spatialecotyper_reproduction/results/tutorials/run-status.tsv` | Tutorial pseudobulk training only; exact paper pseudo-tumour generation and cross-validation orchestration are not supplied |
| Bulk RNA-seq SE recovery | `TUTORIAL_REPRODUCED` | `/mnt/f/spatialecotyper_reproduction/results/tutorials/run-status.tsv` | Tutorial application only; not the complete TCGA and ICI analysis |
| Paper-specific CytoSPACE reconstruction and upstream preprocessing | `METHOD_ONLY` | `/mnt/f/spatialecotyper_reproduction/results/reproducibility/source-code-inventory.tsv` | Rebuilding it would require an independently assembled workflow and is outside the official-material-only scope |
| Assembly of the 132-sample spatial and 144-tumour scRNA atlases | `METHOD_ONLY` | `/mnt/f/spatialecotyper_reproduction/results/reproducibility/gse320042-summary.tsv` | The GEO archive covers 24 generated GSM records rather than all public cohorts and does not provide one end-to-end atlas assembly script |
| Tumour-core versus adjacent-stroma differential-expression analysis | `METHOD_ONLY` | `/mnt/f/spatialecotyper_reproduction/results/reproducibility/publication-evidence.tsv` | No official executable script connects all 120 samples to the reported tables and figure panels |
| Nine-SE pan-cancer discovery on the full spatial atlas | `METHOD_ONLY` | `/mnt/f/spatialecotyper_reproduction/results/reproducibility/publication-evidence.tsv` | Paper-scale inputs, orchestration, perturbation runs and exact figure-level outputs are not packaged together |
| Cross-platform SE validation and spatial colocalization | `METHOD_ONLY` | `/mnt/f/spatialecotyper_reproduction/results/reproducibility/publication-evidence.tsv` | The full held-out 90-sample validation workflow and all platform-specific preprocessing scripts are absent |
| Paired bulk RNA-seq and Visium validation | `METHOD_ONLY` | `/mnt/f/spatialecotyper_reproduction/results/reproducibility/publication-evidence.tsv` | Exact pairing table-to-analysis code and panel-generation script are not in the fixed repository |
| Melanoma tumour spatial SE inference for the paired plasma cohort | `METHOD_ONLY` | `/mnt/f/spatialecotyper_reproduction/results/paper_reproduction/generated_visium_deconvolution/supplementary-table-s17-comparison.tsv` | Paper sample-level SE values require unpublished CytoSPACE cell-count weights; Liquid EcoTyper plasma inference and exact figure code are not public |
| Complete main and extended-data figure generation | `BLOCKED_NOT_PUBLIC` | `/mnt/f/spatialecotyper_reproduction/results/reproducibility/source-code-inventory.tsv` | Exact paper panels cannot be regenerated without unpublished plotting and cohort-integration scripts |
| TCGA and ICI outcome association statistics | `METHOD_ONLY` | `/mnt/f/spatialecotyper_reproduction/results/reproducibility/publication-evidence.tsv` | No official executable analysis script recreates all survival response covariate and multiple-testing results |
| Liquid EcoTyper PyTorch training | `BLOCKED_NOT_PUBLIC` | `/mnt/f/spatialecotyper_reproduction/results/reproducibility/source-code-inventory.tsv` | Network implementation training code exact simulation pipeline seeds and model weights are not locally public in the cited repository |
| Liquid EcoTyper cfDNA prediction and paired-compartment validation | `BLOCKED_NOT_PUBLIC` | `/mnt/f/spatialecotyper_reproduction/results/reproducibility/source-code-inventory.tsv` | A black-box web result is not strict local reproduction; model weights preprocessing code and complete methylation inputs are not packaged here |

## 官方页面证据

- Nature 数据可用性：GSE320042；预处理/标准化数据 DOI `10.25936/pm3t-cn37`；外部公共数据编号见补充表。
- Nature 代码可用性指向 Spatial EcoTyper GitHub 与 Stanford 网站，但固定仓库实测没有 Liquid EcoTyper 的 Python 训练或本地推理代码。
- 因此，Spatial EcoTyper R 方法和 8 个教程可审计运行；Liquid EcoTyper 训练、cfDNA 本地预测、论文完整作图不能按当前公开包严格重现。

来源：https://www.nature.com/articles/s41586-026-10452-4
