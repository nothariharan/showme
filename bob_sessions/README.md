# Bob session exports

This folder holds IBM Bob task history exports for the ShowMe hackathon submission.

Each task has:
- A `.md` file — the full task history export from Bob's History panel
- A `.json` file — the same export as JSON
- A `.png` file — screenshot of the session consumption summary

## Tasks

| File | What the session did |
| --- | --- |
| `prove-suite.md`, `prove-suite.json`, `prove-suite.png` | Bob ran `eval/BOB_PLAN.md`: both test passes, prove for customer 1042, the unknown customer, and the renamed button. The summary shows 132.3k tokens and 13.31. |

## How these were produced

1. Open the ShowMe repo (`C:\Users\HARIHARAN\Desktop\Bob\showme`) in IBM Bob.
2. The workspace has `.bob/mcp.json` which points Bob at `python -m showme.mcp`.
3. Run the task described in the matching `.md` file.
4. Open Bob's History panel, click the task header for the consumption summary, screenshot it.
5. Click **Export task history** and save the `.md` file here.

No API keys or tokens appear in these files.
