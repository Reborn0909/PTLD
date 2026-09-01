#!/usr/bin/env python3
"""Create a non-sending evidence package for official material requests."""

import argparse
import csv
from pathlib import Path


FIELDS = (
    "request_type",
    "recipient",
    "requested_artifacts",
    "version_scope",
    "blocked_panel_ids",
    "official_evidence",
    "access_boundary",
    "status",
)


def read_tsv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _atomic_tsv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(path.name + ".part")
    with part.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    part.replace(path)


def _panel_ids(rows: list[dict], predicate) -> str:
    return ";".join(row["panel_id"] for row in rows if predicate(row))


def build_rows(root: Path) -> list[dict]:
    audit_path = root / "results/reproducibility/paper-panel-audit.tsv"
    snapshots_path = root / "archive/manifests/official-material-snapshots.tsv"
    ledger_path = root / "archive/manifests/paper-access-ledger.tsv"
    panels = read_tsv(audit_path)
    snapshots = read_tsv(snapshots_path)
    ledger = read_tsv(ledger_path)

    protected = [
        row for row in ledger
        if row["access_status"] in {"CONTROLLED_DUA", "REGISTRATION_REQUIRED"}
    ]
    if not protected or any(int(row["resolved_file_count"]) != 0 for row in protected):
        raise ValueError("controlled or registered inputs must remain unresolved")
    stanford = [row for row in snapshots if row["endpoint_id"] == "stanford_normalized_data"]
    if not stanford or stanford[-1]["access_status"] != "REGISTRATION_REQUIRED":
        raise ValueError("latest Stanford normalized-data observation is not registration-gated")

    all_panels = _panel_ids(panels, lambda row: True)
    method_panels = _panel_ids(panels, lambda row: row["status"] == "METHOD_ONLY")
    cytospace_panels = _panel_ids(
        panels, lambda row: "cytospace" in row["limitation"].lower()
    )
    liquid_panels = _panel_ids(panels, lambda row: row["status"] == "BLOCKED_CODE")
    if not all((all_panels, method_panels, cytospace_panels, liquid_panels)):
        raise ValueError("request evidence has an empty blocked-panel group")

    common_recipient = "Corresponding authors through the Nature article contact channel"
    rows = [
        {
            "request_type": "STANFORD_NORMALIZED_DATA",
            "recipient": "Stanford Spatial EcoTyper portal data-access channel",
            "requested_artifacts": (
                "preprocessed and normalized paper data under DOI 10.25936/pm3t-cn37; "
                "file manifest; sample-to-file map; preprocessing metadata"
            ),
            "version_scope": "paper release associated with Nature DOI 10.1038/s41586-026-10452-4",
            "blocked_panel_ids": method_panels,
            "official_evidence": (
                "https://doi.org/10.25936/pm3t-cn37;"
                f"{snapshots_path};{ledger_path}"
            ),
            "access_boundary": "Request portal access; do not bypass sign-in, DUA or cohort restrictions.",
            "status": "NOT_SENT",
        },
        {
            "request_type": "CYTOSPACE_WEIGHTS",
            "recipient": common_recipient,
            "requested_artifacts": (
                "paper-specific CytoSPACE spot-to-cell assignments or per-spot cell-count weights; "
                "sample identifiers; CytoSPACE version; parameters and random seeds"
            ),
            "version_scope": "exact objects used for the published 132-sample atlas and GSE320042 cohort",
            "blocked_panel_ids": cytospace_panels,
            "official_evidence": (
                "https://www.nature.com/articles/s41586-026-10452-4;"
                f"{audit_path}"
            ),
            "access_boundary": "Ask for shareable derived weights only; raw human data remain subject to DUA/IRB.",
            "status": "NOT_SENT",
        },
        {
            "request_type": "LIQUID_ECOTYPER_CODE_WEIGHTS",
            "recipient": common_recipient,
            "requested_artifacts": (
                "Liquid EcoTyper PyTorch 2.2.0 source; training and inference entrypoints; "
                "configuration; CpG preprocessing; checkpoints; model weights; seeds"
            ),
            "version_scope": "exact version used for the 2026 Nature paper",
            "blocked_panel_ids": liquid_panels,
            "official_evidence": (
                "https://github.com/digitalcytometry/spatialecotyper;"
                f"{root / 'results/reproducibility/official-material-update-report.tsv'};"
                f"{root / 'results/reproducibility/source-code-inventory.tsv'}"
            ),
            "access_boundary": "Request official code and weights; do not substitute a newly designed model.",
            "status": "NOT_SENT",
        },
        {
            "request_type": "FIGURE_SCRIPTS",
            "recipient": common_recipient,
            "requested_artifacts": (
                "figure-generation scripts for main, extended and supplementary figures; "
                "intermediate tables; package lockfiles; command order; random seeds"
            ),
            "version_scope": "scripts and intermediate values used for the final published figures",
            "blocked_panel_ids": all_panels,
            "official_evidence": (
                "https://www.nature.com/articles/s41586-026-10452-4;"
                f"{root / 'results/reproducibility/official-material-update-report.tsv'};"
                f"{audit_path}"
            ),
            "access_boundary": "Request non-identifying scripts and derived values; no automatic contact is made.",
            "status": "NOT_SENT",
        },
    ]
    return rows


