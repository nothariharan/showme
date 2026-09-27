"""MCP server for ShowMe. Requires the optional mcp package.

Run with `python -m showme.mcp` after `pip install 'showme[mcp]'`.
Bob, Claude Code, and Cursor can point a stdio MCP entry at that command.
"""

from __future__ import annotations

import sys


def build_server():
    from mcp.server.fastmcp import FastMCP
    from showme.mcp_tools import tool_compile, tool_induce, tool_prove, tool_run, tool_triage

    server = FastMCP("showme")

    @server.tool()
    def showme_induce(bundle: str, out: str) -> str:
        """Turn a two-run bundle JSON file into a parameterized demonstration."""
        return tool_induce(bundle, out)

    @server.tool()
    def showme_compile(demonstration: str, out: str) -> str:
        """Compile a demonstration JSON file into an Agent Skill directory."""
        return tool_compile(demonstration, out)

    @server.tool()
    def showme_prove(skill: str, download_dir: str, sets: list[str] | None = None, customer: str | None = None) -> str:
        """Run a skill and return proof.json. Fails when the PDF check fails."""
        return tool_prove(skill, download_dir, sets, customer)

    @server.tool()
    def showme_run(skill: str, sets: list[str] | None = None, headed: bool = False) -> str:
        """Replay a compiled ShowMe skill in a browser. sets are name=value parameters. Returns the notes it wrote."""
        return tool_run(skill, sets, headed)

    @server.tool()
    def showme_triage(repository: str, headed: bool = False) -> str:
        """Check one public GitHub repository for new issues and pull requests and write the titles into notes.

        repository is owner/repo or a https://github.com/owner/repo URL.
        Uses the triage-repo skill built from two recorded demonstrations.
        Returns the notes. Does not invent titles.
        """
        return tool_triage(repository, headed)

    return server


def main() -> int:
    try:
        server = build_server()
    except ImportError:
        print("The MCP extra is not installed. Install it with: pip install 'showme[mcp]'", file=sys.stderr)
        return 1
    server.run(transport="stdio")
    return 0


if __name__ == "__main__":
    sys.exit(main())
