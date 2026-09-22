"""End-to-end MCP conformance flow, run with the official MCP Python client.

    python demo_flow.py                                   # local Python server
    python demo_flow.py --url https://<live-demo>/mcp     # live Cloudflare Worker

Every gate is exercised through real MCP tool calls; exit code is non-zero if
any check fails. Uses a fresh topic and deletes it (through the gate) at the end.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import uuid

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

SOURCE = (
    "MCP is the Model Context Protocol for agent tools. "
    "Streamable HTTP is the remote transport defined in the 2025-11-25 specification. "
    "Alexa+ can reach a self-hosted server through Agent Skills. "
    "ProofGate re-checks a SHA-256 digest of the topic right before any approved change."
)
EXPECTED_TOOLS = {
    "proofgate_status", "progress", "next_review", "grade_answer",
    "plan_change", "approve_change", "execute_change", "verify_change",
}


def payload(result) -> dict:
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
    return "\n".join(getattr(i, "text", "") for i in getattr(result, "content", []))


class Checks:
    def __init__(self) -> None:
        self.failed = 0

    def __call__(self, name: str, ok: bool, detail: str = "") -> None:
        self.failed += not ok
        print(f"{name:<22}= {'PASS' if ok else 'FAIL'}" + (f" | {detail}" if detail else ""), flush=True)


async def run(url: str) -> int:
    check = Checks()
    topic = f"demo-{uuid.uuid4().hex[:6]}"
    print(f"HERMX ProofGate · Recall — MCP conformance flow\nendpoint: {url}\ntopic:    {topic}")
    async with streamable_http_client(url) as streams:
        async with ClientSession(streams[0], streams[1]) as s:
            init = await s.initialize()
            check("INITIALIZE", bool(init.protocolVersion), f"protocol={init.protocolVersion} server={init.serverInfo.name}")
            tools = {t.name for t in (await s.list_tools()).tools}
            check("TOOL_DISCOVERY", EXPECTED_TOOLS <= tools, f"{len(tools)} tools")

            async def call(name: str, **args):
                return await s.call_tool(name, args)

            plan = payload(await call("plan_change", action="import_deck", topic=topic, source=SOURCE, reason="conformance"))
            check("PLAN_IMPORT", plan.get("status") == "PLANNED", plan.get("effect_summary", ""))
            pid, phrase = plan["plan_id"], plan["approval_phrase"]

            blocked = await call("execute_change", plan_id=pid)
            check("UNAPPROVED_BLOCK", blocked.isError and "APPROVAL_REQUIRED" in error_text(blocked))
            wrong = await call("approve_change", plan_id=pid, approval_phrase="yes")
            check("WRONG_PHRASE_REJECT", wrong.isError and "APPROVAL_MISMATCH" in error_text(wrong))

            code = phrase.split()[1]
            spoken = "approve " + " ".join(code.lower())
            approved = payload(await call("approve_change", plan_id=pid, approval_phrase=spoken))
            check("VOICE_APPROVAL", approved.get("status") == "APPROVED", f'"{spoken}"')
            executed = payload(await call("execute_change", plan_id=pid))
            check("EXECUTE", executed.get("status") == "EXECUTED", executed.get("effect_summary", ""))
            verified = payload(await call("verify_change", plan_id=pid))
            check("VERIFY", verified.get("verified") is True, "topic_sha256=" + verified.get("actual_topic_sha256", "")[:16] + "…")

            card = payload(await call("next_review", topic=topic))
            graded = payload(await call("grade_answer", card_id=card.get("card_id", ""), answer="not sure"))
            check("ROUTINE_REVIEW", "grade" in graded and len(graded.get("audit_head", "")) == 64,
                  f"ungated, audited grade={graded.get('grade')}")

            reset = payload(await call("plan_change", action="reset_topic", topic=topic, reason="drift check"))
            await call("approve_change", plan_id=reset["plan_id"], approval_phrase=reset["approval_phrase"])
            nxt = payload(await call("next_review", topic=topic))
            await call("grade_answer", card_id=nxt.get("card_id", ""), answer="still unsure")
            drift = await call("execute_change", plan_id=reset["plan_id"])
            check("DRIFT_BLOCK", drift.isError and "STATE_DRIFT" in error_text(drift), "state changed after approval")

            delete = payload(await call("plan_change", action="delete_topic", topic=topic, reason="cleanup"))
            await call("approve_change", plan_id=delete["plan_id"], approval_phrase=delete["approval_phrase"])
            gone = payload(await call("execute_change", plan_id=delete["plan_id"]))
            vdel = payload(await call("verify_change", plan_id=delete["plan_id"]))
            check("GATED_DELETE", gone.get("status") == "EXECUTED" and vdel.get("verified") is True)

            status = payload(await call("proofgate_status"))
            check("AUDIT_CHAIN", len(status.get("audit_head", "")) == 64, f"events={status.get('audit_count')}")
            print("EVIDENCE_STATE_SHA256 = " + vdel.get("state_sha256", ""))
            print("EVIDENCE_AUDIT_HEAD   = " + status.get("audit_head", ""))
    print("RESULT = " + ("ALL CHECKS PASSED" if not check.failed else f"{check.failed} CHECK(S) FAILED"))
    return 1 if check.failed else 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8767/mcp")
    raise SystemExit(asyncio.run(run(parser.parse_args().url)))


if __name__ == "__main__":
    main()
