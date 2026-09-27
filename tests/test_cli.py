"""Batch 5: the installed commands, not the library, compile and repeat a skill."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
EXAMPLES = ROOT / "examples"
PORTAL_PATH = EXAMPLES / "billing_portal" / "server.py"


def _cli(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "showme", *args],
        cwd=cwd or ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )


def _portal():
    spec = importlib.util.spec_from_file_location("billing_portal_server_cli", PORTAL_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {PORTAL_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CliTests(unittest.TestCase):
    def test_validate_accepts_both_examples(self) -> None:
        sort_result = _cli("validate", "examples/sort-downloads/demonstration.json")
        portal_result = _cli("validate", "examples/export-customer-pdf/demonstration.json")
        self.assertEqual(sort_result.returncode, 0, sort_result.stderr)
        self.assertIn("sort-downloads: 7 steps", sort_result.stdout)
        self.assertEqual(portal_result.returncode, 0, portal_result.stderr)
        self.assertIn("export-customer-pdf: 6 steps", portal_result.stdout)

    def test_validate_rejects_a_missing_file(self) -> None:
        result = _cli("validate", "examples/does-not-exist.json")
        self.assertEqual(result.returncode, 1)
        self.assertTrue(result.stderr.strip())

    def test_cli_compiles_and_runs_the_sort_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "inbox"
            source.mkdir()
            (source / "march-invoice.pdf").write_text("bill", encoding="utf-8")
            (source / "readme.txt").write_text("keep", encoding="utf-8")
            compiled = _cli(
                "compile",
                str(EXAMPLES / "sort-downloads" / "demonstration.json"),
                "--out",
                str(root / "skills"),
            )
            self.assertEqual(compiled.returncode, 0, compiled.stderr)
            skill = root / "skills" / "sort-downloads"
            self.assertTrue((skill / "SKILL.md").is_file())
            ran = _cli("run", str(skill), "--set", f"source_dir={source}")
            self.assertEqual(ran.returncode, 0, ran.stderr)
            self.assertEqual((source / "Finance" / "march-invoice.pdf").read_text(encoding="utf-8"), "bill")
            self.assertEqual((source / "readme.txt").read_text(encoding="utf-8"), "keep")

    def test_run_rejects_an_unknown_parameter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            compiled = _cli(
                "compile",
                str(EXAMPLES / "sort-downloads" / "demonstration.json"),
                "--out",
                str(root / "skills"),
            )
            self.assertEqual(compiled.returncode, 0, compiled.stderr)
            skill = root / "skills" / "sort-downloads"
            unknown = _cli("run", str(skill), "--set", "folder=inbox")
            broken = _cli("run", str(skill), "--set", "source_dir")
            self.assertEqual(unknown.returncode, 2)
            self.assertIn("unknown parameter", unknown.stderr)
            self.assertEqual(broken.returncode, 2)
            self.assertIn("name=value", broken.stderr)

    def test_cli_runs_the_portal_skill_for_a_new_customer(self) -> None:
        portal = _portal()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            downloads = root / "downloads"
            httpd = portal.start(downloads)
            self.addCleanup(httpd.server_close)
            self.addCleanup(httpd.shutdown)
            port = httpd.server_address[1]
            compiled = _cli(
                "compile",
                str(EXAMPLES / "export-customer-pdf" / "demonstration.json"),
                "--out",
                str(root / "skills"),
            )
            self.assertEqual(compiled.returncode, 0, compiled.stderr)
            skill = root / "skills" / "export-customer-pdf"
            base = f"http://127.0.0.1:{port}"
            first = _cli("run", str(skill), "--set", "customer_id=9921", "--set", f"portal_url={base}")
            second = _cli("run", str(skill), "--set", "customer_id=9921", "--set", f"portal_url={base}")
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertIn("finished on", first.stdout)
            written = (downloads / "tax-9921.pdf").read_text(encoding="utf-8")
            self.assertIn("Northwind", written)
            self.assertIn("45.50", written)
            self.assertFalse((downloads / "tax-1042.pdf").exists())


if __name__ == "__main__":
    unittest.main()
