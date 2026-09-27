"""Batch 1: a demonstration is rejected before a skill is written."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from showme.model import DemoError, parse_demonstration  # noqa: E402


def _demo(**overrides: object) -> dict:
    data: dict = {
        "name": "tidy-desk",
        "description": "Tidy a folder when the user asks.",
        "explanation": "Shown once.",
        "success": "The folder matches the rule.",
        "parameters": [{"name": "source_dir", "description": "Folder", "example": "inbox"}],
        "steps": [
            {
                "id": "make",
                "action": "ensure_dir",
                "path": "{source_dir}/Kept",
                "narration": "Kept is the destination.",
            }
        ],
    }
    data.update(overrides)
    return data


class ModelTests(unittest.TestCase):
    def test_valid_demo_parses(self) -> None:
        demo = parse_demonstration(_demo())
        self.assertEqual(demo.name, "tidy-desk")
        self.assertEqual(demo.steps[0].executor, "local")

    def test_skill_name_must_match_agent_skills_rules(self) -> None:
        with self.assertRaises(DemoError):
            parse_demonstration(_demo(name="Tidy Desk"))

    def test_unknown_placeholder_is_rejected(self) -> None:
        steps = [
            {
                "id": "move",
                "action": "ensure_dir",
                "path": "{missing}",
                "narration": "Make the folder.",
            }
        ]
        with self.assertRaises(DemoError) as caught:
            parse_demonstration(_demo(parameters=[], steps=steps))
        self.assertTrue(any("missing" in error for error in caught.exception.errors))

    def test_duplicate_parameter_is_rejected(self) -> None:
        parameters = [
            {"name": "source_dir", "description": "Folder", "example": "a"},
            {"name": "source_dir", "description": "Again", "example": "b"},
        ]
        with self.assertRaises(DemoError) as caught:
            parse_demonstration(_demo(parameters=parameters))
        self.assertTrue(any("duplicate" in error for error in caught.exception.errors))

    def test_empty_steps_are_rejected(self) -> None:
        with self.assertRaises(DemoError):
            parse_demonstration(_demo(steps=[]))


if __name__ == "__main__":
    unittest.main()
