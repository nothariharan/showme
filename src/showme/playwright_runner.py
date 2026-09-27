"""Optional browser runner. Used only when a command is passed --browser.

The default runner stays the stdlib HTML client. This module imports
Playwright at load time, so missing Playwright fails the import and the CLI
can tell the person how to install the extra.
"""

from __future__ import annotations

from playwright.sync_api import sync_playwright

from showme.html_runner import Page, RunError, _fill
from showme.notes import write_note_file


class PlaywrightSession:
    def __init__(self, headed: bool = False):
        self.headed = headed

    def run(self, trace: dict, params: dict[str, str]) -> Page:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=not self.headed)
            page = browser.new_page()
            page.set_default_navigation_timeout(60000)
            try:
                for step in trace["steps"]:
                    if step["executor"] != "agent":
                        raise RunError(f"step {step['id']} is local; this runner only performs agent steps")
                    fields = {key: _fill(value, params) for key, value in step["fields"].items()}
                    self._step(page, step["id"], step["action"], fields)
                return Page(url=page.url, body=page.content(), links=[], forms=[])
            finally:
                browser.close()

    def _step(self, page, step_id: str, action: str, fields: dict[str, str]) -> None:
        if action == "navigate":
            page.goto(fields["url"])
            return
        if action == "type":
            page.get_by_label(fields["target"], exact=True).fill(fields["text"])
            return
        if action == "click":
            target = fields["target"]
            locator = page.get_by_text(target, exact=True)
            if locator.count() == 0:
                locator = page.get_by_role("link", name=target)
            if locator.count() == 0:
                locator = page.get_by_role("tab", name=target)
            if locator.count() == 0:
                visible = page.locator("a, button").all_inner_texts()
                shown = ", ".join(text.strip() for text in visible if text.strip()) or "none"
                raise RunError(
                    f"page has no link or button named {target!r}. Visible controls: {shown}"
                )
            locator.first.click()
            return
        if action == "wait_for":
            if fields["text"] not in page.content():
                raise RunError(f"step {step_id} did not find {fields['text']!r}")
            return
        if action == "note_links":
            raw = page.eval_on_selector_all(
                "a[href]",
                "els => els.map(el => [(el.innerText || '').trim(), el.href])",
            )
            count = write_note_file(fields["path"], fields["kind"], [(text, href) for text, href in raw])
            if count == 0:
                raise RunError(f"step {step_id} found no {fields['kind']} links on {page.url}")
            print(f"wrote {count} {fields['kind']} to {fields['path']}")
            return
        raise RunError(f"step {step_id} has unknown action {action}")
