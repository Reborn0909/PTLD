#!/usr/bin/env python3
"""Map every paper panel to conservative, auditable reproduction evidence."""

import argparse
from collections import Counter
import csv
from pathlib import Path


ALLOWED_STATUSES = {
    "STRICT_PASS",
    "OFFICIAL_API_PASS",
    "TUTORIAL_REPRODUCED",
    "METHOD_ONLY",
    "METHOD_GAP",
    "BLOCKED_ACCESS",
    "BLOCKED_CODE",
}
OUTPUT_FIELDS = (
    "figure_id",
    "panel_id",
    "panel_label",
    "panel_text",
    "caption_sha256",
    "input_records",
    "official_entrypoint",
    "expected_output",
    "observed_output",
    "status",
    "limitation",
    "evidence_basis",
)


def _read_tsv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _write_tsv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(path.name + ".part")
    with part.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=OUTPUT_FIELDS, delimiter="\t", extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(rows)
    part.replace(path)


def _output_paths(value: str) -> list[Path]:
    return [Path(item.strip()) for item in value.split(";") if item.strip()]


def validate_audit_row(row: dict) -> None:
    panel_id = row.get("panel_id", "")
    status = row.get("status", "")
    if not panel_id:
        raise ValueError("panel audit row has no panel_id")
    if status not in ALLOWED_STATUSES:
        raise ValueError(f"invalid panel audit status for {panel_id}: {status}")
    if status in {"STRICT_PASS", "OFFICIAL_API_PASS"}:
        if not row.get("official_entrypoint", "") or not row.get("observed_output", ""):
            raise ValueError(
                f"{status} requires an official entrypoint and observed output: {panel_id}"
            )
        missing = [str(path) for path in _output_paths(row["observed_output"]) if not path.exists()]
        if missing:
            raise ValueError(f"{status} output is missing for {panel_id}: {';'.join(missing)}")
    for field in ("expected_output", "limitation"):
        if not row.get(field, ""):
            raise ValueError(f"{panel_id} has no {field}")


def _load_rules(config: Path) -> tuple[dict[str, dict], dict[str, dict]]:
    exact: dict[str, dict] = {}
    figures: dict[str, dict] = {}
    for row in _read_tsv(config):
        selector = row.get("selector", "")
        if not selector:
            raise ValueError("panel audit config contains an empty selector")
        if selector.endswith(":*"):
            figure_id = selector[:-2]
            if figure_id in figures:
                raise ValueError(f"duplicate figure selector: {selector}")
            figures[figure_id] = row
        else:
            if selector in exact:
                raise ValueError(f"duplicate panel selector: {selector}")
            exact[selector] = row
    return exact, figures


def build_panel_audit(root: Path, config: Path, output: Path | None = None) -> list[dict]:
    panels_path = root / "archive/manifests/paper-panels.tsv"
    panels = _read_tsv(panels_path)
    if len(panels) != len({row["panel_id"] for row in panels}):
        raise ValueError("paper panel manifest contains duplicate panel_id values")

    exact, figures = _load_rules(config)
    rows = []
    for panel in panels:
        rule = exact.get(panel["panel_id"]) or figures.get(panel["figure_id"])
        if rule is None:
            raise ValueError(f"no reproduction rule covers {panel['panel_id']}")
        row = {
            **panel,
            **{field: rule.get(field, "") for field in OUTPUT_FIELDS},
            "figure_id": panel["figure_id"],
            "panel_id": panel["panel_id"],
            "panel_label": panel["panel_label"],
            "panel_text": panel["panel_text"],
            "caption_sha256": panel["caption_sha256"],
        }
        validate_audit_row(row)
        rows.append(row)

    unused_exact = sorted(set(exact) - {row["panel_id"] for row in panels})
    unused_figures = sorted(set(figures) - {row["figure_id"] for row in panels})
    if unused_exact or unused_figures:
        raise ValueError(
            "unused reproduction selectors: " + ",".join(unused_exact + unused_figures)
        )

    output = output or root / "results/reproducibility/paper-panel-audit.tsv"
    _write_tsv(output, rows)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="/mnt/f/spatialecotyper_reproduction")
    parser.add_argument(
        "--config",
        default=str(Path(__file__).resolve().parents[1] / "config/paper-panel-reproduction.tsv"),
    )
    parser.add_argument("--output")
    args = parser.parse_args()
    rows = build_panel_audit(
        Path(args.root),
        Path(args.config),
        Path(args.output) if args.output else None,
    )
    counts = Counter(row["status"] for row in rows)
    summary = " ".join(f"{key}={counts[key]}" for key in sorted(counts))
    print(f"paper panel audit: PASS panels={len(rows)} {summary}")


if __name__ == "__main__":
    main()
