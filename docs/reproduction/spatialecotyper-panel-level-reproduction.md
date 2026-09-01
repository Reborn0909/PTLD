# Spatial EcoTyper / Nature 2026 逐图板复现审计

生成时间（UTC）：2026-09-01T14:39:34+00:00

## 结论

- 论文图清单：26 张；显式图板：151 个，全部唯一覆盖。
- 图板状态：`METHOD_ONLY` 108 个；`BLOCKED_CODE` 43 个；`STRICT_PASS` 0 个。
- 目前没有论文图板满足严格原图复现：缺少论文级预处理、CytoSPACE派生权重、Liquid EcoTyper实现/检查点或最终作图脚本。
- 这不否定已完成的官方API计算：GSE320042的17个空间样本已完成spot/bin级 `DeconvoluteSE`，但不能据此宣称论文图板严格复现。
- 新增执行门状态：`PASS_NO_ELIGIBLE_PANELS`，可执行图板 0 个。

## 数据集计算就绪度

| 就绪类别 | 数据集数 |
|---|---:|
| BLOCKED_ACCESS | 6 |
| BLOCKED_NOT_PUBLIC | 7 |
| PARTIAL_FILES | 4 |
| PAUSED_CAPACITY | 3 |
| READY_OFFICIAL_PROCESSED | 1 |
| READY_RAW_ONLY | 25 |

## 官方材料更新检查

| 阻塞组件 | 候选文件 | 当前状态 | 最新官方提交 | 改变阻塞状态 |
|---|---|---|---|---|
| LIQUID_ECOTYPER | FALSE | BLOCKED_NO_NEW_OFFICIAL_MATERIAL | `57d37cd2c31c2b0743a7d50e036c4d4a50b61eee` | FALSE |
| CYTOSPACE_WEIGHTS | FALSE | BLOCKED_NO_NEW_OFFICIAL_MATERIAL | `57d37cd2c31c2b0743a7d50e036c4d4a50b61eee` | FALSE |
| FIGURE_SCRIPTS | FALSE | BLOCKED_NO_NEW_OFFICIAL_MATERIAL | `57d37cd2c31c2b0743a7d50e036c4d4a50b61eee` | FALSE |

## 仍需申请的官方材料

以下内容仅形成申请证据，均未自动发送。

| 请求类型 | 关联图板数 | 当前状态 | 用户动作 |
|---|---:|---|---|
| STANFORD_NORMALIZED_DATA | 108 | NOT_SENT | 登录Stanford入口并按许可申请论文标准化数据。 |
| CYTOSPACE_WEIGHTS | 26 | NOT_SENT | 向通讯作者申请论文使用的spot-cell映射或每spot细胞数权重。 |
| LIQUID_ECOTYPER_CODE_WEIGHTS | 43 | NOT_SENT | 向通讯作者申请PyTorch源码、配置、预处理和检查点。 |
| FIGURE_SCRIPTS | 151 | NOT_SENT | 向通讯作者申请最终作图脚本、中间表和软件锁文件。 |

## 逐图逐板证据

### MAIN-1：Multimodal profiling of SEs in human cancer.

| 图板 | 状态 | 输入记录 | 目标输出 | 限制 | 证据 |
|---|---|---|---|---|---|
| MAIN-1:a | METHOD_ONLY | Supplementary Tables 1,2,8 | Main Figure 1 panel and underlying quantitative values | The 132-sample atlas assembly, CytoSPACE reconstruction, exact statistics and plotting workflow are not packaged as an official executable pipeline. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv;source-code-inventory.tsv |
| MAIN-1:b | METHOD_ONLY | Supplementary Tables 1,2,8 | Main Figure 1 panel and underlying quantitative values | The 132-sample atlas assembly, CytoSPACE reconstruction, exact statistics and plotting workflow are not packaged as an official executable pipeline. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv;source-code-inventory.tsv |
| MAIN-1:c | METHOD_ONLY | Supplementary Tables 1,2,8 | Main Figure 1 panel and underlying quantitative values | The 132-sample atlas assembly, CytoSPACE reconstruction, exact statistics and plotting workflow are not packaged as an official executable pipeline. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv;source-code-inventory.tsv |
| MAIN-1:d | METHOD_ONLY | Supplementary Tables 1,2,8 | Main Figure 1 panel and underlying quantitative values | The 132-sample atlas assembly, CytoSPACE reconstruction, exact statistics and plotting workflow are not packaged as an official executable pipeline. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv;source-code-inventory.tsv |

### MAIN-2：Geospatial map of multicellular programs across cancers.

| 图板 | 状态 | 输入记录 | 目标输出 | 限制 | 证据 |
|---|---|---|---|---|---|
| MAIN-2:a | METHOD_ONLY | Supplementary Tables 8-11 | Main Figure 2 panel and underlying quantitative values | Official tutorials demonstrate Spatial EcoTyper components, but the complete discovery cohort inputs, perturbation jobs, seeds and panel-generation code are not packaged. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv;source-code-inventory.tsv |
| MAIN-2:b | METHOD_ONLY | Supplementary Tables 8-11 | Main Figure 2 panel and underlying quantitative values | Official tutorials demonstrate Spatial EcoTyper components, but the complete discovery cohort inputs, perturbation jobs, seeds and panel-generation code are not packaged. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv;source-code-inventory.tsv |
| MAIN-2:c | METHOD_ONLY | Supplementary Tables 8-11 | Main Figure 2 panel and underlying quantitative values | Official tutorials demonstrate Spatial EcoTyper components, but the complete discovery cohort inputs, perturbation jobs, seeds and panel-generation code are not packaged. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv;source-code-inventory.tsv |
| MAIN-2:d | METHOD_ONLY | Supplementary Tables 8-11 | Main Figure 2 panel and underlying quantitative values | Official tutorials demonstrate Spatial EcoTyper components, but the complete discovery cohort inputs, perturbation jobs, seeds and panel-generation code are not packaged. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv;source-code-inventory.tsv |
| MAIN-2:e | METHOD_ONLY | Supplementary Tables 8-11 | Main Figure 2 panel and underlying quantitative values | Official tutorials demonstrate Spatial EcoTyper components, but the complete discovery cohort inputs, perturbation jobs, seeds and panel-generation code are not packaged. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv;source-code-inventory.tsv |
| MAIN-2:f | METHOD_ONLY | Supplementary Tables 8-11 | Main Figure 2 panel and underlying quantitative values | Official tutorials demonstrate Spatial EcoTyper components, but the complete discovery cohort inputs, perturbation jobs, seeds and panel-generation code are not packaged. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv;source-code-inventory.tsv |
| MAIN-2:g | METHOD_ONLY | Supplementary Tables 8-11 | Main Figure 2 panel and underlying quantitative values | Official tutorials demonstrate Spatial EcoTyper components, but the complete discovery cohort inputs, perturbation jobs, seeds and panel-generation code are not packaged. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv;source-code-inventory.tsv |
| MAIN-2:h | METHOD_ONLY | Supplementary Tables 8-11 | Main Figure 2 panel and underlying quantitative values | Official tutorials demonstrate Spatial EcoTyper components, but the complete discovery cohort inputs, perturbation jobs, seeds and panel-generation code are not packaged. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv;source-code-inventory.tsv |

### MAIN-3：Large-scale digital cytometry and clinical characteristics of SEs.

