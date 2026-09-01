# Spatial EcoTyper 官方材料复现运行手册

本手册对应官方 SpatialEcoTyper 1.0.2、固定提交
`48c2c846781d3a312771021c1a2ef5fc383700c5`。官方源码只读使用，运行时输入
适配文件写入 `work`，结果写入 `results`。数据根目录固定为
`/mnt/f/spatialecotyper_reproduction`。

## 目录边界

| 层 | 用途 | 可否重建 |
| --- | --- | --- |
| `raw` | 原始教程文件和 GSE320042 tar | 不应删除 |
| `archive` | SHA、清单、环境锁和官方源码 bundle | 不应删除 |
| `work` | 教程运行时 Rmd 和中间文件 | 可重建 |
| `cache` | 下载、micromamba、renv 缓存 | 可重建 |
| `results` | HTML、日志、状态表、审计报告 | 可由原始材料重算 |

## 首次建立和完整运行

在 WSL Ubuntu 中进入本工作树，然后执行：

```bash
cd /mnt/c/Users/Microsoft/Documents/EBV开题/.worktrees/spatialecotyper-reproduction
bash reproduction/spatialecotyper/scripts/bootstrap_wsl.sh

MAMBA_ROOT_PREFIX=/home/reborn/.local/share/micromamba-spatialecotyper \
  /home/reborn/.local/bin/micromamba run \
  -p /home/reborn/.local/share/micromamba-spatialecotyper/envs/spatialecotyper-1.0.2 \
  Rscript reproduction/spatialecotyper/scripts/extract_official_manifest.R \
  /mnt/c/Users/Microsoft/Documents/EBV开题/external/spatialecotyper-official \
  /mnt/f/spatialecotyper_reproduction/archive/manifests

bash reproduction/spatialecotyper/scripts/download_manifest.sh
bash reproduction/spatialecotyper/tests/test_tutorial_archive.sh

MAMBA_ROOT_PREFIX=/home/reborn/.local/share/micromamba-spatialecotyper \
  /home/reborn/.local/bin/micromamba run \
  -p /home/reborn/.local/share/micromamba-spatialecotyper/envs/spatialecotyper-1.0.2 \
  Rscript reproduction/spatialecotyper/scripts/run_tutorials.R

bash reproduction/spatialecotyper/scripts/download_gse320042.sh

python3 reproduction/spatialecotyper/scripts/archive_paper_sources.py \
  --root /mnt/f/spatialecotyper_reproduction
python3 reproduction/spatialecotyper/scripts/extract_paper_data_manifest.py \
  --xlsx /mnt/f/spatialecotyper_reproduction/archive/paper/41586_2026_10452_MOESM3_ESM.xlsx \
  --output /mnt/f/spatialecotyper_reproduction/archive/manifests
python3 reproduction/spatialecotyper/scripts/resolve_paper_downloads.py \
  --datasets /mnt/f/spatialecotyper_reproduction/archive/manifests/paper-datasets.tsv \
  --root /mnt/f/spatialecotyper_reproduction
bash reproduction/spatialecotyper/scripts/download_paper_data.sh \
  --root /mnt/f/spatialecotyper_reproduction \
  --phase all-actionable --jobs 4 --connections 16
python3 reproduction/spatialecotyper/scripts/validate_paper_files.py \
  --root /mnt/f/spatialecotyper_reproduction
python3 reproduction/spatialecotyper/scripts/validate_paper_samples.py \
  --root /mnt/f/spatialecotyper_reproduction

MAMBA_ROOT_PREFIX=/home/reborn/.local/share/micromamba-spatialecotyper \
  /home/reborn/.local/bin/micromamba run \
  -p /home/reborn/.local/share/micromamba-spatialecotyper/envs/spatialecotyper-1.0.2 \
  Rscript reproduction/spatialecotyper/scripts/prepare_paper_inputs.R

MAMBA_ROOT_PREFIX=/home/reborn/.local/share/micromamba-spatialecotyper \
  /home/reborn/.local/bin/micromamba run \
  -p /home/reborn/.local/share/micromamba-spatialecotyper/envs/spatialecotyper-1.0.2 \
  Rscript reproduction/spatialecotyper/scripts/audit_gse320042_objects.R

MAMBA_ROOT_PREFIX=/home/reborn/.local/share/micromamba-spatialecotyper \
  /home/reborn/.local/bin/micromamba run \
  -p /home/reborn/.local/share/micromamba-spatialecotyper/envs/spatialecotyper-1.0.2 \
  Rscript reproduction/spatialecotyper/scripts/run_paper_reproduction.R

MAMBA_ROOT_PREFIX=/home/reborn/.local/share/micromamba-spatialecotyper \
  /home/reborn/.local/bin/micromamba run \
  -p /home/reborn/.local/share/micromamba-spatialecotyper/envs/spatialecotyper-1.0.2 \
  Rscript reproduction/spatialecotyper/scripts/compare_paper_outputs.R

MAMBA_ROOT_PREFIX=/home/reborn/.local/share/micromamba-spatialecotyper \
  /home/reborn/.local/bin/micromamba run \
  -p /home/reborn/.local/share/micromamba-spatialecotyper/envs/spatialecotyper-1.0.2 \
  Rscript reproduction/spatialecotyper/scripts/audit_reproducibility.R

bash reproduction/spatialecotyper/scripts/final_audit.sh
```

