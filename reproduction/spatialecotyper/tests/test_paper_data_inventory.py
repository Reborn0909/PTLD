#!/usr/bin/env python3
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / "reproduction/spatialecotyper/scripts/write_paper_data_inventory.py"


class PaperDataInventoryTest(unittest.TestCase):
    def test_reports_verified_and_blocked_materials(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifests = root / "archive/manifests"
            results = root / "results/reproducibility"
            manifests.mkdir(parents=True)
            results.mkdir(parents=True)
            (manifests / "paper-downloads.tsv").write_text(
                "source_record_id\taccession\trepository\tfile_name\tdownload_url\t"
                "size_bytes\tchecksum_type\tchecksum\tlicense\taccess_status\tresolver_note\n"
                "A\tGSE1\tNCBI_GEO\ta.tar\thttps://example/a\t10\tmd5\tabc\t\tPUBLIC_API\tok\n",
                encoding="utf-8",
            )
            (results / "paper-download-capacity.tsv").write_text(
                "source_record_id\taccession\taccess_status\tresolved_file_count\tknown_bytes\t"
                "unknown_size_files\tsource_gate\tfree_bytes\tknown_total_bytes\t"
                "actionable_total_bytes\tglobal_gate\treason\n"
                "A\tGSE1\tPUBLIC_API\t1\t10\t0\tPASS\t1000\t210\t10\tPASS\tok\n"
                "B\tPRJ1\tPUBLIC_API\t1\t200\t0\tPAUSE_OVER_100GB\t1000\t210\t10\tPASS\tlarge\n"
                "C\tHRA1\tCONTROLLED_DUA\t0\t0\t0\tPASS\t1000\t210\t10\tPASS\tcontrolled\n",
                encoding="utf-8",
            )
            (manifests / "paper-file-sha256.tsv").write_text(
                "source_record_id\taccession\trepository\tfile_name\tdownload_url\t"
                "expected_bytes\tactual_bytes\texpected_checksum\tchecksum_type\tsha256\t"
                "local_path\tstatus\tdownloaded_utc\n"
                "A\tGSE1\tNCBI_GEO\ta.tar\thttps://example/a\t10\t10\tabc\tmd5\tdef\t"
                "/tmp/a.tar\tDOWNLOADED_VERIFIED\t2026-01-01T00:00:00Z\n",
                encoding="utf-8",
            )
            (results / "paper-file-validation.tsv").write_text(
                "source_record_id\tvalidation_status\nA\tPASS\n", encoding="utf-8"
            )
            output = root / "inventory.md"
            subprocess.run(
                ["python3", str(SCRIPT), "--root", str(root), "--output", str(output)],
                check=True,
            )
            text = output.read_text(encoding="utf-8")
            self.assertIn("1 个文件", text)
            self.assertIn("10 字节", text)
            self.assertIn("PAUSE_OVER_100GB", text)
            self.assertIn("CONTROLLED_DUA", text)
            self.assertIn("1/1", text)


if __name__ == "__main__":
    unittest.main()
