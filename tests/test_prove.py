"""Prove checks a portal download and writes proof.json. It does not invent a PDF."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from showme.__main__ import main  # noqa: E402
from showme.compile import compile_path  # noqa: E402

EXAMPLE = ROOT / "examples" / "export-customer-pdf" / "demonstration.json"
PORTAL_PATH = ROOT / "examples" / "billing_portal" / "server.py"


def _portal():
    spec = importlib.util.spec_from_file_location("billing_portal_server_prove", PORTAL_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {PORTAL_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _prove(*args: str) -> tuple[int, str, str]:
    stdout, stderr = StringIO(), StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = main(["prove", *args])
    return code, stdout.getvalue(), stderr.getvalue()


class ProveTests(unittest.TestCase):
    def test_compiled_skill_proves_customer_1042(self) -> None:
        portal = _portal()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            downloads = root / "downloads"
            httpd = portal.start(downloads)
            self.addCleanup(httpd.server_close)
            self.addCleanup(httpd.shutdown)
            port = httpd.server_address[1]
            skill = compile_path(EXAMPLE, root / "skills")
            code, stdout, _stderr = _prove(
                str(skill),
                "--set",
                "customer_id=1042",
                "--set",
                f"portal_url=http://127.0.0.1:{port}",
                "--download-dir",
                str(downloads),
            )
            self.assertEqual(code, 0, _stderr)
            proof = json.loads((downloads / "proof.json").read_text(encoding="utf-8"))
            artifact = downloads / "tax-1042.pdf"
            self.assertIs(proof["ok"], True)
            self.assertEqual(proof["url"], f"http://127.0.0.1:{port}/billing/customer/1042/export")
            self.assertEqual(proof["artifact"], str(artifact))
            written = artifact.read_text(encoding="utf-8")
            self.assertIn("1042", written)
            self.assertIn("Acme", written)
            self.assertIn("120.00", written)
            self.assertEqual(stdout, f"proof ok {artifact}\n")

    def test_unknown_customer_writes_failed_proof_without_pdf(self) -> None:
        portal = _portal()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            downloads = root / "downloads"
            httpd = portal.start(downloads)
            self.addCleanup(httpd.server_close)
            self.addCleanup(httpd.shutdown)
            port = httpd.server_address[1]
            skill = compile_path(EXAMPLE, root / "skills")
            code, stdout, _stderr = _prove(
                str(skill),
                "--set",
                "customer_id=0000",
                "--set",
                f"portal_url=http://127.0.0.1:{port}",
                "--download-dir",
                str(downloads),
            )
            self.assertEqual(code, 1)
            proof = json.loads((downloads / "proof.json").read_text(encoding="utf-8"))
            self.assertIs(proof["ok"], False)
            self.assertIn("Tax summary", proof["error"])
            self.assertEqual(list(downloads.glob("*.pdf")), [])
            self.assertEqual(stdout, "")

    def test_renamed_export_button_stops_without_a_pdf(self) -> None:
        portal = _portal()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            downloads = root / "downloads"
            httpd = portal.start(downloads, export_label="Download PDF")
            self.addCleanup(httpd.server_close)
            self.addCleanup(httpd.shutdown)
            port = httpd.server_address[1]
            skill = compile_path(EXAMPLE, root / "skills")
            code, _stdout, _stderr = _prove(
                str(skill),
                "--set",
                "customer_id=1042",
                "--set",
                f"portal_url=http://127.0.0.1:{port}",
                "--download-dir",
                str(downloads),
            )
            self.assertEqual(code, 1)
            proof = json.loads((downloads / "proof.json").read_text(encoding="utf-8"))
            self.assertIs(proof["ok"], False)
            self.assertIn("Export PDF", proof["error"])
            self.assertIn("Download PDF", proof["error"])
            self.assertEqual(list(downloads.glob("*.pdf")), [])


if __name__ == "__main__":
    unittest.main()
