#!/usr/bin/env python3
import csv
import gzip
import importlib.util
import io
from pathlib import Path
import tarfile
import tempfile
import unittest
import zipfile

import h5py


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "reproduction/spatialecotyper/scripts/index_paper_archives.py"


def load_module():
    if not SCRIPT.is_file():
        raise AssertionError(f"missing archive indexer: {SCRIPT}")
    spec = importlib.util.spec_from_file_location("index_paper_archives", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def add_tar_member(archive, name, payload):
    info = tarfile.TarInfo(name)
    info.size = len(payload)
    archive.addfile(info, io.BytesIO(payload))


class PaperArchiveIndexTest(unittest.TestCase):
    def make_fixture(self, root):
        raw = root / "raw"
        raw.mkdir(parents=True)
        tar_path = raw / "sample.tar"
        with tarfile.open(tar_path, "w") as archive:
            add_tar_member(archive, "matrix.mtx", b"matrix")
            add_tar_member(archive, "spatial/tissue_positions.csv", b"coords")
        tgz_path = raw / "sample.tar.gz"
        with tarfile.open(tgz_path, "w:gz") as archive:
            add_tar_member(archive, "features.tsv", b"features")
            add_tar_member(archive, "barcodes.tsv", b"barcodes")
        zip_path = raw / "sample.zip"
        with zipfile.ZipFile(zip_path, "w") as archive:
            archive.writestr("metadata.tsv", "sample\tgroup\n")
            archive.writestr("image.png", b"png")
        gzip_path = raw / "counts.tsv.gz"
        with gzip.open(gzip_path, "wb") as handle:
            handle.write(b"gene\tcell\n")
        h5_path = raw / "matrix.h5"
        with h5py.File(h5_path, "w") as handle:
            matrix = handle.create_group("matrix")
            matrix.create_dataset("data", data=[1, 2, 3])
            matrix.create_dataset("barcodes", data=[b"A", b"B"])
        plain_path = raw / "model.rds"
        plain_path.write_bytes(b"model")
        return [tar_path, tgz_path, zip_path, gzip_path, h5_path, plain_path]

    def test_inspects_supported_containers_without_extracting(self):
        module = load_module()
        self.assertEqual(
            module.classify_content_role(
                "filtered_feature_bc_matrix/matrix.mtx.gz"
            ),
            "expression",
        )
        self.assertEqual(
            module.classify_content_role("GSM4453576_P1_exp.txt.gz"),
            "expression",
        )
        self.assertEqual(
            module.classify_content_role("GSM3036911_PDAC-A-ST1-HE.jpg.gz"),
            "image",
        )
        for table_name in (
            "prostate-twelve/P3.2.tsv",
            "GSM4416534_PT-3232.csv.gz",
            "GSE72056_melanoma_single_cell_revised_v2.txt",
            "GSE91061_BMS038109Sample.hg19KnownGene.fpkm.csv",
        ):
            self.assertEqual(
                module.classify_content_role(table_name), "expression", table_name
            )
        self.assertEqual(
            module.classify_content_role(
                "GSE91061_BMS038109Sample_Cytolytic_Score_20161026.txt"
            ),
            "other",
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = self.make_fixture(root)
            before = sorted(path.relative_to(root) for path in root.rglob("*") if path.is_file())
            rows = [row for path in paths for row in module.inspect_container(path)]
            after = sorted(path.relative_to(root) for path in root.rglob("*") if path.is_file())
            self.assertEqual(before, after)
            by_member = {row["member_path"]: row for row in rows}
            self.assertEqual(by_member["matrix.mtx"]["content_role"], "expression")
            self.assertEqual(
                by_member["spatial/tissue_positions.csv"]["content_role"],
                "coordinate",
            )
            self.assertEqual(by_member["features.tsv"]["content_role"], "feature")
            self.assertEqual(by_member["barcodes.tsv"]["content_role"], "barcode")
            self.assertEqual(by_member["metadata.tsv"]["content_role"], "metadata")
            self.assertEqual(by_member["image.png"]["content_role"], "image")
            self.assertEqual(by_member["model.rds"]["content_role"], "model")
            self.assertTrue(all(row["inspection_status"] == "PASS" for row in rows))

    def test_build_index_requires_matching_pass_validation(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = self.make_fixture(root)
            manifests = root / "archive/manifests"
            results = root / "results/reproducibility"
            manifests.mkdir(parents=True)
            results.mkdir(parents=True)
            manifest_fields = ["source_record_id", "local_path", "actual_bytes", "sha256"]
            with (manifests / "paper-file-sha256.tsv").open(
                "w", newline="", encoding="utf-8"
            ) as handle:
                writer = csv.DictWriter(handle, fieldnames=manifest_fields, delimiter="\t")
                writer.writeheader()
                for index, path in enumerate(paths):
                    writer.writerow(
                        {
                            "source_record_id": f"R{index}",
                            "local_path": str(path),
                            "actual_bytes": path.stat().st_size,
                            "sha256": "fixture",
                        }
                    )
            validation_fields = ["local_path", "validation_status"]
            with (results / "paper-file-validation.tsv").open(
                "w", newline="", encoding="utf-8"
            ) as handle:
                writer = csv.DictWriter(handle, fieldnames=validation_fields, delimiter="\t")
                writer.writeheader()
                for path in paths:
                    writer.writerow({"local_path": str(path), "validation_status": "PASS"})
            members, summaries = module.build_index(root, expected_count=len(paths))
            self.assertEqual(len(summaries), len(paths))
            self.assertGreater(len(members), len(paths))

            raw_hidden = root / "raw-hidden"
            (root / "raw").replace(raw_hidden)
            reclassified_members, reclassified_summaries = module.reclassify_existing(
                root, expected_count=len(paths)
            )
            self.assertEqual(len(reclassified_members), len(members))
            self.assertEqual(len(reclassified_summaries), len(summaries))
            raw_hidden.replace(root / "raw")

            with (results / "paper-file-validation.tsv").open(
                newline="", encoding="utf-8"
            ) as handle:
                rows = list(csv.DictReader(handle, delimiter="\t"))
            rows[-1]["validation_status"] = "FAIL"
            with (results / "paper-file-validation.tsv").open(
                "w", newline="", encoding="utf-8"
            ) as handle:
                writer = csv.DictWriter(handle, fieldnames=validation_fields, delimiter="\t")
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaisesRegex(ValueError, "not validated PASS"):
                module.build_index(root, expected_count=len(paths))


if __name__ == "__main__":
    unittest.main()