| 图板 | 状态 | 输入记录 | 目标输出 | 限制 | 证据 |
|---|---|---|---|---|---|
| MAIN-3:a | METHOD_ONLY | Supplementary Tables 12-16 | Main Figure 3 panel and underlying quantitative values | The fixed repository lacks the paper-scale pseudo-bulk generation, paired-cohort integration, clinical modelling and plotting workflow needed for this panel. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv;source-code-inventory.tsv |
| MAIN-3:b | METHOD_ONLY | Supplementary Tables 12-16 | Main Figure 3 panel and underlying quantitative values | The fixed repository lacks the paper-scale pseudo-bulk generation, paired-cohort integration, clinical modelling and plotting workflow needed for this panel. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv;source-code-inventory.tsv |
| MAIN-3:c | METHOD_ONLY | Supplementary Tables 12-16 | Main Figure 3 panel and underlying quantitative values | The fixed repository lacks the paper-scale pseudo-bulk generation, paired-cohort integration, clinical modelling and plotting workflow needed for this panel. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv;source-code-inventory.tsv |
| MAIN-3:d | METHOD_ONLY | Supplementary Tables 12-16 | Main Figure 3 panel and underlying quantitative values | The fixed repository lacks the paper-scale pseudo-bulk generation, paired-cohort integration, clinical modelling and plotting workflow needed for this panel. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv;source-code-inventory.tsv |
| MAIN-3:e | METHOD_ONLY | Supplementary Tables 12-16 | Main Figure 3 panel and underlying quantitative values | The fixed repository lacks the paper-scale pseudo-bulk generation, paired-cohort integration, clinical modelling and plotting workflow needed for this panel. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv;source-code-inventory.tsv |
| MAIN-3:f | METHOD_ONLY | Supplementary Tables 12-16 | Main Figure 3 panel and underlying quantitative values | The fixed repository lacks the paper-scale pseudo-bulk generation, paired-cohort integration, clinical modelling and plotting workflow needed for this panel. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv;source-code-inventory.tsv |
| MAIN-3:g | METHOD_ONLY | Supplementary Tables 12-16 | Main Figure 3 panel and underlying quantitative values | The fixed repository lacks the paper-scale pseudo-bulk generation, paired-cohort integration, clinical modelling and plotting workflow needed for this panel. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv;source-code-inventory.tsv |
| MAIN-3:h | METHOD_ONLY | Supplementary Tables 12-16 | Main Figure 3 panel and underlying quantitative values | The fixed repository lacks the paper-scale pseudo-bulk generation, paired-cohort integration, clinical modelling and plotting workflow needed for this panel. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv;source-code-inventory.tsv |
| MAIN-3:i | METHOD_ONLY | Supplementary Tables 12-16 | Main Figure 3 panel and underlying quantitative values | The fixed repository lacks the paper-scale pseudo-bulk generation, paired-cohort integration, clinical modelling and plotting workflow needed for this panel. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv;source-code-inventory.tsv |

### MAIN-4：Non-invasive detection of the TME from plasma cell-free DNA.

| 图板 | 状态 | 输入记录 | 目标输出 | 限制 | 证据 |
|---|---|---|---|---|---|
| MAIN-4:a | BLOCKED_CODE | GSE320042;Supplementary Tables 17,18,21 | Main Figure 4 panel and underlying Liquid EcoTyper predictions | Liquid EcoTyper PyTorch training, local inference code, checkpoints and complete preprocessing are absent from the fixed official repository; tumour sample-level weighting also requires unpublished CytoSPACE weights. | source-code-inventory.tsv;publication-evidence.tsv;supplementary-table-s17-comparison.tsv |
| MAIN-4:b | BLOCKED_CODE | GSE320042;Supplementary Tables 17,18,21 | Main Figure 4 panel and underlying Liquid EcoTyper predictions | Liquid EcoTyper PyTorch training, local inference code, checkpoints and complete preprocessing are absent from the fixed official repository; tumour sample-level weighting also requires unpublished CytoSPACE weights. | source-code-inventory.tsv;publication-evidence.tsv;supplementary-table-s17-comparison.tsv |
| MAIN-4:c | BLOCKED_CODE | GSE320042;Supplementary Tables 17,18,21 | Main Figure 4 panel and underlying Liquid EcoTyper predictions | Liquid EcoTyper PyTorch training, local inference code, checkpoints and complete preprocessing are absent from the fixed official repository; tumour sample-level weighting also requires unpublished CytoSPACE weights. | source-code-inventory.tsv;publication-evidence.tsv;supplementary-table-s17-comparison.tsv |
| MAIN-4:d | BLOCKED_CODE | GSE320042;Supplementary Tables 17,18,21 | Main Figure 4 panel and underlying Liquid EcoTyper predictions | Liquid EcoTyper PyTorch training, local inference code, checkpoints and complete preprocessing are absent from the fixed official repository; tumour sample-level weighting also requires unpublished CytoSPACE weights. | source-code-inventory.tsv;publication-evidence.tsv;supplementary-table-s17-comparison.tsv |
| MAIN-4:e | BLOCKED_CODE | GSE320042;Supplementary Tables 17,18,21 | Main Figure 4 panel and underlying Liquid EcoTyper predictions | Liquid EcoTyper PyTorch training, local inference code, checkpoints and complete preprocessing are absent from the fixed official repository; tumour sample-level weighting also requires unpublished CytoSPACE weights. | source-code-inventory.tsv;publication-evidence.tsv;supplementary-table-s17-comparison.tsv |
| MAIN-4:f | BLOCKED_CODE | GSE320042;Supplementary Tables 17,18,21 | Main Figure 4 panel and underlying Liquid EcoTyper predictions | Liquid EcoTyper PyTorch training, local inference code, checkpoints and complete preprocessing are absent from the fixed official repository; tumour sample-level weighting also requires unpublished CytoSPACE weights. | source-code-inventory.tsv;publication-evidence.tsv;supplementary-table-s17-comparison.tsv |
| MAIN-4:g | BLOCKED_CODE | GSE320042;Supplementary Tables 17,18,21 | Main Figure 4 panel and underlying Liquid EcoTyper predictions | Liquid EcoTyper PyTorch training, local inference code, checkpoints and complete preprocessing are absent from the fixed official repository; tumour sample-level weighting also requires unpublished CytoSPACE weights. | source-code-inventory.tsv;publication-evidence.tsv;supplementary-table-s17-comparison.tsv |
| MAIN-4:h | BLOCKED_CODE | GSE320042;Supplementary Tables 17,18,21 | Main Figure 4 panel and underlying Liquid EcoTyper predictions | Liquid EcoTyper PyTorch training, local inference code, checkpoints and complete preprocessing are absent from the fixed official repository; tumour sample-level weighting also requires unpublished CytoSPACE weights. | source-code-inventory.tsv;publication-evidence.tsv;supplementary-table-s17-comparison.tsv |
| MAIN-4:i | BLOCKED_CODE | GSE320042;Supplementary Tables 17,18,21 | Main Figure 4 panel and underlying Liquid EcoTyper predictions | Liquid EcoTyper PyTorch training, local inference code, checkpoints and complete preprocessing are absent from the fixed official repository; tumour sample-level weighting also requires unpublished CytoSPACE weights. | source-code-inventory.tsv;publication-evidence.tsv;supplementary-table-s17-comparison.tsv |

### MAIN-5：Non-invasive early assessment of immunotherapy response with SEs.

