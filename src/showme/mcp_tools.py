"""Plain functions the MCP server exposes. They do not import the MCP SDK."""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlparse

from showme.compile import compile_path
from showme.induce import induce_bundle
from showme.__main__ import _prove_skill, _run_skill

_ROOT = Path(__file__).resolve().parents[2]
_TRIAGE_BUNDLE = _ROOT / "examples" / "triage-repo" / "two-runs.json"
_TRIAGE_DEMO = _ROOT / "examples" / "triage-repo" / "demonstration.json"
_TRIAGE_SKILL = _ROOT / ".agents" / "skills" / "triage-repo"


def tool_induce(bundle: str, out: str) -> str:
    demonstration = induce_bundle(json.loads(Path(bundle).read_text(encoding="utf-8")))
    destination = Path(out)
    destination.write_text(json.dumps(demonstration, indent=2) + "\n", encoding="utf-8")
    return str(destination)


def tool_compile(demonstration: str, out: str) -> str:
    return str(compile_path(Path(demonstration), Path(out)))


def parse_repository(repository: str) -> tuple[str, str]:
    text = repository.strip().rstrip("/")
    if "github.com" in text:
        parts = [part for part in urlparse(text).path.split("/") if part]
    elif text.count("/") == 1:
        parts = text.split("/", 1)
    else:
        parts = []
    if len(parts) < 2 or not parts[0] or not parts[1]:
        raise ValueError("repository must be owner/repo or a https://github.com/owner/repo URL")
    return parts[0], parts[1]


def ensure_triage_skill() -> Path:
    trace = _TRIAGE_SKILL / "references" / "trace.json"
    if trace.is_file():
        return _TRIAGE_SKILL
    if not _TRIAGE_BUNDLE.is_file():
        raise FileNotFoundError(f"missing {_TRIAGE_BUNDLE}")
    _TRIAGE_DEMO.parent.mkdir(parents=True, exist_ok=True)
    tool_induce(str(_TRIAGE_BUNDLE), str(_TRIAGE_DEMO))
    _TRIAGE_SKILL.parent.mkdir(parents=True, exist_ok=True)
    return Path(tool_compile(str(_TRIAGE_DEMO), str(_TRIAGE_SKILL.parent)))


@contextmanager
def _working_directory(path: Path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def tool_run(skill: str, sets: list[str] | None = None, headed: bool = False) -> str:
    skill_path = Path(skill)
    with _working_directory(skill_path):
        code = _run_skill(skill_path, list(sets or []), browser=True, headed=headed)
    if code != 0:
        raise RuntimeError(f"showme run exited {code}")
    notes_dir = skill_path / "notes"
    parts: list[str] = []
    if notes_dir.is_dir():
        for path in sorted(notes_dir.glob("*.md")):
            parts.append(path.read_text(encoding="utf-8").rstrip())
    if not parts:
        raise RuntimeError(f"run finished without notes in {notes_dir}")
    return "\n\n".join(parts) + "\n"


def tool_triage(repository: str, headed: bool = False) -> str:
    owner, repo = parse_repository(repository)
    skill = ensure_triage_skill()
    return tool_run(str(skill), [f"owner={owner}", f"repo={repo}"], headed=headed)


def tool_prove(skill: str, download_dir: str, sets: list[str] | None = None, customer: str | None = None) -> str:
    code = _prove_skill(Path(skill), list(sets or []), Path(download_dir), customer)
    proof_path = Path(download_dir) / "proof.json"
    body = proof_path.read_text(encoding="utf-8") if proof_path.is_file() else ""
    if code != 0:
        raise RuntimeError(body or f"prove exited {code}")
    return body
