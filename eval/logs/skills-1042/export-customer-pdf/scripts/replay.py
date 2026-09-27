"""Player for one ShowMe skill. Uses only the standard library.

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