| 图板 | 状态 | 输入记录 | 目标输出 | 限制 | 证据 |
|---|---|---|---|---|---|
| MAIN-5:a | BLOCKED_CODE | Supplementary Tables 19,20,22-28 | Main Figure 5 panel and underlying Liquid EcoTyper clinical predictions | Liquid EcoTyper code and model weights are not public locally, and the complete clinical methylation inputs and figure-analysis scripts are not packaged. | source-code-inventory.tsv;publication-evidence.tsv;paper-access-ledger.tsv |
| MAIN-5:b | BLOCKED_CODE | Supplementary Tables 19,20,22-28 | Main Figure 5 panel and underlying Liquid EcoTyper clinical predictions | Liquid EcoTyper code and model weights are not public locally, and the complete clinical methylation inputs and figure-analysis scripts are not packaged. | source-code-inventory.tsv;publication-evidence.tsv;paper-access-ledger.tsv |
| MAIN-5:c | BLOCKED_CODE | Supplementary Tables 19,20,22-28 | Main Figure 5 panel and underlying Liquid EcoTyper clinical predictions | Liquid EcoTyper code and model weights are not public locally, and the complete clinical methylation inputs and figure-analysis scripts are not packaged. | source-code-inventory.tsv;publication-evidence.tsv;paper-access-ledger.tsv |
| MAIN-5:d | BLOCKED_CODE | Supplementary Tables 19,20,22-28 | Main Figure 5 panel and underlying Liquid EcoTyper clinical predictions | Liquid EcoTyper code and model weights are not public locally, and the complete clinical methylation inputs and figure-analysis scripts are not packaged. | source-code-inventory.tsv;publication-evidence.tsv;paper-access-ledger.tsv |
| MAIN-5:e | BLOCKED_CODE | Supplementary Tables 19,20,22-28 | Main Figure 5 panel and underlying Liquid EcoTyper clinical predictions | Liquid EcoTyper code and model weights are not public locally, and the complete clinical methylation inputs and figure-analysis scripts are not packaged. | source-code-inventory.tsv;publication-evidence.tsv;paper-access-ledger.tsv |
| MAIN-5:f | BLOCKED_CODE | Supplementary Tables 19,20,22-28 | Main Figure 5 panel and underlying Liquid EcoTyper clinical predictions | Liquid EcoTyper code and model weights are not public locally, and the complete clinical methylation inputs and figure-analysis scripts are not packaged. | source-code-inventory.tsv;publication-evidence.tsv;paper-access-ledger.tsv |

### EXTENDED-1：Extended analysis of TME spatial polarization.

| 图板 | 状态 | 输入记录 | 目标输出 | 限制 | 证据 |
|---|---|---|---|---|---|
| EXTENDED-1:a | METHOD_ONLY | Supplementary Tables 1-7 | Extended Data Figure 1 panel and quantitative values | Paper-specific tumour-stroma annotation, CytoSPACE reconstruction, cross-platform statistics and plotting code are not packaged. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv |
| EXTENDED-1:b | METHOD_ONLY | Supplementary Tables 1-7 | Extended Data Figure 1 panel and quantitative values | Paper-specific tumour-stroma annotation, CytoSPACE reconstruction, cross-platform statistics and plotting code are not packaged. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv |
| EXTENDED-1:c | METHOD_ONLY | Supplementary Tables 1-7 | Extended Data Figure 1 panel and quantitative values | Paper-specific tumour-stroma annotation, CytoSPACE reconstruction, cross-platform statistics and plotting code are not packaged. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv |
| EXTENDED-1:d | METHOD_ONLY | Supplementary Tables 1-7 | Extended Data Figure 1 panel and quantitative values | Paper-specific tumour-stroma annotation, CytoSPACE reconstruction, cross-platform statistics and plotting code are not packaged. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv |
| EXTENDED-1:e | METHOD_ONLY | Supplementary Tables 1-7 | Extended Data Figure 1 panel and quantitative values | Paper-specific tumour-stroma annotation, CytoSPACE reconstruction, cross-platform statistics and plotting code are not packaged. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv |
| EXTENDED-1:f | METHOD_ONLY | Supplementary Tables 1-7 | Extended Data Figure 1 panel and quantitative values | Paper-specific tumour-stroma annotation, CytoSPACE reconstruction, cross-platform statistics and plotting code are not packaged. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv |
| EXTENDED-1:g | METHOD_ONLY | Supplementary Tables 1-7 | Extended Data Figure 1 panel and quantitative values | Paper-specific tumour-stroma annotation, CytoSPACE reconstruction, cross-platform statistics and plotting code are not packaged. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv |

### EXTENDED-2：Framework for spatial ecotype discovery.

| 图板 | 状态 | 输入记录 | 目标输出 | 限制 | 证据 |
|---|---|---|---|---|---|
| EXTENDED-2:a | METHOD_ONLY | Supplementary Table 8 | Extended Data Figure 2 panel and workflow outputs | The official repository documents the method but does not package the exact discovery cohort orchestration and panel output. | paper-computation-matrix.tsv;source-code-inventory.tsv |
| EXTENDED-2:b | METHOD_ONLY | Supplementary Table 8 | Extended Data Figure 2 panel and workflow outputs | The official repository documents the method but does not package the exact discovery cohort orchestration and panel output. | paper-computation-matrix.tsv;source-code-inventory.tsv |
| EXTENDED-2:c | METHOD_ONLY | Supplementary Table 8 | Extended Data Figure 2 panel and workflow outputs | The official repository documents the method but does not package the exact discovery cohort orchestration and panel output. | paper-computation-matrix.tsv;source-code-inventory.tsv |

### EXTENDED-3：Benchmarking, MERSCOPE samples, and analysis of spatial neighbourhoods from Spatial EcoTyper embeddings.

| 图板 | 状态 | 输入记录 | 目标输出 | 限制 | 证据 |
|---|---|---|---|---|---|
| EXTENDED-3:a | METHOD_ONLY | Supplementary Table 8 | Extended Data Figure 3 benchmarking panel and quantitative values | Benchmarking inputs, competing-method configurations, seeds and paper plotting code are not supplied as one executable official workflow. | paper-dataset-readiness.tsv;source-code-inventory.tsv |
| EXTENDED-3:b | METHOD_ONLY | Supplementary Table 8 | Extended Data Figure 3 benchmarking panel and quantitative values | Benchmarking inputs, competing-method configurations, seeds and paper plotting code are not supplied as one executable official workflow. | paper-dataset-readiness.tsv;source-code-inventory.tsv |
| EXTENDED-3:c | METHOD_ONLY | Supplementary Table 8 | Extended Data Figure 3 benchmarking panel and quantitative values | Benchmarking inputs, competing-method configurations, seeds and paper plotting code are not supplied as one executable official workflow. | paper-dataset-readiness.tsv;source-code-inventory.tsv |
| EXTENDED-3:d | METHOD_ONLY | Supplementary Table 8 | Extended Data Figure 3 benchmarking panel and quantitative values | Benchmarking inputs, competing-method configurations, seeds and paper plotting code are not supplied as one executable official workflow. | paper-dataset-readiness.tsv;source-code-inventory.tsv |
| EXTENDED-3:e | METHOD_ONLY | Supplementary Table 8 | Extended Data Figure 3 benchmarking panel and quantitative values | Benchmarking inputs, competing-method configurations, seeds and paper plotting code are not supplied as one executable official workflow. | paper-dataset-readiness.tsv;source-code-inventory.tsv |
| EXTENDED-3:f | METHOD_ONLY | Supplementary Table 8 | Extended Data Figure 3 benchmarking panel and quantitative values | Benchmarking inputs, competing-method configurations, seeds and paper plotting code are not supplied as one executable official workflow. | paper-dataset-readiness.tsv;source-code-inventory.tsv |
| EXTENDED-3:g | METHOD_ONLY | Supplementary Table 8 | Extended Data Figure 3 benchmarking panel and quantitative values | Benchmarking inputs, competing-method configurations, seeds and paper plotting code are not supplied as one executable official workflow. | paper-dataset-readiness.tsv;source-code-inventory.tsv |
| EXTENDED-3:h | METHOD_ONLY | Supplementary Table 8 | Extended Data Figure 3 benchmarking panel and quantitative values | Benchmarking inputs, competing-method configurations, seeds and paper plotting code are not supplied as one executable official workflow. | paper-dataset-readiness.tsv;source-code-inventory.tsv |
| EXTENDED-3:i | METHOD_ONLY | Supplementary Table 8 | Extended Data Figure 3 benchmarking panel and quantitative values | Benchmarking inputs, competing-method configurations, seeds and paper plotting code are not supplied as one executable official workflow. | paper-dataset-readiness.tsv;source-code-inventory.tsv |

