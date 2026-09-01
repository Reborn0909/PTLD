#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / "reproduction/spatialecotyper/scripts/validate_paper_samples.py"


def load_module():
    if not SCRIPT.is_file():
        raise AssertionError(f"missing sample validator: {SCRIPT}")
    spec = importlib.util.spec_from_file_location("validate_paper_samples", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PaperSampleValidationTest(unittest.TestCase):
    def test_s8_tenx_files_and_gated_platform_are_audited_without_guessing(self):
        module = load_module()
        samples = [
            {
                "source_record_id": "TableS1-R20", "sheet": "Table S1",
                "platform": "10x Visium HD", "sample_id": "",
                "reported_sample_count": "1", "cohort": "",
            },
            {
                "source_record_id": "TableS1-R19", "sheet": "Table S1",
                "platform": "MERSCOPE", "sample_id": "",
                "reported_sample_count": "1", "cohort": "",
            },
            {
                "source_record_id": "TableS8-R30", "sheet": "Table S8",
                "platform": "Visium HD", "sample_id": "HD_A",
                "reported_sample_count": "", "cohort": "Extended validation",
            },
            {
                "source_record_id": "TableS8-R6", "sheet": "Table S8",
                "platform": "MERSCOPE", "sample_id": "MERSCOPE_A",
                "reported_sample_count": "", "cohort": "Discovery",
            },
        ]
        downloads = [
            {"source_record_id": "TableS1-R20", "file_name": "HD_A__bins.tar.gz"},
            {"source_record_id": "TableS1-R20", "file_name": "HD_A__spatial.tar.gz"},
        ]
        verified = [
            {"source_record_id": "TableS1-R20", "file_name": "HD_A__bins.tar.gz"},
        ]
        ledger = [
            {"source_record_id": "TableS1-R20", "access_status": "PUBLIC_API", "reason": "official files"},
            {"source_record_id": "TableS1-R19", "access_status": "REGISTRATION_REQUIRED", "reason": "form required"},
        ]
        tenx = [
            {
                "source_record_id": "TableS1-R20", "platform": "Visium HD",
                "paper_sample_id": "HD_A", "required_files": "bins.tar.gz;spatial.tar.gz",
            }
        ]

        rows = module.build_sample_audit(samples, downloads, verified, [], ledger, tenx)
        by_id = {row["source_record_id"]: row for row in rows}
        self.assertEqual("PARTIAL", by_id["TableS8-R30"]["availability"])
        self.assertEqual(2, by_id["TableS8-R30"]["resolved_files"])
        self.assertEqual(1, by_id["TableS8-R30"]["verified_files"])
        self.assertEqual("TableS1-R20", by_id["TableS8-R30"]["download_source_record_id"])
        self.assertEqual("BLOCKED_ACCESS", by_id["TableS8-R6"]["availability"])
        self.assertEqual("TableS1-R19", by_id["TableS8-R6"]["download_source_record_id"])

    def test_summary_preserves_all_availability_states(self):
        module = load_module()
        rows = [
            {"sheet": "Table S8", "availability": "VERIFIED"},
            {"sheet": "Table S8", "availability": "VERIFIED"},
            {"sheet": "Table S8", "availability": "BLOCKED_ACCESS"},
        ]
        summary = module.summarize(rows)
        keyed = {(row["sheet"], row["availability"]): row["records"] for row in summary}
        self.assertEqual(2, keyed[("Table S8", "VERIFIED")])
        self.assertEqual(1, keyed[("Table S8", "BLOCKED_ACCESS")])


if __name__ == "__main__":
    unittest.main()
