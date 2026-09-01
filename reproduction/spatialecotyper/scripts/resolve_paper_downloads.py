#!/usr/bin/env python3
"""Resolve official paper dataset records to public files, access status and size gates."""

import argparse
import csv
import json
import re
import shutil
import time
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin, urlparse
from urllib.request import Request, urlopen


USER_AGENT = "SpatialEcoTyper-paper-reproduction/1.0"
DOWNLOAD_FIELDS = [
    "source_record_id", "accession", "repository", "file_name", "download_url",
    "size_bytes", "checksum_type", "checksum", "license", "access_status", "resolver_note",
]


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)


def http_bytes(url: str, method: str = "GET", headers=None, attempts: int = 5, timeout: int = 60) -> tuple:
    request_headers = {"User-Agent": USER_AGENT, **(headers or {})}
    last_error = None
    for attempt in range(attempts):
        try:
            response = urlopen(Request(url, headers=request_headers, method=method), timeout=timeout)
            return response.read(), response.headers, getattr(response, "status", 200), response.geturl()
        except (HTTPError, URLError, TimeoutError, ConnectionError) as error:
            last_error = error
            if isinstance(error, HTTPError) and error.code not in {429, 500, 502, 503, 504}:
                raise
            time.sleep(min(2 ** attempt, 8))
    raise last_error


def parse_apache_index(html: str, base_url: str) -> list:
    parser = LinkParser()
    parser.feed(html)
    files = []
    base = urlparse(base_url)
    for href in parser.links:
        resolved = urljoin(base_url, href)
        parsed = urlparse(resolved)
        name = href.rsplit("/", 1)[-1]
        if (not name or href.endswith("/") or name == "filelist.txt" or href.startswith("?")
                or parsed.netloc != base.netloc or not parsed.path.startswith(base.path)):
            continue
        files.append({"file_name": name, "download_url": resolved})
    return files


def parse_zenodo_record(payload: bytes) -> tuple:
    record = json.loads(payload.decode("utf-8"))
    metadata = record.get("metadata", {})
    license_value = metadata.get("license", {})
    if isinstance(license_value, dict):
        license_value = license_value.get("id", "")
    files = []
    for item in record.get("files", []):
        checksum_type, _, checksum = item.get("checksum", "").partition(":")
        files.append({
            "file_name": item.get("key", ""),
            "download_url": item.get("links", {}).get("self", ""),
            "size_bytes": int(item.get("size", 0)),
            "checksum_type": checksum_type,
            "checksum": checksum,
        })
    return files, {"license": license_value, "access_right": metadata.get("access_right", "")}


def parse_geo_filelist(payload: bytes) -> dict:
    text = payload.decode("utf-8-sig", "replace").splitlines()
    if not text:
        return {}
    rows = csv.DictReader(text, delimiter="\t")
    sizes = {}
    for row in rows:
        name = row.get("Name", "")
        size = row.get("Size", "")
        if name and str(size).isdigit():
            sizes[name] = int(size)
    return sizes


def parse_ena_report(payload: bytes) -> list:
    rows = csv.DictReader(payload.decode("utf-8-sig", "replace").splitlines(), delimiter="\t")
    files = []
    for row in rows:
        urls = (row.get("fastq_ftp") or "").split(";")
        sizes = (row.get("fastq_bytes") or "").split(";")
        checksums = (row.get("fastq_md5") or "").split(";")
        for index, path in enumerate(urls):
            if not path:
                continue
            url = path if path.startswith("http") else "https://" + path
            files.append({
                "file_name": path.rsplit("/", 1)[-1], "download_url": url,
                "size_bytes": int(sizes[index]) if index < len(sizes) and sizes[index].isdigit() else 0,
                "checksum_type": "md5", "checksum": checksums[index] if index < len(checksums) else "",
            })
    return files


def resolve_ena(accession: str) -> list:
    query = urlencode({
        "accession": accession, "result": "read_run",
        "fields": "run_accession,fastq_ftp,fastq_bytes,fastq_md5", "format": "tsv",
    })
    payload, _, _, _ = http_bytes(f"https://www.ebi.ac.uk/ena/portal/api/filereport?{query}")
    return parse_ena_report(payload)


