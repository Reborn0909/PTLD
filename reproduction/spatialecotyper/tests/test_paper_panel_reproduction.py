#!/usr/bin/env python3
import csv
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "reproduction/spatialecotyper/scripts/audit_paper_panels.py"
CONFIG = REPO_ROOT / "reproduction/spatialecotyper/config/paper-panel-reproduction.tsv"
DATA_ROOT = Path(os.environ.get("SPATIALECOTYPER_ROOT", "/mnt/f/spatialecotyper_reproduction"))
ALLOWED = {
    "STRICT_PASS",
    "OFFICIAL_API_PASS",
    "TUTORIAL_REPRODUCED",
    "METHOD_ONLY",
    "METHOD_GAP",
    "BLOCKED_ACCESS",
    "BLOCKED_CODE",
}


def load_module():
    if not SCRIPT.is_file():
        raise AssertionError(f"missing panel audit script: {SCRIPT}")
    if not CONFIG.is_file():
        raise AssertionError(f"missing panel audit config: {CONFIG}")
    spec = importlib.util.spec_from_file_location("audit_paper_panels", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class PaperPanelReproductionTest(unittest.TestCase):
    def test_audit_covers_every_panel_once_with_valid_evidence(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "paper-panel-audit.tsv"
            rows = module.build_panel_audit(DATA_ROOT, CONFIG, output)
            with (
                DATA_ROOT / "archive/manifests/paper-panels.tsv"
            ).open(newline="", encoding="utf-8") as handle:
                panels = list(csv.DictReader(handle, delimiter="\t"))
            self.assertEqual(len(rows), len(panels))
            self.assertEqual(len(rows), 151)
            self.assertEqual(
                {row["panel_id"] for row in rows},
                {row["panel_id"] for row in panels},
            )
            self.assertEqual(len(rows), len({row["panel_id"] for row in rows}))
            self.assertTrue(all(row["status"] in ALLOWED for row in rows))
            self.assertTrue(all(row["expected_output"] for row in rows))
            self.assertTrue(all(row["limitation"] for row in rows))

    def test_liquid_panels_remain_code_blocked_and_spatial_panels_are_not_strict(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            rows = module.build_panel_audit(DATA_ROOT, CONFIG, Path(tmp) / "audit.tsv")
            by_id = {row["panel_id"]: row for row in rows}
            for panel_id in (
                "MAIN-4:a",
                "MAIN-5:a",
                "EXTENDED-10:a",
                "EXTENDED-11:a",
                "EXTENDED-12:a",
                "SUPPLEMENTARY-7:whole",
                "SUPPLEMENTARY-8:whole",
                "SUPPLEMENTARY-9:a",
            ):
                self.assertEqual(by_id[panel_id]["status"], "BLOCKED_CODE", panel_id)
            for panel_id in ("MAIN-2:a", "MAIN-3:b", "EXTENDED-8:i"):
                self.assertEqual(by_id[panel_id]["status"], "METHOD_ONLY", panel_id)
            self.assertFalse(any(row["status"] == "STRICT_PASS" for row in rows))

    def test_strict_status_requires_callable_entrypoint_and_observed_output(self):
        module = load_module()
        invalid = {
            "panel_id": "MAIN-1:a",
            "status": "STRICT_PASS",
            "official_entrypoint": "",
            "observed_output": "",
        }
        with self.assertRaisesRegex(ValueError, "STRICT_PASS"):
            module.validate_audit_row(invalid)


if __name__ == "__main__":
    unittest.main()
