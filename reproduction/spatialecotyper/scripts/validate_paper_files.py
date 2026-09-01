#!/usr/bin/env python3
"""Verify archived paper files against local SHA and upstream checksums."""

import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path
import re
import tarfile
import zipfile


def digest_file(path: Path, algorithm: str, chunk_size: int = 8 * 1024 ** 2) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def s3_multipart_etag(path: Path, chunk_size: int = 8 * 1024 ** 2) -> str:
    digests = []
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digests.append(hashlib.md5(chunk).digest())
    if not digests:
        digests.append(hashlib.md5(b"").digest())
    return hashlib.md5(b"".join(digests)).hexdigest() + f"-{len(digests)}"


def validate_format(path: Path) -> str:
    name = path.name.lower()
    if name.endswith((".tar.gz", ".tgz")):
        with tarfile.open(path, mode="r|gz") as archive:
            for _ in archive:
                pass
        return "tar.gz"
    if name.endswith(".tar"):
        with tarfile.open(path, mode="r|") as archive:
            for _ in archive:
                pass
        return "tar"
    if name.endswith(".gz"):
        with gzip.open(path, "rb") as handle:
            while handle.read(8 * 1024 ** 2):
                pass
        return "gzip"
    if name.endswith(".zip"):
        with zipfile.ZipFile(path) as archive:
            bad = archive.testzip()
            if bad:
                raise ValueError(f"corrupt zip member: {bad}")
        return "zip"
    if name.endswith((".json", ".xenium")):
        with path.open(encoding="utf-8") as handle:
            json.load(handle)
        return "json"
    if name.endswith((".h5", ".h5ad")):
        import h5py
        with h5py.File(path, "r") as handle:
            handle.visit(lambda _: None)
        return "hdf5"
    if name.endswith(".pdf"):
        with path.open("rb") as handle:
            if handle.read(5) != b"%PDF-":
                raise ValueError("missing PDF signature")
        return "pdf"
    return "manifest_only"


def validate_file(row: dict) -> dict:
    path = Path(row["local_path"])
    result = dict(row)
    result.update(
        observed_bytes="", observed_sha256="", observed_upstream_checksum="",
        format_check="", validation_status="FAIL", validation_error="",
    )
    try:
        if not path.is_file():
            raise FileNotFoundError(path)
        observed_bytes = path.stat().st_size
        expected_bytes = int(row.get("expected_bytes", row.get("actual_bytes", 0)) or 0)
        if expected_bytes and observed_bytes != expected_bytes:
            raise ValueError(f"size mismatch expected={expected_bytes} actual={observed_bytes}")
        observed_sha = digest_file(path, "sha256")
        if row.get("sha256") and observed_sha != row["sha256"].lower():
            raise ValueError("SHA-256 differs from download manifest")
        checksum = row.get("expected_checksum", "").lower()
        checksum_type = row.get("checksum_type", "")
        observed_upstream = ""
        if checksum_type == "s3_multipart_etag_8m" or re.fullmatch(r"[0-9a-f]{32}-\d+", checksum):
            observed_upstream = s3_multipart_etag(path)
        elif checksum_type == "md5" or re.fullmatch(r"[0-9a-f]{32}", checksum):
            observed_upstream = digest_file(path, "md5")
        if checksum and observed_upstream != checksum:
            raise ValueError(
                f"upstream checksum mismatch expected={checksum} actual={observed_upstream}"
            )
        result.update(
            observed_bytes=observed_bytes, observed_sha256=observed_sha,
            observed_upstream_checksum=observed_upstream,
            format_check=validate_format(path), validation_status="PASS",
        )
    except Exception as error:
        result["validation_error"] = f"{type(error).__name__}: {error}"
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="/mnt/f/spatialecotyper_reproduction")
    args = parser.parse_args()
    root = Path(args.root)
    manifest = root / "archive/manifests/paper-file-sha256.tsv"
    with manifest.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    results = [validate_file(row) for row in rows]
    output = root / "results/reproducibility/paper-file-validation.tsv"
    fields = list(results[0]) if results else []
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)
    failed = [row for row in results if row["validation_status"] != "PASS"]
    if failed:
        raise SystemExit(f"paper file validation: FAIL files={len(failed)} output={output}")
    print(f"paper file validation: PASS files={len(results)} output={output}")


if __name__ == "__main__":
    main()
