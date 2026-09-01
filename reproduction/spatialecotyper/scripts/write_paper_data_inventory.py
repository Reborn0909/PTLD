#!/usr/bin/env python3
"""Write an evidence-backed inventory from the paper download audit tables."""

import argparse
import csv
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


PUBLIC_ACCESS = {"PUBLIC_API", "PUBLIC_DIRECT"}


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def integer(row: dict[str, str], key: str) -> int:
    value = row.get(key, "")
    return int(value) if value and value.isdigit() else 0


def human_bytes(value: int) -> str:
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    amount = float(value)
    for unit in units:
        if amount < 1024 or unit == units[-1]:
            return f"{amount:.2f} {unit}"
        amount /= 1024
    raise AssertionError("unreachable")


def markdown(root: Path) -> str:
    manifests = root / "archive/manifests"
    results = root / "results/reproducibility"
    downloads = read_tsv(manifests / "paper-downloads.tsv")
    capacity = read_tsv(results / "paper-download-capacity.tsv")
    files = read_tsv(manifests / "paper-file-sha256.tsv")
    validation = read_tsv(results / "paper-file-validation.tsv")

    source_gate = {row["source_record_id"]: row["source_gate"] for row in capacity}
    seen_urls: set[str] = set()
    actionable: list[dict[str, str]] = []
    for row in downloads:
        url = row.get("download_url", "")
        if source_gate.get(row["source_record_id"]) != "PASS":
            continue
        if integer(row, "size_bytes") <= 0 or not url or url in seen_urls:
            continue
        seen_urls.add(url)
        actionable.append(row)

    actionable_bytes = sum(integer(row, "size_bytes") for row in actionable)
    verified_bytes = sum(integer(row, "actual_bytes") for row in files)
    passed = sum(row.get("validation_status") == "PASS" for row in validation)
    failed = len(validation) - passed
    repositories: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for row in files:
        item = repositories[row.get("repository", "UNKNOWN")]
        item[0] += 1
        item[1] += integer(row, "actual_bytes")

    boundary_rows = [
        row for row in capacity
        if row.get("source_gate") != "PASS" or row.get("access_status") not in PUBLIC_ACCESS
    ]
    paused_bytes = sum(
        integer(row, "known_bytes") for row in capacity if row.get("source_gate") != "PASS"
    )

    lines = [
        "# Spatial EcoTyper / Nature 2026 原文数据清单",
        "",
        f"生成时间（UTC）：{datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "",
        "## 可公开获取数据",
        "",
        f"- 容量闸门通过并去重：{len(actionable)} 个文件，{actionable_bytes} 字节（{human_bytes(actionable_bytes)}）。",
        f"- 本地下载清单：{len(files)} 个文件，{verified_bytes} 字节（{human_bytes(verified_bytes)}）。",
        f"- 完整性验证：{passed}/{len(validation)} 通过；失败 {failed} 个。",
        "- 每个文件均保留原始 URL、accession、预期/实际字节数、SHA-256；上游提供 MD5 或 S3 multipart ETag 时另行校验。",
        "",
        "### 按官方仓库汇总",
        "",
        "| 仓库 | 文件数 | 字节数 | 易读容量 |",
        "|---|---:|---:|---:|",
    ]
    for repository, (count, size) in sorted(repositories.items()):
        lines.append(f"| {repository} | {count} | {size} | {human_bytes(size)} |")

    lines.extend([
        "",
        "## 无法直接归档的边界",
        "",
        f"- 因单一来源超过 100 GB 而暂停的已知数据：{paused_bytes} 字节（{human_bytes(paused_bytes)}）。",
        "- 注册、数据使用协议或受控人类数据不绕过权限，只保留可核验的 accession 与阻断原因。",
        "",
        "| 来源记录 | accession | 访问状态 | 容量闸门 | 原因 |",
        "|---|---|---|---|---|",
    ])
    for row in boundary_rows:
        reason = row.get("reason", "").replace("|", "\\|")
        lines.append(
            f"| {row.get('source_record_id', '')} | {row.get('accession', '')} | "
            f"{row.get('access_status', '')} | {row.get('source_gate', '')} | {reason} |"
        )

    run_status = root / "results/paper_reproduction/generated_visium_deconvolution/run-status.tsv"
    if run_status.exists():
        runs = read_tsv(run_status)
        reproduced = [row for row in runs if row.get("status") == "SPOT_LEVEL_REPRODUCED"]
        locations = sum(integer(row, "locations") for row in reproduced)
        patients = len({row.get("patient_id", "") for row in reproduced})
        lines.extend([
            "",
            "## 已执行的原文计算",
            "",
            f"- 研究生成空间队列：{len(reproduced)} 个空间样本、{patients} 位患者、{locations} 个过滤后 spot/bin。",
            "- 输入从原始 counts 按原文重算 log2(CPM+1)，仅调用固定版本官方 `SpatialEcoTyper::DeconvoluteSE()`。",
            "- 输出为 NonSE 与 SE1–SE9 spot/bin 分数；样本平面的加权汇总因缺失论文使用的 CytoSPACE 细胞数权重而标记为 `METHOD_GAP`。",
        ])

    lines.extend([
        "",
        "## 证据文件",
        "",
        f"- `{manifests / 'paper-downloads.tsv'}`",
        f"- `{manifests / 'paper-file-sha256.tsv'}`",
        f"- `{results / 'paper-download-capacity.tsv'}`",
        f"- `{results / 'paper-file-validation.tsv'}`",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="/mnt/f/spatialecotyper_reproduction")
    parser.add_argument(
        "--output", default="docs/reproduction/spatialecotyper-paper-data-inventory.md"
    )
    args = parser.parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_suffix(output.suffix + ".part")
    temp.write_text(markdown(Path(args.root)), encoding="utf-8")
    temp.replace(output)
    print(f"paper data inventory: PASS output={output}")


if __name__ == "__main__":
    main()
