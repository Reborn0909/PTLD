#!/usr/bin/env python3
import importlib.util
import json
from http.client import RemoteDisconnected
from pathlib import Path
import unittest
from unittest.mock import patch


REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / "reproduction/spatialecotyper/scripts/resolve_paper_downloads.py"
TENX_MAP = REPO / "reproduction/spatialecotyper/config/tenx-paper-samples.tsv"


def load_module():
    if not SCRIPT.is_file():
        raise AssertionError(f"missing resolver: {SCRIPT}")
    spec = importlib.util.spec_from_file_location("resolve_paper_downloads", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PaperDownloadResolutionTest(unittest.TestCase):
    def test_http_bytes_retries_remote_disconnect(self):
        module = load_module()

        class Response:
            headers = {}
            status = 200

            def read(self):
                return b"ok"

            def geturl(self):
                return "https://example.org/final"

        with patch.object(
            module,
            "urlopen",
            side_effect=[RemoteDisconnected("transient"), Response()],
        ) as mocked:
            payload, _, status, final_url = module.http_bytes(
                "https://example.org/data", attempts=2
            )
        self.assertEqual(b"ok", payload)
        self.assertEqual(200, status)
        self.assertEqual("https://example.org/final", final_url)
        self.assertEqual(2, mocked.call_count)

    def test_geo_index_parser_returns_only_files(self):
        module = load_module()
        html = '''<a href="../">Parent</a>
        <a href="GSE1_RAW.tar">GSE1_RAW.tar</a>
        <a href="matrix.h5ad.gz">matrix.h5ad.gz</a>
        <a href="filelist.txt">filelist.txt</a>
        <a href="https://www.hhs.gov/vulnerability-disclosure-policy/index.html">HHS</a>'''
        files = module.parse_apache_index(html, "https://ftp.ncbi.nlm.nih.gov/test/")
        self.assertEqual(["GSE1_RAW.tar", "matrix.h5ad.gz"], [row["file_name"] for row in files])

    def test_zenodo_parser_preserves_size_checksum_and_url(self):
        module = load_module()
        payload = {
            "metadata": {"access_right": "open", "license": {"id": "cc-by-4.0"}},
            "files": [{"key": "counts.tar.gz", "size": 123, "checksum": "md5:abc",
                       "links": {"self": "https://zenodo.org/api/records/1/files/counts/content"}}],
        }
        files, metadata = module.parse_zenodo_record(json.dumps(payload).encode())
        self.assertEqual(123, files[0]["size_bytes"])
        self.assertEqual("md5", files[0]["checksum_type"])
        self.assertEqual("abc", files[0]["checksum"])
        self.assertEqual("cc-by-4.0", metadata["license"])

    def test_geo_filelist_parser_returns_exact_archive_size(self):
        module = load_module()
        payload = b"#Archive/File\tName\tTime\tSize\tType\nArchive\tGSE1_RAW.tar\t01/01/2020 00:00:00\t71618560\tTAR\n"
        self.assertEqual({"GSE1_RAW.tar": 71618560}, module.parse_geo_filelist(payload))

    def test_content_range_parser_returns_total_bytes(self):
        module = load_module()
        self.assertEqual(987654321, module.content_range_total("bytes 0-0/987654321"))
        self.assertEqual(0, module.content_range_total(""))

    def test_s3_etag_classification_identifies_8m_multipart_checksum(self):
        module = load_module()
        checksum_type, checksum = module.classify_s3_etag(
            15886623172, '"1004f1244bd469bfa13f97bb7de15d07-1894"'
        )
        self.assertEqual("s3_multipart_etag_8m", checksum_type)
        self.assertEqual("1004f1244bd469bfa13f97bb7de15d07-1894", checksum)
        self.assertEqual(
            ("md5", "0123456789abcdef0123456789abcdef"),
            module.classify_s3_etag(100, '"0123456789abcdef0123456789abcdef"'),
        )

    def test_capacity_total_deduplicates_download_urls(self):
        module = load_module()
        rows = [
            {"source_record_id": "A", "download_url": "https://example.org/a", "size_bytes": 10},
            {"source_record_id": "A", "download_url": "https://example.org/a", "size_bytes": 10},
            {"source_record_id": "B", "download_url": "https://example.org/b", "size_bytes": 20},
        ]
        self.assertEqual(30, module.deduplicated_known_bytes(rows))
        self.assertEqual(20, module.actionable_known_bytes(rows, {"A"}))

    def test_ena_report_parser_expands_paired_fastq_files(self):
        module = load_module()
        payload = ("run_accession\tfastq_ftp\tfastq_bytes\tfastq_md5\n"
                   "ERR1\tftp.sra.ebi.ac.uk/a_1.fastq.gz;ftp.sra.ebi.ac.uk/a_2.fastq.gz\t10;20\taa;bb\n")
        files = module.parse_ena_report(payload.encode())
        self.assertEqual(2, len(files))
        self.assertEqual(30, sum(row["size_bytes"] for row in files))
        self.assertEqual("https://ftp.sra.ebi.ac.uk/a_1.fastq.gz", files[0]["download_url"])
        self.assertEqual("aa", files[0]["checksum"])

    def test_access_classification_is_explicit(self):
        module = load_module()
        self.assertEqual("CONTROLLED_DUA", module.classify_record({"accession": "HRA000437", "data_url": "", "dataset_name": ""})[0])
        self.assertEqual("REGISTRATION_REQUIRED", module.classify_record({"accession": "", "data_url": "https://data.mendeley.com/datasets/x/1", "dataset_name": ""})[0])
        self.assertEqual("PUBLIC_API", module.classify_record({"accession": "GSE171351", "data_url": "", "dataset_name": ""})[0])

    def test_tenx_map_contains_all_included_single_cell_scale_samples(self):
        module = load_module()
        rows = module.load_tenx_map(TENX_MAP)
        self.assertEqual(12, len(rows))
        self.assertEqual(5, sum(row["platform"] == "Xenium V1" for row in rows))
        self.assertEqual(4, sum(row["platform"] == "Xenium V3 Prime" for row in rows))
        self.assertEqual(3, sum(row["platform"] == "Visium HD" for row in rows))
        self.assertEqual(12, len({row["paper_sample_id"] for row in rows}))
        breast = next(row for row in rows if row["paper_sample_id"] == "Visium_HD_FF_Human_Breast_Cancer")
        url = module.tenx_url(breast, "binned_outputs.tar.gz")
        self.assertEqual(
            "https://cf.10xgenomics.com/samples/spatial-exp/3.1.2/Visium_HD_FF_Human_Breast_Cancer/Visium_HD_FF_Human_Breast_Cancer_binned_outputs.tar.gz",
            url,
        )


if __name__ == "__main__":
    unittest.main()
