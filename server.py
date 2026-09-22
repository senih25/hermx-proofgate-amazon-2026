from __future__ import annotations

import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse

from proofgate_core import ProofGateStore

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
PORT = int(os.environ.get("PROOFGATE_PORT", "8767"))
store = ProofGateStore(os.environ.get("PROOFGATE_RUNTIME", ROOT / "runtime"))

mcp = FastMCP(
    "HERMX ProofGate · Recall",
    instructions=(
        "Hands-free learning coach with approval-gated effects. Routine reviews "
        "(next_review, grade_answer, progress) run directly. Importing, resetting or "
        "deleting a topic must be planned first, approved with the exact spoken "
        "approval phrase, executed, then verified. Read each tool's 'say' field aloud."
    ),
    host=os.environ.get("PROOFGATE_HOST", "127.0.0.1"),
    port=PORT,
    streamable_http_path="/mcp",
    json_response=True,
    stateless_http=True,
)


@mcp.tool()
def proofgate_status() -> dict:
    """Service status, safety contract, audit-chain head and state digest."""
    return store.status()


@mcp.tool()
def progress() -> dict:
    """Spoken recap of cards, learned cards and cards due, per topic."""
    return store.progress()


@mcp.tool()
def next_review(topic: str = "") -> dict:
    """Next due flashcard (optionally within one topic) to read aloud."""
    return store.next_review(topic)


@mcp.tool()
def grade_answer(card_id: str, answer: str) -> dict:
    """Routine effect: grade a spoken answer and reschedule the card (SM-2). Audited, not gated."""
    return store.grade_answer(card_id, answer)


@mcp.tool()
def plan_change(action: str, topic: str, source: str = "", reason: str = "") -> dict:
    """Plan a consequential change without executing it.

    action: import_deck (needs source text), reset_topic, or delete_topic.
    topic: lowercase slug, e.g. "kubernetes".
    """
    return store.plan_change(action, topic, source, reason)


@mcp.tool()
def approve_change(plan_id: str, approval_phrase: str) -> dict:
    """Approve one exact plan with its plan-bound phrase, e.g. "APPROVE 7F3A9C"."""
    return store.approve_change(plan_id, approval_phrase)


@mcp.tool()
def execute_change(plan_id: str) -> dict:
    """Execute an approved plan only if the topic state still matches the plan."""
    return store.execute_change(plan_id)


@mcp.tool()
def verify_change(plan_id: str) -> dict:
    """Verify the result against the approved plan; returns SHA-256 evidence."""
    return store.verify_change(plan_id)


@mcp.custom_route("/", methods=["GET"])
async def index(_: Request):
    return FileResponse(WEB / "index.html")


@mcp.custom_route("/app.js", methods=["GET"])
async def app_js(_: Request):
    return FileResponse(WEB / "app.js", media_type="text/javascript")


@mcp.custom_route("/styles.css", methods=["GET"])
async def styles(_: Request):
    return FileResponse(WEB / "styles.css", media_type="text/css")


@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request):
    return JSONResponse({"ok": True, "service": "hermx-proofgate-recall", "runtime": "python"})


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
