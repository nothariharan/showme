"""Compile, replay, and prove ShowMe skills from the command line."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from showme.compile import compile_path, retarget
from showme.html_runner import RunError, HtmlSession
from showme.induce import InduceError, induce_bundle
from showme.model import DemoError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="showme", description="Compile a shown workflow into an Agent Skill.")
    sub = parser.add_subparsers(dest="command", required=True)

    compile_parser = sub.add_parser("compile", help="Write an Agent Skills directory from a demonstration JSON file.")
    compile_parser.add_argument("demonstration", type=Path)
    compile_parser.add_argument("--out", type=Path, required=True, help="Parent directory. The skill folder is created inside it.")

    validate_parser = sub.add_parser("validate", help="Check a demonstration file without writing a skill.")
    validate_parser.add_argument("demonstration", type=Path)

    run_parser = sub.add_parser("run", help="Repeat a compiled skill. Local skills run replay.py. HTML skills run against the live page.")
    run_parser.add_argument("skill", type=Path)
    run_parser.add_argument("--set", action="append", default=[], metavar="NAME=VALUE")

    induce_parser = sub.add_parser("induce", help="Compile two or more demonstrations into one parameterized demonstration.")
    induce_parser.add_argument("bundle", type=Path)
    induce_parser.add_argument("--out", type=Path, required=True)

    retarget_parser = sub.add_parser("retarget", help="Point one click in a compiled skill at a renamed control.")
    retarget_parser.add_argument("skill", type=Path)
    retarget_parser.add_argument("step_id")
    retarget_parser.add_argument("target")

    prove_parser = sub.add_parser("prove", help="Run an HTML skill and check the tax PDF it downloaded.")
    prove_parser.add_argument("skill", type=Path)
    prove_parser.add_argument("--set", action="append", default=[], metavar="NAME=VALUE")
    prove_parser.add_argument("--download-dir", type=Path, required=True)
    prove_parser.add_argument(
        "--customer",
        help="Customer id that must appear in the PDF name and text. Defaults to customer_id, then customer_search_box.",
    )

    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            from showme.model import load_demonstration

            demo = load_demonstration(args.demonstration)
            print(f"{demo.name}: {len(demo.steps)} steps, {len(demo.parameters)} parameters")
            return 0
        if args.command == "run":
            return _run_skill(args.skill, args.set)
        if args.command == "prove":
            return _prove_skill(args.skill, args.set, args.download_dir, args.customer)
        if args.command == "induce":
            demonstration = induce_bundle(json.loads(args.bundle.read_text(encoding="utf-8")))
            args.out.write_text(json.dumps(demonstration, indent=2) + "\n", encoding="utf-8")
            print(args.out)
            return 0
        if args.command == "retarget":
            retarget(args.skill, args.step_id, args.target)
            print(f"{args.step_id} now clicks {args.target}")
            return 0
        skill_dir = compile_path(args.demonstration, args.out)
    except (DemoError, InduceError, FileExistsError, OSError, json.JSONDecodeError, RunError, KeyError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print(skill_dir)
    return 0


def _apply_sets(trace: dict, pairs: list[str]) -> dict[str, str] | None:
    params = {item["name"]: item.get("example", "") for item in trace.get("parameters", [])}
    for pair in pairs:
        if "=" not in pair:
            print(f"expected name=value, got {pair}", file=sys.stderr)
            return None
        key, value = pair.split("=", 1)
        if key not in params:
            print(f"unknown parameter {key}", file=sys.stderr)
            return None
        params[key] = value
    return params


def _run_skill(skill: Path, pairs: list[str]) -> int:
    trace_path = skill / "references" / "trace.json"
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    params = _apply_sets(trace, pairs)
    if params is None:
        return 2
    executors = {step["executor"] for step in trace["steps"]}
    if executors == {"local"}:
        command = [sys.executable, str(skill / "scripts" / "replay.py")]
        command.extend(arg for pair in pairs for arg in ("--set", pair))
        completed = subprocess.run(command, check=False)
        return completed.returncode
    if executors == {"agent"}:
        page = HtmlSession().run(trace, params)
        print(f"finished on {page.url}")
        return 0
    print("this skill mixes local and agent steps; run those parts separately", file=sys.stderr)
    return 2


def _prove_skill(skill: Path, pairs: list[str], download_dir: Path, customer: str | None) -> int:
    trace = json.loads((skill / "references" / "trace.json").read_text(encoding="utf-8"))
    params = _apply_sets(trace, pairs)
    if params is None:
        return 2
    executors = {step["executor"] for step in trace["steps"]}
    if executors != {"agent"} and executors != {"local"}:
        print("this skill mixes local and agent steps; run those parts separately", file=sys.stderr)
        return 2
    try:
        page = HtmlSession().run(trace, params)
    except RunError as exc:
        _write_proof(download_dir, {"ok": False, "error": str(exc)})
        print(exc, file=sys.stderr)
        return 1
    customer_id = _customer_id(customer, params)
    artifact = download_dir / f"tax-{customer_id}.pdf"
    error = _proof_failure(page.body, artifact, customer_id)
    if error is not None:
        _write_proof(download_dir, {"ok": False, "error": error})
        print(error, file=sys.stderr)
        return 1
    _write_proof(download_dir, {"ok": True, "url": page.url, "artifact": str(artifact)})
    print(f"proof ok {artifact}")
    return 0


def _customer_id(explicit: str | None, params: dict[str, str]) -> str:
    if explicit:
        return explicit
    for name in ("customer_id", "customer_search_box"):
        value = params.get(name, "")
        if value:
            return value
    return ""


def _proof_failure(body: str, artifact: Path, customer_id: str) -> str | None:
    if "Download started" not in body:
        return "page body does not contain 'Download started'"
    if not customer_id:
        return "missing customer id"
    if not artifact.is_file():
        return f"missing {artifact}"
    if customer_id not in artifact.read_text(encoding="utf-8"):
        return f"{artifact.name} does not contain {customer_id}"
    return None


def _write_proof(download_dir: Path, proof: dict[str, object]) -> None:
    download_dir.mkdir(parents=True, exist_ok=True)
    (download_dir / "proof.json").write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
