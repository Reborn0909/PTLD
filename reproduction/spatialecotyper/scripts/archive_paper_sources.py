#!/usr/bin/env python3
"""Archive immutable paper sources with resumable downloads and SHA-256 checks."""

import argparse
import csv
import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def request(url: str, method: str = "GET", start: int = 0):
    headers = {"User-Agent": "Mozilla/5.0 SpatialEcoTyper-reproduction/1.0"}
    if start:
        headers["Range"] = f"bytes={start}-"
    return urlopen(Request(url, headers=headers, method=method), timeout=120)


def download(row: dict, archive: Path) -> dict:
    target = archive / row["filename"]
    part = target.with_name(target.name + ".part")
    expected_size = int(row["expected_bytes"])
    expected_hash = row["sha256"]
    if target.is_file() and target.stat().st_size == expected_size and sha256(target) == expected_hash:
        status = "VERIFIED_EXISTING"
    elif part.is_file() and part.stat().st_size == expected_size and sha256(part) == expected_hash:
        os.replace(part, target)
        status = "FINALIZED_VERIFIED_PART"
    else:
        start = part.stat().st_size if part.exists() else 0
        response = request(row["url"], start=start)
        append = start > 0 and getattr(response, "status", None) == 206
        with part.open("ab" if append else "wb") as handle:
            for chunk in iter(lambda: response.read(1024 * 1024), b""):
                handle.write(chunk)
        if part.stat().st_size != expected_size:
            raise RuntimeError(f"size mismatch for {part}: {part.stat().st_size} != {expected_size}")
        actual_hash = sha256(part)
        if actual_hash != expected_hash:
            raise RuntimeError(f"SHA-256 mismatch for {part}: {actual_hash} != {expected_hash}")
        os.replace(part, target)
        status = "DOWNLOADED_VERIFIED"

    etag = ""
    last_modified = ""
    if status == "DOWNLOADED_VERIFIED":
        try:
            head = request(row["url"], method="HEAD")
            etag = head.headers.get("ETag", "")
            last_modified = head.headers.get("Last-Modified", "")
        except HTTPError:
            pass
    return {
        **row,
        "actual_bytes": target.stat().st_size,
        "actual_sha256": sha256(target),
        "etag": etag,
        "last_modified": last_modified,
        "archived_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="/mnt/f/spatialecotyper_reproduction")
    parser.add_argument(
        "--config",
        default=str(Path(__file__).resolve().parents[1] / "config/paper-source-lock.tsv"),
    )
    args = parser.parse_args()
    root = Path(args.root)
    archive = root / "archive/paper"
    manifest_path = root / "archive/manifests/paper-files.tsv"
    archive.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with Path(args.config).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    results = [download(row, archive) for row in rows]
    with manifest_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=results[0].keys(), delimiter="\t")
        writer.writeheader()
        writer.writerows(results)
    for result in results:
        print(f"{result['status']}\t{result['filename']}\t{result['actual_sha256']}")


if __name__ == "__main__":
    main()
