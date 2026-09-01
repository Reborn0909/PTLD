#!/usr/bin/env python3
"""Extract a canonical figure and panel inventory from the archived paper."""

import argparse
from collections import Counter
import csv
import hashlib
from pathlib import Path
import re

from bs4 import BeautifulSoup

try:
    import pymupdf as fitz
except ImportError:  # PyMuPDF versions before the pymupdf import name.
    import fitz


FIGURE_FIELDS = (
    "figure_id",
    "figure_family",
    "figure_number",
    "title",
    "caption",
    "source_path",
    "source_locator",
    "source_sha256",
)
PANEL_FIELDS = (
    "figure_id",
    "panel_id",
    "panel_label",
    "panel_text",
    "caption_sha256",
)
LABEL_RE = re.compile(r"^[a-z](?:[\-–][a-z])?$")
MARKER_RE = re.compile(r"\[\[PANEL:([a-z](?:[\-–][a-z])?)\]\]")
PDF_PANEL_RE = re.compile(r"(?:^|\s)([a-z](?:[\-–][a-z])?),\s+(?=[A-Z])")


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _marked_html_caption(node) -> tuple[str, list[dict]]:
    fragment = BeautifulSoup(str(node), "html.parser")
    for bold in fragment.find_all("b"):
        label = normalize(bold.get_text()).lower().replace("−", "-")
        following = bold.next_sibling
        following_text = "" if following is None else str(following).lstrip()
        if LABEL_RE.fullmatch(label) and following_text.startswith(","):
            bold.replace_with(f" [[PANEL:{label}]] ")
    marked = normalize(fragment.get_text(" ", strip=True))
    matches = list(MARKER_RE.finditer(marked))
    panels = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(marked)
        panels.append(
            {
                "label": match.group(1).replace("–", "-"),
                "text": normalize(marked[match.end() : end]).lstrip(", "),
            }
        )
    caption = normalize(MARKER_RE.sub("", marked))
    return caption, panels


def extract_html_figures(path: Path) -> list[dict]:
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    source_sha = sha256_file(path)
    rows = []

    for node in soup.select('div[data-test="figure"]'):
        title_node = node.select_one('[data-test="figure-caption-text"]')
        caption_node = node.select_one('[data-test="bottom-caption"]')
        if title_node is None or caption_node is None:
            continue
        match = re.match(r"Fig\.\s*(\d+):\s*(.*)", normalize(title_node.get_text()))
        if not match:
            continue
        number = int(match.group(1))
        caption, panels = _marked_html_caption(caption_node)
        rows.append(
            {
                "figure_id": f"MAIN-{number}",
                "figure_family": "MAIN",
                "figure_number": number,
                "title": normalize(match.group(2)),
                "caption": caption,
                "source_path": str(path),
                "source_locator": f"#Fig{number}",
                "source_sha256": source_sha,
                "_panels": panels,
            }
        )

    for node in soup.select('div[data-test="supp-item"][id^="Fig"]'):
        title_node = node.select_one("h3")
        caption_node = node.select_one('[data-component="thumbnail-container"]')
        if title_node is None or caption_node is None:
            continue
        title_text = normalize(title_node.get_text(" ", strip=True))
        match = re.match(r"Extended Data Fig\.\s*(\d+)\s*(.*)", title_text)
        if not match:
            continue
        number = int(match.group(1))
        caption, panels = _marked_html_caption(caption_node)
        rows.append(
            {
                "figure_id": f"EXTENDED-{number}",
                "figure_family": "EXTENDED",
                "figure_number": number,
                "title": normalize(match.group(2)),
                "caption": caption,
                "source_path": str(path),
                "source_locator": f"#{node.get('id')}",
                "source_sha256": source_sha,
                "_panels": panels,
            }
        )

    family_order = {"MAIN": 0, "EXTENDED": 1}
    return sorted(rows, key=lambda row: (family_order[row["figure_family"]], row["figure_number"]))


def _pdf_panels(caption: str) -> list[dict]:
    matches = list(PDF_PANEL_RE.finditer(caption))
    panels = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(caption)
        panels.append(
            {
                "label": match.group(1).replace("–", "-"),
                "text": normalize(caption[match.end() : end]),
            }
        )
    return panels


