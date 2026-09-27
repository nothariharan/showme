# ShowMe Build Plan — record + MCP + verification

## Overview

Three features are built in order, each independent of the next until the final test pass.

1. **`showme record`** — a CLI command that starts the billing portal, opens a browser for
   the user to perform the work twice, collects both recordings, assembles the bundle, and
   calls induce automatically. Zero new external dependencies for the portal-based version.

2. **`showme mcp`** — an MCP server module (`src/showme/mcp.py`) that exposes
   `showme_compile`, `showme_prove`, and `showme_induce` as native tools. Drop a config
   into `.bob/mcp.json` and IBM Bob (or any MCP client) can call them directly.

3. **Optional Playwright back-end for `record` and `run/prove`** — when
   `playwright` is installed, the runner uses a real Chromium browser instead of the stdlib
   HTTP client. This unblocks JS-heavy portals. When it is absent the existing stdlib path
   is used unchanged.

4. **Sub-agent test pass** — after all three features are built a verification sub-agent
   runs the full test suite, exercises the new commands end-to-end, and writes a short
   findings summary.

---

## Sub-Task 1 — `showme record` command

**Status:** `[ ] pending`

### Intent

Close the only user-facing gap in the pipeline. Right now the person must GET
`/showme/recording`, manually assemble `two-runs.json`, and call `induce`. This sub-task
makes the full loop — record → induce → compile — a single command sequence.

The portal already injects a JS recording shim into every page response. All the data is
already there. The work is wiring it into the CLI.

### Expected Outcomes

- `python -m showme record --portal-url http://127.0.0.1:PORT --out run1.json` opens the
  portal URL in the default browser, waits for the user to click a "Done" button (or press
  Enter at the prompt), GETs `/showme/recording`, and writes the event list to `run1.json`.
- `python -m showme record --bundle run1.json run2.json --name my-skill --description "..." --explanation "..." --success "..." --out demonstration.json` assembles the bundle and
  calls `induce_bundle`, writing the result.
- All new behaviour covered by at least one new test in `tests/test_record.py`.
- Existing 28 tests still pass.

### Todo List

1. Add `record` subparser to `__main__.py` with two modes:
   - `--portal-url URL --out FILE` — capture one run
   - `--bundle FILE FILE ... --name STR --description STR --explanation STR --success STR --out FILE` — assemble + induce
2. Implement the capture path:
   - POST to `{portal_url}/showme/recording/reset` to clear old events
   - Open `portal_url` in browser via `webbrowser.open()` (stdlib, no deps)
   - Print "Use the portal. Press Enter when finished."
   - `input()` blocks until the user presses Enter
   - GET `{portal_url}/showme/recording` and write the event list as JSON to `--out`
3. Implement the bundle+induce path:
   - Read each file from `--bundle`, parse its JSON
   - For files that are raw event lists (a JSON array), wrap each in `{"events": [...]}` 
   - For files that are already run objects (a JSON object with "events" or "steps"), use as-is
   - Assemble `{"name":..., "description":..., "explanation":..., "success":..., "runs":[...]}`
   - Call `induce_bundle()` from `showme.induce`
   - Write result to `--out`
4. Write `tests/test_record.py`:
   - Test capture path: start a test portal, call the capture logic with a mock `input()`, assert the output file contains the expected events
   - Test bundle path: feed two known run files, assert the induced demonstration matches expectations

### Relevant Context

- `src/showme/__main__.py` — add the subparser here, follow the same `try/except` pattern as existing commands
- `src/showme/induce.py` — `induce_bundle(bundle: dict)` is the function to call
- `examples/billing_portal/server.py` — `GET /showme/recording` returns `list[dict]`, `POST /showme/recording/reset` clears it
- `examples/export-customer-pdf/two-runs.json` — the exact bundle format `induce_bundle` expects
- `webbrowser` — stdlib module, no import needed from outside std

---

## Sub-Task 2 — `showme mcp` MCP server

**Status:** `[ ] pending`

### Intent

Expose ShowMe as native agent tools via the Model Context Protocol so IBM Bob (and any
MCP-compatible client) can call `showme_compile`, `showme_prove`, and `showme_induce`
without the user typing CLI commands.

### Expected Outcomes

- `src/showme/mcp.py` exists and is a runnable MCP server (`python -m showme.mcp`).
- Three tools registered: `showme_compile`, `showme_prove`, `showme_induce`.
- `.bob/mcp.json` exists at the repo root with the server configured.
- Running the server and calling a tool from a test script produces a valid JSON response.
- No new runtime dependencies (MCP SDK is the only addition; it is a dev/optional dep).

### Tool signatures

**`showme_compile`**
- Input: `demonstration_path` (string path), `out_dir` (string path)
- Output: `{"skill_dir": "...", "ok": true}` or `{"ok": false, "error": "..."}`

**`showme_prove`**
- Input: `skill_dir` (string path), `download_dir` (string path), `params` (object of name→value)
- Output: the contents of `proof.json` as a JSON object

**`showme_induce`**
- Input: `bundle_path` (string path to a two-runs.json file), `out_path` (string path)
- Output: `{"demonstration_path": "...", "ok": true}` or `{"ok": false, "error": "..."}`

### Todo List

1. Add `mcp.py` to `src/showme/`:
   - Import `compile_path` from `showme.compile`, `induce_bundle` from `showme.induce`, and the prove logic from `showme.__main__`
   - Register the three tools using the MCP SDK `registerTool` API
   - Each tool wraps its corresponding library function in a try/except and returns structured JSON
