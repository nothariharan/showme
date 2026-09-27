# ShowMe

ShowMe turns a piece of repeatable work into a folder any coding agent can run again.

You explain when the work should happen, and you show the steps once, including which values change next time. ShowMe compiles that into an [Agent Skill](https://agentskills.io/specification): a `SKILL.md` plus a trace and a player. Claude Code, Cursor, Codex, and any other agent that reads Agent Skills can pick it up. The skill is the transferable object. The original session is not.

This is the open version of a pattern the industry already ships in pieces. Recorders (Playwright, Chrome Recorder, OpenAdapt, Codex Record & Replay) capture a demonstration. Agent Skills is the folder those coding agents already load. ShowMe is the bridge: demonstration in, that folder out.

Two examples are in the repo:

- `examples/sort-downloads` is a daily chore. The player moves the files itself.
- `examples/export-customer-pdf` is a portal path with no API. The skill tells the agent which clicks to repeat, and which field is the customer id.

The format is described in [PROTOCOL.md](PROTOCOL.md). Version 0.1 takes a recorded action trace, not a video. One demonstration is evidence. Two demonstrations decide which values are inputs. A click whose label changed stops the run until you point the skill at the new label.

## Run

```bash
python -m showme validate examples/sort-downloads/demonstration.json
python -m showme compile examples/sort-downloads/demonstration.json --out .agents/skills
python .agents/skills/sort-downloads/scripts/replay.py --set source_dir=C:/path/to/inbox
```

Requires Python 3.11+. No third-party packages.

`showme run` repeats a compiled skill. A skill whose steps are all local shells out to `scripts/replay.py`. A skill whose steps are all clicks and typing opens the page named in the trace and uses the visible label of each control.

```bash
python -m showme run .agents/skills/sort-downloads --set source_dir=C:/path/to/inbox
python -m showme induce examples/export-customer-pdf/two-runs.json --out examples/export-customer-pdf/induced.json
```

`showme induce` compares two or more recordings. A typed value or a server address that changes becomes a parameter. A click, a path, or a success check that changes is a different workflow, and induction refuses it. `showme retarget <skill> <step-id> "New label"` updates one click after a control is renamed. The billing portal records the same events a person produces: `POST /showme/record` while the page is used, then `GET /showme/recording`.

`showme record --portal-url http://127.0.0.1:PORT --out run.json` opens that page and waits until you press Enter, then writes the event list. `--fetch` skips the browser and the prompt. Two saved runs become a demonstration with `showme record --bundle run1.json run2.json --name ... --description ... --explanation ... --success ... --out demonstration.json`.

`python -m showme.mcp` exposes `showme_induce`, `showme_compile`, and `showme_prove` after `pip install 'showme[mcp]'`. `.bob/mcp.json` points Bob at that module. `showme run --browser` and `showme prove --browser` use Playwright when `pip install 'showme[browser]'` is present, and otherwise print that install line. The default runner stays the stdlib HTML client.

## Tests

The checks are split into four batches. Run them together:

```bash
python -m unittest discover -s tests -v
```

1. `tests/test_model.py` rejects a demonstration that is not a valid skill: bad name, unknown parameter, duplicate parameter, empty steps.
2. `tests/test_compile.py` checks the written folder: `SKILL.md`, `references/trace.json`, `scripts/replay.py`, and a refusal to overwrite an existing skill.
3. `tests/test_sort_replay.py` runs the file chore. Matching files move. Unrelated files stay. An existing destination file stops the run.
4. `tests/test_portal_run.py` starts the sample billing portal and repeats `export-customer-pdf` for customers 1042 and 9921. A missing customer stops before any PDF is written. A click before the page is open fails.
5. `tests/test_cli.py` drives `python -m showme` itself: validate, compile, run the sort, reject a bad `--set`, and run the portal skill twice for customer 9921.
6. `tests/test_induce.py` records two portal runs, induces the customer and the server as parameters, repeats the skill for a customer that was not hard-coded, and halts when the export button is renamed until `retarget` points at the new label.
