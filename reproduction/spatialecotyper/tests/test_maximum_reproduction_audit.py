#!/usr/bin/env python3
import csv
import hashlib
import os
from pathlib import Path
import re
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = Path(os.environ.get("SPATIALECOTYPER_ROOT", "/mnt/f/spatialecotyper_reproduction"))


def read_tsv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


class MaximumReproductionAuditTest(unittest.TestCase):
    def test_all_second_stage_outputs_obey_their_contracts(self):
        manifests = DATA_ROOT / "archive/manifests"
        results = DATA_ROOT / "results/reproducibility"
        figures = read_tsv(manifests / "paper-figures.tsv")
        panels = read_tsv(manifests / "paper-panels.tsv")
        containers = read_tsv(results / "paper-container-summary.tsv")
        readiness = read_tsv(results / "paper-dataset-readiness.tsv")
        panel_audit = read_tsv(results / "paper-panel-audit.tsv")
        gate = read_tsv(
            DATA_ROOT / "results/paper_reproduction/ready_analyses/execution-gate.tsv"
        )
        summary = read_tsv(
            DATA_ROOT / "results/paper_reproduction/ready_analyses/execution-summary.tsv"
        )
        updates = read_tsv(results / "official-material-update-report.tsv")
        requests = read_tsv(results / "access-request-evidence.tsv")

        self.assertEqual(len(figures), 26)
        self.assertEqual(len(panels), 151)
        self.assertEqual(len({row["panel_id"] for row in panels}), 151)
        self.assertEqual(len(containers), 74)
        self.assertTrue(all(row["inspection_status"] == "PASS" for row in containers))
        self.assertEqual(sum(int(row["member_count"]) for row in containers), 1442)

        allowed_readiness = {
            "READY_OFFICIAL_PROCESSED", "READY_RAW_ONLY", "PARTIAL_FILES",
            "PAUSED_CAPACITY", "BLOCKED_ACCESS", "BLOCKED_NOT_PUBLIC", "METHOD_GAP",
        }
        self.assertEqual(len(readiness), 46)
        self.assertTrue(all(row["readiness_class"] in allowed_readiness for row in readiness))

        allowed_panel = {
            "STRICT_PASS", "OFFICIAL_API_PASS", "TUTORIAL_REPRODUCED", "METHOD_ONLY",
            "METHOD_GAP", "BLOCKED_ACCESS", "BLOCKED_CODE",
        }
        self.assertEqual(len(panel_audit), 151)
        self.assertEqual(len({row["panel_id"] for row in panel_audit}), 151)
        self.assertTrue(all(row["status"] in allowed_panel for row in panel_audit))
        self.assertTrue(all(row["expected_output"] and row["limitation"] for row in panel_audit))
        for row in panel_audit:
            if row["status"] == "STRICT_PASS":
                self.assertTrue(row["official_entrypoint"] and row["observed_output"])
                self.assertTrue(all(Path(item).exists() for item in row["observed_output"].split(";") if item))

        self.assertEqual(len(gate), 151)
        self.assertTrue(all(row["eligible"] == "FALSE" for row in gate))
        self.assertEqual(len(summary), 1)
        self.assertEqual(summary[0]["status"], "PASS_NO_ELIGIBLE_PANELS")
        self.assertEqual(summary[0]["panel_rows"], "151")
        self.assertEqual(summary[0]["eligible_rows"], "0")

        self.assertEqual(len(updates), 3)
        self.assertTrue(all(row["candidate_found"] == "FALSE" for row in updates))
        self.assertTrue(all(row["changes_current_blocker"] == "FALSE" for row in updates))
        self.assertEqual(len(requests), 4)
        self.assertTrue(all(row["status"] == "NOT_SENT" for row in requests))
        self.assertTrue(all(row["blocked_panel_ids"] and row["official_evidence"] for row in requests))
        self.assertTrue(all("@" not in row["recipient"] for row in requests))

        report = REPO_ROOT / "docs/reproduction/spatialecotyper-panel-level-reproduction.md"
        text = report.read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r"^### ", text, flags=re.MULTILINE)), 26)

    def test_latest_official_source_archive_matches_snapshot_hash(self):
        snapshots = read_tsv(
            DATA_ROOT / "archive/manifests/official-material-snapshots.tsv"
        )
        archives = [row for row in snapshots if row["artifact_type"] == "SOURCE_ARCHIVE"]
        self.assertTrue(archives)
        row = archives[-1]
        revision = row["revision"]
        archive = DATA_ROOT / "archive/official-updates" / f"spatialecotyper-{revision}.tar.gz"
        self.assertTrue(archive.is_file())
        expected = re.search(r"sha256=([0-9a-f]{64})", row["detail"])
        self.assertIsNotNone(expected)
        self.assertEqual(sha256(archive), expected.group(1))


if __name__ == "__main__":
    unittest.main()