def content_range_total(value: str) -> int:
    match = re.search(r"/(\d+)$", value or "")
    return int(match.group(1)) if match else 0


def classify_s3_etag(size_bytes: int, etag: str) -> tuple:
    checksum = (etag or "").strip().strip('"').lower()
    simple = re.fullmatch(r"[0-9a-f]{32}", checksum)
    if simple:
        return "md5", checksum
    multipart = re.fullmatch(r"[0-9a-f]{32}-(\d+)", checksum)
    if multipart:
        parts = int(multipart.group(1))
        if size_bytes > 0 and (size_bytes + 8 * 1024 ** 2 - 1) // (8 * 1024 ** 2) == parts:
            return "s3_multipart_etag_8m", checksum
        return "s3_multipart_etag", checksum
    return "", ""


def http_metadata(url: str, method: str = "HEAD", headers=None, attempts: int = 2, timeout: int = 20) -> tuple:
    request_headers = {"User-Agent": USER_AGENT, **(headers or {})}
    last_error = None
    for attempt in range(attempts):
        try:
            response = urlopen(Request(url, headers=request_headers, method=method), timeout=timeout)
            metadata = response.headers
            status = getattr(response, "status", 200)
            final_url = response.geturl()
            response.close()
            return metadata, status, final_url
        except (HTTPError, URLError, TimeoutError, ConnectionError) as error:
            last_error = error
            if isinstance(error, HTTPError) and error.code not in {429, 500, 502, 503, 504}:
                raise
            time.sleep(min(2 ** attempt, 4))
    raise last_error


def classify_record(record: dict) -> tuple:
    accession = record.get("accession", "").upper()
    url = record.get("data_url", "").lower()
    name = record.get("dataset_name", "").lower()
    if accession.startswith("HRA"):
        return "CONTROLLED_DUA", "GSA-Human accession requires approved human-data access"
    if "mendeley.com" in url:
        return "REGISTRATION_REQUIRED", "guest page exposes metadata but file API returned HTTP 401"
    if "humantumoratlas" in url or name == "htan":
        return "REGISTRATION_REQUIRED", "HTAN files require portal/Synapse authentication and terms"
    if "vizgen" in url or name == "vizgen":
        return "REGISTRATION_REQUIRED", "Vizgen showcase download is gated by a registration form"
    if "spatialecotyper.stanford.edu" in url:
        return "REGISTRATION_REQUIRED", "Stanford DOI download is shown only after sign in"
    if re.search(r"(?:GSE|GSM)\d+", accession):
        return "PUBLIC_API", "NCBI GEO public supplementary-file index"
    if "zenodo.org" in url:
        return "PUBLIC_API", "Zenodo public records API"
    if "github.com" in url:
        return "PUBLIC_API", "GitHub public repository API"
    if "spatialresearch.org" in url:
        return "PUBLIC_DIRECT", "public dataset landing page; direct links resolved from page"
    if "10xgenomics.com" in url:
        return "PUBLIC_API", "public 10x catalog link is generic; exact sample mapping required from Table S8"
    if accession.startswith(("CRA", "OMIX", "PRJEB")):
        return "PUBLIC_API", "public repository accession; processed-file mapping requires repository-specific metadata"
    if url.startswith("http"):
        return "PUBLIC_DIRECT", "public landing page; no stable file API identified"
    return "NOT_PUBLIC", "supplementary table provides no accession or stable public file URL"


def geo_base(accession: str) -> str:
    match = re.fullmatch(r"(GSE|GSM)(\d+)", accession.upper())
    if not match:
        raise ValueError(f"not a GEO accession: {accession}")
    prefix, digits = match.groups()
    group = prefix + (digits[:-3] if len(digits) > 3 else "") + "nnn"
    level = "series" if prefix == "GSE" else "samples"
    return f"https://ftp.ncbi.nlm.nih.gov/geo/{level}/{group}/{accession.upper()}/suppl/"


