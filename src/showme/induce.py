"""Turn repeated demonstrations into one parameterized skill.

A value that changes between runs becomes a parameter. A click, a label, or a
success check that changes is a different workflow, and induction refuses it
instead of guessing.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from showme.model import parse_demonstration

_SLUG_RE = re.compile(r"[^a-z0-9]+")


class InduceError(ValueError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("\n".join(errors))


def induce_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    for key in ("name", "description", "explanation", "success"):
        if not isinstance(bundle.get(key), str) or not bundle[key].strip():
            errors.append(f"{key} is required")
    runs = bundle.get("runs")
    if not isinstance(runs, list) or len(runs) < 2:
        errors.append("runs must contain at least two demonstrations")
        runs = []
    parsed: list[list[dict[str, Any]]] = []
    for index, run in enumerate(runs, start=1):
        if not isinstance(run, dict):
            errors.append(f"runs[{index}] must be an object")
            continue
        if "events" in run:
            parsed.append(steps_from_events(run["events"], label=f"runs[{index}]"))
        elif isinstance(run.get("steps"), list):
            parsed.append(run["steps"])
        else:
            errors.append(f"runs[{index}] needs events or steps")
    if errors:
        raise InduceError(errors)
    return induce_runs(
        parsed,
        name=bundle["name"].strip(),
        description=bundle["description"].strip(),
        explanation=bundle["explanation"].strip(),
        success=bundle["success"].strip(),
    )


def steps_from_events(events: list[dict[str, Any]], label: str = "events") -> list[dict[str, Any]]:
    if not isinstance(events, list) or not events:
        raise InduceError([f"{label} must be a non-empty list"])
    steps: list[dict[str, Any]] = []
    for index, event in enumerate(events, start=1):
        if not isinstance(event, dict) or "type" not in event:
            raise InduceError([f"{label}[{index}] must be an object with type"])
        kind = event["type"]
        step_id = str(event.get("id") or f"step-{index}")
        if kind == "navigate":
            steps.append(_event_step(step_id, "navigate", "Opened this page.", url=_need(event, "url", label, index)))
        elif kind == "type":
            steps.append(
                _event_step(
                    step_id,
                    "type",
                    "Typed the value that can change between runs.",
                    target=_need(event, "target", label, index),
                    text=_need(event, "text", label, index),
                )
            )
        elif kind == "click":
            steps.append(
                _event_step(
                    step_id,
                    "click",
                    "Activated the control with this visible label.",
                    target=_need(event, "target", label, index),
                )
            )
        elif kind == "wait_for":
            steps.append(
                _event_step(
                    step_id,
                    "wait_for",
                    "Finished only when this text was on the page.",
                    text=_need(event, "text", label, index),
                )
            )
        else:
            raise InduceError([f"{label}[{index}] has unknown event type {kind!r}"])
    return steps


def induce_runs(
    runs: list[list[dict[str, Any]]],
    *,
    name: str,
    description: str,
    explanation: str,
    success: str,
) -> dict[str, Any]:
    if len(runs) < 2:
        raise InduceError(["at least two runs are required"])
    width = len(runs[0])
    if width == 0 or any(len(run) != width for run in runs):
        raise InduceError(["every run must contain the same non-empty number of steps"])

    parameters: dict[str, str] = {}
    steps: list[dict[str, Any]] = []
    errors: list[str] = []
    for index, first in enumerate(runs[0]):
        action = first.get("action")
        if not isinstance(action, str):
            errors.append(f"step {index + 1} is missing action")
            continue
        for run_index, run in enumerate(runs[1:], start=2):
            if run[index].get("action") != action:
                errors.append(f"step {index + 1} is {action} in run 1 and {run[index].get('action')} in run {run_index}")
        reserved = {"id", "action", "narration", "executor"}
        keys = [key for key in first if key not in reserved]
        fields: dict[str, str] = {}
        for key in keys:
            values = [_field(run[index], key) for run in runs]
            if any(value is None for value in values):
                errors.append(f"step {index + 1} field {key} is missing in a run")
                continue
            texts = [str(value) for value in values]
            if len(set(texts)) == 1:
                fields[key] = texts[0]
                continue
            placeholder = _varying_field(action, key, first, texts, parameters, errors, index)
            if placeholder:
                fields[key] = placeholder
        if not errors:
            steps.append(
                {
                    "id": str(first.get("id") or f"step-{index + 1}"),
                    "action": action,
                    "narration": str(first.get("narration") or "Repeated from the demonstration."),
                    **fields,
                }
            )
    if errors:
        raise InduceError(errors)
    demonstration = {
        "name": name,
        "description": description,
        "explanation": explanation,
        "success": success,
        "parameters": [
            {
                "name": param,
                "description": f"Changes between demonstrations. Example taken from the first run.",
                "example": example,
            }
            for param, example in parameters.items()
        ],
        "steps": steps,
    }
    parse_demonstration(demonstration)
    return demonstration


def _varying_field(
    action: str,
    key: str,
    step: dict[str, Any],
    values: list[str],
    parameters: dict[str, str],
    errors: list[str],
    index: int,
) -> str:
    if action == "type" and key == "text":
        target = step.get("target")
        if not isinstance(target, str) or not target.strip():
            errors.append(f"step {index + 1} changes typed text but has no target to name the parameter")
            return ""
        return "{" + _bind(parameters, _slug(target), values[0]) + "}"
    if action == "navigate" and key == "url":
        origins = []
        paths = []
        for value in values:
            parsed = urlparse(value)
            if not parsed.scheme or not parsed.netloc:
                errors.append(f"step {index + 1} has a relative url {value!r} and runs disagree")
                return ""
            origins.append(f"{parsed.scheme}://{parsed.netloc}")
            rest = parsed.path or "/"
            if parsed.query:
                rest += "?" + parsed.query
            paths.append(rest)
        if len(set(paths)) != 1:
            errors.append(f"step {index + 1} changes the path, not just the server")
            return ""
        return "{" + _bind(parameters, "portal_url", origins[0]) + "}" + paths[0]
    errors.append(
        f"step {index + 1} field {key} differs across runs ({values[0]!r} vs {values[1]!r}) and is not an input"
    )
    return ""


def _bind(parameters: dict[str, str], name: str, example: str) -> str:
    if name not in parameters:
        parameters[name] = example
        return name
    if parameters[name] == example:
        return name
    suffix = 2
    while f"{name}_{suffix}" in parameters:
        suffix += 1
    renamed = f"{name}_{suffix}"
    parameters[renamed] = example
    return renamed


def _slug(text: str) -> str:
    slug = _SLUG_RE.sub("_", text.lower()).strip("_")
    if not slug or not slug[0].isalpha():
        slug = f"value_{slug}".strip("_")
    return slug[:48]


def _field(step: dict[str, Any], key: str) -> Any:
    if key in step:
        return step[key]
    fields = step.get("fields")
    if isinstance(fields, dict) and key in fields:
        return fields[key]
    return None


def _need(event: dict[str, Any], key: str, label: str, index: int) -> str:
    value = event.get(key)
    if not isinstance(value, str) or not value.strip():
        raise InduceError([f"{label}[{index}] requires {key}"])
    return value.strip()


def _event_step(step_id: str, action: str, narration: str, **fields: str) -> dict[str, Any]:
    return {"id": step_id, "action": action, "narration": narration, **fields}
