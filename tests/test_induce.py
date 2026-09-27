"""Two demonstrations become one skill. A renamed button stops the run."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from showme.compile import compile_demonstration, retarget  # noqa: E402
from showme.html_runner import HtmlSession, RunError  # noqa: E402
from showme.induce import InduceError, induce_bundle  # noqa: E402
from showme.model import parse_demonstration  # noqa: E402

BUNDLE = ROOT / "examples" / "export-customer-pdf" / "two-runs.json"
PORTAL_PATH = ROOT / "examples" / "billing_portal" / "server.py"


def _portal():
    spec = importlib.util.spec_from_file_location("billing_portal_induce", PORTAL_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {PORTAL_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _events(origin: str, customer: str, export_label: str = "Export PDF") -> list[dict[str, str]]:
    return [
        {"type": "navigate", "url": f"{origin}/billing"},
        {"type": "type", "target": "Customer search box", "text": customer},
        {"type": "click", "target": "Search"},
        {"type": "click", "target": "Tax summary"},
        {"type": "click", "target": export_label},
        {"type": "wait_for", "text": "Download started"},
    ]


def _post_json(url: str, payload: dict) -> None:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request) as response:
        response.read()


def _get_json(url: str):
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read().decode("utf-8"))


class InduceTests(unittest.TestCase):
    def test_two_runs_name_only_the_values_that_change(self) -> None:
        demonstration = induce_bundle(json.loads(BUNDLE.read_text(encoding="utf-8")))
        demo = parse_demonstration(demonstration)
        names = [item.name for item in demo.parameters]
        self.assertEqual(names, ["portal_url", "customer_search_box"])
        navigate = demo.steps[0]
        typed = demo.steps[1]
        self.assertEqual(navigate.fields["url"], "{portal_url}/billing")
        self.assertEqual(typed.fields["text"], "{customer_search_box}")
        self.assertEqual(demo.steps[4].fields["target"], "Export PDF")

    def test_a_changed_click_is_rejected(self) -> None:
        bundle = json.loads(BUNDLE.read_text(encoding="utf-8"))
        bundle["runs"][1]["events"][4]["target"] = "Download PDF"
        with self.assertRaises(InduceError) as caught:
            induce_bundle(bundle)
        self.assertIn("not an input", str(caught.exception))

    def test_different_length_runs_are_rejected(self) -> None:
        bundle = json.loads(BUNDLE.read_text(encoding="utf-8"))
        bundle["runs"][1]["events"].pop()
        with self.assertRaises(InduceError) as caught:
            induce_bundle(bundle)
        self.assertIn("same non-empty number of steps", str(caught.exception))

    def test_recorded_runs_compile_and_repeat(self) -> None:
        portal = _portal()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = self._record(portal, root / "first", "1042")
            second = self._record(portal, root / "second", "9921")
            self.assertEqual(first[1]["text"], "1042")
            bundle = json.loads(BUNDLE.read_text(encoding="utf-8"))
            bundle["runs"] = [{"events": first}, {"events": second}]
            demonstration = induce_bundle(bundle)
            skill = compile_demonstration(parse_demonstration(demonstration), root / "skills")
            live = portal.start(root / "downloads")
            self.addCleanup(live.server_close)
            self.addCleanup(live.shutdown)
            origin = f"http://127.0.0.1:{live.server_address[1]}"
            page = HtmlSession().run(
                json.loads((skill / "references" / "trace.json").read_text(encoding="utf-8")),
                {"portal_url": origin, "customer_search_box": "9921"},
            )
            self.assertIn("Download started", page.body)
            pdf = (root / "downloads" / "tax-9921.pdf").read_text(encoding="utf-8")
            self.assertIn("Northwind", pdf)
            self.assertIn("45.50", pdf)

    def test_renamed_button_halts_until_retarget(self) -> None:
        portal = _portal()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            demonstration = induce_bundle(json.loads(BUNDLE.read_text(encoding="utf-8")))
            skill = compile_demonstration(parse_demonstration(demonstration), root / "skills")
            downloads = root / "downloads"
            httpd = portal.start(downloads, export_label="Download PDF")
            self.addCleanup(httpd.server_close)
            self.addCleanup(httpd.shutdown)
            origin = f"http://127.0.0.1:{httpd.server_address[1]}"
            trace = json.loads((skill / "references" / "trace.json").read_text(encoding="utf-8"))
            params = {"portal_url": origin, "customer_search_box": "1042"}
            with self.assertRaises(RunError) as caught:
                HtmlSession().run(trace, params)
            self.assertIn("Export PDF", str(caught.exception))
            self.assertIn("Download PDF", str(caught.exception))
            self.assertFalse((downloads / "tax-1042.pdf").exists())
            export_step = next(step["id"] for step in trace["steps"] if step["fields"].get("target") == "Export PDF")
            retarget(skill, export_step, "Download PDF")
            updated = json.loads((skill / "references" / "trace.json").read_text(encoding="utf-8"))
            page = HtmlSession().run(updated, params)
            self.assertIn("Download started", page.body)
            self.assertIn("Acme", (downloads / "tax-1042.pdf").read_text(encoding="utf-8"))
            self.assertIn("Download PDF", (skill / "SKILL.md").read_text(encoding="utf-8"))

    def test_cli_induce(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "demonstration.json"
            env = os.environ.copy()
            env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
            completed = subprocess.run(
                [sys.executable, "-m", "showme", "induce", str(BUNDLE), "--out", str(out)],
                cwd=ROOT,
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            written = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(written["parameters"][0]["name"], "portal_url")

    def _record(self, portal, downloads: Path, customer: str) -> list[dict]:
        httpd = portal.start(downloads)
        self.addCleanup(httpd.server_close)
        self.addCleanup(httpd.shutdown)
        origin = f"http://127.0.0.1:{httpd.server_address[1]}"
        for event in _events(origin, customer):
            _post_json(origin + "/showme/record", event)
        recorded = _get_json(origin + "/showme/recording")
        self.assertEqual(recorded, _events(origin, customer))
        return recorded
