#!/usr/bin/env python3
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / "reproduction/spatialecotyper/scripts/validate_paper_files.py"


def load_module():
    if not SCRIPT.is_file():
        raise AssertionError(f"missing file validator: {SCRIPT}")
    spec = importlib.util.spec_from_file_location("validate_paper_files", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PaperFileValidationTest(unittest.TestCase):
    def test_s3_multipart_etag_uses_binary_md5_digest_concatenation(self):
        module = load_module()
        payload = b"abcdefghijklmnopqrst"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.bin"
            path.write_bytes(payload)
            digests = [hashlib.md5(payload[i:i + 8]).digest() for i in range(0, len(payload), 8)]
            expected = hashlib.md5(b"".join(digests)).hexdigest() + "-3"
            self.assertEqual(expected, module.s3_multipart_etag(path, chunk_size=8))

    def test_json_and_manifest_checks_are_verified(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "experiment.xenium"
            path.write_text(json.dumps({"major_version": 1}), encoding="utf-8")
            sha = hashlib.sha256(path.read_bytes()).hexdigest()
            result = module.validate_file({
                "local_path": str(path), "expected_bytes": str(path.stat().st_size),
                "sha256": sha, "expected_checksum": "", "checksum_type": "",
            })
            self.assertEqual("PASS", result["validation_status"])
            self.assertEqual("json", result["format_check"])


if __name__ == "__main__":
    unittest.main()
