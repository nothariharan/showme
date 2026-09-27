"""Plain functions the MCP server exposes. They do not import the MCP SDK."""

from __future__ import annotations

import json
from pathlib import Path

from showme.compile import compile_path
from showme.induce import induce_bundle
from showme.__main__ import _prove_skill


def tool_induce(bundle: str, out: str) -> str:
    demonstration = induce_bundle(json.loads(Path(bundle).read_text(encoding="utf-8")))
    destination = Path(out)
    destination.write_text(json.dumps(demonstration, indent=2) + "\n", encoding="utf-8")
    return str(destination)


def tool_compile(demonstration: str, out: str) -> str:
    return str(compile_path(Path(demonstration), Path(out)))


def tool_prove(skill: str, download_dir: str, sets: list[str] | None = None, customer: str | None = None) -> str:
    code = _prove_skill(Path(skill), list(sets or []), Path(download_dir), customer)
    proof_path = Path(download_dir) / "proof.json"
    body = proof_path.read_text(encoding="utf-8") if proof_path.is_file() else ""
    if code != 0:
        raise RuntimeError(body or f"prove exited {code}")
    return body