def probe_size(url: str) -> int:
    try:
        headers, _, _ = http_metadata(url, method="HEAD")
        if headers.get("Content-Length"):
            return int(headers["Content-Length"])
    except (HTTPError, URLError, TimeoutError, ConnectionError):
        pass
    try:
        headers, _, _ = http_metadata(url, method="GET", headers={"Range": "bytes=0-0"})
        return content_range_total(headers.get("Content-Range", ""))
    except (HTTPError, URLError, TimeoutError, ConnectionError):
        return 0


def probe_object_metadata(url: str) -> dict:
    try:
        headers, _, _ = http_metadata(url, method="HEAD")
        size = int(headers.get("Content-Length", 0) or 0)
        checksum_type, checksum = classify_s3_etag(size, headers.get("ETag", ""))
        return {"size_bytes": size, "checksum_type": checksum_type, "checksum": checksum}
    except (HTTPError, URLError, TimeoutError, ConnectionError):
        return {"size_bytes": probe_size(url), "checksum_type": "", "checksum": ""}


def resolve_geo(accession: str) -> list:
    base = geo_base(accession)
    payload, _, _, _ = http_bytes(base)
    files = parse_apache_index(payload.decode("utf-8", "replace"), base)
    sizes = {}
    try:
        filelist, _, _, _ = http_bytes(urljoin(base, "filelist.txt"), attempts=2)
        sizes = parse_geo_filelist(filelist)
    except (HTTPError, URLError, TimeoutError):
        pass
    unresolved = [item for item in files if item["file_name"] not in sizes]
    with ThreadPoolExecutor(max_workers=min(8, max(1, len(unresolved)))) as pool:
        probed = list(pool.map(lambda item: probe_size(item["download_url"]), unresolved))
    probed_sizes = {item["file_name"]: size for item, size in zip(unresolved, probed)}
    for item in files:
        item.update(size_bytes=sizes.get(item["file_name"], probed_sizes.get(item["file_name"], 0)),
                    checksum_type="", checksum="")
    return files


def resolve_zenodo(url: str) -> tuple:
    match = re.search(r"zenodo\.org/(?:record|records)/(\d+)", url)
    if not match:
        raise ValueError(f"Zenodo record ID missing from {url}")
    payload, _, _, _ = http_bytes(f"https://zenodo.org/api/records/{match.group(1)}")
    return parse_zenodo_record(payload)


def resolve_github(url: str) -> list:
    match = re.search(r"github\.com/([^/]+)/([^/#?]+)", url)
    if not match:
        return []
    owner, repo = match.groups()
    payload, _, _, _ = http_bytes(f"https://api.github.com/repos/{owner}/{repo}")
    metadata = json.loads(payload.decode("utf-8"))
    branch = metadata["default_branch"]
    return [{
        "file_name": f"{owner}-{repo}-{branch}.zip",
        "download_url": f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip",
        "size_bytes": 0, "checksum_type": "", "checksum": "",
    }]


def resolve_direct_page(url: str) -> list:
    payload, _, _, final_url = http_bytes(url)
    parser = LinkParser()
    parser.feed(payload.decode("utf-8", "replace"))
    extensions = (".zip", ".tar", ".tar.gz", ".tgz", ".gz", ".h5", ".h5ad", ".rds", ".csv", ".tsv")
    files = []
    for href in parser.links:
        clean = href.split("?", 1)[0].lower()
        if clean.endswith(extensions):
            download_url = urljoin(final_url, href)
            files.append({"file_name": download_url.rsplit("/", 1)[-1].split("?", 1)[0],
                          "download_url": download_url, "size_bytes": probe_size(download_url),
                          "checksum_type": "", "checksum": ""})
    return list({item["download_url"]: item for item in files}.values())


