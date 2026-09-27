# Bob triage task

You are IBM Bob. The repo is `C:\Users\HARIHARAN\Desktop\Bob\showme`.

## What to do

1. Confirm the `showme` MCP server is running. Its tools include `showme_triage`. If the tool
   list does not show `showme_triage`, restart the MCP server, then run:
   ```
   pip install "showme[mcp]" "showme[browser]"
   playwright install chromium
   ```

2. Read `.agents/skills/triage-repo/SKILL.md`. That file says:
   > Do not open GitHub yourself and do not invent issue titles.
   > Call the ShowMe MCP tool `showme_triage` with the repository URL.

3. Call `showme_triage` with `https://github.com/openclaw/openclaw`.
   The tool will open Chromium, navigate to the issues and pull requests pages,
   and write the titles it finds into notes. It returns the notes as a string.

4. Write everything that happened — the tool call, its return value, and the
   issue/PR titles — to `eval/logs/bob-triage.md`.

## Shell fallback (only if the MCP tool is still missing after reinstall)

```bash
python -m showme run .agents/skills/triage-repo --browser \
    --set owner=openclaw --set repo=openclaw
```

Then read `notes/issues.md` and `notes/pulls.md` from inside the skill folder
and copy them into `eval/logs/bob-triage.md`.

## What a passing run looks like

- `eval/logs/bob-triage.md` exists and is not empty.
- The file contains links like `https://github.com/openclaw/openclaw/issues/N`
  and `https://github.com/openclaw/openclaw/pull/N`.
- No titles are invented. Every title came from the live GitHub page.
- Do not change any file under `src/` or `tests/`.