2. Add `showme.mcp` entry to `[project.scripts]` in `pyproject.toml` so
   `python -m showme.mcp` works.
3. Add `[project.optional-dependencies]` section to `pyproject.toml`:
   - `mcp = ["mcp"]` — the MCP SDK as an optional dep
4. Write `.bob/mcp.json` at the repo root:
   ```json
   {
     "mcpServers": {
       "showme": {
         "command": "python",
         "args": ["-m", "showme.mcp"]
       }
     }
   }
   ```
5. Write a smoke test in `tests/test_mcp.py` that imports `showme.mcp`, instantiates the
   server object, and verifies the three tool names are registered — without requiring a
   live MCP connection.

### Relevant Context

- `src/showme/__main__.py` — `_prove_skill()`, `compile_path()`, `induce_bundle()` are the
  three functions to wrap; reuse them directly, don't duplicate logic
- `src/showme/compile.py` — `compile_path(demonstration: Path, out_dir: Path) -> Path`
- `src/showme/induce.py` — `induce_bundle(bundle: dict) -> dict`
- MCP SDK pattern: use `registerTool(name, description, input_schema, handler)` — load the
  `build-mcp-server` skill for the exact API if needed
- The server must be stdio transport (standard for local MCP servers)

---

## Sub-Task 3 — Optional Playwright back-end

**Status:** `[ ] pending`

### Intent

Make `showme run`, `showme prove`, and `showme record` work against JavaScript-rendered
portals (React, Angular, SPAs). When `playwright` is not installed the existing stdlib path
is used unchanged — no breakage, no new hard dependency.

### Expected Outcomes

- A new `src/showme/playwright_runner.py` module with a `PlaywrightSession` class that
  mirrors `HtmlSession.run(trace, params) -> Page` exactly.
- `__main__.py` detects `playwright` at runtime: if available and `--browser` flag is
  passed (or env var `SHOWME_BROWSER=1`), use `PlaywrightSession`; otherwise use
  `HtmlSession`.
- `showme record` gains an optional `--browser` flag that, when Playwright is available,
  uses `page.on("request")` to capture navigations instead of the portal shim.
- `[project.optional-dependencies]` gains `browser = ["playwright"]`.
- `pyproject.toml` updated: `install_requires` stays empty; new optional group `browser`.
- Existing tests unchanged. New `tests/test_playwright_runner.py` with a skip decorator
  (`@unittest.skipUnless(importlib.util.find_spec("playwright"), "playwright not installed")`).

### Todo List

1. Create `src/showme/playwright_runner.py`:
   - `class PlaywrightSession` with `run(trace, params) -> Page` signature matching `HtmlSession`
   - Use `sync_playwright` context manager
   - `navigate` → `page.goto(url)`
   - `type` → `page.get_by_label(target).fill(text)` with fallback to `page.get_by_placeholder(target).fill(text)`
   - `click` → `page.get_by_role("button", name=target).click()` with fallback to `page.get_by_text(target).click()`
   - `wait_for` → `page.wait_for_selector(f"text={text}")`
   - After each step, build a `Page`-like return from the final URL and page content
2. Modify `__main__.py` `_run_skill` and `_prove_skill` to accept a `use_browser=False`
   parameter and import `PlaywrightSession` lazily:
   ```python
   if use_browser:
       try:
           from showme.playwright_runner import PlaywrightSession as Session
       except ImportError:
           print("playwright not installed; run: pip install showme[browser]", file=sys.stderr)
           return 2
   else:
       Session = HtmlSession
   ```
3. Add `--browser` flag to `run`, `prove`, and `record` subparsers.
4. Update `pyproject.toml` optional-dependencies with `browser = ["playwright>=1.40"]`.
5. Write `tests/test_playwright_runner.py` with skip guard.

### Relevant Context

- `src/showme/html_runner.py` — `HtmlSession` is the exact interface to mirror
- `examples/billing_portal/server.py` — the test portal works with both runners
- Playwright sync API: `playwright.sync_api.sync_playwright`, `Page`, `Browser`

---

## Sub-Task 4 — Sub-agent verification pass

**Status:** `[ ] pending`

### Intent

After all three features are built, a verification sub-agent runs the full test suite
(including the new test files), exercises the new commands against the billing portal
end-to-end, and writes a short `eval/build-findings.md` report.

### Expected Outcomes

- All unit tests pass (original 28 + new tests).
- `showme record` capture + bundle paths run without error.
- `showme mcp` server starts and lists its tools.
- `eval/build-findings.md` exists with a pass/fail row for each new command.

### Todo List

1. Run `python -W default -m unittest discover -s tests -v` — all tests must pass.
2. Run the `showme record` capture path against the billing portal; assert the output file
   contains the expected events.
3. Run the `showme record` bundle path; assert the induced demonstration is valid.
4. Start `python -m showme.mcp` and verify it starts without error (kill after 2 seconds).
5. Write `eval/build-findings.md` with a pass/fail row for each check.

### Relevant Context

- `eval/BOB_PLAN.md` — pattern for how findings are written
- `eval/findings.md` — existing findings format to match

---

## Implementation Notes

- **No product code changes to make tests pass** — if a new test fails, fix the feature, not the test.
- **The stdlib HTTP path must remain the default** — Playwright is opt-in.
- **induce_bundle is the single source of truth for parameterisation** — the record command does not re-implement any induction logic.
- **mcp.py wraps existing functions only** — no business logic lives in mcp.py.
