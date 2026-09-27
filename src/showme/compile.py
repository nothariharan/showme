"""Turn a ShowMe demonstration into an Agent Skills directory.

The output follows https://agentskills.io/specification. Coding agents discover
SKILL.md. They do not need to understand this package.
"""

from __future__ import annotations

import json
from pathlib import Path

from showme.model import Demonstration, load_demonstration

REPLAY_SOURCE = r'''"""Player for one ShowMe skill. Uses only the standard library.

Local steps run here. Agent steps are printed for the coding agent to perform.
The trace lives in references/trace.json beside this script.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import shutil
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
TRACE_PATH = SKILL_ROOT / "references" / "trace.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Repeat the ShowMe skill in this folder.")
    parser.add_argument("--set", action="append", default=[], metavar="NAME=VALUE", help="Override a parameter. Repeatable.")
    args = parser.parse_args(argv)
    trace = json.loads(TRACE_PATH.read_text(encoding="utf-8"))
    params = {item["name"]: item.get("example", "") for item in trace.get("parameters", [])}
    for pair in args.set:
        if "=" not in pair:
            print(f"expected name=value, got {pair}", file=sys.stderr)
            return 2
        key, value = pair.split("=", 1)
        if key not in params:
            print(f"unknown parameter {key}", file=sys.stderr)
            return 2
        params[key] = value
    return run(trace, params)


def run(trace: dict, params: dict[str, str]) -> int:
    agent_steps: list[str] = []
    for step in trace["steps"]:
        fields = {key: _fill(value, params) for key, value in step["fields"].items()}
        if step["executor"] == "agent":
            rendered = ", ".join(f"{key}={value}" for key, value in fields.items())
            line = f"agent step {step['id']}: {step['action']} {rendered}"
            agent_steps.append(line)
            print(line)
            continue
        _run_local(step["action"], fields)
        print(f"local step {step['id']}: {step['action']} ok")
    if agent_steps:
        print(f"{len(agent_steps)} step(s) are for the agent named in SKILL.md")
    print(f"success check: {trace['success']}")
    return 0


def _run_local(action: str, fields: dict[str, str]) -> None:
    if action == "ensure_dir":
        Path(fields["path"]).mkdir(parents=True, exist_ok=True)
        return
    if action == "move_matching":
        source = Path(fields["source"])
        destination = Path(fields["destination"])
        destination.mkdir(parents=True, exist_ok=True)
        if not source.exists():
            return
        for path in source.iterdir():
            if path.is_file() and fnmatch.fnmatch(path.name.lower(), fields["pattern"].lower()):
                target = destination / path.name
                if target.exists():
                    raise SystemExit(f"refusing to overwrite {target}")
                shutil.move(str(path), str(target))
        return
    if action == "assert_none_matching":
        source = Path(fields["source"])
        if not source.exists():
            return
        left = [
            path.name
            for path in source.iterdir()
            if path.is_file() and fnmatch.fnmatch(path.name.lower(), fields["pattern"].lower())
        ]
        if left:
            raise SystemExit(f"files still matching {fields['pattern']}: {', '.join(left)}")
        return
    raise SystemExit(f"no local runner for {action}")


def _fill(text: str, params: dict[str, str]) -> str:
    for key, value in params.items():
        text = text.replace("{" + key + "}", value)
    return text


if __name__ == "__main__":
    sys.exit(main())
'''


def compile_demonstration(demo: Demonstration, out_dir: Path) -> Path:
    skill_dir = out_dir / demo.name
    if skill_dir.exists():
        raise FileExistsError(f"{skill_dir} already exists")
    scripts = skill_dir / "scripts"
    references = skill_dir / "references"
    scripts.mkdir(parents=True)
    references.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(_skill_md(demo), encoding="utf-8")
    (references / "trace.json").write_text(_trace_json(demo), encoding="utf-8")
    (scripts / "replay.py").write_text(REPLAY_SOURCE, encoding="utf-8")
    return skill_dir


