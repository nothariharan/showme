"""Capture a portal recording and turn two recordings into a demonstration.

The billing portal stores events at /showme/recording. A person uses the page,
then ShowMe fetches that list. Two of those lists become one parameterized
demonstration through the existing inducer.
"""

from __future__ import annotations

import json
import webbrowser
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse
from urllib.request import urlopen

from showme.induce import induce_bundle


class RecordError(ValueError):
    pass


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
