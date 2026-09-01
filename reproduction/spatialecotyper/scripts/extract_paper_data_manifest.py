#!/usr/bin/env python3
"""Extract canonical paper dataset/sample manifests from the official XLSX."""

import argparse
import csv
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL_NS = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}
DOC_REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"

SECTIONS = [
    ("Table S1", 5, 6, 23, "public_spatial"),
    ("Table S2", 4, 5, 18, "public_scrna"),
    ("Table S8", 5, 6, 36, "single_cell_spatial"),
    ("Table S12", 4, 5, 11, "paired_scrna_bulk"),
    ("Table S15", 4, 5, 17, "ici_bulk"),
    ("Table S17", 7, 8, 30, "paired_liquid"),
    ("Table S17", 34, 35, 51, "liquid_spatial"),
]


def column_number(reference: str) -> int:
    letters = re.match(r"[A-Z]+", reference).group(0)
    value = 0
    for letter in letters:
        value = value * 26 + ord(letter) - 64
    return value


def load_xlsx(path: Path) -> dict:
    """Read cell values with the Python standard library, preserving Excel rows."""
    with zipfile.ZipFile(path) as archive:
        shared = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root.findall("m:si", NS):
                shared.append("".join(node.text or "" for node in item.findall(".//m:t", NS)))
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        rels = {rel.attrib["Id"]: rel.attrib["Target"] for rel in relationships.findall("r:Relationship", REL_NS)}
        sheet_targets = {}
        for sheet in workbook.findall("m:sheets/m:sheet", NS):
            target = rels[sheet.attrib[DOC_REL]].lstrip("/")
            if not target.startswith("xl/"):
                target = "xl/" + target
            sheet_targets[sheet.attrib["name"]] = target

        result = {}
        for sheet_name, target in sheet_targets.items():
            if sheet_name not in {section[0] for section in SECTIONS}:
                continue
            root = ET.fromstring(archive.read(target))
            rows = {}
            for row in root.findall("m:sheetData/m:row", NS):
                row_number = int(row.attrib["r"])
                values = {}
                for cell in row.findall("m:c", NS):
                    col = column_number(cell.attrib["r"])
                    cell_type = cell.attrib.get("t", "")
                    value_node = cell.find("m:v", NS)
                    if cell_type == "inlineStr":
                        value = "".join(n.text or "" for n in cell.findall(".//m:t", NS))
                    elif value_node is None:
                        value = ""
                    elif cell_type == "s":
                        value = shared[int(value_node.text)]
                    else:
                        value = value_node.text or ""
                        if cell_type != "str":
                            try:
                                number = float(value)
                                value = int(number) if number.is_integer() else number
                            except ValueError:
                                pass
                    values[col] = value
                rows[row_number] = values
            result[sheet_name] = rows
        return result


def clean_header(value, column: int) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text or f"column_{column}"


def extract_accession(*values) -> str:
    text = " ".join(str(value or "") for value in values)
    patterns = [
        r"GSE\d+", r"GSM\d+", r"PRJ(?:NA|EB)\d+", r"HRA\d+", r"CRA\d+",
        r"OMIX\d+", r"E-MTAB-\d+", r"syn\d+", r"phs\d+(?:\.v\d+\.p\d+)?",
    ]
    found = []
    for pattern in patterns:
        found.extend(re.findall(pattern, text, flags=re.IGNORECASE))
    return ";".join(dict.fromkeys(item.upper() for item in found))


