#!/usr/bin/env python3
"""Build a read-only member index for every validated paper data file."""

import argparse
from collections import Counter
import csv
import gzip
from pathlib import Path
import tarfile
import zipfile

import h5py


MEMBER_FIELDS = (
    "source_record_id",
    "local_path",
    "member_path",
    "member_bytes",
    "container_type",
    "content_role",
    "inspection_status",
    "inspection_error",
)
SUMMARY_FIELDS = (
    "source_record_id",
    "local_path",
    "container_type",
    "container_bytes",
    "member_count",
    "indexed_member_bytes",
    "content_roles",
    "inspection_status",
    "inspection_error",
)


def classify_content_role(member_path: str) -> str:
    name = member_path.lower().replace("\\", "/")
    base = name.rsplit("/", 1)[-1]
    logical_base = base[:-3] if base.endswith(".gz") else base
    if "barcode" in name:
        return "barcode"
    if any(token in name for token in ("tissue_position", "coordinate", "coords")):
        return "coordinate"
    if any(token in name for token in ("segment", "boundary", "polygon")):
        return "segmentation"
    if logical_base.endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff", ".svs")):
        return "image"
    if "model" in name or "weight" in name or "checkpoint" in name:
        return "model"
    if any(token in name for token in ("metadata", "meta.tsv", "meta.csv", "annotation", "clinical")):
        return "metadata"
    if (
        logical_base.startswith(("features.", "genes."))
        or "/features/" in name
        or "gene_names" in name
    ):
        return "feature"
    if any(
        token in name
        for token in (
            "matrix",
            "count",
            "expression",
            "expr",
            "_exp.",
            "indrop",
            "data/",
            "filtered.txt",
        )
    ) or logical_base.endswith(
        (".mtx", ".h5", ".h5ad", ".rds")
    ):
        return "expression"
    if re_search_spatial_expression(logical_base):
        return "expression"
    if "feature" in name:
        return "feature"
    return "other"


def re_search_spatial_expression(base: str) -> bool:
    stem = base.rsplit(".", 1)[0]
    return stem.endswith(("-st", "-st1", "-st2", "-st3", "_st", "_st1", "_st2", "_st3"))


def _member(path: Path, member_path: str, member_bytes, container_type: str) -> dict:
    return {
        "local_path": str(path),
        "member_path": member_path,
        "member_bytes": member_bytes,
        "container_type": container_type,
        "content_role": classify_content_role(member_path),
        "inspection_status": "PASS",
        "inspection_error": "",
    }


def inspect_container(path: Path):
    lower = path.name.lower()
    if lower.endswith((".tar.gz", ".tgz", ".tar")):
        container_type = "tar.gz" if lower.endswith((".tar.gz", ".tgz")) else "tar"
        with tarfile.open(path, mode="r|*") as archive:
            for info in archive:
                if info.isfile():
                    yield _member(path, info.name, info.size, container_type)
        return
    if lower.endswith(".zip"):
        with zipfile.ZipFile(path) as archive:
            for info in archive.infolist():
                if not info.is_dir():
                    yield _member(path, info.filename, info.file_size, "zip")
        return
    if lower.endswith((".h5", ".h5ad")):
        records = []
        with h5py.File(path, "r") as handle:
            def visitor(name, item):
                if isinstance(item, h5py.Dataset):
                    size = int(item.size * item.dtype.itemsize)
                    records.append(_member(path, name, size, "hdf5"))
            handle.visititems(visitor)
        yield from records
        return
    if lower.endswith(".gz"):
        with gzip.GzipFile(filename=path, mode="rb") as handle:
            handle.peek(1)
        yield _member(path, path.name[:-3], "", "gzip")
        return
    yield _member(path, path.name, path.stat().st_size, "plain")


def _read_tsv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _write_tsv(path: Path, fields, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(path.name + ".part")
    with part.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    part.replace(path)


def build_index(root: Path, expected_count: int = 74) -> tuple[list[dict], list[dict]]:
    manifest_path = root / "archive/manifests/paper-file-sha256.tsv"
    validation_path = root / "results/reproducibility/paper-file-validation.tsv"
    manifest = _read_tsv(manifest_path)
    validation = _read_tsv(validation_path)
    if len(manifest) != expected_count:
        raise ValueError(f"expected {expected_count} manifest rows, observed {len(manifest)}")
    validation_by_path = {row["local_path"]: row for row in validation}
    if len(validation_by_path) != len(validation):
        raise ValueError("duplicate local_path in paper file validation")

    all_members = []
    summaries = []
    for source in manifest:
        local_path = source["local_path"]
        validation_row = validation_by_path.get(local_path)
        if validation_row is None or validation_row.get("validation_status") != "PASS":
            raise ValueError(f"not validated PASS: {local_path}")
        path = Path(local_path)
        if not path.is_file():
            raise ValueError(f"missing validated file: {local_path}")
        try:
            members = list(inspect_container(path))
            if not members:
                raise ValueError("container has no indexable file or dataset members")
            for row in members:
                row["source_record_id"] = source["source_record_id"]
            roles = Counter(row["content_role"] for row in members)
            indexed_bytes = sum(
                int(row["member_bytes"]) for row in members if str(row["member_bytes"]).isdigit()
            )
            summary = {
                "source_record_id": source["source_record_id"],
                "local_path": local_path,
                "container_type": members[0]["container_type"],
                "container_bytes": path.stat().st_size,
                "member_count": len(members),
                "indexed_member_bytes": indexed_bytes,
                "content_roles": ";".join(f"{role}:{roles[role]}" for role in sorted(roles)),
                "inspection_status": "PASS",
                "inspection_error": "",
            }
            all_members.extend(members)
        except Exception as error:
            summary = {
                "source_record_id": source["source_record_id"],
                "local_path": local_path,
                "container_type": "unknown",
                "container_bytes": path.stat().st_size,
                "member_count": 0,
                "indexed_member_bytes": 0,
                "content_roles": "",
                "inspection_status": "FAIL",
                "inspection_error": f"{type(error).__name__}: {error}",
            }
        summaries.append(summary)

    output = root / "results/reproducibility"
    _write_tsv(output / "paper-archive-members.tsv", MEMBER_FIELDS, all_members)
    _write_tsv(output / "paper-container-summary.tsv", SUMMARY_FIELDS, summaries)
    return all_members, summaries


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="/mnt/f/spatialecotyper_reproduction")
    parser.add_argument("--expected-count", type=int, default=74)
    args = parser.parse_args()
    members, summaries = build_index(Path(args.root), args.expected_count)
    failed = [row for row in summaries if row["inspection_status"] != "PASS"]
    if failed:
        raise SystemExit(
            f"paper archive index: FAIL containers={len(summaries)} failed={len(failed)}"
        )
    print(f"paper archive index: PASS containers={len(summaries)} members={len(members)}")


if __name__ == "__main__":
    main()
