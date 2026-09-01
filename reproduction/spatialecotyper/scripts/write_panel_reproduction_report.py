#!/usr/bin/env python3
"""Generate the Chinese panel-level maximum-reproduction report."""

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
from pathlib import Path


def read_tsv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def clean(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def report(root: Path) -> str:
    reproducibility = root / "results/reproducibility"
    manifests = root / "archive/manifests"
    panels = read_tsv(reproducibility / "paper-panel-audit.tsv")
    figures = read_tsv(manifests / "paper-figures.tsv")
    readiness = read_tsv(reproducibility / "paper-dataset-readiness.tsv")
    updates = read_tsv(reproducibility / "official-material-update-report.tsv")
    requests = read_tsv(reproducibility / "access-request-evidence.tsv")
    execution = read_tsv(
        root / "results/paper_reproduction/ready_analyses/execution-summary.tsv"
    )
    status_counts = Counter(row["status"] for row in panels)
    readiness_counts = Counter(row["readiness_class"] for row in readiness)
    panels_by_figure = {}
    for row in panels:
        panels_by_figure.setdefault(row["figure_id"], []).append(row)

    lines = [
        "# Spatial EcoTyper / Nature 2026 逐图板复现审计",
        "",
        f"生成时间（UTC）：{datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "",
        "## 结论",
        "",
        f"- 论文图清单：{len(figures)} 张；显式图板：{len(panels)} 个，全部唯一覆盖。",
        f"- 图板状态：`METHOD_ONLY` {status_counts['METHOD_ONLY']} 个；`BLOCKED_CODE` {status_counts['BLOCKED_CODE']} 个；`STRICT_PASS` {status_counts['STRICT_PASS']} 个。",
        "- 目前没有论文图板满足严格原图复现：缺少论文级预处理、CytoSPACE派生权重、Liquid EcoTyper实现/检查点或最终作图脚本。",
        "- 这不否定已完成的官方API计算：GSE320042的17个空间样本已完成spot/bin级 `DeconvoluteSE`，但不能据此宣称论文图板严格复现。",
        f"- 新增执行门状态：`{execution[0]['status']}`，可执行图板 {execution[0]['eligible_rows']} 个。",
        "",
        "## 数据集计算就绪度",
        "",
        "| 就绪类别 | 数据集数 |",
        "|---|---:|",
    ]
    for status, count in sorted(readiness_counts.items()):
        lines.append(f"| {status} | {count} |")

    lines.extend(
        [
            "",
            "## 官方材料更新检查",
            "",
            "| 阻塞组件 | 候选文件 | 当前状态 | 最新官方提交 | 改变阻塞状态 |",
            "|---|---|---|---|---|",
        ]
    )
    for row in updates:
        lines.append(
            f"| {row['component']} | {row['candidate_found']} | {row['status']} | "
            f"`{row['latest_revision']}` | {row['changes_current_blocker']} |"
        )

    lines.extend(
        [
            "",
            "## 仍需申请的官方材料",
            "",
            "以下内容仅形成申请证据，均未自动发送。",
            "",
            "| 请求类型 | 关联图板数 | 当前状态 | 用户动作 |",
            "|---|---:|---|---|",
        ]
    )
    actions = {
        "STANFORD_NORMALIZED_DATA": "登录Stanford入口并按许可申请论文标准化数据。",
        "CYTOSPACE_WEIGHTS": "向通讯作者申请论文使用的spot-cell映射或每spot细胞数权重。",
        "LIQUID_ECOTYPER_CODE_WEIGHTS": "向通讯作者申请PyTorch源码、配置、预处理和检查点。",
        "FIGURE_SCRIPTS": "向通讯作者申请最终作图脚本、中间表和软件锁文件。",
    }
    for row in requests:
        count = len(row["blocked_panel_ids"].split(";"))
        lines.append(
            f"| {row['request_type']} | {count} | {row['status']} | "
            f"{actions[row['request_type']]} |"
        )

    lines.extend(["", "## 逐图逐板证据", ""])
    figure_titles = {row["figure_id"]: row["title"] for row in figures}
    for figure_id, figure_panels in panels_by_figure.items():
        lines.extend(
            [
                f"### {figure_id}：{clean(figure_titles.get(figure_id, ''))}",
                "",
                "| 图板 | 状态 | 输入记录 | 目标输出 | 限制 | 证据 |",
                "|---|---|---|---|---|---|",
            ]
        )
        for row in figure_panels:
            lines.append(
                f"| {row['panel_id']} | {row['status']} | {clean(row['input_records'])} | "
                f"{clean(row['expected_output'])} | {clean(row['limitation'])} | "
                f"{clean(row['evidence_basis'])} |"
            )
        lines.append("")

    lines.extend(
        [
            "## 核心证据路径",
            "",
            f"- `{manifests / 'paper-figures.tsv'}`",
            f"- `{manifests / 'paper-panels.tsv'}`",
            f"- `{reproducibility / 'paper-container-summary.tsv'}`",
            f"- `{reproducibility / 'paper-dataset-readiness.tsv'}`",
            f"- `{reproducibility / 'paper-panel-audit.tsv'}`",
            f"- `{reproducibility / 'official-material-update-report.tsv'}`",
            f"- `{reproducibility / 'access-request-evidence.tsv'}`",
            f"- `{reproducibility / 'final-audit.txt'}`",
            "",
            "## 状态解释",
            "",
            "- `METHOD_ONLY`：官方方法或API可核验，但论文级输入变换、参数、派生权重或图板生成链不完整。",
            "- `BLOCKED_CODE`：关键实现、模型检查点或权重未在官方公开材料中提供。",
            "- `STRICT_PASS`：要求完整公开输入、官方代码、版本/参数/随机性和目标输出均本地验证通过；当前为0。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="/mnt/f/spatialecotyper_reproduction")
    parser.add_argument(
        "--output", default="docs/reproduction/spatialecotyper-panel-level-reproduction.md"
    )
    args = parser.parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    part = output.with_name(output.name + ".part")
    part.write_text(report(Path(args.root)), encoding="utf-8")
    part.replace(output)
    print(f"panel-level report: PASS output={output}")


if __name__ == "__main__":
    main()