def extract_supplementary_figures(path: Path) -> list[dict]:
    source_sha = sha256_file(path)
    rows = []
    document = fitz.open(path)
    try:
        for page_index, page in enumerate(document):
            text = normalize(page.get_text("text"))
            match = re.search(r"Supplementary Fig\.\s*(\d+):\s*(.*)", text)
            if not match:
                continue
            number = int(match.group(1))
            if not 1 <= number <= 9 or any(row["figure_number"] == number for row in rows):
                continue
            caption = normalize(match.group(2))
            title = caption.split(". ", 1)[0].rstrip(".")
            rows.append(
                {
                    "figure_id": f"SUPPLEMENTARY-{number}",
                    "figure_family": "SUPPLEMENTARY",
                    "figure_number": number,
                    "title": title,
                    "caption": caption,
                    "source_path": str(path),
                    "source_locator": f"page:{page_index + 1}",
                    "source_sha256": source_sha,
                    "_panels": _pdf_panels(caption),
                }
            )
    finally:
        document.close()
    return sorted(rows, key=lambda row: row["figure_number"])


def _expand_label(label: str) -> list[str]:
    if "-" not in label:
        return [label]
    start, end = label.split("-", 1)
    if len(start) != 1 or len(end) != 1 or ord(start) > ord(end):
        return [label]
    return [chr(code) for code in range(ord(start), ord(end) + 1)]


def _canonical_panels(panels: list[dict]) -> list[dict]:
    specific = {}
    ranges = []
    for panel in panels:
        label = panel["label"].replace("–", "-")
        if "-" in label:
            ranges.append({"label": label, "text": panel["text"]})
        elif label not in specific:
            specific[label] = {"label": label, "text": panel["text"]}
    for panel in ranges:
        for label in _expand_label(panel["label"]):
            specific.setdefault(label, {"label": label, "text": panel["text"]})
    return [specific[label] for label in sorted(specific)]


def extract_panels(figures: list[dict]) -> list[dict]:
    rows = []
    for figure in figures:
        explicit = _canonical_panels(figure.get("_panels", []))
        if not explicit:
            explicit = [{"label": "whole", "text": figure["caption"]}]
        for panel in explicit:
            label = panel["label"]
            rows.append(
                {
                    "figure_id": figure["figure_id"],
                    "panel_id": f"{figure['figure_id']}:{label}",
                    "panel_label": label,
                    "panel_text": panel["text"] or figure["caption"],
                    "caption_sha256": hashlib.sha256(
                        figure["caption"].encode("utf-8")
                    ).hexdigest(),
                }
            )
    return rows


def _write_tsv(path: Path, fields: tuple[str, ...], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(path.name + ".part")
    with part.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    part.replace(path)


def build_manifests(root: Path) -> tuple[list[dict], list[dict]]:
    paper = root / "archive/paper"
    figures = extract_html_figures(paper / "nature-article.html")
    figures.extend(
        extract_supplementary_figures(
            paper / "41586_2026_10452_MOESM1_ESM.pdf"
        )
    )
    family_order = {"MAIN": 0, "EXTENDED": 1, "SUPPLEMENTARY": 2}
    figures.sort(key=lambda row: (family_order[row["figure_family"]], row["figure_number"]))
    panels = extract_panels(figures)
    manifests = root / "archive/manifests"
    _write_tsv(manifests / "paper-figures.tsv", FIGURE_FIELDS, figures)
    _write_tsv(manifests / "paper-panels.tsv", PANEL_FIELDS, panels)
    return figures, panels


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="/mnt/f/spatialecotyper_reproduction")
    args = parser.parse_args()
    figures, panels = build_manifests(Path(args.root))
    counts = Counter(row["figure_family"] for row in figures)
    expected = {"MAIN": 5, "EXTENDED": 12, "SUPPLEMENTARY": 9}
    if dict(counts) != expected:
        raise SystemExit(f"paper panel manifest: FAIL figure_counts={dict(counts)}")
    print(f"paper panel manifest: PASS figures={len(figures)} panels={len(panels)}")


if __name__ == "__main__":
    main()