### EXTENDED-4：Discovery and robustness testing of nine spatial ecotypes from MERSCOPE data.

| 图板 | 状态 | 输入记录 | 目标输出 | 限制 | 证据 |
|---|---|---|---|---|---|
| EXTENDED-4:a | METHOD_ONLY | Supplementary Tables 8,9 | Extended Data Figure 4 robustness panel and quantitative values | The fixed repository lacks the full perturbation grid, exact seeds, intermediate matrices and panel-generation scripts used for paper robustness testing. | paper-computation-matrix.tsv;source-code-inventory.tsv |
| EXTENDED-4:b | METHOD_ONLY | Supplementary Tables 8,9 | Extended Data Figure 4 robustness panel and quantitative values | The fixed repository lacks the full perturbation grid, exact seeds, intermediate matrices and panel-generation scripts used for paper robustness testing. | paper-computation-matrix.tsv;source-code-inventory.tsv |
| EXTENDED-4:c | METHOD_ONLY | Supplementary Tables 8,9 | Extended Data Figure 4 robustness panel and quantitative values | The fixed repository lacks the full perturbation grid, exact seeds, intermediate matrices and panel-generation scripts used for paper robustness testing. | paper-computation-matrix.tsv;source-code-inventory.tsv |
| EXTENDED-4:d | METHOD_ONLY | Supplementary Tables 8,9 | Extended Data Figure 4 robustness panel and quantitative values | The fixed repository lacks the full perturbation grid, exact seeds, intermediate matrices and panel-generation scripts used for paper robustness testing. | paper-computation-matrix.tsv;source-code-inventory.tsv |
| EXTENDED-4:e | METHOD_ONLY | Supplementary Tables 8,9 | Extended Data Figure 4 robustness panel and quantitative values | The fixed repository lacks the full perturbation grid, exact seeds, intermediate matrices and panel-generation scripts used for paper robustness testing. | paper-computation-matrix.tsv;source-code-inventory.tsv |
| EXTENDED-4:f | METHOD_ONLY | Supplementary Tables 8,9 | Extended Data Figure 4 robustness panel and quantitative values | The fixed repository lacks the full perturbation grid, exact seeds, intermediate matrices and panel-generation scripts used for paper robustness testing. | paper-computation-matrix.tsv;source-code-inventory.tsv |
| EXTENDED-4:g | METHOD_ONLY | Supplementary Tables 8,9 | Extended Data Figure 4 robustness panel and quantitative values | The fixed repository lacks the full perturbation grid, exact seeds, intermediate matrices and panel-generation scripts used for paper robustness testing. | paper-computation-matrix.tsv;source-code-inventory.tsv |
| EXTENDED-4:h | METHOD_ONLY | Supplementary Tables 8,9 | Extended Data Figure 4 robustness panel and quantitative values | The fixed repository lacks the full perturbation grid, exact seeds, intermediate matrices and panel-generation scripts used for paper robustness testing. | paper-computation-matrix.tsv;source-code-inventory.tsv |
| EXTENDED-4:i | METHOD_ONLY | Supplementary Tables 8,9 | Extended Data Figure 4 robustness panel and quantitative values | The fixed repository lacks the full perturbation grid, exact seeds, intermediate matrices and panel-generation scripts used for paper robustness testing. | paper-computation-matrix.tsv;source-code-inventory.tsv |
| EXTENDED-4:j | METHOD_ONLY | Supplementary Tables 8,9 | Extended Data Figure 4 robustness panel and quantitative values | The fixed repository lacks the full perturbation grid, exact seeds, intermediate matrices and panel-generation scripts used for paper robustness testing. | paper-computation-matrix.tsv;source-code-inventory.tsv |
| EXTENDED-4:k | METHOD_ONLY | Supplementary Tables 8,9 | Extended Data Figure 4 robustness panel and quantitative values | The fixed repository lacks the full perturbation grid, exact seeds, intermediate matrices and panel-generation scripts used for paper robustness testing. | paper-computation-matrix.tsv;source-code-inventory.tsv |
| EXTENDED-4:l | METHOD_ONLY | Supplementary Tables 8,9 | Extended Data Figure 4 robustness panel and quantitative values | The fixed repository lacks the full perturbation grid, exact seeds, intermediate matrices and panel-generation scripts used for paper robustness testing. | paper-computation-matrix.tsv;source-code-inventory.tsv |

### EXTENDED-5：Distinguishability of spatial ecotypes by archetypal analysis.

| 图板 | 状态 | 输入记录 | 目标输出 | 限制 | 证据 |
|---|---|---|---|---|---|
| EXTENDED-5:a | METHOD_ONLY | Supplementary Table 8 | Extended Data Figure 5 archetypal-analysis panel and quantitative values | The paper-specific archetypal-analysis inputs and plotting workflow are described but not packaged in the official code archive. | paper-dataset-readiness.tsv;source-code-inventory.tsv |
| EXTENDED-5:b | METHOD_ONLY | Supplementary Table 8 | Extended Data Figure 5 archetypal-analysis panel and quantitative values | The paper-specific archetypal-analysis inputs and plotting workflow are described but not packaged in the official code archive. | paper-dataset-readiness.tsv;source-code-inventory.tsv |
| EXTENDED-5:c | METHOD_ONLY | Supplementary Table 8 | Extended Data Figure 5 archetypal-analysis panel and quantitative values | The paper-specific archetypal-analysis inputs and plotting workflow are described but not packaged in the official code archive. | paper-dataset-readiness.tsv;source-code-inventory.tsv |
| EXTENDED-5:d | METHOD_ONLY | Supplementary Table 8 | Extended Data Figure 5 archetypal-analysis panel and quantitative values | The paper-specific archetypal-analysis inputs and plotting workflow are described but not packaged in the official code archive. | paper-dataset-readiness.tsv;source-code-inventory.tsv |
| EXTENDED-5:e | METHOD_ONLY | Supplementary Table 8 | Extended Data Figure 5 archetypal-analysis panel and quantitative values | The paper-specific archetypal-analysis inputs and plotting workflow are described but not packaged in the official code archive. | paper-dataset-readiness.tsv;source-code-inventory.tsv |
| EXTENDED-5:f | METHOD_ONLY | Supplementary Table 8 | Extended Data Figure 5 archetypal-analysis panel and quantitative values | The paper-specific archetypal-analysis inputs and plotting workflow are described but not packaged in the official code archive. | paper-dataset-readiness.tsv;source-code-inventory.tsv |
| EXTENDED-5:g | METHOD_ONLY | Supplementary Table 8 | Extended Data Figure 5 archetypal-analysis panel and quantitative values | The paper-specific archetypal-analysis inputs and plotting workflow are described but not packaged in the official code archive. | paper-dataset-readiness.tsv;source-code-inventory.tsv |

