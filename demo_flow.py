from __future__ import annotations

import asyncio
import json

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

MCP_URL = "http://127.0.0.1:8767/mcp"


def payload(result):
    if getattr(result, "structuredContent", None):
        return result.structuredContent
    for item in getattr(result, "content", []):
        text = getattr(item, "text", None)
        if text:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {"text": text}
    return {}


def error_text(result) -> str:
    return "\n".join(getattr(item, "text", "") for item in getattr(result, "content", []))


async def main() -> None:
    print("HERMX ProofGate — live MCP demo")
    print(f"Connecting to {MCP_URL} ...")

    async with streamable_http_client(MCP_URL) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            initialized = await session.initialize()
            print(f"INITIALIZE = PASS | protocol={initialized.protocolVersion}")

            listed = await session.list_tools()
            print("TOOLS = " + ", ".join(tool.name for tool in listed.tools))

            plan_result = await session.call_tool(
                "plan_change",
                {
                    "key": "feature_mode",
                    "value": "demo",
                    "reason": "Alexa+ hackathon live demonstration",
                },
            )
            plan = payload(plan_result)
            plan_id = plan["plan_id"]
            approval_phrase = plan["approval_phrase"]
            print(f"PLAN = PASS | {plan['before']} -> {plan['after']} | id={plan_id}")

            blocked = await session.call_tool("execute_change", {"plan_id": plan_id})
            blocked_ok = bool(getattr(blocked, "isError", False)) and "APPROVAL_REQUIRED" in error_text(blocked)
            print("UNAPPROVED_BLOCK = " + ("PASS" if blocked_ok else "FAIL"))

            approved_result = await session.call_tool(
                "approve_change",
                {"plan_id": plan_id, "approval_phrase": approval_phrase},
            )
            approved = payload(approved_result)
            print("APPROVE = " + ("PASS" if approved.get("status") == "APPROVED" else "FAIL"))

            executed_result = await session.call_tool("execute_change", {"plan_id": plan_id})
            executed = payload(executed_result)
            print("EXECUTE = " + ("PASS" if executed.get("status") == "EXECUTED" else "FAIL"))

            verified_result = await session.call_tool("verify_change", {"plan_id": plan_id})
            verified = payload(verified_result)
            verify_ok = verified.get("verified") is True and len(verified.get("state_sha256", "")) == 64
            print("VERIFY = " + ("PASS" if verify_ok else "FAIL"))
            print("EVIDENCE_SHA256 = " + verified.get("state_sha256", ""))

            if not blocked_ok or approved.get("status") != "APPROVED" or executed.get("status") != "EXECUTED" or not verify_ok:
                raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
