#!/usr/bin/env python3
"""Audit paper dataset/sample availability against resolved and verified files."""

import argparse
import csv
from collections import Counter
from pathlib import Path


FIELDS = [
    "source_record_id", "sheet", "sample_id", "platform", "cohort", "included",
    "expected_samples", "download_source_record_id", "access_status", "resolved_files",
    "verified_files", "skipped_files", "availability", "reason",
]


def read_tsv(path: Path, required: bool = True) -> list:
    if not path.is_file():
        if required:
            raise FileNotFoundError(path)
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def index_rows(rows: list, key: str) -> dict:
    result = {}
    for row in rows:
        result.setdefault(row.get(key, ""), []).append(row)
    return result


def access_availability(access_status: str) -> str:
    if access_status.startswith("CONTROLLED") or access_status == "REGISTRATION_REQUIRED":
        return "BLOCKED_ACCESS"
    if access_status == "NOT_PUBLIC":
        return "BLOCKED_NOT_PUBLIC"
    return ""


def build_sample_audit(samples: list, downloads: list, verified: list, skipped: list,
                       ledger: list, tenx_rows: list) -> list:
    downloads_by_source = index_rows(downloads, "source_record_id")
    verified_by_source = index_rows(verified, "source_record_id")
    skipped_by_source = index_rows(skipped, "source_record_id")
    ledger_by_source = {row.get("source_record_id", ""): row for row in ledger}
    tenx_by_sample = {row.get("paper_sample_id", ""): row for row in tenx_rows}

    platform_sources = {}
    for row in samples:
        if row.get("sheet") == "Table S1" and row.get("platform"):
            normalized = row["platform"].replace("10x ", "")
            platform_sources.setdefault(normalized, row["source_record_id"])

    audit = []
    for sample in samples:
        source = sample.get("source_record_id", "")
        sample_id = sample.get("sample_id", "")
        tenx = tenx_by_sample.get(sample_id)
        if tenx:
            download_source = tenx["source_record_id"]
            prefix = sample_id + "__"
            resolved_rows = [row for row in downloads_by_source.get(download_source, [])
                             if row.get("file_name", "").startswith(prefix)]
            verified_rows = [row for row in verified_by_source.get(download_source, [])
                             if row.get("file_name", "").startswith(prefix)]
            skipped_rows = [row for row in skipped_by_source.get(download_source, [])
                            if row.get("file_name", "").startswith(prefix)]
        elif sample.get("sheet") == "Table S8" and sample.get("platform") == "MERSCOPE":
            download_source = platform_sources.get("MERSCOPE", source)
            resolved_rows = downloads_by_source.get(download_source, [])
            verified_rows = verified_by_source.get(download_source, [])
            skipped_rows = skipped_by_source.get(download_source, [])
        else:
            download_source = source
            resolved_rows = downloads_by_source.get(download_source, [])
            verified_rows = verified_by_source.get(download_source, [])
            skipped_rows = skipped_by_source.get(download_source, [])

        access = ledger_by_source.get(download_source, {})
        access_status = access.get("access_status", "UNRESOLVED")
        availability = access_availability(access_status)
        if not availability:
            if not resolved_rows:
                availability = "UNRESOLVED_PUBLIC"
            elif len(verified_rows) == len(resolved_rows):
                availability = "VERIFIED"
            elif verified_rows:
                availability = "PARTIAL"
            else:
                availability = "DOWNLOAD_PENDING"

        reported = sample.get("reported_sample_count", "")
        expected_samples = int(reported) if str(reported).isdigit() else 1
        cohort = sample.get("cohort", "")
        audit.append({
            "source_record_id": source,
            "sheet": sample.get("sheet", ""),
            "sample_id": sample_id,
            "platform": sample.get("platform", ""),
            "cohort": cohort,
            "included": "NO" if cohort.lower().startswith("excluded") else "YES",
            "expected_samples": expected_samples,
            "download_source_record_id": download_source,
            "access_status": access_status,
            "resolved_files": len(resolved_rows),
            "verified_files": len(verified_rows),
            "skipped_files": len(skipped_rows),
            "availability": availability,
            "reason": access.get("reason", "no access-ledger record"),
        })
    return audit


def summarize(rows: list) -> list:
    counts = Counter((row["sheet"], row["availability"]) for row in rows)
    return [
        {"sheet": sheet, "availability": availability, "records": count}
        for (sheet, availability), count in sorted(counts.items())
    ]


def write_tsv(path: Path, rows: list, fields: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="/mnt/f/spatialecotyper_reproduction")
    parser.add_argument(
        "--tenx-map",
        default=str(Path(__file__).resolve().parents[1] / "config/tenx-paper-samples.tsv"),
    )
    args = parser.parse_args()
    root = Path(args.root)
    manifests = root / "archive/manifests"
    samples = read_tsv(manifests / "paper-samples.tsv")
    downloads = read_tsv(manifests / "paper-downloads.tsv")
    verified = read_tsv(manifests / "paper-file-sha256.tsv", required=False)
    skipped = read_tsv(manifests / "paper-download-skipped.tsv", required=False)
    ledger = read_tsv(manifests / "paper-access-ledger.tsv")
    tenx = read_tsv(Path(args.tenx_map))
    rows = build_sample_audit(samples, downloads, verified, skipped, ledger, tenx)
    output = root / "results/reproducibility/paper-sample-availability.tsv"
    summary = root / "results/reproducibility/paper-sample-availability-summary.tsv"
    write_tsv(output, rows, FIELDS)
    write_tsv(summary, summarize(rows), ["sheet", "availability", "records"])
    print(f"paper sample validation: records={len(rows)} verified="
          f"{sum(row['availability'] == 'VERIFIED' for row in rows)} output={output}")


if __name__ == "__main__":
    main()
