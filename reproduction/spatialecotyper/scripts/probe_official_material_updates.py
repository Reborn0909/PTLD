#!/usr/bin/env python3
"""Record immutable observations of official material endpoints and blocker candidates."""

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


FIXED_COMMIT = "48c2c846781d3a312771021c1a2ef5fc383700c5"
SNAPSHOT_FIELDS = (
    "observation_id",
    "endpoint_id",
    "url",
    "http_status",
    "revision",
    "etag",
    "artifact_type",
    "access_status",
    "detail",
    "observed_utc",
)
REPORT_FIELDS = (
    "component",
    "candidate_found",
    "status",
    "candidate_paths",
    "latest_revision",
    "fixed_revision",
    "changes_current_blocker",
)


def read_tsv(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _write_tsv(path: Path, rows: list[dict], fields: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(path.name + ".part")
    with part.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    part.replace(path)


def observation_id(row: dict) -> str:
    stable = "\t".join(
        str(row.get(field, ""))
        for field in SNAPSHOT_FIELDS
        if field not in {"observation_id", "observed_utc"}
    )
    return hashlib.sha256(stable.encode("utf-8")).hexdigest()


def make_observation(**values) -> dict:
    row = {field: str(values.get(field, "")) for field in SNAPSHOT_FIELDS}
    row["observation_id"] = observation_id(row)
    return row


def append_snapshot(path: Path, row: dict) -> bool:
    rows = read_tsv(path)
    seen = {item["observation_id"] for item in rows}
    if row["observation_id"] in seen:
        return False
    _write_tsv(path, rows + [row], SNAPSHOT_FIELDS)
    return True


def classify_access(http_status: int, text: str, url: str) -> str:
    content = text.lower()
    if http_status in {401, 403}:
        return "REGISTRATION_REQUIRED"
    login_terms = ("sign in", "log in", "login", "registration required", "create account")
    if any(term in content for term in login_terms) and (
        "stanford" in content or "stanford" in url.lower() or "download" in content
    ):
        return "REGISTRATION_REQUIRED"
    if 200 <= http_status < 400:
        return "PUBLIC"
    return "UNAVAILABLE"


def _request(url: str, accept: str = "application/json") -> tuple[int, dict, bytes, str]:
    request = Request(
        url,
        headers={
            "Accept": accept,
            "User-Agent": "SpatialEcoTyper-auditable-reproduction/1.0",
        },
    )
    try:
        with urlopen(request, timeout=45) as response:
            body = response.read()
            return response.status, dict(response.headers.items()), body, response.geturl()
    except HTTPError as error:
        return error.code, dict(error.headers.items()), error.read(), error.geturl()
    except URLError as error:
        return 0, {}, str(error.reason).encode("utf-8", errors="replace"), url


def detect_candidate_unblockers(paths: list[str], latest_revision: str = "") -> list[dict]:
    normalized = [path.lower() for path in paths]
    definitions = {
        "LIQUID_ECOTYPER": lambda path: (
            "liquid" in path
            and (path.endswith((".py", ".ipynb", ".pt", ".pth", ".ckpt", ".onnx")) or "checkpoint" in path)
        ),
        "CYTOSPACE_WEIGHTS": lambda path: (
            "cytospace" in path and bool(re.search(r"weight|cell.?count|assignment", path))
        ),
        "FIGURE_SCRIPTS": lambda path: (
            bool(re.search(r"(^|/)(fig|figure|plot)", path))
            and path.endswith((".r", ".py", ".ipynb", ".sh", ".rmd"))
        ),
    }
    report = []
    for component, predicate in definitions.items():
        candidates = [paths[index] for index, path in enumerate(normalized) if predicate(path)]
        found = bool(candidates)
        report.append(
            {
                "component": component,
                "candidate_found": str(found).upper(),
                "status": (
                    "CANDIDATE_REQUIRES_ARCHIVE_VALIDATION"
                    if found
                    else "BLOCKED_NO_NEW_OFFICIAL_MATERIAL"
                ),
                "candidate_paths": ";".join(candidates),
                "latest_revision": latest_revision,
                "fixed_revision": FIXED_COMMIT,
                "changes_current_blocker": "FALSE",
            }
        )
    return report


def _observe_endpoint(
    endpoint_id: str, url: str, artifact_type: str, observed_utc: str
) -> tuple[dict, bytes, str]:
    status, headers, body, final_url = _request(url, "text/html,application/json")
    text = body.decode("utf-8", errors="replace")
    detail = f"final_url={final_url};bytes={len(body)};sha256={hashlib.sha256(body).hexdigest()}"
    access_status = classify_access(status, text, final_url)
    if endpoint_id == "stanford_normalized_data" and (
        "supporting data are available" in text.lower()
        and not re.search(r'href=["\'][^"\']+\.(zip|tar|gz|rds|csv|tsv|xlsx)', text, re.I)
    ):
        access_status = "REGISTRATION_REQUIRED"
        detail += ";landing_page_only=TRUE;direct_data_files=0"
    row = make_observation(
        endpoint_id=endpoint_id,
        url=url,
        http_status=status,
        revision="",
        etag=headers.get("ETag", ""),
        artifact_type=artifact_type,
        access_status=access_status,
        detail=detail,
        observed_utc=observed_utc,
    )
    return row, body, final_url


def _archive_latest_commit(root: Path, revision: str, observed_utc: str) -> dict:
    url = f"https://codeload.github.com/digitalcytometry/spatialecotyper/tar.gz/{revision}"
    output = root / "archive/official-updates" / f"spatialecotyper-{revision}.tar.gz"
    output.parent.mkdir(parents=True, exist_ok=True)
    if not output.is_file():
        part = output.with_name(output.name + ".part")
        request = Request(url, headers={"User-Agent": "SpatialEcoTyper-auditable-reproduction/1.0"})
        digest = hashlib.sha256()
        total = 0
        with urlopen(request, timeout=120) as response:
            expected = int(response.headers.get("Content-Length", "0") or 0)
            if expected and expected > shutil.disk_usage(output.parent).free * 0.7:
                raise RuntimeError("official update archive exceeds the 70% free-space gate")
            with part.open("wb") as handle:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    handle.write(chunk)
                    digest.update(chunk)
                    total += len(chunk)
        if expected and total != expected:
            raise RuntimeError(f"official update archive size mismatch: {total} != {expected}")
        part.replace(output)
    else:
        digest = hashlib.sha256()
        total = 0
        with output.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                digest.update(chunk)
                total += len(chunk)
    return make_observation(
        endpoint_id="github_source_archive",
        url=url,
        http_status=200,
        revision=revision,
        etag="",
        artifact_type="SOURCE_ARCHIVE",
        access_status="PUBLIC_ARCHIVED",
        detail=f"local_path={output};bytes={total};sha256={digest.hexdigest()}",
        observed_utc=observed_utc,
    )


def probe(root: Path) -> tuple[list[dict], list[dict]]:
    observed_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    snapshot_path = root / "archive/manifests/official-material-snapshots.tsv"
    observations = []

    repo_url = "https://api.github.com/repos/digitalcytometry/spatialecotyper"
    repo_status, repo_headers, repo_body, _ = _request(repo_url)
    repo_payload = json.loads(repo_body) if repo_status == 200 else {}
    default_branch = repo_payload.get("default_branch", "master")
    commit_url = f"{repo_url}/commits/{default_branch}"
    commit_status, commit_headers, commit_body, _ = _request(commit_url)
    commit_payload = json.loads(commit_body) if commit_status == 200 else {}
    latest_revision = commit_payload.get("sha", "")
    observations.append(
        make_observation(
            endpoint_id="github_repository",
            url=repo_url,
            http_status=repo_status,
            revision=latest_revision,
            etag=repo_headers.get("ETag", commit_headers.get("ETag", "")),
            artifact_type="SOURCE_REPOSITORY",
            access_status="PUBLIC" if repo_status == 200 else "UNAVAILABLE",
            detail=f"default_branch={default_branch};fixed_commit={FIXED_COMMIT}",
            observed_utc=observed_utc,
        )
    )

    tree_paths = []
    if latest_revision:
        tree_url = f"{repo_url}/git/trees/{latest_revision}?recursive=1"
        tree_status, tree_headers, tree_body, _ = _request(tree_url)
        tree_payload = json.loads(tree_body) if tree_status == 200 else {}
        tree_paths = [item["path"] for item in tree_payload.get("tree", []) if item.get("type") == "blob"]
        observations.append(
            make_observation(
                endpoint_id="github_recursive_tree",
                url=tree_url,
                http_status=tree_status,
                revision=latest_revision,
                etag=tree_headers.get("ETag", ""),
                artifact_type="SOURCE_TREE",
                access_status="PUBLIC" if tree_status == 200 else "UNAVAILABLE",
                detail=f"blob_paths={len(tree_paths)};truncated={tree_payload.get('truncated', '')}",
                observed_utc=observed_utc,
            )
        )
        if latest_revision != FIXED_COMMIT:
            observations.append(_archive_latest_commit(root, latest_revision, observed_utc))

    endpoints = (
        (
            "nature_article",
            "https://www.nature.com/articles/s41586-026-10452-4",
            "PUBLICATION",
        ),
        (
            "stanford_normalized_data",
            "https://doi.org/10.25936/pm3t-cn37",
            "NORMALIZED_DATA_ARCHIVE",
        ),
        (
            "stanford_model_interface",
            "https://spatialecotyper.stanford.edu",
            "MODEL_INTERFACE",
        ),
    )
    for endpoint_id, url, artifact_type in endpoints:
        observation, _, _ = _observe_endpoint(endpoint_id, url, artifact_type, observed_utc)
        observations.append(observation)

    for observation in observations:
        append_snapshot(snapshot_path, observation)

    report = detect_candidate_unblockers(tree_paths, latest_revision)
    report_path = root / "results/reproducibility/official-material-update-report.tsv"
    _write_tsv(report_path, report, REPORT_FIELDS)
    return observations, report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="/mnt/f/spatialecotyper_reproduction")
    args = parser.parse_args()
    observations, report = probe(Path(args.root))
    candidates = sum(row["candidate_found"] == "TRUE" for row in report)
    print(
        f"official material probe: PASS endpoints={len(observations)} "
        f"candidate_unblockers={candidates}"
    )


if __name__ == "__main__":
    main()
