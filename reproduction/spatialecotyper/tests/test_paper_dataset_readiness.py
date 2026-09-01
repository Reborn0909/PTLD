#!/usr/bin/env python3
import csv
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = (
    REPO_ROOT
    / "reproduction/spatialecotyper/scripts/classify_paper_dataset_readiness.py"
)
DATA_ROOT = Path(os.environ.get("SPATIALECOTYPER_ROOT", "/mnt/f/spatialecotyper_reproduction"))


def load_module():
    if not SCRIPT.is_file():
        raise AssertionError(f"missing dataset readiness classifier: {SCRIPT}")
    spec = importlib.util.spec_from_file_location("classify_paper_dataset_readiness", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class PaperDatasetReadinessTest(unittest.TestCase):
    def test_classifies_every_allowed_boundary_conservatively(self):
        module = load_module()
        base = {
            "source_record_id": "R1",
            "section": "public_spatial",
            "modality": "spatial_transcriptomics",
            "platform": "10x Visium",
            "data_url": "https://example.test/data",
        }
        cases = [
            (
                {**base, "source_record_id": "GENERATED-GSE320042", "section": "generated_in_this_work"},
                None,
                {"access_status": "PUBLIC_API", "reason": "GEO"},
                {"expression", "coordinate", "metadata"},
                "READY_OFFICIAL_PROCESSED",
            ),
            (base, {"availability": "VERIFIED", "reason": "files verified"}, {"access_status": "PUBLIC_API", "reason": "GEO"}, {"expression", "coordinate"}, "READY_RAW_ONLY"),
            (base, {"availability": "VERIFIED", "reason": "images only"}, {"access_status": "PUBLIC_API", "reason": "Zenodo"}, {"image"}, "PARTIAL_FILES"),
            (base, {"availability": "PAUSED_CAPACITY", "reason": "over 100 GB"}, {"access_status": "PUBLIC_API", "reason": "ENA"}, set(), "PAUSED_CAPACITY"),
            (base, {"availability": "BLOCKED_ACCESS", "reason": "DUA required"}, {"access_status": "CONTROLLED_DUA", "reason": "DUA required"}, set(), "BLOCKED_ACCESS"),
            (base, {"availability": "BLOCKED_NOT_PUBLIC", "reason": "no accession"}, {"access_status": "NOT_PUBLIC", "reason": "no accession"}, set(), "BLOCKED_NOT_PUBLIC"),
            (base, None, None, set(), "METHOD_GAP"),
        ]
        observed = []
        for record, availability, access, roles, expected in cases:
            row = module.classify_readiness(record, availability, access, roles)
            observed.append(row["readiness_class"])
            self.assertEqual(row["readiness_class"], expected)
            if not expected.startswith("READY_"):
                self.assertTrue(row["blocking_evidence"])
        self.assertEqual(set(observed), module.ALLOWED_CLASSES)

    def test_controlled_or_registered_data_never_becomes_ready_without_verified_files(self):
        module = load_module()
        record = {
            "source_record_id": "R2",
            "section": "public_spatial",
            "modality": "spatial_transcriptomics",
            "platform": "Visium",
            "data_url": "https://example.test/controlled",
        }
        for access_status in ("CONTROLLED_DUA", "REGISTRATION_REQUIRED"):
            row = module.classify_readiness(
                record,
                {"availability": "BLOCKED_ACCESS", "reason": "authorization required"},
                {"access_status": access_status, "reason": "authorization required"},
                {"expression", "coordinate", "metadata"},
            )
            self.assertEqual(row["readiness_class"], "BLOCKED_ACCESS")

    def test_real_manifest_conserves_all_canonical_dataset_records(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "readiness.tsv"
            rows = module.build_readiness(DATA_ROOT, output)
            with (
                DATA_ROOT / "archive/manifests/paper-datasets.tsv"
            ).open(newline="", encoding="utf-8") as handle:
                datasets = list(csv.DictReader(handle, delimiter="\t"))
            self.assertEqual(len(rows), len(datasets))
            self.assertEqual(
                {row["source_record_id"] for row in rows},
                {row["source_record_id"] for row in datasets},
            )
            self.assertEqual(len(rows), len({row["source_record_id"] for row in rows}))
            self.assertTrue(all(row["readiness_class"] in module.ALLOWED_CLASSES for row in rows))
            by_id = {row["source_record_id"]: row for row in rows}
            for shared_source_id in ("TableS2-R7", "TableS2-R8", "TableS2-R9", "TableS2-R16"):
                self.assertEqual(
                    by_id[shared_source_id]["readiness_class"],
                    "READY_RAW_ONLY",
                    shared_source_id,
                )
                self.assertGreater(
                    int(by_id[shared_source_id]["verified_container_count"]),
                    0,
                    shared_source_id,
                )


if __name__ == "__main__":
    unittest.main()
