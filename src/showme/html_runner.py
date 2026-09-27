"""Repeat agent steps against a live HTML page.

The skill names controls by the text a person sees ("Search", "Export PDF").
This runner finds that text in the current page and submits the matching form
or follows the matching link. It is the stand-in for a computer-use agent on
ordinary HTML, not a desktop agent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen


class RunError(RuntimeError):
    pass


@dataclass
class Page:
    url: str
    body: str
    links: list[tuple[str, str]]
    forms: list[dict[str, object]]


@dataclass
class HtmlSession:
    page: Page | None = None
    typed: dict[str, str] = field(default_factory=dict)

    def run(self, trace: dict, params: dict[str, str]) -> Page:
        for step in trace["steps"]:
            if step["executor"] != "agent":
                raise RunError(f"step {step['id']} is local; this runner only performs agent steps")
            fields = {key: _fill(value, params) for key, value in step["fields"].items()}
            action = step["action"]
            if action == "navigate":
                self.page = _fetch("GET", fields["url"])
            elif action == "type":
                self.typed[fields["target"]] = fields["text"]
            elif action == "click":
                self.page = _click(self._require_page(step["id"]), fields["target"], self.typed)
            elif action == "wait_for":
                page = self._require_page(step["id"])
                if fields["text"] not in page.body:
                    raise RunError(f"step {step['id']} did not find {fields['text']!r}")
            elif action == "press":
                raise RunError(f"step {step['id']} uses press, which this HTML runner does not perform")
            else:
                raise RunError(f"step {step['id']} has unknown action {action}")
        if self.page is None:
            raise RunError("skill finished without opening a page")
        return self.page

    def _require_page(self, step_id: str) -> Page:
        if self.page is None:
            raise RunError(f"step {step_id} ran before navigate")
        return self.page


def _click(page: Page, target: str, typed: dict[str, str]) -> Page:
    for text, href in page.links:
        if text == target:
            return _fetch("GET", urljoin(page.url, href))
    for form in page.forms:
        if target not in form["buttons"]:
            continue
        payload: dict[str, str] = {}
        labels: dict[str, str] = form["labels"]  # type: ignore[assignment]
        names: dict[str, str] = form["inputs"]  # type: ignore[assignment]
        for input_id, name in names.items():
            label = labels.get(input_id, "")
            if label in typed:
                payload[name] = typed[label]
        return _fetch("POST", urljoin(page.url, str(form["action"])), payload)
    visible = [text for text, _href in page.links]
    visible.extend(button for form in page.forms for button in form["buttons"])  # type: ignore[misc]
    shown = ", ".join(str(item) for item in visible) or "none"
    raise RunError(f"page has no link or button named {target!r}. Visible controls: {shown}")


def _fetch(method: str, url: str, form: dict[str, str] | None = None) -> Page:
    data = urlencode(form).encode("utf-8") if form is not None else None
    request = Request(url, data=data, method=method)
    with urlopen(request, timeout=5) as response:  # noqa: S310
        body = response.read().decode("utf-8")
        final_url = response.geturl()
    parsed = _parse(body)
    return Page(url=final_url, body=body, links=parsed[0], forms=parsed[1])


class _Parser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self.forms: list[dict[str, object]] = []
        self._href: str | None = None
        self._capture: str | None = None
        self._buf: list[str] = []
        self._form: dict[str, object] | None = None
        self._label_for: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        if tag == "a":
            self._href = values.get("href")
            self._start_text()
        elif tag == "form":
            self._form = {
                "action": values.get("action", ""),
                "buttons": [],
                "inputs": {},
                "labels": {},
            }
        elif tag == "input" and self._form is not None:
            inputs: dict[str, str] = self._form["inputs"]  # type: ignore[assignment]
            inputs[values.get("id", "")] = values.get("name", "")
        elif tag == "label":
            self._label_for = values.get("for")
            self._start_text()
        elif tag == "button":
            self._start_text()

    def handle_data(self, data: str) -> None:
        if self._capture is not None:
            self._buf.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href is not None:
            self.links.append(("".join(self._buf).strip(), self._href))
            self._href = None
            self._capture = None
        elif tag == "label" and self._form is not None and self._label_for is not None:
            labels: dict[str, str] = self._form["labels"]  # type: ignore[assignment]
            labels[self._label_for] = "".join(self._buf).strip()
            self._label_for = None
            self._capture = None
        elif tag == "button" and self._form is not None:
            buttons: list[str] = self._form["buttons"]  # type: ignore[assignment]
            buttons.append("".join(self._buf).strip())
            self._capture = None
        elif tag == "form" and self._form is not None:
            self.forms.append(self._form)
            self._form = None

    def _start_text(self) -> None:
        self._capture = "text"
        self._buf = []


def _parse(body: str) -> tuple[list[tuple[str, str]], list[dict[str, object]]]:
    parser = _Parser()
    parser.feed(body)
    return parser.links, parser.forms


def _fill(text: str, params: dict[str, str]) -> str:
    for key, value in params.items():
        text = text.replace("{" + key + "}", value)
    return text