### EXTENDED-6：Cell states, geographic features, and cross-platform detectability of spatial ecotypes.

| 图板 | 状态 | 输入记录 | 目标输出 | 限制 | 证据 |
|---|---|---|---|---|---|
| EXTENDED-6:a | METHOD_ONLY | Supplementary Tables 1,8-10 | Extended Data Figure 6 panel and quantitative values | Tutorials cover recovery components, but complete LOOCV, cross-platform colocalization, Xenium discovery and figure orchestration are not packaged. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv |
| EXTENDED-6:b | METHOD_ONLY | Supplementary Tables 1,8-10 | Extended Data Figure 6 panel and quantitative values | Tutorials cover recovery components, but complete LOOCV, cross-platform colocalization, Xenium discovery and figure orchestration are not packaged. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv |
| EXTENDED-6:c | METHOD_ONLY | Supplementary Tables 1,8-10 | Extended Data Figure 6 panel and quantitative values | Tutorials cover recovery components, but complete LOOCV, cross-platform colocalization, Xenium discovery and figure orchestration are not packaged. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv |
| EXTENDED-6:f | METHOD_ONLY | Supplementary Tables 1,8-10 | Extended Data Figure 6 panel and quantitative values | Tutorials cover recovery components, but complete LOOCV, cross-platform colocalization, Xenium discovery and figure orchestration are not packaged. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv |
| EXTENDED-6:g | METHOD_ONLY | Supplementary Tables 1,8-10 | Extended Data Figure 6 panel and quantitative values | Tutorials cover recovery components, but complete LOOCV, cross-platform colocalization, Xenium discovery and figure orchestration are not packaged. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv |
| EXTENDED-6:h | METHOD_ONLY | Supplementary Tables 1,8-10 | Extended Data Figure 6 panel and quantitative values | Tutorials cover recovery components, but complete LOOCV, cross-platform colocalization, Xenium discovery and figure orchestration are not packaged. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv |
| EXTENDED-6:i | METHOD_ONLY | Supplementary Tables 1,8-10 | Extended Data Figure 6 panel and quantitative values | Tutorials cover recovery components, but complete LOOCV, cross-platform colocalization, Xenium discovery and figure orchestration are not packaged. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv |
| EXTENDED-6:j | METHOD_ONLY | Supplementary Tables 1,8-10 | Extended Data Figure 6 panel and quantitative values | Tutorials cover recovery components, but complete LOOCV, cross-platform colocalization, Xenium discovery and figure orchestration are not packaged. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv |
| EXTENDED-6:k | METHOD_ONLY | Supplementary Tables 1,8-10 | Extended Data Figure 6 panel and quantitative values | Tutorials cover recovery components, but complete LOOCV, cross-platform colocalization, Xenium discovery and figure orchestration are not packaged. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv |
| EXTENDED-6:l | METHOD_ONLY | Supplementary Tables 1,8-10 | Extended Data Figure 6 panel and quantitative values | Tutorials cover recovery components, but complete LOOCV, cross-platform colocalization, Xenium discovery and figure orchestration are not packaged. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv |
| EXTENDED-6:m | METHOD_ONLY | Supplementary Tables 1,8-10 | Extended Data Figure 6 panel and quantitative values | Tutorials cover recovery components, but complete LOOCV, cross-platform colocalization, Xenium discovery and figure orchestration are not packaged. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv |
| EXTENDED-6:n | METHOD_ONLY | Supplementary Tables 1,8-10 | Extended Data Figure 6 panel and quantitative values | Tutorials cover recovery components, but complete LOOCV, cross-platform colocalization, Xenium discovery and figure orchestration are not packaged. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv |
| EXTENDED-6:o | METHOD_ONLY | Supplementary Tables 1,8-10 | Extended Data Figure 6 panel and quantitative values | Tutorials cover recovery components, but complete LOOCV, cross-platform colocalization, Xenium discovery and figure orchestration are not packaged. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv |

### EXTENDED-7：Extended analysis of SE generalizability and molecular features.

| 图板 | 状态 | 输入记录 | 目标输出 | 限制 | 证据 |
|---|---|---|---|---|---|
| EXTENDED-7:a | METHOD_ONLY | Supplementary Tables 2,10,11 | Extended Data Figure 7 panel and quantitative values | The 144-tumour scRNA atlas assembly, marker validation and complete statistical/plotting scripts are not available as an official executable workflow. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv |
| EXTENDED-7:b | METHOD_ONLY | Supplementary Tables 2,10,11 | Extended Data Figure 7 panel and quantitative values | The 144-tumour scRNA atlas assembly, marker validation and complete statistical/plotting scripts are not available as an official executable workflow. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv |
| EXTENDED-7:c | METHOD_ONLY | Supplementary Tables 2,10,11 | Extended Data Figure 7 panel and quantitative values | The 144-tumour scRNA atlas assembly, marker validation and complete statistical/plotting scripts are not available as an official executable workflow. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv |
| EXTENDED-7:d | METHOD_ONLY | Supplementary Tables 2,10,11 | Extended Data Figure 7 panel and quantitative values | The 144-tumour scRNA atlas assembly, marker validation and complete statistical/plotting scripts are not available as an official executable workflow. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv |
| EXTENDED-7:e | METHOD_ONLY | Supplementary Tables 2,10,11 | Extended Data Figure 7 panel and quantitative values | The 144-tumour scRNA atlas assembly, marker validation and complete statistical/plotting scripts are not available as an official executable workflow. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv |
| EXTENDED-7:f | METHOD_ONLY | Supplementary Tables 2,10,11 | Extended Data Figure 7 panel and quantitative values | The 144-tumour scRNA atlas assembly, marker validation and complete statistical/plotting scripts are not available as an official executable workflow. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv |
| EXTENDED-7:g | METHOD_ONLY | Supplementary Tables 2,10,11 | Extended Data Figure 7 panel and quantitative values | The 144-tumour scRNA atlas assembly, marker validation and complete statistical/plotting scripts are not available as an official executable workflow. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv |
| EXTENDED-7:h | METHOD_ONLY | Supplementary Tables 2,10,11 | Extended Data Figure 7 panel and quantitative values | The 144-tumour scRNA atlas assembly, marker validation and complete statistical/plotting scripts are not available as an official executable workflow. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv |
| EXTENDED-7:i | METHOD_ONLY | Supplementary Tables 2,10,11 | Extended Data Figure 7 panel and quantitative values | The 144-tumour scRNA atlas assembly, marker validation and complete statistical/plotting scripts are not available as an official executable workflow. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv |
| EXTENDED-7:j | METHOD_ONLY | Supplementary Tables 2,10,11 | Extended Data Figure 7 panel and quantitative values | The 144-tumour scRNA atlas assembly, marker validation and complete statistical/plotting scripts are not available as an official executable workflow. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv |

### EXTENDED-8：Multimodal validation of SE deconvolution.

