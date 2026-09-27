"""Demonstration document. This is the ShowMe input. The Agent Skill folder is the output."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PLACEHOLDER_RE = re.compile(r"\{([a-z][a-z0-9_]*)\}")

LOCAL_ACTIONS = {
    "ensure_dir": ("path",),
    "move_matching": ("source", "pattern", "destination"),
    "assert_none_matching": ("source", "pattern"),
}
AGENT_ACTIONS = {
    "navigate": ("url",),
    "click": ("target",),
    "type": ("target", "text"),
    "press": ("key",),
    "wait_for": ("text",),
    "note_links": ("kind", "path"),
}
ACTIONS = {**LOCAL_ACTIONS, **AGENT_ACTIONS}


class DemoError(ValueError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("\n".join(errors))


@dataclass
class Parameter:
    name: str
    description: str
    example: str


@dataclass
class Step:
    id: str
    action: str
    narration: str
    fields: dict[str, str]
    executor: str


@dataclass
class Demonstration:
    name: str
    description: str
    explanation: str
    parameters: list[Parameter]
    steps: list[Step]
    success: str
    raw: dict[str, Any] = field(repr=False, default_factory=dict)

    @property
    def needs_agent(self) -> bool:
        return any(step.executor == "agent" for step in self.steps)


def load_demonstration(path: Path) -> Demonstration:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise DemoError(["demonstration must be a JSON object"])
    return parse_demonstration(data)


def parse_demonstration(data: dict[str, Any]) -> Demonstration:
    errors: list[str] = []
    name = _string(data, "name", errors)
    description = _string(data, "description", errors)
    explanation = _string(data, "explanation", errors)
    success = _string(data, "success", errors)

    if name and not NAME_RE.match(name):
        errors.append(
            "name must be 1-64 chars, lowercase letters, digits, and single hyphens, "
            "matching the Agent Skills spec"
        )
    if name and len(name) > 64:
        errors.append("name must be at most 64 characters")
    if description and not (1 <= len(description) <= 1024):
        errors.append("description must be 1-1024 characters and say what the skill does and when to use it")

    parameters = _parameters(data.get("parameters", []), errors)
    known = {item.name for item in parameters}
    steps = _steps(data.get("steps"), known, errors)

    if errors:
        raise DemoError(errors)

    return Demonstration(
        name=name,
        description=description,
        explanation=explanation,
        parameters=parameters,
        steps=steps,
        success=success,
        raw=data,
    )


def _parameters(value: Any, errors: list[str]) -> list[Parameter]:
    if not isinstance(value, list):
        errors.append("parameters must be a list")
        return []
    parsed: list[Parameter] = []
    seen: set[str] = set()
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            errors.append(f"parameters[{index}] must be an object")
            continue
        name = _string(item, "name", errors, label=f"parameters[{index}].name")
        description = _string(item, "description", errors, label=f"parameters[{index}].description")
        example = item.get("example", "")
        if not isinstance(example, str):
            errors.append(f"parameters[{index}].example must be a string")
            example = ""
        if name:
            if not re.match(r"^[a-z][a-z0-9_]*$", name):
                errors.append(f"parameters[{index}].name must be lowercase identifier, got {name!r}")
            elif name in seen:
                errors.append(f"duplicate parameter {name!r}")
            else:
                seen.add(name)
                parsed.append(Parameter(name=name, description=description, example=example))
    return parsed


def _steps(value: Any, known: set[str], errors: list[str]) -> list[Step]:
    if not isinstance(value, list) or not value:
        errors.append("steps must be a non-empty list")
        return []
    parsed: list[Step] = []
    seen: set[str] = set()
    for index, item in enumerate(value, start=1):
        label = f"steps[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object")
            continue
        step_id = _string(item, "id", errors, label=f"{label}.id")
        action = _string(item, "action", errors, label=f"{label}.action")
        narration = _string(item, "narration", errors, label=f"{label}.narration")
        if step_id:
            if step_id in seen:
                errors.append(f"duplicate step id {step_id!r}")
            seen.add(step_id)
        if action and action not in ACTIONS:
            errors.append(
                f"{label}.action {action!r} is unknown. "
                f"Local: {', '.join(LOCAL_ACTIONS)}. Agent: {', '.join(AGENT_ACTIONS)}."
            )
            continue
        if not action:
            continue
        required = ACTIONS[action]
        fields: dict[str, str] = {}
        for key in required:
            text = _string(item, key, errors, label=f"{label}.{key}")
            if text:
                fields[key] = text
                _check_placeholders(text, known, f"{label}.{key}", errors)
        if step_id and action and len(fields) == len(required) and narration:
            if action == "note_links" and fields.get("kind") not in {"issues", "pulls"}:
                errors.append(f"{label}.kind must be issues or pulls")
                continue
            executor = "local" if action in LOCAL_ACTIONS else "agent"
            parsed.append(Step(id=step_id, action=action, narration=narration, fields=fields, executor=executor))
    return parsed


def _check_placeholders(text: str, known: set[str], label: str, errors: list[str]) -> None:
    for match in PLACEHOLDER_RE.findall(text):
        if match not in known:
            errors.append(f"{label} uses {{{match}}} but parameters does not declare it")


def _string(data: dict[str, Any], key: str, errors: list[str], label: str | None = None) -> str:
    label = label or key
    if key not in data:
        errors.append(f"{label} is required")
        return ""
    value = data[key]
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label} must be a non-empty string")
        return ""
    return value.strip()


def substitute(text: str, params: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in params:
            raise KeyError(key)
        return params[key]

    return PLACEHOLDER_RE.sub(replace, text)
