"""Capture a portal recording and turn two recordings into a demonstration.

The billing portal stores events at /showme/recording. A person uses the page,
then ShowMe fetches that list. Two of those lists become one parameterized
demonstration through the existing inducer.
"""

from __future__ import annotations

import json
import re
import webbrowser
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse
from urllib.request import urlopen

from showme.induce import induce_bundle


class RecordError(ValueError):
    pass


_TAB = re.compile(r"^(Issues|Pull requests)(?: \d+)?$")

_RECORDER_JS = r"""
if (!window.__showmeRecorder) {
  window.__showmeRecorder = true;
  document.addEventListener("click", (event) => {
    const node = event.target && event.target.closest
      ? event.target.closest("a, button, [role='tab'], [role='button']")
      : null;
    if (!node || node.id === "showme-save-notes") return;
    let text = (node.innerText || node.getAttribute("aria-label") || "").replace(/\s+/g, " ").trim();
    text = text.replace(/^(Issues|Pull requests) \d+$/, "$1");
    if (text && window.showmeSend) window.showmeSend({type: "click", target: text});
  }, true);
}
"""

_NOTES_BUTTON_JS = r"""
() => {
  if (document.getElementById("showme-save-notes")) return;
  const button = document.createElement("button");
  button.id = "showme-save-notes";
  button.type = "button";
  button.textContent = "Save this list to notes";
  button.style.cssText = "position:fixed;bottom:16px;right:16px;z-index:2147483647;padding:10px 14px;font:14px sans-serif;background:#111;color:#fff;border:0;cursor:pointer;";
  button.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    const parts = location.pathname.split("/").filter(Boolean);
    const leaf = parts[parts.length - 1] || "";
    let kind = "";
    if (leaf === "pulls" || leaf === "pull") kind = "pulls";
    else if (leaf === "issues" || leaf === "issue") kind = "issues";
    if (kind && window.showmeSend) {
      window.showmeSend({type: "note_links", kind: kind, path: "notes/" + kind + ".md"});
    }
  }, true);
  (document.documentElement || document.body).appendChild(button);
}
"""


def normalize_tab(text: str) -> str:
    match = _TAB.match(" ".join(text.split()))
    return match.group(1) if match else ""


def accept_recorded_event(events: list[dict[str, Any]], event: dict[str, Any]) -> dict[str, Any] | None:
    kind = event.get("type")
    if kind == "navigate":
        parsed = urlparse(str(event.get("url") or ""))
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return None
        clean = parsed._replace(query="", fragment="").geturl()
        if events and events[-1].get("type") == "navigate" and events[-1].get("url") == clean:
            return None
        kept: dict[str, Any] = {"type": "navigate", "url": clean}
    elif kind == "click":
        label = normalize_tab(str(event.get("target") or ""))
        if not label:
            return None
        kept = {"type": "click", "target": label}
    elif kind == "note_links":
        link_kind = event.get("kind")
        path = event.get("path")
        if link_kind not in {"issues", "pulls"} or not isinstance(path, str) or not path.strip():
            return None
        kept = {"type": "note_links", "kind": link_kind, "path": path.strip()}
    else:
        return None
    events.append(kept)
    return kept


def recording_url(portal_url: str) -> str:
    parsed = urlparse(portal_url.strip())
    if parsed.path.rstrip("/").endswith("/showme/recording") and parsed.scheme and parsed.netloc:
        return portal_url.strip()
    if not parsed.scheme or not parsed.netloc:
        raise RecordError(f"portal url needs a host, got {portal_url!r}")
    return f"{parsed.scheme}://{parsed.netloc}/showme/recording"


def fetch_recording(portal_url: str) -> list[dict[str, Any]]:
    target = recording_url(portal_url)
    with urlopen(target) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, list):
        raise RecordError(f"{target} did not return a list of events")
    return payload


def capture_browser(
    portal_url: str,
    out: Path,
    *,
    wait: Callable[[str], str] = input,
) -> list[dict[str, Any]]:
    """Open a real page in Chromium and record the triage workflow.

    Navigations, the Issues and Pull requests tabs, and the notes button are
    kept. Other clicks are dropped so two demonstrations stay the same shape.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RecordError("Playwright is not installed. Install it with: pip install 'showme[browser]'") from exc

    events: list[dict[str, Any]] = []

    def accept(_source: object, event: dict[str, Any]) -> None:
        kept = accept_recorded_event(events, event)
        if kept is not None:
            detail = ", ".join(f"{key}={value}" for key, value in kept.items() if key != "type")
            print(f"recorded {kept['type']} {detail}", flush=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        context.expose_binding("showmeSend", accept)
        context.add_init_script(_RECORDER_JS)
        page = context.new_page()

        def on_frame(frame: object) -> None:
            if getattr(frame, "parent_frame", None) is not None:
                return
            url = getattr(frame, "url", "")
            accept(None, {"type": "navigate", "url": url})
            try:
                page.evaluate(_NOTES_BUTTON_JS)
            except Exception:
                return

        page.on("framenavigated", on_frame)
        page.goto(portal_url, wait_until="domcontentloaded")
        page.evaluate(_NOTES_BUTTON_JS)
        print(
            "Chromium is open. Click Save this list to notes on the issue list, "
            "open Pull requests, then save that list too. Press Enter here when both lists are saved.",
            flush=True,
        )
        try:
            wait("Press Enter when both lists are saved.")
        finally:
            browser.close()
    if not events:
        raise RecordError("recording is empty")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(events, indent=2) + "\n", encoding="utf-8")
    return events


def capture(
    portal_url: str,
    out: Path,
    *,
    fetch_only: bool = False,
    open_browser: Callable[[str], object] = webbrowser.open,
    wait: Callable[[str], str] = input,
) -> list[dict[str, Any]]:
    if not fetch_only:
        open_browser(portal_url)
        wait("Use the portal, then press Enter when done.")
    events = fetch_recording(portal_url)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(events, indent=2) + "\n", encoding="utf-8")
    return events


def _as_run(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return {"events": data}
    if isinstance(data, dict) and ("events" in data or "steps" in data):
        return data
    raise RecordError(f"{path} must be an event list or a run object")


def bundle_recordings(
    first: Path,
    second: Path,
    out: Path,
    *,
    name: str,
    description: str,
    explanation: str,
    success: str,
) -> dict[str, Any]:
    demonstration = induce_bundle(
        {
            "name": name,
            "description": description,
            "explanation": explanation,
            "success": success,
            "runs": [_as_run(first), _as_run(second)],
        }
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(demonstration, indent=2) + "\n", encoding="utf-8")
    return demonstration
