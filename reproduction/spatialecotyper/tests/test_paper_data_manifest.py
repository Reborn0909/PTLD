#!/usr/bin/env python3
import csv
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / "reproduction/spatialecotyper/scripts/extract_paper_data_manifest.py"
ROOT = Path(os.environ.get("SPATIALECOTYPER_ROOT", "/mnt/f/spatialecotyper_reproduction"))
XLSX = ROOT / "archive/paper/41586_2026_10452_MOESM3_ESM.xlsx"


class PaperDataManifestTest(unittest.TestCase):
    def test_supplementary_tables_are_extracted_with_provenance(self):
        self.assertTrue(SCRIPT.is_file(), f"missing extractor: {SCRIPT}")
        self.assertTrue(XLSX.is_file(), f"missing workbook: {XLSX}")
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(
                [sys.executable, str(SCRIPT), "--xlsx", str(XLSX), "--output", tmp],
                check=True,
            )
            samples_path = Path(tmp) / "paper-samples.tsv"
            datasets_path = Path(tmp) / "paper-datasets.tsv"
            ledger_path = Path(tmp) / "paper-access-ledger.tsv"
            audit_path = Path(tmp) / "paper-manifest-audit.tsv"
            self.assertTrue(samples_path.is_file())
            self.assertTrue(datasets_path.is_file())
            self.assertTrue(ledger_path.is_file())
            self.assertTrue(audit_path.is_file())
            with samples_path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle, delimiter="\t"))
            counts = {}
            for row in rows:
                counts[row["sheet"]] = counts.get(row["sheet"], 0) + 1
                self.assertGreater(int(row["excel_row"]), 0)
                self.assertTrue(row["section"])
                raw = json.loads(row["raw_json"])
                self.assertIsInstance(raw, dict)
                self.assertTrue(raw)
            self.assertEqual(
                {
                    "Table S1": 18,
                    "Table S2": 14,
                    "Table S8": 31,
                    "Table S12": 7,
                    "Table S15": 13,
                    "Table S17": 40,
                },
                counts,
            )
            self.assertEqual(123, len(rows))
            with audit_path.open(newline="", encoding="utf-8") as handle:
                audit = {row["metric"]: row["value"] for row in csv.DictReader(handle, delimiter="\t")}
            self.assertEqual("235", audit["s1_reported_sample_sum"])
            self.assertEqual("123", audit["canonical_sample_rows"])


if __name__ == "__main__":
    unittest.main()