def canonical_record(sheet: str, row_number: int, section: str, raw: dict) -> dict:
    values = list(raw.values())
    record = {
        "source_record_id": f"{sheet.replace(' ', '')}-R{row_number}",
        "sheet": sheet,
        "excel_row": row_number,
        "section": section,
        "dataset_name": "",
        "modality": "",
        "platform": "",
        "cancer_type": "",
        "reported_sample_count": "",
        "accession": "",
        "data_url": "",
        "publication": "",
        "pmid": "",
        "sample_id": "",
        "cohort": "",
        "raw_json": json.dumps(raw, ensure_ascii=False, sort_keys=True),
    }
    if section == "public_spatial":
        record.update(dataset_name=values[0], modality="spatial_transcriptomics", platform=values[1],
                      cancer_type=values[2], reported_sample_count=values[3], publication=values[4],
                      pmid=values[5], data_url=values[6], accession=extract_accession(values[6]))
    elif section == "public_scrna":
        record.update(dataset_name=values[0], modality="single_cell_rna", cancer_type=values[1],
                      platform=values[2], publication=values[3], pmid=values[4],
                      accession=extract_accession(values[5]), data_url=str(values[5]))
    elif section == "single_cell_spatial":
        record.update(dataset_name=values[1], modality="single_cell_spatial", platform=values[8],
                      cancer_type=values[2], sample_id=values[0], cohort=values[9])
    elif section == "paired_scrna_bulk":
        record.update(dataset_name="Generated cohort 1", modality="single_cell_rna;bulk_rna",
                      cancer_type=values[0], sample_id=values[1], accession="GSE320042")
    elif section == "ici_bulk":
        record.update(dataset_name=values[0], modality="bulk_rna", cancer_type=values[1],
                      reported_sample_count=f"fig3h={values[3]};fig3i={values[4]}", pmid=values[5],
                      accession=extract_accession(values[6]), data_url=str(values[6]))
    elif section == "paired_liquid":
        record.update(dataset_name="Generated paired tumour/plasma cohort", modality="spatial;emseq",
                      cancer_type=values[1], sample_id=values[0], accession="GSE320042")
    elif section == "liquid_spatial":
        record.update(dataset_name="Generated Liquid EcoTyper ST cohort", modality="spatial_transcriptomics",
                      cancer_type=values[0], platform=values[1], sample_id=values[2], accession="GSE320042")
    return {key: "" if value is None else value for key, value in record.items()}


def write_tsv(path: Path, rows: list, fields: list) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--xlsx", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    workbook = load_xlsx(Path(args.xlsx))
    samples = []
    for sheet, header_row, first_row, last_row, section in SECTIONS:
        headers = workbook[sheet][header_row]
        for row_number in range(first_row, last_row + 1):
            row = workbook[sheet].get(row_number, {})
            raw = {
                clean_header(headers.get(column), column): row.get(column, "")
                for column in sorted(headers)
                if headers.get(column) not in (None, "")
            }
            if any(value not in (None, "") for value in raw.values()):
                samples.append(canonical_record(sheet, row_number, section, raw))

    fields = list(samples[0].keys())
    write_tsv(output / "paper-samples.tsv", samples, fields)
    datasets = [row for row in samples if row["section"] in {"public_spatial", "public_scrna", "ici_bulk"}]
    datasets.extend([
        {**samples[0], "source_record_id": "GENERATED-GSE320042", "sheet": "Data availability",
         "excel_row": 0, "section": "generated_in_this_work", "dataset_name": "Author-generated genomic data",
         "modality": "spatial;single_cell_rna;bulk_rna;emseq", "platform": "multiple", "cancer_type": "multiple",
         "reported_sample_count": "", "accession": "GSE320042", "data_url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE320042",
         "publication": "", "pmid": "", "sample_id": "", "cohort": "", "raw_json": "{}"}
    ])
    write_tsv(output / "paper-datasets.tsv", datasets, fields)
    ledger_fields = ["source_record_id", "accession", "data_url", "access_status", "evidence_url", "reason"]
    ledger = [{
        "source_record_id": row["source_record_id"], "accession": row["accession"],
        "data_url": row["data_url"], "access_status": "UNRESOLVED",
        "evidence_url": row["data_url"], "reason": "pending repository resolution",
    } for row in datasets]
    write_tsv(output / "paper-access-ledger.tsv", ledger, ledger_fields)
    counts = {}
    for row in samples:
        counts[row["sheet"]] = counts.get(row["sheet"], 0) + 1
    for sheet, count in counts.items():
        print(f"{sheet}\t{count}")
    accessions = []
    for row in samples:
        accessions.extend(item for item in str(row["accession"]).split(";") if item)
    accession_counts = {item: accessions.count(item) for item in set(accessions)}
    audit = [
        {"metric": "canonical_sample_rows", "value": len(samples)},
        {"metric": "s1_reported_sample_sum", "value": sum(
            int(row["reported_sample_count"]) for row in samples if row["section"] == "public_spatial"
        )},
        {"metric": "unique_accessions", "value": len(set(accessions))},
        {"metric": "duplicated_accessions", "value": sum(count > 1 for count in accession_counts.values())},
    ]
    audit.extend({"metric": f"rows_{sheet.replace(' ', '_').lower()}", "value": count}
                 for sheet, count in sorted(counts.items()))
    write_tsv(output / "paper-manifest-audit.tsv", audit, ["metric", "value"])


if __name__ == "__main__":
    main()