| 图板 | 状态 | 输入记录 | 目标输出 | 限制 | 证据 |
|---|---|---|---|---|---|
| EXTENDED-8:a | METHOD_ONLY | Supplementary Tables 12,13 | Extended Data Figure 8 deconvolution panel and quantitative values | The official repository lacks exact pseudo-tumour generation, held-out cohorts, stochastic seeds, paired-data integration and paper output scripts. | paper-computation-matrix.tsv;source-code-inventory.tsv |
| EXTENDED-8:b | METHOD_ONLY | Supplementary Tables 12,13 | Extended Data Figure 8 deconvolution panel and quantitative values | The official repository lacks exact pseudo-tumour generation, held-out cohorts, stochastic seeds, paired-data integration and paper output scripts. | paper-computation-matrix.tsv;source-code-inventory.tsv |
| EXTENDED-8:c | METHOD_ONLY | Supplementary Tables 12,13 | Extended Data Figure 8 deconvolution panel and quantitative values | The official repository lacks exact pseudo-tumour generation, held-out cohorts, stochastic seeds, paired-data integration and paper output scripts. | paper-computation-matrix.tsv;source-code-inventory.tsv |
| EXTENDED-8:d | METHOD_ONLY | Supplementary Tables 12,13 | Extended Data Figure 8 deconvolution panel and quantitative values | The official repository lacks exact pseudo-tumour generation, held-out cohorts, stochastic seeds, paired-data integration and paper output scripts. | paper-computation-matrix.tsv;source-code-inventory.tsv |
| EXTENDED-8:e | METHOD_ONLY | Supplementary Tables 12,13 | Extended Data Figure 8 deconvolution panel and quantitative values | The official repository lacks exact pseudo-tumour generation, held-out cohorts, stochastic seeds, paired-data integration and paper output scripts. | paper-computation-matrix.tsv;source-code-inventory.tsv |
| EXTENDED-8:f | METHOD_ONLY | Supplementary Tables 12,13 | Extended Data Figure 8 deconvolution panel and quantitative values | The official repository lacks exact pseudo-tumour generation, held-out cohorts, stochastic seeds, paired-data integration and paper output scripts. | paper-computation-matrix.tsv;source-code-inventory.tsv |
| EXTENDED-8:g | METHOD_ONLY | Supplementary Tables 12,13 | Extended Data Figure 8 deconvolution panel and quantitative values | The official repository lacks exact pseudo-tumour generation, held-out cohorts, stochastic seeds, paired-data integration and paper output scripts. | paper-computation-matrix.tsv;source-code-inventory.tsv |
| EXTENDED-8:h | METHOD_ONLY | Supplementary Tables 12,13 | Extended Data Figure 8 deconvolution panel and quantitative values | The official repository lacks exact pseudo-tumour generation, held-out cohorts, stochastic seeds, paired-data integration and paper output scripts. | paper-computation-matrix.tsv;source-code-inventory.tsv |
| EXTENDED-8:i | METHOD_ONLY | Supplementary Tables 12,13 | Extended Data Figure 8 deconvolution panel and quantitative values | The official repository lacks exact pseudo-tumour generation, held-out cohorts, stochastic seeds, paired-data integration and paper output scripts. | paper-computation-matrix.tsv;source-code-inventory.tsv |

### EXTENDED-9：Extended analysis of SE deconvolution from paired ST profiles and large clinical cohorts.

| 图板 | 状态 | 输入记录 | 目标输出 | 限制 | 证据 |
|---|---|---|---|---|---|
| EXTENDED-9:a | METHOD_ONLY | Supplementary Tables 8,11,14-16 | Extended Data Figure 9 panel and quantitative values | Co-registered sections, clinical covariates and paper-specific association/plotting scripts are not packaged together. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv |
| EXTENDED-9:b | METHOD_ONLY | Supplementary Tables 8,11,14-16 | Extended Data Figure 9 panel and quantitative values | Co-registered sections, clinical covariates and paper-specific association/plotting scripts are not packaged together. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv |
| EXTENDED-9:c | METHOD_ONLY | Supplementary Tables 8,11,14-16 | Extended Data Figure 9 panel and quantitative values | Co-registered sections, clinical covariates and paper-specific association/plotting scripts are not packaged together. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv |
| EXTENDED-9:d | METHOD_ONLY | Supplementary Tables 8,11,14-16 | Extended Data Figure 9 panel and quantitative values | Co-registered sections, clinical covariates and paper-specific association/plotting scripts are not packaged together. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv |
| EXTENDED-9:e | METHOD_ONLY | Supplementary Tables 8,11,14-16 | Extended Data Figure 9 panel and quantitative values | Co-registered sections, clinical covariates and paper-specific association/plotting scripts are not packaged together. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv |
| EXTENDED-9:f | METHOD_ONLY | Supplementary Tables 8,11,14-16 | Extended Data Figure 9 panel and quantitative values | Co-registered sections, clinical covariates and paper-specific association/plotting scripts are not packaged together. | paper-dataset-readiness.tsv;paper-computation-matrix.tsv |

### EXTENDED-10：Development and technical assessment of Liquid EcoTyper.

| 图板 | 状态 | 输入记录 | 目标输出 | 限制 | 证据 |
|---|---|---|---|---|---|
| EXTENDED-10:a | BLOCKED_CODE | Supplementary Tables 11,17 | Extended Data Figure 10 Liquid EcoTyper panel and quantitative values | Liquid EcoTyper simulation, PyTorch training, ablation, checkpoints and local inference code are absent from the fixed official repository. | source-code-inventory.tsv;publication-evidence.tsv |
| EXTENDED-10:b | BLOCKED_CODE | Supplementary Tables 11,17 | Extended Data Figure 10 Liquid EcoTyper panel and quantitative values | Liquid EcoTyper simulation, PyTorch training, ablation, checkpoints and local inference code are absent from the fixed official repository. | source-code-inventory.tsv;publication-evidence.tsv |
| EXTENDED-10:c | BLOCKED_CODE | Supplementary Tables 11,17 | Extended Data Figure 10 Liquid EcoTyper panel and quantitative values | Liquid EcoTyper simulation, PyTorch training, ablation, checkpoints and local inference code are absent from the fixed official repository. | source-code-inventory.tsv;publication-evidence.tsv |
| EXTENDED-10:d | BLOCKED_CODE | Supplementary Tables 11,17 | Extended Data Figure 10 Liquid EcoTyper panel and quantitative values | Liquid EcoTyper simulation, PyTorch training, ablation, checkpoints and local inference code are absent from the fixed official repository. | source-code-inventory.tsv;publication-evidence.tsv |
| EXTENDED-10:e | BLOCKED_CODE | Supplementary Tables 11,17 | Extended Data Figure 10 Liquid EcoTyper panel and quantitative values | Liquid EcoTyper simulation, PyTorch training, ablation, checkpoints and local inference code are absent from the fixed official repository. | source-code-inventory.tsv;publication-evidence.tsv |
| EXTENDED-10:f | BLOCKED_CODE | Supplementary Tables 11,17 | Extended Data Figure 10 Liquid EcoTyper panel and quantitative values | Liquid EcoTyper simulation, PyTorch training, ablation, checkpoints and local inference code are absent from the fixed official repository. | source-code-inventory.tsv;publication-evidence.tsv |
| EXTENDED-10:g | BLOCKED_CODE | Supplementary Tables 11,17 | Extended Data Figure 10 Liquid EcoTyper panel and quantitative values | Liquid EcoTyper simulation, PyTorch training, ablation, checkpoints and local inference code are absent from the fixed official repository. | source-code-inventory.tsv;publication-evidence.tsv |
| EXTENDED-10:h | BLOCKED_CODE | Supplementary Tables 11,17 | Extended Data Figure 10 Liquid EcoTyper panel and quantitative values | Liquid EcoTyper simulation, PyTorch training, ablation, checkpoints and local inference code are absent from the fixed official repository. | source-code-inventory.tsv;publication-evidence.tsv |
| EXTENDED-10:i | BLOCKED_CODE | Supplementary Tables 11,17 | Extended Data Figure 10 Liquid EcoTyper panel and quantitative values | Liquid EcoTyper simulation, PyTorch training, ablation, checkpoints and local inference code are absent from the fixed official repository. | source-code-inventory.tsv;publication-evidence.tsv |

