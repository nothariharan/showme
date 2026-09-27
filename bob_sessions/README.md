# Bob session exports

This folder holds IBM Bob task history exports for the ShowMe hackathon submission.

Each task has:
- A `.md` file — the full task history export from Bob's History panel
- A `.png` file — screenshot of the session consumption summary

## Tasks

| File | What the session did |
| --- | --- |
| `prove-suite.md` | Ran the full 37-test suite, compiled export-customer-pdf, proved customer 1042 against the billing portal, wrote eval/bob-session.md |

## How these were produced

1. Open the ShowMe repo (`C:\Users\HARIHARAN\Desktop\Bob\showme`) in IBM Bob.
2. The workspace has `.bob/mcp.json` which points Bob at `python -m showme.mcp`.
3. Run the task described in the matching `.md` file.
4. Open Bob's History panel, click the task header for the consumption summary, screenshot it.
5. Click **Export task history** and save the `.md` file here.

No API keys or tokens appear in these files.
