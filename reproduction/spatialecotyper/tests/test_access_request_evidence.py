#!/usr/bin/env python3
import csv
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "reproduction/spatialecotyper/scripts/write_access_request_evidence.py"
DATA_ROOT = Path(os.environ.get("SPATIALECOTYPER_ROOT", "/mnt/f/spatialecotyper_reproduction"))


def load_module():
    if not SCRIPT.is_file():
        raise AssertionError(f"missing request evidence writer: {SCRIPT}")
    spec = importlib.util.spec_from_file_location("write_access_request_evidence", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class AccessRequestEvidenceTest(unittest.TestCase):
    def test_request_package_is_complete_and_does_not_invent_contacts(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "checklist.md"
            evidence = Path(tmp) / "evidence.tsv"
            rows = module.write_request_evidence(DATA_ROOT, output, evidence)
            self.assertEqual(
                {row["request_type"] for row in rows},
                {
                    "STANFORD_NORMALIZED_DATA",
                    "CYTOSPACE_WEIGHTS",
                    "LIQUID_ECOTYPER_CODE_WEIGHTS",
                    "FIGURE_SCRIPTS",
                },
            )
            self.assertTrue(all(row["blocked_panel_ids"] for row in rows))
            self.assertTrue(all(row["official_evidence"] for row in rows))
            self.assertTrue(all("@" not in row["recipient"] for row in rows))
            self.assertTrue(output.is_file())
            text = output.read_text(encoding="utf-8")
            self.assertIn("不会自动发送", text)
            self.assertIn("not sent automatically", text)
            with evidence.open(newline="", encoding="utf-8") as handle:
                persisted = list(csv.DictReader(handle, delimiter="\t"))
            self.assertEqual(len(persisted), 4)

    def test_controlled_rows_are_not_relabelled(self):
        module = load_module()
        ledger = module.read_tsv(DATA_ROOT / "archive/manifests/paper-access-ledger.tsv")
        protected = [
            row for row in ledger
            if row["access_status"] in {"CONTROLLED_DUA", "REGISTRATION_REQUIRED"}
        ]
        self.assertTrue(protected)
        self.assertTrue(all(int(row["resolved_file_count"]) == 0 for row in protected))


if __name__ == "__main__":
    unittest.main()
