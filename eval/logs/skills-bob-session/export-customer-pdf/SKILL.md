---
name: export-customer-pdf
description: "Export a customer's tax summary PDF from the billing portal. Use when the user gives a customer id and asks for that customer's tax summary."
compatibility: ShowMe skill. Requires Python 3.11+ for scripts/replay.py. Agent steps need a computer-use agent.
metadata:
  author: showme
  version: "0.1.0"
---

# export-customer-pdf

The portal has no API. The person showed the path: open billing, search the customer id, open the tax summary, and export the PDF. The customer id changes every run. The menus do not.

## When this applies

Export a customer's tax summary PDF from the billing portal. Use when the user gives a customer id and asks for that customer's tax summary.

## Parameters

- `customer_id`: Customer number to export. Example: `1042`.
- `portal_url`: Billing portal address. Example: `http://127.0.0.1:8765`.

Pass each one to the player as `--set name=value`. Values in the trace written as `{name}` are these parameters, not constants.

## Steps

1. **navigate** (agent). Start on the billing home, already signed in. `url` = `{portal_url}/billing`.
2. **type** (agent). The search box is the only value that changes between customers. `target` = `Customer search box`, `text` = `{customer_id}`.
3. **click** (agent). Run the search. `target` = `Search`.
4. **click** (agent). Open that customer's tax summary, not the invoice list. `target` = `Tax summary`.
5. **click** (agent). Export writes the PDF. CSV is the wrong format. `target` = `Export PDF`.
6. **wait_for** (agent). The run is finished only when the portal confirms the download. `text` = `Download started`.

## How to repeat it

Run `scripts/replay.py` for the local steps. Perform every step marked `agent` yourself, in order, using the arguments passed for this run. Stop if a local step fails or the success check is not true.

The full trace is `references/trace.json`.

## Done when

A PDF for the requested customer id was downloaded, and the page shows Download started.
