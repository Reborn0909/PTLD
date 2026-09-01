#!/usr/bin/env python3
"""Classify canonical paper datasets by locally auditable computation readiness."""

import argparse
from collections import Counter, defaultdict
import csv
from pathlib import Path


ALLOWED_CLASSES = {
    "READY_OFFICIAL_PROCESSED",
    "READY_RAW_ONLY",
    "PARTIAL_FILES",
    "PAUSED_CAPACITY",
    "BLOCKED_ACCESS",
    "BLOCKED_NOT_PUBLIC",
    "METHOD_GAP",
}
OUTPUT_FIELDS = (
    "source_record_id",
    "sheet",
    "section",
    "dataset_name",
    "modality",
    "platform",
    "accession",
    "resolved_source_record_id",
    "access_status",
    "availability",
    "verified_container_count",
    "expression_status",
    "metadata_status",
    "spatial_status",
    "official_preprocessing_status",
    "readiness_class",
    "blocking_evidence",
    "evidence_paths",
)


def _is_spatial(record: dict) -> bool:
    text = " ".join(
        (record.get("section", ""), record.get("modality", ""), record.get("platform", ""))
    ).lower()
    return "spatial" in text or "visium" in text or "merscope" in text or "xenium" in text


def classify_readiness(
    record: dict,
    availability: dict | None,
    access: dict | None,
    roles: set[str],
) -> dict:
    access_status = (access or {}).get("access_status", "")
    availability_status = (availability or {}).get("availability", "")
    evidence = (
        (availability or {}).get("reason", "")
        or (access or {}).get("reason", "")
        or record.get("data_url", "")
    )
    expression_status = "AVAILABLE" if "expression" in roles else "MISSING"
    metadata_status = "AVAILABLE" if "metadata" in roles else "MISSING_OR_EMBEDDED"
    spatial = _is_spatial(record)
    spatial_status = (
        "AVAILABLE" if "coordinate" in roles else "MISSING"
    ) if spatial else "NOT_APPLICABLE"
    generated = record.get("section") == "generated_in_this_work"

    if access_status in {"CONTROLLED_DUA", "REGISTRATION_REQUIRED"}:
        readiness = "BLOCKED_ACCESS"
        preprocessing = "ACCESS_BLOCKED"
        evidence = evidence or f"access status {access_status}"
    elif availability_status == "BLOCKED_ACCESS":
        readiness = "BLOCKED_ACCESS"
        preprocessing = "ACCESS_BLOCKED"
        evidence = evidence or "sample availability is access-blocked"
    elif access_status == "NOT_PUBLIC" or availability_status == "BLOCKED_NOT_PUBLIC":
        readiness = "BLOCKED_NOT_PUBLIC"
        preprocessing = "NOT_PUBLIC"
        evidence = evidence or "official source provides no public input"
    elif availability_status == "PAUSED_CAPACITY":
        readiness = "PAUSED_CAPACITY"
        preprocessing = "CAPACITY_GATED"
        evidence = evidence or "source exceeds the configured capacity gate"
    elif generated:
        if {"expression", "coordinate", "metadata"}.issubset(roles):
            readiness = "READY_OFFICIAL_PROCESSED"
            preprocessing = "PAPER_GENERATED_OBJECTS_VERIFIED"
            evidence = ""
        else:
            readiness = "METHOD_GAP"
            preprocessing = "PAPER_GENERATED_OBJECTS_INCOMPLETE"
            missing = sorted({"expression", "coordinate", "metadata"} - roles)
            evidence = "generated GSE320042 objects missing roles: " + ",".join(missing)
    elif availability_status == "VERIFIED":
        if "expression" in roles:
            readiness = "READY_RAW_ONLY"
            preprocessing = "PAPER_ATLAS_PREPROCESSING_NOT_PACKAGED"
            evidence = (
                "verified expression is available, but the paper-scale atlas preprocessing "
                "and exact integration workflow are not packaged"
            )
        else:
            readiness = "PARTIAL_FILES"
            preprocessing = "EXPRESSION_NOT_IDENTIFIED"
            evidence = evidence or "verified files contain no indexed expression role"
    elif availability_status in {"UNRESOLVED_PUBLIC", "PARTIAL", "DOWNLOAD_PENDING"}:
        readiness = "PARTIAL_FILES"
        preprocessing = "PUBLIC_FILES_INCOMPLETE"
        evidence = evidence or f"sample availability is {availability_status}"
    else:
        readiness = "METHOD_GAP"
        preprocessing = "NO_CANONICAL_AVAILABILITY_MAPPING"
        evidence = evidence or "no canonical availability record links this dataset to inputs"

    return {
        "expression_status": expression_status,
        "metadata_status": metadata_status,
        "spatial_status": spatial_status,
        "official_preprocessing_status": preprocessing,
        "readiness_class": readiness,
        "blocking_evidence": evidence,
        "access_status": access_status,
        "availability": availability_status,
    }


