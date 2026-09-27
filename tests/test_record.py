"""Record fetches a portal trace, and two traces become one demonstration."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
import tempfile
import unittest
from unittest import mock
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from showme.__main__ import main  # noqa: E402
from showme.record import capture, recording_url  # noqa: E402

PORTAL_PATH = ROOT / "examples" / "billing_portal" / "server.py"
EVENTS = [
    {"type": "navigate", "url": "http://127.0.0.1/billing"},
    {"type": "type", "target": "Customer search box", "text": "1042"},
    {"type": "click", "target": "Search"},
]


def _portal():
    spec = importlib.util.spec_from_file_location("billing_portal_server_record", PORTAL_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {PORTAL_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _post_json(url: str, payload: dict) -> None:
    data = json.dumps(payload).encode("utf-8")
    request = Request(url, data=data, headers={"Content-Type": "application/json"})
    with urlopen(request) as response:
        response.read()


def _cli(*args: str) -> tuple[int, str, str]:
    stdout, stderr = StringIO(), StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = main(list(args))
    return code, stdout.getvalue(), stderr.getvalue()


class RecordTests(unittest.TestCase):
    def test_recording_url_uses_the_portal_host(self) -> None:
        self.assertEqual(
            recording_url("http://127.0.0.1:9/billing"),
            "http://127.0.0.1:9/showme/recording",
        )
        self.assertEqual(
            recording_url("http://127.0.0.1:9/showme/recording"),
            "http://127.0.0.1:9/showme/recording",
        )

    def test_fetch_writes_events_without_opening_a_browser(self) -> None:
        portal = _portal()
        with tempfile.TemporaryDirectory() as tmp:
            httpd = portal.start(Path(tmp) / "downloads")
            self.addCleanup(httpd.server_close)
            self.addCleanup(httpd.shutdown)
            port = httpd.server_address[1]
            origin = f"http://127.0.0.1:{port}"
            for event in EVENTS:
                _post_json(origin + "/showme/record", event)
            opened: list[str] = []
            out = Path(tmp) / "run1.json"
            events = capture(
                origin + "/billing",
                out,
                fetch_only=True,
                open_browser=lambda url: opened.append(url),
                wait=lambda _prompt: (_ for _ in ()).throw(AssertionError("waited")),
            )
            self.assertEqual(opened, [])
            self.assertEqual(events, EVENTS)
            self.assertEqual(json.loads(out.read_text(encoding="utf-8")), EVENTS)

    def test_interactive_capture_opens_the_page_and_waits(self) -> None:
        portal = _portal()
        with tempfile.TemporaryDirectory() as tmp:
            httpd = portal.start(Path(tmp) / "downloads")
            self.addCleanup(httpd.server_close)
            self.addCleanup(httpd.shutdown)
            port = httpd.server_address[1]
            origin = f"http://127.0.0.1:{port}"
            _post_json(origin + "/showme/record", EVENTS[0])
            opened: list[str] = []
            prompts: list[str] = []
            out = Path(tmp) / "run.json"
            capture(
                origin + "/billing",
                out,
                open_browser=lambda url: opened.append(url) or True,
                wait=lambda prompt: prompts.append(prompt) or "",
            )
            self.assertEqual(opened, [origin + "/billing"])
            self.assertIn("press Enter", prompts[0])
            self.assertEqual(json.loads(out.read_text(encoding="utf-8")), [EVENTS[0]])

    def test_cli_fetch_and_bundle(self) -> None:
        portal = _portal()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            httpd = portal.start(root / "downloads")
            self.addCleanup(httpd.server_close)
            self.addCleanup(httpd.shutdown)
            origin = f"http://127.0.0.1:{httpd.server_address[1]}"
            first = [
                {"type": "navigate", "url": origin + "/billing"},
                {"type": "type", "target": "Customer search box", "text": "1042"},
                {"type": "click", "target": "Search"},
            ]
            for event in first:
                _post_json(origin + "/showme/record", event)
            run1 = root / "run1.json"
            code, stdout, stderr = _cli("record", "--portal-url", origin + "/billing", "--out", str(run1), "--fetch")
            self.assertEqual(code, 0, stderr)
            self.assertEqual(stdout.strip(), str(run1))
            _post_json(origin + "/showme/recording/reset", {})
            second = [
                {"type": "navigate", "url": "http://127.0.0.1:9/billing"},
                {"type": "type", "target": "Customer search box", "text": "9921"},
                {"type": "click", "target": "Search"},
            ]
            run2 = root / "run2.json"
            run2.write_text(json.dumps(second), encoding="utf-8")
            demo = root / "demonstration.json"
            code, stdout, stderr = _cli(
                "record",
                "--bundle",
                str(run1),
                str(run2),
                "--name",
                "export-customer-pdf",
                "--description",
                "Export a customer tax PDF from the billing portal.",
                "--explanation",
                "The customer id and the portal address change. The clicks do not.",
                "--success",
                "The page says Download started.",
                "--out",
                str(demo),
            )
            self.assertEqual(code, 0, stderr)
            written = json.loads(demo.read_text(encoding="utf-8"))
            names = [item["name"] for item in written["parameters"]]
            self.assertIn("customer_search_box", names)
            self.assertIn("portal_url", names)

    def test_cli_capture_without_arguments_exits_2(self) -> None:
        code, _stdout, stderr = _cli("record")
        self.assertEqual(code, 2)
        self.assertIn("--portal-url", stderr)


class BrowserFlagTests(unittest.TestCase):
    def test_browser_flag_names_the_extra_when_playwright_is_absent(self) -> None:
        import builtins

        real_import = builtins.__import__

        def blocked(name, globals=None, locals=None, fromlist=(), level=0):  # noqa: A002
            if name == "showme.playwright_runner" or name.startswith("playwright"):
                raise ImportError("blocked for test")
            return real_import(name, globals, locals, fromlist, level)

        example = ROOT / "examples" / "export-customer-pdf" / "demonstration.json"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            code, _stdout, stderr = _cli("compile", str(example), "--out", str(root))
            self.assertEqual(code, 0, stderr)
            skill = root / "export-customer-pdf"
            with mock.patch("builtins.__import__", blocked):
                code, _stdout, stderr = _cli(
                    "run",
                    str(skill),
                    "--browser",
                    "--set",
                    "customer_id=1042",
                    "--set",
                    "portal_url=http://127.0.0.1:9",
                )
            self.assertEqual(code, 1)
            self.assertIn("pip install 'showme[browser]'", stderr)


class McpToolTests(unittest.TestCase):
    def test_tools_induce_compile_and_prove_without_the_mcp_package(self) -> None:
        from showme.mcp_tools import tool_compile, tool_induce, tool_prove

        portal = _portal()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle = root / "two-runs.json"
            bundle.write_text(
                (ROOT / "examples" / "export-customer-pdf" / "two-runs.json").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            demo = Path(tool_induce(str(bundle), str(root / "demonstration.json")))
            skill = Path(tool_compile(str(demo), str(root / "skills")))
            downloads = root / "downloads"
            httpd = portal.start(downloads)
            self.addCleanup(httpd.server_close)
            self.addCleanup(httpd.shutdown)
            port = httpd.server_address[1]
            body = tool_prove(
                str(skill),
                str(downloads),
                [f"portal_url=http://127.0.0.1:{port}", "customer_search_box=1042"],
            )
            proof = json.loads(body)
            self.assertIs(proof["ok"], True)
            self.assertIn("1042", (downloads / "tax-1042.pdf").read_text(encoding="utf-8"))

    def test_mcp_module_reports_the_extra_when_the_sdk_is_absent(self) -> None:
        import builtins

        from showme.mcp import main as mcp_main

        real_import = builtins.__import__

        def blocked(name, globals=None, locals=None, fromlist=(), level=0):  # noqa: A002
            if name == "mcp" or name.startswith("mcp."):
                raise ImportError("blocked for test")
            return real_import(name, globals, locals, fromlist, level)

        stderr = StringIO()
        with mock.patch("builtins.__import__", blocked), redirect_stderr(stderr):
            code = mcp_main()
        self.assertEqual(code, 1)
        self.assertIn("pip install 'showme[mcp]'", stderr.getvalue())

    def test_server_registers_the_three_tools_when_the_sdk_is_present(self) -> None:
        try:
            from showme.mcp import build_server
        except ImportError:
            self.skipTest("mcp extra missing")
        try:
            server = build_server()
        except ImportError:
            self.skipTest("mcp extra missing")
        names = sorted(tool.name for tool in asyncio.run(server.list_tools()))
        self.assertEqual(names, ["showme_compile", "showme_induce", "showme_prove"])
