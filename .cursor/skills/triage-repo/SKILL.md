---
name: triage-repo
description: "Read one GitHub repository's newest open issues and pull requests and write the titles into notes. Use when someone asks to check a repository for new issues or to triage a repo."
compatibility: ShowMe skill. Requires Python 3.11+ for scripts/replay.py. Agent steps need a computer-use agent.
metadata:
  author: showme
  version: "0.1.0"
---

# triage-repo

Two demonstrations opened the issue list, saved every visible title, opened Pull requests, and saved those titles. The repository changed. The tabs and the notes button did not.

## When this applies

Read one GitHub repository's newest open issues and pull requests and write the titles into notes. Use when someone asks to check a repository for new issues or to triage a repo.

## Parameters

- `owner`: Changes between demonstrations. Example taken from the first run. Example: `openai`.
- `repo`: Changes between demonstrations. Example taken from the first run. Example: `openai-agents-python`.

Pass each one to the player as `--set name=value`. Values in the trace written as `{name}` are these parameters, not constants.

## Steps

1. **navigate** (agent). Opened this page. `url` = `https://github.com/{owner}/{repo}/issues`.
2. **note_links** (agent). Wrote each visible title on this list into a notes file. `kind` = `issues`, `path` = `notes/issues.md`.
3. **click** (agent). Activated the control with this visible label. `target` = `Pull requests`.
4. **navigate** (agent). Opened this page. `url` = `https://github.com/{owner}/{repo}/pulls`.
5. **note_links** (agent). Wrote each visible title on this list into a notes file. `kind` = `pulls`, `path` = `notes/pulls.md`.

## How to repeat it

Do not open GitHub yourself and do not invent issue titles. Call the ShowMe MCP tool `showme_triage` with the repository URL. It replays this skill and returns notes/issues.md and notes/pulls.md. Without MCP, from this skill's folder run `python -m showme run . --browser --set owner=OWNER --set repo=REPO`.

The full trace is `references/trace.json`.

## Done when

notes/issues.md and notes/pulls.md list the titles from the live GitHub pages.
