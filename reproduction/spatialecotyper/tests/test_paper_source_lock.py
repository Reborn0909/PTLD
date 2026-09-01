#!/usr/bin/env python3
import csv
import hashlib
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


REPO = Path(__file__).resolve().parents[3]
CONFIG = REPO / "reproduction/spatialecotyper/config/paper-source-lock.tsv"
ARCHIVE = Path(os.environ.get(
    "SPATIALECOTYPER_ROOT", "/mnt/f/spatialecotyper_reproduction"
)) / "archive/paper"
SCRIPT = REPO / "reproduction/spatialecotyper/scripts/archive_paper_sources.py"


def load_archive_module():
    spec = importlib.util.spec_from_file_location("archive_paper_sources", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PaperSourceLockTest(unittest.TestCase):
    def test_complete_part_is_finalized_without_network_request(self):
        module = load_archive_module()
        payload = b"immutable snapshot"
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp)
            part = archive / "source.bin.part"
            part.write_bytes(payload)
            row = {
                "filename": "source.bin",
                "url": "https://example.invalid/source.bin",
                "expected_bytes": str(len(payload)),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
            with patch.object(module, "request", side_effect=AssertionError("network called")):
                result = module.download(row, archive)
            self.assertEqual("FINALIZED_VERIFIED_PART", result["status"])
            self.assertFalse(part.exists())
            self.assertEqual(payload, (archive / "source.bin").read_bytes())

    def test_locked_sources_exist_and_match_archive(self):
        self.assertTrue(CONFIG.is_file(), f"missing source lock: {CONFIG}")
        with CONFIG.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
        self.assertEqual(4, len(rows))
        self.assertEqual("10.1038/s41586-026-10452-4", rows[0]["doi"])
        self.assertEqual(
            {"article_html", "supplementary_pdf", "reporting_summary_pdf", "supplementary_tables_xlsx"},
            {row["source_id"] for row in rows},
        )
        for row in rows:
            self.assertTrue(row["url"].startswith("https://"))
            self.assertRegex(row["sha256"], r"^[0-9a-f]{64}$")
            target = ARCHIVE / row["filename"]
            self.assertTrue(target.is_file(), f"missing archived source: {target}")
            self.assertEqual(int(row["expected_bytes"]), target.stat().st_size)
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            self.assertEqual(row["sha256"], digest)


if __name__ == "__main__":
    unittest.main()
