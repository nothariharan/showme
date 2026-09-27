# ShowMe build findings

Date: 2026-09-27

Commands were run from `C:\Users\HARIHARAN\Desktop\Bob\showme` with `$env:PYTHONPATH = "src"`, except the live loop and the Playwright prove, which ran with `PYTHONPATH` set to that repo's `src` directory and the working directory set to a temp folder so `skills` and `downloads` stayed out of the repo. No product files were edited.

## Check 1 — unittest

Command:

```
python -W default -m unittest discover -s tests -v
```

Exit code: 0

Result: Ran 37 tests in 16.564s. OK. No skips, no errors, no failures.

PASS

During `test_record.McpToolTests.test_server_registers_the_three_tools_when_the_sdk_is_present` the process printed this warning, and the test still passed:

```
C:\Users\HARIHARAN\AppData\Local\Programs\Python\Python312\Lib\site-packages\pydantic_settings\sources\utils.py:47: IncompleteFieldDefinitionWarning: Field 'lifespan' has an incomplete definition: its annotation contains an unresolved forward reference, so settings sources may fail to correctly resolve its value. Call `model_rebuild()` on the model where the field is defined, once all the referenced types are defined.
  warnings.warn(
```

After the `OK` line, stdout also contained:

```
proof ok C:\Users\HARIHA~1\AppData\Local\Temp\tmpg1fjtxwx\downloads\tax-1042.pdf
```

## Check 2 — live record, compile, prove

Portal: `examples/billing_portal/server.py` `start(downloads)` on port 0. Origin: `http://127.0.0.1:53279`. Temp directory: `C:\Users\HARIHA~1\AppData\Local\Temp\showme-live-eo3f8zws`. Each event was POSTed on its own to `/showme/record` (the handler appends one JSON value per request). Reset was `POST /showme/recording/reset`. The server was shut down after prove.

Both traces:

- navigate `{origin}/billing`
- type `Customer search box` with `1042`, then `9921` on the second list
- click `Search`
- click `Tax summary`
- click `Export PDF`
- wait_for `Download started`

| Command | Exit |
| --- | --- |
| `python -m showme record --portal-url http://127.0.0.1:53279/billing --out run1.json --fetch` | 0 |
| `python -m showme record --portal-url http://127.0.0.1:53279/billing --out run2.json --fetch` | 0 |
| `python -m showme record --bundle run1.json run2.json --name export-customer-pdf --description "Export a customer tax PDF from the billing portal." --explanation "The customer id and the portal address change. The clicks do not." --success "The page says Download started and the tax PDF for that customer is on disk." --out demonstration.json` | 0 |
| `python -m showme compile demonstration.json --out skills` | 0 |
| `python -m showme prove skills/export-customer-pdf --set portal_url=http://127.0.0.1:53279 --set customer_search_box=1042 --download-dir downloads` | 2 |

`run1.json` matched the first event list. `run2.json` matched the second. Bundle and compile wrote `skills\export-customer-pdf`.

The induced demonstration has one parameter, `customer_search_box` (example `1042`). The navigate URL is the literal `http://127.0.0.1:53279/billing`, because both recordings used that origin.

Prove stderr:

```
unknown parameter portal_url
```

`downloads/proof.json` was not written. `downloads/tax-1042.pdf` was not written. The downloads directory was empty.

FAIL

## Check 3 — MCP tool registration

Command (does not call `server.run`):

```
python -c "import asyncio; from showme.mcp import build_server; s=build_server(); print(sorted(t.name for t in asyncio.run(s.list_tools())))"
```

Exit code: 0

Tool names: `showme_compile`, `showme_induce`, `showme_prove`

The same `IncompleteFieldDefinitionWarning` for `lifespan` was printed. The tool list matches the expected names.

PASS

## Check 4 — Playwright

`python -c "import playwright"` exited 0 (`playwright` imported from site-packages).

Chromium launch:

```
python -c "from playwright.sync_api import sync_playwright; p=sync_playwright().start(); b=p.chromium.launch(headless=True); print('chromium-ok', b.version); b.close(); p.stop()"
```

Exit code: 0. Output: `chromium-ok 153.0.8010.12`

Fresh portal origin: `http://127.0.0.1:62980`. Temp directory: `C:\Users\HARIHA~1\AppData\Local\Temp\showme-pw-mwut_ab1`. Skill compiled from `examples/export-customer-pdf/demonstration.json`. Parameters used: `customer_id` and `portal_url`.

| Command | Exit |
| --- | --- |
| `python -m showme compile examples/export-customer-pdf/demonstration.json --out skills` | 0 |
| `python -m showme prove skills/export-customer-pdf --browser --set customer_id=1042 --set portal_url=http://127.0.0.1:62980 --download-dir downloads` | 0 |

stdout: `proof ok downloads\tax-1042.pdf`

`downloads/proof.json`:

```json
{
  "ok": true,
  "url": "http://127.0.0.1:62980/billing/customer/1042/export",
  "artifact": "downloads\\tax-1042.pdf"
}
```

`downloads/tax-1042.pdf` text: `tax summary for 1042 Acme amount 120.00` (contains `1042`). The server was shut down.

PASS

## Check 5 — record with no arguments

Command:

```
python -m showme record
```

Exit code: 2

stderr:

```
capture mode needs --portal-url and --out
```

The message mentions `--portal-url`.

PASS

## Bugs

The exit 2 in check 2 is the prove command passing `--set portal_url=...` for a parameter the demonstration does not have. Both recordings used one host, so induction kept that URL as a literal and only declared `customer_search_box`. That refusal is the existing unknown-parameter check.

A follow-up on a new portal, same two traces, compiled the induced skill and ran:

```
python -m showme prove skills/export-customer-pdf --set customer_search_box=1042 --download-dir downloads
```

Exit code: 0. `proof.json` was `ok: true` at `http://127.0.0.1:51495/billing/customer/1042/export`. The PDF text was `tax summary for 1042 Acme amount 120.00`.

Bug count: 0
