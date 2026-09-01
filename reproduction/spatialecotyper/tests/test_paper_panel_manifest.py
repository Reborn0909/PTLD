#!/usr/bin/env python3
import csv
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "reproduction/spatialecotyper/scripts/extract_paper_panels.py"
DATA_ROOT = Path(os.environ.get("SPATIALECOTYPER_ROOT", "/mnt/f/spatialecotyper_reproduction"))


def load_module():
    if not SCRIPT.is_file():
        raise AssertionError(f"missing panel extractor: {SCRIPT}")
    spec = importlib.util.spec_from_file_location("extract_paper_panels", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class PaperPanelManifestTest(unittest.TestCase):
    def test_extracts_all_official_figure_families_and_panels(self):
        module = load_module()
        html_path = DATA_ROOT / "archive/paper/nature-article.html"
        supplement_path = (
            DATA_ROOT / "archive/paper/41586_2026_10452_MOESM1_ESM.pdf"
        )
        figures = module.extract_html_figures(html_path)
        figures.extend(module.extract_supplementary_figures(supplement_path))
        panels = module.extract_panels(figures)

        counts = {}
        for row in figures:
            counts[row["figure_family"]] = counts.get(row["figure_family"], 0) + 1
        self.assertEqual(
            counts, {"MAIN": 5, "EXTENDED": 12, "SUPPLEMENTARY": 9}
        )
        self.assertEqual(len({row["figure_id"] for row in figures}), 26)
        self.assertTrue(all(row["figure_id"] and row["caption"] for row in figures))
        self.assertTrue(all(row["panel_id"] and row["panel_text"] for row in panels))
        self.assertEqual(
            {row["figure_id"] for row in panels},
            {row["figure_id"] for row in figures},
        )
        main_one_labels = [
            row["panel_label"] for row in panels if row["figure_id"] == "MAIN-1"
        ]
        self.assertEqual(main_one_labels, ["a", "b", "c", "d"])
        for figure_id in {row["figure_id"] for row in panels}:
            labels = [
                row["panel_label"] for row in panels if row["figure_id"] == figure_id
            ]
            self.assertEqual(len(labels), len(set(labels)), figure_id)

    def test_writes_stable_tsv_manifests(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paper = root / "archive/paper"
            paper.mkdir(parents=True)
            source_paper = DATA_ROOT / "archive/paper"
            (paper / "nature-article.html").write_bytes(
                (source_paper / "nature-article.html").read_bytes()
            )
            (paper / "41586_2026_10452_MOESM1_ESM.pdf").write_bytes(
                (source_paper / "41586_2026_10452_MOESM1_ESM.pdf").read_bytes()
            )
            module.build_manifests(root)
            figure_path = root / "archive/manifests/paper-figures.tsv"
            panel_path = root / "archive/manifests/paper-panels.tsv"
            with figure_path.open(newline="", encoding="utf-8") as handle:
                figures = list(csv.DictReader(handle, delimiter="\t"))
            with panel_path.open(newline="", encoding="utf-8") as handle:
                panels = list(csv.DictReader(handle, delimiter="\t"))
            self.assertEqual(len(figures), 26)
            self.assertGreater(len(panels), 26)
            self.assertEqual(
                [row["figure_id"] for row in figures[:5]],
                [f"MAIN-{number}" for number in range(1, 6)],
            )


if __name__ == "__main__":
    unittest.main()
