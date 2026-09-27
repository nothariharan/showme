"""Batch 4: the same portal skill, run twice, exports two different customers."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from showme.compile import compile_path  # noqa: E402
from showme.html_runner import HtmlSession, RunError  # noqa: E402

EXAMPLE = ROOT / "examples" / "export-customer-pdf" / "demonstration.json"
PORTAL_PATH = ROOT / "examples" / "billing_portal" / "server.py"


def _portal():
    spec = importlib.util.spec_from_file_location("billing_portal_server", PORTAL_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {PORTAL_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PortalRunTests(unittest.TestCase):
    def test_one_skill_exports_two_customers(self) -> None:
        portal = _portal()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            downloads = root / "downloads"
            httpd = portal.start(downloads)
            self.addCleanup(httpd.server_close)
            self.addCleanup(httpd.shutdown)
            port = httpd.server_address[1]
            skill = compile_path(EXAMPLE, root / "skills")
            trace = json.loads((skill / "references" / "trace.json").read_text(encoding="utf-8"))
            base = f"http://127.0.0.1:{port}"
            for customer_id, name, amount in (("1042", "Acme", "120.00"), ("9921", "Northwind", "45.50")):
                page = HtmlSession().run(
                    trace,
                    {"customer_id": customer_id, "portal_url": base},
                )
                self.assertIn("Download started", page.body)
                written = (downloads / f"tax-{customer_id}.pdf").read_text(encoding="utf-8")
                self.assertIn(customer_id, written)
                self.assertIn(name, written)
                self.assertIn(amount, written)

    def test_missing_customer_stops_before_export(self) -> None:
        portal = _portal()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            httpd = portal.start(root / "downloads")
            self.addCleanup(httpd.server_close)
            self.addCleanup(httpd.shutdown)
            port = httpd.server_address[1]
            skill = compile_path(EXAMPLE, root / "skills")
            trace = json.loads((skill / "references" / "trace.json").read_text(encoding="utf-8"))
            with self.assertRaises(RunError) as caught:
                HtmlSession().run(trace, {"customer_id": "0000", "portal_url": f"http://127.0.0.1:{port}"})
            self.assertIn("Tax summary", str(caught.exception))
            self.assertEqual(list((root / "downloads").glob("*.pdf")), [])

    def test_click_before_navigate_fails(self) -> None:
        trace = {
            "steps": [
                {
                    "id": "too-soon",
                    "action": "click",
                    "executor": "agent",
                    "fields": {"target": "Search"},
                }
            ]
        }
        with self.assertRaises(RunError) as caught:
            HtmlSession().run(trace, {})
        self.assertIn("before navigate", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
