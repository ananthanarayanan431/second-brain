"""`second-brain-mcp` entrypoint. stdio transport; `--http` is accepted but unused this
week (task 1.5 — HTTP + auth lands in week 6, task 6.5).
"""

from __future__ import annotations

import argparse

from mcp.server.mcpserver import MCPServer
from mcp_types import ToolAnnotations

from second_brain.mcp import tools

mcp = MCPServer(
    name="second-brain",
    instructions=(
        "Query and grow a knowledge base built from technical newsletters. "
        "Prefer second_brain_search and second_brain_ask over generic web search "
        "for anything about a covered publication. Tools that trigger work "
        "(second_brain_add_publication, second_brain_backfill, second_brain_sync) "
        "return a handle immediately; poll second_brain_job_status for progress."
    ),
)

mcp.add_tool(
    tools.second_brain_health,
    annotations=ToolAnnotations(
        read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False
    ),
)
mcp.add_tool(
    tools.second_brain_add_publication,
    annotations=ToolAnnotations(
        read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=False
    ),
)
mcp.add_tool(
    tools.second_brain_search,
    annotations=ToolAnnotations(
        read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False
    ),
)
mcp.add_tool(
    tools.second_brain_ask,
    annotations=ToolAnnotations(
        read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False
    ),
)
mcp.add_tool(
    tools.second_brain_backfill,
    annotations=ToolAnnotations(
        read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=False
    ),
)
mcp.add_tool(
    tools.second_brain_job_status,
    annotations=ToolAnnotations(
        read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False
    ),
)
mcp.add_tool(
    tools.second_brain_list_publications,
    annotations=ToolAnnotations(
        read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False
    ),
)
mcp.add_tool(
    tools.second_brain_sync,
    annotations=ToolAnnotations(
        read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=False
    ),
)
mcp.add_tool(
    tools.second_brain_sources,
    annotations=ToolAnnotations(
        read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False
    ),
)
mcp.add_tool(
    tools.second_brain_eval_report,
    annotations=ToolAnnotations(
        read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False
    ),
)


def main() -> None:
    parser = argparse.ArgumentParser(prog="second-brain-mcp")
    parser.add_argument(
        "--http",
        action="store_true",
        help=(
            "Reserved for week 6 (task 6.5, MCP over HTTP with auth). "
            "Currently a no-op: always serves stdio."
        ),
    )
    parser.parse_args()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