def write_tsv(path: Path, rows: list, fields: list) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def deduplicated_known_bytes(rows: list) -> int:
    sizes = {}
    for row in rows:
        url = row.get("download_url", "")
        size = int(row.get("size_bytes", 0) or 0)
        if url:
            sizes[url] = max(sizes.get(url, 0), size)
    return sum(sizes.values())


def actionable_known_bytes(rows: list, paused_sources: set) -> int:
    return deduplicated_known_bytes([
        row for row in rows if row.get("source_record_id", "") not in paused_sources
    ])


def load_tenx_map(path: Path) -> list:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    required = {"source_record_id", "platform", "paper_sample_id", "download_sample_id",
                "analysis_version", "assay_path", "expected_cells", "required_files"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError(f"invalid 10x paper sample map: {path}")
    return rows


def tenx_url(row: dict, suffix: str) -> str:
    sample = row["download_sample_id"]
    return (f"https://cf.10xgenomics.com/samples/{row['assay_path']}/{row['analysis_version']}/"
            f"{sample}/{sample}_{suffix}")


def resolve_tenx_samples(rows: list) -> list:
    files = []
    for row in rows:
        for suffix in row["required_files"].split(";"):
            url = tenx_url(row, suffix)
            metadata = probe_object_metadata(url)
            files.append({
                "file_name": f"{row['paper_sample_id']}__{suffix}", "download_url": url,
                "size_bytes": metadata["size_bytes"],
                "checksum_type": metadata["checksum_type"], "checksum": metadata["checksum"],
                "paper_sample_id": row["paper_sample_id"],
            })
    return files


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--datasets", required=True)
    parser.add_argument("--root", default="/mnt/f/spatialecotyper_reproduction")
    parser.add_argument(
        "--tenx-map",
        default=str(Path(__file__).resolve().parents[1] / "config/tenx-paper-samples.tsv"),
    )
    args = parser.parse_args()
    root = Path(args.root)
    manifests = root / "archive/manifests"
    results_dir = root / "results/reproducibility"
    manifests.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    with Path(args.datasets).open(newline="", encoding="utf-8") as handle:
        records = list(csv.DictReader(handle, delimiter="\t"))
    tenx_rows = load_tenx_map(Path(args.tenx_map))
    tenx_by_source = {}
    for row in tenx_rows:
        tenx_by_source.setdefault(row["source_record_id"], []).append(row)
    records.append({
        "source_record_id": "STANFORD-DOI-PM3T-CN37", "accession": "10.25936/pm3t-cn37",
        "data_url": "https://spatialecotyper.stanford.edu/DOI", "dataset_name": "Author processed/normalized data",
    })

    downloads = []
    ledger = []
    capacity = []
    resolution_cache = {}
    for record in records:
        status, reason = classify_record(record)
        files = []
        license_value = ""
        error = ""
        try:
            geo_accession = next((item for item in record.get("accession", "").split(";")
                                  if re.fullmatch(r"(?:GSE|GSM)\d+", item)), "")
            if status == "PUBLIC_API" and geo_accession:
                cache_key = "GEO:" + geo_accession
                if cache_key not in resolution_cache:
                    resolution_cache[cache_key] = resolve_geo(geo_accession)
                files = resolution_cache[cache_key]
                repository = "NCBI_GEO"
            elif status == "PUBLIC_API" and "zenodo.org" in record.get("data_url", ""):
                cache_key = "ZENODO:" + record["data_url"]
                if cache_key not in resolution_cache:
                    resolution_cache[cache_key] = resolve_zenodo(record["data_url"])
                files, metadata = resolution_cache[cache_key]
                license_value = metadata["license"]
                repository = "ZENODO"
            elif status == "PUBLIC_API" and "github.com" in record.get("data_url", ""):
                cache_key = "GITHUB:" + record["data_url"]
                if cache_key not in resolution_cache:
                    resolution_cache[cache_key] = resolve_github(record["data_url"])
                files = resolution_cache[cache_key]
                repository = "GITHUB"
            elif status == "PUBLIC_API" and record["source_record_id"] in tenx_by_source:
                cache_key = "TENX:" + record["source_record_id"]
                if cache_key not in resolution_cache:
                    resolution_cache[cache_key] = resolve_tenx_samples(tenx_by_source[record["source_record_id"]])
                files = resolution_cache[cache_key]
                license_value = "CC-BY-4.0"
                repository = "TENX"
                reason = "exact Table S8 sample/version mapping; minimal paper-required processed inputs"
            elif status == "PUBLIC_API" and record.get("accession", "").startswith("PRJEB"):
                ena_accession = record["accession"].split(";")[0]
                cache_key = "ENA:" + ena_accession
                if cache_key not in resolution_cache:
                    resolution_cache[cache_key] = resolve_ena(ena_accession)
                files = resolution_cache[cache_key]
                repository = "ENA"
                reason = "ENA public raw FASTQ inventory; capacity-gated because paper used processed expression"
            elif status == "PUBLIC_DIRECT" and "spatialresearch.org" in record.get("data_url", ""):
                cache_key = "DIRECT:" + record["data_url"]
                if cache_key not in resolution_cache:
                    resolution_cache[cache_key] = resolve_direct_page(record["data_url"])
                files = resolution_cache[cache_key]
                repository = "SPATIALRESEARCH"
            else:
                repository = "OTHER"
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            repository = "ERROR"
        if not files and status in {"PUBLIC_API", "PUBLIC_DIRECT"}:
            reason = f"{reason}; no direct file resolved" + (f"; {error}" if error else "")
        for item in files:
            downloads.append({
                "source_record_id": record["source_record_id"], "accession": record.get("accession", ""),
                "repository": repository, "file_name": item["file_name"],
                "download_url": item["download_url"], "size_bytes": item.get("size_bytes", 0),
                "checksum_type": item.get("checksum_type", ""), "checksum": item.get("checksum", ""),
                "license": license_value, "access_status": status, "resolver_note": reason,
            })
        ledger.append({
            "source_record_id": record["source_record_id"], "accession": record.get("accession", ""),
            "data_url": record.get("data_url", ""), "access_status": status,
            "evidence_url": record.get("data_url", ""), "resolved_file_count": len(files), "reason": reason,
        })
        known_bytes = sum(int(item.get("size_bytes", 0)) for item in files)
        capacity.append({
            "source_record_id": record["source_record_id"], "accession": record.get("accession", ""),
            "access_status": status, "resolved_file_count": len(files), "known_bytes": known_bytes,
            "unknown_size_files": sum(not int(item.get("size_bytes", 0)) for item in files),
            "source_gate": "PAUSE_OVER_100GB" if known_bytes > 100 * 1024 ** 3 else "PASS",
            "reason": reason,
        })

    write_tsv(manifests / "paper-downloads.tsv", downloads, DOWNLOAD_FIELDS)
    write_tsv(manifests / "paper-access-ledger.tsv", ledger,
              ["source_record_id", "accession", "data_url", "access_status", "evidence_url", "resolved_file_count", "reason"])
    free_bytes = shutil.disk_usage(root).free
    known_total = deduplicated_known_bytes(downloads)
    paused_sources = {row["source_record_id"] for row in capacity if row["source_gate"] != "PASS"}
    actionable_total = actionable_known_bytes(downloads, paused_sources)
    for row in capacity:
        row.update(free_bytes=free_bytes, known_total_bytes=known_total,
                   actionable_total_bytes=actionable_total,
                   global_gate="PASS" if actionable_total <= int(free_bytes * 0.70) else "PAUSE_OVER_70_PERCENT")
    write_tsv(results_dir / "paper-download-capacity.tsv", capacity,
              ["source_record_id", "accession", "access_status", "resolved_file_count", "known_bytes",
               "unknown_size_files", "source_gate", "free_bytes", "known_total_bytes",
               "actionable_total_bytes", "global_gate", "reason"])
    print(f"records={len(records)} files={len(downloads)} known_bytes={known_total} "
          f"actionable_bytes={actionable_total} free_bytes={free_bytes}")


if __name__ == "__main__":
    main()