### EXTENDED-11：Extended assessment of Liquid EcoTyper using paired tumour and plasma profiles.

| 图板 | 状态 | 输入记录 | 目标输出 | 限制 | 证据 |
|---|---|---|---|---|---|
| EXTENDED-11:a | BLOCKED_CODE | GSE320042;Supplementary Tables 17,18,21 | Extended Data Figure 11 paired tumour-plasma panel and quantitative values | Liquid EcoTyper model code and weights are absent; sample-level tumour values additionally require unpublished CytoSPACE weights and complete paired methylation inputs. | source-code-inventory.tsv;supplementary-table-s17-comparison.tsv;paper-access-ledger.tsv |
| EXTENDED-11:b | BLOCKED_CODE | GSE320042;Supplementary Tables 17,18,21 | Extended Data Figure 11 paired tumour-plasma panel and quantitative values | Liquid EcoTyper model code and weights are absent; sample-level tumour values additionally require unpublished CytoSPACE weights and complete paired methylation inputs. | source-code-inventory.tsv;supplementary-table-s17-comparison.tsv;paper-access-ledger.tsv |
| EXTENDED-11:c | BLOCKED_CODE | GSE320042;Supplementary Tables 17,18,21 | Extended Data Figure 11 paired tumour-plasma panel and quantitative values | Liquid EcoTyper model code and weights are absent; sample-level tumour values additionally require unpublished CytoSPACE weights and complete paired methylation inputs. | source-code-inventory.tsv;supplementary-table-s17-comparison.tsv;paper-access-ledger.tsv |
| EXTENDED-11:d | BLOCKED_CODE | GSE320042;Supplementary Tables 17,18,21 | Extended Data Figure 11 paired tumour-plasma panel and quantitative values | Liquid EcoTyper model code and weights are absent; sample-level tumour values additionally require unpublished CytoSPACE weights and complete paired methylation inputs. | source-code-inventory.tsv;supplementary-table-s17-comparison.tsv;paper-access-ledger.tsv |
| EXTENDED-11:e | BLOCKED_CODE | GSE320042;Supplementary Tables 17,18,21 | Extended Data Figure 11 paired tumour-plasma panel and quantitative values | Liquid EcoTyper model code and weights are absent; sample-level tumour values additionally require unpublished CytoSPACE weights and complete paired methylation inputs. | source-code-inventory.tsv;supplementary-table-s17-comparison.tsv;paper-access-ledger.tsv |
| EXTENDED-11:f | BLOCKED_CODE | GSE320042;Supplementary Tables 17,18,21 | Extended Data Figure 11 paired tumour-plasma panel and quantitative values | Liquid EcoTyper model code and weights are absent; sample-level tumour values additionally require unpublished CytoSPACE weights and complete paired methylation inputs. | source-code-inventory.tsv;supplementary-table-s17-comparison.tsv;paper-access-ledger.tsv |

### EXTENDED-12：Non-invasive early assessment of melanoma patient survival and immunotherapy response with liquid SEs.

| 图板 | 状态 | 输入记录 | 目标输出 | 限制 | 证据 |
|---|---|---|---|---|---|
| EXTENDED-12:a | BLOCKED_CODE | Supplementary Tables 19,20,24,26,28 | Extended Data Figure 12 clinical panel and quantitative values | Liquid EcoTyper predictions cannot be regenerated without unpublished code and checkpoints; complete clinical inputs and figure scripts are also not packaged. | source-code-inventory.tsv;paper-access-ledger.tsv |
| EXTENDED-12:b | BLOCKED_CODE | Supplementary Tables 19,20,24,26,28 | Extended Data Figure 12 clinical panel and quantitative values | Liquid EcoTyper predictions cannot be regenerated without unpublished code and checkpoints; complete clinical inputs and figure scripts are also not packaged. | source-code-inventory.tsv;paper-access-ledger.tsv |
| EXTENDED-12:c | BLOCKED_CODE | Supplementary Tables 19,20,24,26,28 | Extended Data Figure 12 clinical panel and quantitative values | Liquid EcoTyper predictions cannot be regenerated without unpublished code and checkpoints; complete clinical inputs and figure scripts are also not packaged. | source-code-inventory.tsv;paper-access-ledger.tsv |
| EXTENDED-12:d | BLOCKED_CODE | Supplementary Tables 19,20,24,26,28 | Extended Data Figure 12 clinical panel and quantitative values | Liquid EcoTyper predictions cannot be regenerated without unpublished code and checkpoints; complete clinical inputs and figure scripts are also not packaged. | source-code-inventory.tsv;paper-access-ledger.tsv |
| EXTENDED-12:e | BLOCKED_CODE | Supplementary Tables 19,20,24,26,28 | Extended Data Figure 12 clinical panel and quantitative values | Liquid EcoTyper predictions cannot be regenerated without unpublished code and checkpoints; complete clinical inputs and figure scripts are also not packaged. | source-code-inventory.tsv;paper-access-ledger.tsv |
| EXTENDED-12:f | BLOCKED_CODE | Supplementary Tables 19,20,24,26,28 | Extended Data Figure 12 clinical panel and quantitative values | Liquid EcoTyper predictions cannot be regenerated without unpublished code and checkpoints; complete clinical inputs and figure scripts are also not packaged. | source-code-inventory.tsv;paper-access-ledger.tsv |
| EXTENDED-12:g | BLOCKED_CODE | Supplementary Tables 19,20,24,26,28 | Extended Data Figure 12 clinical panel and quantitative values | Liquid EcoTyper predictions cannot be regenerated without unpublished code and checkpoints; complete clinical inputs and figure scripts are also not packaged. | source-code-inventory.tsv;paper-access-ledger.tsv |
| EXTENDED-12:h | BLOCKED_CODE | Supplementary Tables 19,20,24,26,28 | Extended Data Figure 12 clinical panel and quantitative values | Liquid EcoTyper predictions cannot be regenerated without unpublished code and checkpoints; complete clinical inputs and figure scripts are also not packaged. | source-code-inventory.tsv;paper-access-ledger.tsv |
| EXTENDED-12:i | BLOCKED_CODE | Supplementary Tables 19,20,24,26,28 | Extended Data Figure 12 clinical panel and quantitative values | Liquid EcoTyper predictions cannot be regenerated without unpublished code and checkpoints; complete clinical inputs and figure scripts are also not packaged. | source-code-inventory.tsv;paper-access-ledger.tsv |

### SUPPLEMENTARY-1：Inventory of publicly available scRNA-seq and ST datasets

