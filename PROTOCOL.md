# ShowMe protocol

ShowMe is a small input format that compiles into an [Agent Skill](https://agentskills.io/specification). Claude Code, Cursor, and Codex already load that folder. ShowMe does not define a second skill format.

A workflow is two things the person provides:

1. **The explanation.** When to run it, what must stay constant, and which values change. This becomes `SKILL.md`.
2. **The demonstration.** The ordered steps of the work, each with a narration of why that step exists. This becomes `references/trace.json` and, for local steps, `scripts/replay.py`.

An agent that has never seen the original session repeats the work by reading the skill and running the player with new parameter values.

## File layout

Input, written by a person or by a future recorder:

```text
examples/sort-downloads/demonstration.json
```

Output, one directory per workflow:

```text
sort-downloads/
├── SKILL.md                 # required by the Agent Skills spec
├── references/trace.json    # normalized steps, parameters, success check
└── scripts/replay.py        # standard-library player
```

Put that directory in `.agents/skills/`, `.claude/skills/`, or `.cursor/skills/`. The `name` in `SKILL.md` matches the directory name. `description` says what the skill does and when to use it, which is how agents decide to load it.

## Step language, version 0.1

Local steps run inside `scripts/replay.py` with no model call:

| Action | Fields | Effect |
| --- | --- | --- |
| `ensure_dir` | `path` | Create a directory. |
| `move_matching` | `source`, `pattern`, `destination` | Move files in `source` whose names match the glob. |
| `assert_none_matching` | `source`, `pattern` | Fail if any matching file is still there. |

Agent steps are instructions. The player prints them. The coding agent performs them on the live screen:

| Action | Fields |
| --- | --- |
| `navigate` | `url` |
| `click` | `target` |
| `type` | `target`, `text` |
| `press` | `key` |
| `wait_for` | `text` |

`{parameter}` inside a field is an input, not a constant. Every placeholder must be declared in `parameters`.

## Induction

One recording is evidence, not a spec. `showme induce` takes a bundle of two or more runs. A typed value or an origin that differs becomes a parameter. A click label, a path, or a success check that differs is rejected. The command does not guess.

The billing portal records the events while the page is used (`POST /showme/record`, `GET /showme/recording`). Those events are the runs in the bundle. See `examples/export-customer-pdf/two-runs.json`.

If a later run cannot find a control, the player stops and lists the labels that are actually on the page. `showme retarget <skill> <step-id> "New label"` writes the new label into the trace and `SKILL.md`. It does not click a nearby control.

## What this is not yet

Version 0.1 does not read an mp4 or watch pixels. The recording is the action trace (navigate, type, click, wait), which is what a recorder already knows. The skill folder stays the same, so agents do not have to change when a screen recorder is added later.

The industry pieces ShowMe reuses, and does not replace:

- Agent Skills, for discovery and invocation.
- A deterministic player for steps a machine can check, the same idea as a macro or a Playwright script.
- Prose instructions for steps that still need an agent looking at a screen.

## Compile and run

```bash
python -m showme compile examples/sort-downloads/demonstration.json --out .agents/skills
python -m showme run .agents/skills/sort-downloads --set source_dir=C:/path/to/inbox
```

`showme run` on an HTML skill reads `references/trace.json`, opens `portal_url`, and activates each control by the visible text in the step (`Search`, `Tax summary`, `Export PDF`). The sample portal is `examples/billing_portal/server.py`.