def compile_path(demonstration: Path, out_dir: Path) -> Path:
    return compile_demonstration(load_demonstration(demonstration), out_dir)


def retarget(skill_dir: Path, step_id: str, new_target: str) -> None:
    trace_path = skill_dir / "references" / "trace.json"
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    matched = [step for step in trace["steps"] if step["id"] == step_id]
    if len(matched) != 1:
        raise KeyError(f"skill has no single step {step_id!r}")
    fields = matched[0].get("fields")
    if not isinstance(fields, dict) or "target" not in fields:
        raise KeyError(f"step {step_id} has no target to retarget")
    fields["target"] = new_target
    trace_path.write_text(json.dumps(trace, indent=2) + "\n", encoding="utf-8")
    (skill_dir / "SKILL.md").write_text(_skill_md(demonstration_from_trace(trace)), encoding="utf-8")


def demonstration_from_trace(trace: dict) -> Demonstration:
    from showme.model import parse_demonstration

    steps = []
    for step in trace["steps"]:
        item = {"id": step["id"], "action": step["action"], "narration": step["narration"]}
        item.update(step["fields"])
        steps.append(item)
    return parse_demonstration(
        {
            "name": trace["name"],
            "description": trace["description"],
            "explanation": trace["explanation"],
            "success": trace["success"],
            "parameters": trace["parameters"],
            "steps": steps,
        }
    )


def _skill_md(demo: Demonstration) -> str:
    parameter_lines = "\n".join(
        f"- `{item.name}`: {item.description} Example: `{item.example}`."
        for item in demo.parameters
    ) or "- This skill takes no parameters."
    step_lines = "\n".join(
        f"{index}. **{step.action}** ({step.executor}). {step.narration} "
        + ", ".join(f"`{key}` = `{value}`" for key, value in step.fields.items())
        + "."
        for index, step in enumerate(demo.steps, start=1)
    )
    notes_step = any(step.action == "note_links" for step in demo.steps)
    if notes_step:
        runner = (
            "Do not open GitHub yourself and do not invent issue titles. "
            "Call the ShowMe MCP tool `showme_triage` with the repository URL. "
            "It replays this skill and returns notes/issues.md and notes/pulls.md. "
            "Without MCP, from this skill's folder run "
            "`python -m showme run . --browser --set owner=OWNER --set repo=REPO`."
        )
    elif demo.needs_agent:
        runner = (
            "Run `scripts/replay.py` for the local steps. "
            "Perform every step marked `agent` yourself, in order, using the arguments passed for this run. "
            "Stop if a local step fails or the success check is not true."
        )
    else:
        runner = (
            "Run `scripts/replay.py` with `--set name=value` for each parameter. "
            "Do not redo the work by hand when the script succeeds."
        )
    quoted_description = json.dumps(demo.description, ensure_ascii=False)
    return f"""---
name: {demo.name}
description: {quoted_description}
compatibility: ShowMe skill. Requires Python 3.11+ for scripts/replay.py. Agent steps need a computer-use agent.
metadata:
  author: showme
  version: "0.1.0"
---

# {demo.name}

{demo.explanation}

## When this applies

{demo.description}

## Parameters

{parameter_lines}

Pass each one to the player as `--set name=value`. Values in the trace written as `{{name}}` are these parameters, not constants.

## Steps

{step_lines}

## How to repeat it

{runner}

The full trace is `references/trace.json`.

## Done when

{demo.success}
"""


def _trace_json(demo: Demonstration) -> str:
    payload = {
        "showme": "0.1.0",
        "name": demo.name,
        "description": demo.description,
        "explanation": demo.explanation,
        "success": demo.success,
        "parameters": [
            {"name": item.name, "description": item.description, "example": item.example}
            for item in demo.parameters
        ],
        "steps": [
            {
                "id": step.id,
                "action": step.action,
                "executor": step.executor,
                "narration": step.narration,
                "fields": step.fields,
            }
            for step in demo.steps
        ],
    }
    return json.dumps(payload, indent=2) + "\n"
