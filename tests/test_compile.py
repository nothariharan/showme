"""Batch 2: compile writes an Agent Skills directory and nothing else."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
sys.path.insert(0, str(ROOT / "src"))

from showme.compile import compile_path  # noqa: E402


class CompileTests(unittest.TestCase):
    def test_sort_skill_matches_agent_skills_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            skill = compile_path(EXAMPLES / "sort-downloads" / "demonstration.json", out)
            text = (skill / "SKILL.md").read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\nname: sort-downloads\n"))
            self.assertIn("Sort loose files out of a downloads folder", text)
            trace = json.loads((skill / "references" / "trace.json").read_text(encoding="utf-8"))
            self.assertEqual(trace["name"], "sort-downloads")
            self.assertTrue(all(step["executor"] == "local" for step in trace["steps"]))
            self.assertTrue((skill / "scripts" / "replay.py").is_file())

    def test_compile_refuses_to_replace_an_existing_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            compile_path(EXAMPLES / "sort-downloads" / "demonstration.json", out)
            with self.assertRaises(FileExistsError):
                compile_path(EXAMPLES / "sort-downloads" / "demonstration.json", out)

    def test_portal_skill_marks_agent_steps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill = compile_path(EXAMPLES / "export-customer-pdf" / "demonstration.json", Path(tmp))
            text = (skill / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("Perform every step marked `agent`", text)
            trace = json.loads((skill / "references" / "trace.json").read_text(encoding="utf-8"))
            self.assertTrue(all(step["executor"] == "agent" for step in trace["steps"]))


if __name__ == "__main__":
    unittest.main()