论文公开队列的下载范围由补充表和容量闸门共同决定。当前去重后为 69 个
可操作文件，61,207,712,053 字节；两个 ENA 原始测序来源合计约 1.94 TB，
因单来源超过 100 GB 闸门而暂停。注册、DUA 或受控数据不绕过权限。

下载脚本均使用 `.part` 临时文件，成功后才原子改名。首次下载中网络中断后，
重新执行同一命令即可断点续传。归档 SHA/成员基线一旦生成便不会静默覆盖；再次
执行下载命令只校验现有 raw，任何不一致都会失败。确需更新基线时必须人工另存带
时间戳的新版本并说明原因。GSE320042 脚本会在每次重试前重新读取已下载字节数。

## 教程重跑

直接重跑某个教程且不改变状态表：

```bash
MAMBA_ROOT_PREFIX=/home/reborn/.local/share/micromamba-spatialecotyper \
  /home/reborn/.local/bin/micromamba run \
  -p /home/reborn/.local/share/micromamba-spatialecotyper/envs/spatialecotyper-1.0.2 \
  Rscript reproduction/spatialecotyper/scripts/run_tutorials.R --render-one T04
```

`T01` 至 `T08` 的顺序由 `config/tutorial-order.tsv` 固定。完整重跑并重新生成
计时状态时，先把现有 `run-status.tsv` 移到 `archive/manifests` 留档，再执行不带
参数的 `run_tutorials.R`。不要删除 `raw/tutorial`。

```bash
data_root=/mnt/f/spatialecotyper_reproduction
stamp=$(date -u +%Y%m%dT%H%M%SZ)
mv "$data_root/results/tutorials/run-status.tsv" \
  "$data_root/archive/manifests/run-status.$stamp.tsv"

MAMBA_ROOT_PREFIX=/home/reborn/.local/share/micromamba-spatialecotyper \
  /home/reborn/.local/bin/micromamba run \
  -p /home/reborn/.local/share/micromamba-spatialecotyper/envs/spatialecotyper-1.0.2 \
  Rscript reproduction/spatialecotyper/scripts/run_tutorials.R
```

T02 的官方归档 RDS 缺少固定版本代码要求的 `Spot.X/Spot.Y`。严格材料尝试日志
保存在 `results/tutorials/T02/strict-material-attempt.log`；当前流程明确标记
`FAIL_INPUT_SCHEMA_WITH_OFFICIAL_UPSTREAM_FALLBACK`，并使用官方 T01 在本环境生成的
上游结果。它是教程级复现，不应表述为严格材料复现。

## 校验和日志定位

```bash
bash reproduction/spatialecotyper/tests/test_tutorial_archive.sh
bash reproduction/spatialecotyper/tests/test_gse320042_archive.sh
bash reproduction/spatialecotyper/scripts/final_audit.sh
```

教程状态总表在 `results/tutorials/run-status.tsv`，每个教程的运行日志在
`results/tutorials/T01` 至 `T08` 下。GEO 下载日志在
`results/logs/download_gse320042.log`。最终审计写入
`results/reproducibility/final-audit.txt`；审计失败时保留带 `.part` 后缀的报告，
不得把失败改写成 `SKIP`。

## 可恢复地清理缓存

以下操作只移动 `cache`，不会触碰 `raw` 或 `archive`。确认新环境可用后再由人工
决定是否删除留档目录。

```bash
data_root=/mnt/f/spatialecotyper_reproduction
stamp=$(date -u +%Y%m%dT%H%M%SZ)
retired="$data_root/work/cache-retired/$stamp"
mkdir -p "$data_root/work/cache-retired" "$data_root/cache"/{micromamba,renv,downloads}
mkdir "$retired"
for source_path in \
  "$data_root/cache/micromamba" \
  "$data_root/cache/renv" \
  "$data_root/cache/downloads/micromamba-linux-64.tar.bz2"; do
  if [[ -e "$source_path" ]]; then
    mv -- "$source_path" "$retired/"
  fi
done
mkdir -p "$data_root/cache"/{micromamba,renv,downloads}
```

保留 `cache/downloads/presto-7636b3d0465c468c35853f82f1717d3a64b3c8f6.tar.gz`；
它是固定环境的源包证据，并由最终审计校验。

## PTLD 输入和调用

PTLD 层只做输入验证、显式细胞类型映射和官方 API 调用，不过滤、不自动归一化、
不合并样本，也不修改 Spatial EcoTyper。表达矩阵为 genes × cells；元数据行名须
与细胞列名一致，并包含 `X`、`Y`、`CellType`、`SampleID`。每次运行复制
`ptld-run-config.example.tsv`，填写输入 SHA-256、归一化方法、坐标单位和参数。

完整示例和限制见 `reproduction/spatialecotyper/ptld/README.md`。映射后的目标标签
禁止包含句点，因为官方代码把句点作为内部名称分隔符。`SampleID` 和输出前缀必须
是去标识、文件名安全的单段字符。

## 复现状态解释

- `STRICT_REPRODUCED`：同一官方材料与固定环境可严格重算；当前为 0 项。
- `TUTORIAL_REPRODUCED`：官方八个教程已成功运行；共 8 项。
- `METHOD_ONLY`：方法和部分数据公开，但缺少论文级端到端脚本；共 8 项。
- `BLOCKED_NOT_PUBLIC`：缺少公开实现或权重，无法本地严格复现；共 3 项。

三项公开材料阻断是完整论文作图流水线、Liquid EcoTyper 的 PyTorch 训练，以及
cfDNA 本地推理。不得用自行搭建的替代代码将它们标记为严格复现。
