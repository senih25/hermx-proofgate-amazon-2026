from __future__ import annotations

import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from proofgate_core import ProofGateStore

ROOT = Path(__file__).resolve().parent
PORT = int(os.environ.get("PROOFGATE_PORT", "8767"))
store = ProofGateStore(ROOT / "runtime")

mcp = FastMCP(
    "HERMX ProofGate",
    instructions=(
        "Approval-gated demo MCP. Always plan first, request the exact approval phrase, "
        "execute only after approval, then verify the resulting evidence."
    ),
    host="127.0.0.1",
    port=PORT,
    streamable_http_path="/mcp",
    json_response=True,
    stateless_http=True,
)


@mcp.tool()
def proofgate_status() -> dict:
    """Return the public-safe service status and safety contract."""
    return store.status()


@mcp.tool()
def plan_change(key: str, value: str, reason: str) -> dict:
    """Plan a bounded demo-state change without executing it."""
    return store.plan_change(key, value, reason)


@mcp.tool()
def approve_change(plan_id: str, approval_phrase: str) -> dict:
    """Approve one exact plan using its exact one-shot approval phrase."""
    return store.approve_change(plan_id, approval_phrase)


@mcp.tool()
def execute_change(plan_id: str) -> dict:
    """Execute an approved plan if the pre-execution state still matches."""
    return store.execute_change(plan_id)


@mcp.tool()
def verify_change(plan_id: str) -> dict:
    """Verify the resulting state and return a SHA-256 evidence digest."""
    return store.verify_change(plan_id)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