def render_markdown(rows: list[dict]) -> str:
    lines = [
        "# Spatial EcoTyper 缺失材料与访问申请清单",
        "",
        "本清单只生成证据充分的申请内容，**不会自动发送**。This package is **not sent automatically**.",
        "",
        "固定论文代码提交：`48c2c846781d3a312771021c1a2ef5fc383700c5`。任何新收到的材料都应单独归档、计算 SHA-256，并在改变复现状态前完成本地验证。",
        "",
    ]
    for index, row in enumerate(rows, 1):
        panel_count = len(row["blocked_panel_ids"].split(";"))
        lines.extend(
            [
                f"## {index}. {row['request_type']}",
                "",
                f"- 建议渠道：{row['recipient']}",
                f"- 请求材料：{row['requested_artifacts']}",
                f"- 版本范围：{row['version_scope']}",
                f"- 关联图板：{panel_count} 个；完整 ID 见 `access-request-evidence.tsv`。",
                f"- 官方证据：{row['official_evidence']}",
                f"- 边界：{row['access_boundary']}",
                f"- 当前状态：`{row['status']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## 收到材料后的验证顺序",
            "",
            "1. 保存原始下载文件、来源 URL、访问日期、许可条款和 SHA-256。",
            "2. 检查样本映射、软件版本、参数、随机种子及权重是否齐全。",
            "3. 在独立 `work/` 目录调用官方算法，不修改 Spatial EcoTyper。",
            "4. 只有目标图板输出与论文值可核验一致时，才考虑升级复现状态。",
            "",
        ]
    )
    return "\n".join(lines)


def write_request_evidence(root: Path, output: Path, evidence: Path | None = None) -> list[dict]:
    rows = build_rows(root)
    evidence = evidence or root / "results/reproducibility/access-request-evidence.tsv"
    _atomic_tsv(evidence, rows)
    output.parent.mkdir(parents=True, exist_ok=True)
    part = output.with_name(output.name + ".part")
    part.write_text(render_markdown(rows), encoding="utf-8")
    part.replace(output)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="/mnt/f/spatialecotyper_reproduction")
    parser.add_argument(
        "--output", default="docs/reproduction/spatialecotyper-access-request-checklist.md"
    )
    parser.add_argument("--evidence")
    args = parser.parse_args()
    root = Path(args.root)
    rows = write_request_evidence(
        root, Path(args.output), Path(args.evidence) if args.evidence else None
    )
    print(f"access request evidence: PASS request_types={len(rows)} sent=0")


if __name__ == "__main__":
    main()