| 图板 | 状态 | 输入记录 | 目标输出 | 限制 | 证据 |
|---|---|---|---|---|---|
| SUPPLEMENTARY-1:a | METHOD_ONLY | Supplementary Tables 1,2 | Supplementary Figure 1 panel and quantitative values | The complete post-processing and annotation workflow for all public atlas datasets is not packaged in the fixed official repository. | paper-dataset-readiness.tsv;source-code-inventory.tsv |
| SUPPLEMENTARY-1:b | METHOD_ONLY | Supplementary Tables 1,2 | Supplementary Figure 1 panel and quantitative values | The complete post-processing and annotation workflow for all public atlas datasets is not packaged in the fixed official repository. | paper-dataset-readiness.tsv;source-code-inventory.tsv |
| SUPPLEMENTARY-1:c | METHOD_ONLY | Supplementary Tables 1,2 | Supplementary Figure 1 panel and quantitative values | The complete post-processing and annotation workflow for all public atlas datasets is not packaged in the fixed official repository. | paper-dataset-readiness.tsv;source-code-inventory.tsv |

### SUPPLEMENTARY-2：Framework for distinguishing tumour from adjacent stroma

| 图板 | 状态 | 输入记录 | 目标输出 | 限制 | 证据 |
|---|---|---|---|---|---|
| SUPPLEMENTARY-2:a | METHOD_ONLY | Supplementary Tables 1-4 | Supplementary Figure 2 panel and quantitative values | The tumour-stroma classifier training objects, pathologist labels and paper panel scripts are not packaged as an executable official workflow. | paper-dataset-readiness.tsv;source-code-inventory.tsv |
| SUPPLEMENTARY-2:b | METHOD_ONLY | Supplementary Tables 1-4 | Supplementary Figure 2 panel and quantitative values | The tumour-stroma classifier training objects, pathologist labels and paper panel scripts are not packaged as an executable official workflow. | paper-dataset-readiness.tsv;source-code-inventory.tsv |
| SUPPLEMENTARY-2:c | METHOD_ONLY | Supplementary Tables 1-4 | Supplementary Figure 2 panel and quantitative values | The tumour-stroma classifier training objects, pathologist labels and paper panel scripts are not packaged as an executable official workflow. | paper-dataset-readiness.tsv;source-code-inventory.tsv |

### SUPPLEMENTARY-3：Spatial polarization of previous cell state signatures in the TME

| 图板 | 状态 | 输入记录 | 目标输出 | 限制 | 证据 |
|---|---|---|---|---|---|
| SUPPLEMENTARY-3:whole | METHOD_ONLY | Supplementary Table 5 | Supplementary Figure 3 panel and quantitative values | The complete spatial-polarization input atlas and paper statistics/plotting code are not packaged. | paper-dataset-readiness.tsv;source-code-inventory.tsv |

### SUPPLEMENTARY-4：Scalability of Spatial EcoTyper discovery mode

| 图板 | 状态 | 输入记录 | 目标输出 | 限制 | 证据 |
|---|---|---|---|---|---|
| SUPPLEMENTARY-4:a | METHOD_ONLY | Supplementary Table 8 | Supplementary Figure 4 panel and quantitative values | The exact scalability experiment grid, hardware capture and comparison-output script are not packaged with the official tutorials. | paper-computation-matrix.tsv;source-code-inventory.tsv |
| SUPPLEMENTARY-4:b | METHOD_ONLY | Supplementary Table 8 | Supplementary Figure 4 panel and quantitative values | The exact scalability experiment grid, hardware capture and comparison-output script are not packaged with the official tutorials. | paper-computation-matrix.tsv;source-code-inventory.tsv |

### SUPPLEMENTARY-5：Benchmarking spatial meta-cells

| 图板 | 状态 | 输入记录 | 目标输出 | 限制 | 证据 |
|---|---|---|---|---|---|
| SUPPLEMENTARY-5:whole | METHOD_ONLY | Supplementary Table 8 | Supplementary Figure 5 panel and quantitative values | Benchmark configurations and the complete spatial meta-cell evaluation workflow are not present in the fixed repository. | paper-dataset-readiness.tsv;source-code-inventory.tsv |

### SUPPLEMENTARY-6：Robustness of SE consensus markers

| 图板 | 状态 | 输入记录 | 目标输出 | 限制 | 证据 |
|---|---|---|---|---|---|
| SUPPLEMENTARY-6:whole | METHOD_ONLY | Supplementary Table 11 | Supplementary Figure 6 panel and quantitative values | Consensus-marker inputs and exact robustness/plotting scripts for the full paper atlas are not packaged. | paper-dataset-readiness.tsv;source-code-inventory.tsv |

### SUPPLEMENTARY-7：Spatial ecotype complexity versus Liquid EcoTyper performance

| 图板 | 状态 | 输入记录 | 目标输出 | 限制 | 证据 |
|---|---|---|---|---|---|
| SUPPLEMENTARY-7:whole | BLOCKED_CODE | Supplementary Tables 11,17 | Supplementary Figure 7 Liquid EcoTyper performance panel and quantitative values | Liquid EcoTyper predictions and performance values require unpublished model code and checkpoints. | source-code-inventory.tsv;publication-evidence.tsv |

### SUPPLEMENTARY-8：CpG sets versus predicted SE levels across clinical cohorts

| 图板 | 状态 | 输入记录 | 目标输出 | 限制 | 证据 |
|---|---|---|---|---|---|
| SUPPLEMENTARY-8:whole | BLOCKED_CODE | Supplementary Tables 17-20 | Supplementary Figure 8 Liquid EcoTyper panel and quantitative values | Liquid EcoTyper CpG-set inference code, learned weights and complete clinical methylation inputs are not packaged. | source-code-inventory.tsv;paper-access-ledger.tsv |

### SUPPLEMENTARY-9：Time-dependent AUC analysis

| 图板 | 状态 | 输入记录 | 目标输出 | 限制 | 证据 |
|---|---|---|---|---|---|
| SUPPLEMENTARY-9:a | BLOCKED_CODE | Supplementary Tables 19,20,24 | Supplementary Figure 9 clinical panel and quantitative values | Time-dependent AUC inputs depend on unpublished Liquid EcoTyper predictions and unavailable paper-specific clinical analysis scripts. | source-code-inventory.tsv;paper-access-ledger.tsv |
| SUPPLEMENTARY-9:b | BLOCKED_CODE | Supplementary Tables 19,20,24 | Supplementary Figure 9 clinical panel and quantitative values | Time-dependent AUC inputs depend on unpublished Liquid EcoTyper predictions and unavailable paper-specific clinical analysis scripts. | source-code-inventory.tsv;paper-access-ledger.tsv |

## 核心证据路径

- `/mnt/f/spatialecotyper_reproduction/archive/manifests/paper-figures.tsv`
- `/mnt/f/spatialecotyper_reproduction/archive/manifests/paper-panels.tsv`
- `/mnt/f/spatialecotyper_reproduction/results/reproducibility/paper-container-summary.tsv`
- `/mnt/f/spatialecotyper_reproduction/results/reproducibility/paper-dataset-readiness.tsv`
- `/mnt/f/spatialecotyper_reproduction/results/reproducibility/paper-panel-audit.tsv`
- `/mnt/f/spatialecotyper_reproduction/results/reproducibility/official-material-update-report.tsv`
- `/mnt/f/spatialecotyper_reproduction/results/reproducibility/access-request-evidence.tsv`
- `/mnt/f/spatialecotyper_reproduction/results/reproducibility/final-audit.txt`

## 状态解释

- `METHOD_ONLY`：官方方法或API可核验，但论文级输入变换、参数、派生权重或图板生成链不完整。
- `BLOCKED_CODE`：关键实现、模型检查点或权重未在官方公开材料中提供。
- `STRICT_PASS`：要求完整公开输入、官方代码、版本/参数/随机性和目标输出均本地验证通过；当前为0。
