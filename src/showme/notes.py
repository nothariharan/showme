"""Write issue and pull-request titles from a page into a notes file."""

from __future__ import annotations

import re
from pathlib import Path

_ISSUE = re.compile(r"/issues/(\d+)$")
_PULL = re.compile(r"/pull/(\d+)$")


def matching_links(links: list[tuple[str, str]], kind: str) -> list[tuple[str, str]]:
    pattern = _ISSUE if kind == "issues" else _PULL
    found: dict[str, str] = {}
    for text, href in links:
        clean = href.split("?", 1)[0].rstrip("/")
        if pattern.search(clean) is None:
            continue
        title = text.strip().splitlines()[0].strip() if text.strip() else ""
        title = " ".join(title.split())
        if not title or title.startswith("#") or title.isdigit():
            continue
        previous = found.get(clean)
        if previous is None or len(title) > len(previous):
            found[clean] = title
    return [(title, href) for href, title in found.items()]


def write_note_file(path: str, kind: str, links: list[tuple[str, str]]) -> int:
    items = matching_links(links, kind)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# {kind}", ""]
    for title, href in items:
        lines.append(f"- {title}")
        lines.append(f"  {href}")
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(items)
