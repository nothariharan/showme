"""Tiny billing portal used to prove a ShowMe skill can be repeated.

No framework. One process, two routes that matter: search a customer, export a PDF.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

CUSTOMERS = {
    "1042": {"name": "Acme", "tax": "120.00"},
    "9921": {"name": "Northwind", "tax": "45.50"},
}


def start(
    download_dir: Path,
    host: str = "127.0.0.1",
    port: int = 0,
    export_label: str = "Export PDF",
) -> ThreadingHTTPServer:
    download_dir.mkdir(parents=True, exist_ok=True)
    handler = _handler(download_dir, export_label)
    httpd = ThreadingHTTPServer((host, port), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd


def _handler(download_dir: Path, export_label: str) -> type[BaseHTTPRequestHandler]:
    recorded: list[dict] = []
    lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: object) -> None:
            return

        def do_GET(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            if path == "/showme/recording":
                with lock:
                    payload = json.dumps(recorded).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
                return
            if path == "/billing":
                self._html(_search_page())
                return
            customer_id, leaf = _customer_path(path)
            if customer_id and leaf == "":
                self._html(_result_page(customer_id))
                return
            if customer_id and leaf == "summary":
                self._html(_summary_page(customer_id, export_label))
                return
            self.send_error(404)

        def do_POST(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            body = self.rfile.read(int(self.headers.get("Content-Length", "0"))).decode("utf-8")
            if path == "/showme/record":
                event = json.loads(body)
                with lock:
                    recorded.append(event)
                self._html("<p>recorded</p>")
                return
            if path == "/showme/recording/reset":
                with lock:
                    recorded.clear()
                self._html("<p>cleared</p>")
                return
            form = {key: values[0] for key, values in parse_qs(body).items()}
            if path == "/billing/search":
                customer_id = form.get("customer_id", "")
                if customer_id not in CUSTOMERS:
                    self._html("<p>Customer not found</p>")
                    return
                self.send_response(303)
                self.send_header("Location", f"/billing/customer/{customer_id}")
                self.end_headers()
                return
            customer_id, leaf = _customer_path(path)
            if customer_id and leaf == "export":
                record = CUSTOMERS.get(customer_id)
                if record is None:
                    self.send_error(404)
                    return
                text = f"tax summary for {customer_id} {record['name']} amount {record['tax']}\n"
                (download_dir / f"tax-{customer_id}.pdf").write_text(text, encoding="utf-8")
                self._html(f"<p>Download started</p><p>Customer {customer_id}</p><p>Amount {record['tax']}</p>")
                return
            self.send_error(404)

        def _html(self, content: str) -> None:
            payload = (
                "<!DOCTYPE html><html><body>"
                f"{content}"
                "<script>"
                "function showmeSend(event){fetch('/showme/record',{method:'POST',"
                "headers:{'Content-Type':'application/json'},body:JSON.stringify(event),keepalive:true});}"
                "showmeSend({type:'navigate',url:location.href});"
                "if(document.body&&document.body.textContent.indexOf('Download started')!==-1)"
                "showmeSend({type:'wait_for',text:'Download started'});"
                "document.addEventListener('submit',function(e){"
                "var form=e.target;"
                "form.querySelectorAll('input').forEach(function(input){"
                "var label=input.id&&form.querySelector('label[for=\"'+input.id+'\"]');"
                "if(label&&input.value)showmeSend({type:'type',target:label.textContent.trim(),text:input.value});"
                "});"
                "if(e.submitter)showmeSend({type:'click',target:e.submitter.textContent.trim()});"
                "},true);"
                "document.addEventListener('click',function(e){"
                "var link=e.target.closest&&e.target.closest('a');"
                "if(link)showmeSend({type:'click',target:link.textContent.trim()});"
                "},true);"
                "</script></body></html>"
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    return Handler


def _customer_path(path: str) -> tuple[str, str]:
    prefix = "/billing/customer/"
    if not path.startswith(prefix):
        return "", ""
    rest = path[len(prefix) :]
    if "/" not in rest:
        return rest, ""
    customer_id, leaf = rest.split("/", 1)
    return customer_id, leaf


def _search_page() -> str:
    return """
<form action="/billing/search" method="post">
  <label for="customer_id">Customer search box</label>
  <input id="customer_id" name="customer_id">
  <button type="submit">Search</button>
</form>
"""


def _result_page(customer_id: str) -> str:
    record = CUSTOMERS[customer_id]
    return f"""
<p>Results for {record['name']}</p>
<p><a href="/billing/customer/{customer_id}/summary">Tax summary</a></p>
"""


def _summary_page(customer_id: str, export_label: str = "Export PDF") -> str:
    record = CUSTOMERS[customer_id]
    return f"""
<p>{record['name']} owes {record['tax']}</p>
<form action="/billing/customer/{customer_id}/export" method="post">
  <button type="submit">{export_label}</button>
</form>
"""
