"""Batch 3: the sort skill repeats a file chore and stops on a collision."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from showme.compile import compile_path  # noqa: E402

EXAMPLE = ROOT / "examples" / "sort-downloads" / "demonstration.json"


class SortReplayTests(unittest.TestCase):
    def test_replay_sorts_matching_files_and_leaves_the_rest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "inbox"
            source.mkdir()
            (source / "acme-invoice.pdf").write_text("bill", encoding="utf-8")
            (source / "lunch-receipt.txt").write_text("meal", encoding="utf-8")
            (source / "screenshot-monday.png").write_text("img", encoding="utf-8")
            (source / "notes.txt").write_text("keep", encoding="utf-8")
            skill = compile_path(EXAMPLE, Path(tmp) / "skills")
            completed = _replay(skill, source)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual((source / "Finance" / "acme-invoice.pdf").read_text(encoding="utf-8"), "bill")
            self.assertEqual((source / "Finance" / "lunch-receipt.txt").read_text(encoding="utf-8"), "meal")
            self.assertEqual((source / "Images" / "screenshot-monday.png").read_text(encoding="utf-8"), "img")
            self.assertEqual((source / "notes.txt").read_text(encoding="utf-8"), "keep")
            self.assertFalse((source / "acme-invoice.pdf").exists())

    def test_replay_refuses_to_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "inbox"
            finance = source / "Finance"
            finance.mkdir(parents=True)
            (source / "acme-invoice.pdf").write_text("new", encoding="utf-8")
            (finance / "acme-invoice.pdf").write_text("old", encoding="utf-8")
            skill = compile_path(EXAMPLE, Path(tmp) / "skills")
            completed = _replay(skill, source)
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("overwrite", completed.stderr)
            self.assertEqual((finance / "acme-invoice.pdf").read_text(encoding="utf-8"), "old")

    def test_second_run_leaves_a_sorted_inbox_alone(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "inbox"
            source.mkdir()
            (source / "ACME-INVOICE.PDF").write_text("bill", encoding="utf-8")
            (source / "notes.txt").write_text("keep", encoding="utf-8")
            (source / "invoice-pile").mkdir()
            (source / "invoice-pile" / "hidden-invoice.txt").write_text("nested", encoding="utf-8")
            skill = compile_path(EXAMPLE, Path(tmp) / "skills")
            first = _replay(skill, source)
            second = _replay(skill, source)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual((source / "Finance" / "ACME-INVOICE.PDF").read_text(encoding="utf-8"), "bill")
            self.assertEqual((source / "notes.txt").read_text(encoding="utf-8"), "keep")
            self.assertEqual((source / "invoice-pile" / "hidden-invoice.txt").read_text(encoding="utf-8"), "nested")
            self.assertFalse((source / "ACME-INVOICE.PDF").exists())


def _replay(skill: Path, source: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(skill / "scripts" / "replay.py"), "--set", f"source_dir={source}"],
        check=False,
        capture_output=True,
        text=True,
    )


if __name__ == "__main__":
    unittest.main()
