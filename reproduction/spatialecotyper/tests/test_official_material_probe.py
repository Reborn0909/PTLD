#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "reproduction/spatialecotyper/scripts/probe_official_material_updates.py"


def load_module():
    if not SCRIPT.is_file():
        raise AssertionError(f"missing official material probe: {SCRIPT}")
    spec = importlib.util.spec_from_file_location("official_material_probe", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class OfficialMaterialProbeTest(unittest.TestCase):
    def test_snapshots_are_idempotent_but_new_commit_is_preserved(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "snapshots.tsv"
            first = module.make_observation(
                endpoint_id="github_repository",
                url="https://api.github.com/repos/digitalcytometry/spatialecotyper",
                http_status=200,
                revision="abc",
                etag='"one"',
                artifact_type="SOURCE_REPOSITORY",
                access_status="PUBLIC",
                detail="fixture",
                observed_utc="2026-09-01T00:00:00Z",
            )
            self.assertTrue(module.append_snapshot(path, first))
            self.assertFalse(module.append_snapshot(path, first))
            second = dict(first, revision="def", observed_utc="2026-09-02T00:00:00Z")
            second["observation_id"] = module.observation_id(second)
            self.assertTrue(module.append_snapshot(path, second))
            rows = module.read_tsv(path)
            self.assertEqual([row["revision"] for row in rows], ["abc", "def"])

    def test_login_content_remains_registration_required(self):
        module = load_module()
        status = module.classify_access(
            200,
            "Sign in to access and download Stanford Digital Repository files",
            "https://purl.stanford.edu/pm3t-cn37",
        )
        self.assertEqual(status, "REGISTRATION_REQUIRED")

    def test_tree_candidates_do_not_silently_unblock(self):
        module = load_module()
        paths = ["R/SpatialEcoTyper.R", "vignettes/SpatialEcoTyper.Rmd"]
        report = module.detect_candidate_unblockers(paths)
        self.assertFalse(any(row["candidate_found"] == "TRUE" for row in report))
        paths.append("models/liquid_ecotyper/checkpoint.pt")
        report = module.detect_candidate_unblockers(paths)
        liquid = next(row for row in report if row["component"] == "LIQUID_ECOTYPER")
        self.assertEqual(liquid["candidate_found"], "TRUE")
        self.assertEqual(liquid["status"], "CANDIDATE_REQUIRES_ARCHIVE_VALIDATION")


if __name__ == "__main__":
    unittest.main()