def _read_tsv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _parse_roles(value: str) -> set[str]:
    return {item.split(":", 1)[0] for item in value.split(";") if item}


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


def build_readiness(root: Path, output: Path | None = None) -> list[dict]:
    manifests = root / "archive/manifests"
    reproducibility = root / "results/reproducibility"
    datasets = _read_tsv(manifests / "paper-datasets.tsv")
    access_rows = _read_tsv(manifests / "paper-access-ledger.tsv")
    download_rows = _read_tsv(manifests / "paper-downloads.tsv")
    file_rows = _read_tsv(manifests / "paper-file-sha256.tsv")
    availability_rows = _read_tsv(reproducibility / "paper-sample-availability.tsv")
    container_rows = _read_tsv(reproducibility / "paper-container-summary.tsv")

    if len(datasets) != len({row["source_record_id"] for row in datasets}):
        raise ValueError("paper datasets contain duplicate source_record_id values")
    access_by_id = {row["source_record_id"]: row for row in access_rows}
    availability_by_id = {row["source_record_id"]: row for row in availability_rows}
    roles_by_id = defaultdict(set)
    paths_by_id = defaultdict(set)
    roles_by_path = defaultdict(set)
    for row in container_rows:
        if row["inspection_status"] != "PASS":
            raise ValueError(f"container inspection failed: {row['local_path']}")
        path = row["local_path"]
        parsed_roles = _parse_roles(row["content_roles"])
        roles_by_path[path].update(parsed_roles)
        roles_by_id[row["source_record_id"]].update(parsed_roles)
        paths_by_id[row["source_record_id"]].add(path)
    path_by_url = {row["download_url"]: row["local_path"] for row in file_rows}
    for row in download_rows:
        path = path_by_url.get(row["download_url"])
        if not path or path not in roles_by_path:
            continue
        source_id = row["source_record_id"]
        roles_by_id[source_id].update(roles_by_path[path])
        paths_by_id[source_id].add(path)

    rows = []
    for record in datasets:
        source_id = record["source_record_id"]
        availability = availability_by_id.get(source_id)
        availability_source_id = (availability or {}).get("download_source_record_id", "")
        resolved_source_id = source_id if roles_by_id.get(source_id) else availability_source_id or source_id
        roles = roles_by_id.get(resolved_source_id, set())
        classified = classify_readiness(
            record, availability, access_by_id.get(source_id), roles
        )
        row = {
            **{field: record.get(field, "") for field in OUTPUT_FIELDS},
            **classified,
            "resolved_source_record_id": resolved_source_id,
            "verified_container_count": len(paths_by_id.get(resolved_source_id, set())),
            "evidence_paths": ";".join(
                (
                    str(manifests / "paper-datasets.tsv"),
                    str(manifests / "paper-downloads.tsv"),
                    str(manifests / "paper-file-sha256.tsv"),
                    str(reproducibility / "paper-sample-availability.tsv"),
                    str(reproducibility / "paper-container-summary.tsv"),
                )
            ),
        }
        if row["readiness_class"] not in ALLOWED_CLASSES:
            raise ValueError(f"invalid readiness class: {row['readiness_class']}")
        rows.append(row)

    output = output or reproducibility / "paper-dataset-readiness.tsv"
    _write_tsv(output, rows)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="/mnt/f/spatialecotyper_reproduction")
    parser.add_argument("--output")
    args = parser.parse_args()
    root = Path(args.root)
    output = Path(args.output) if args.output else None
    rows = build_readiness(root, output)
    counts = Counter(row["readiness_class"] for row in rows)
    print(
        "paper dataset readiness: PASS "
        f"datasets={len(rows)} classes="
        + ";".join(f"{key}:{counts[key]}" for key in sorted(counts))
    )


if __name__ == "__main__":
    main()
