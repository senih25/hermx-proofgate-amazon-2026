# Product feedback

## Tools, APIs and SDKs used

| Tool | What we used it for |
| --- | --- |
| **MCP Python SDK 1.28.1 (FastMCP)** | Reference server: eight tools over Streamable HTTP at `/mcp`, protocol `2025-11-25`; the official client runs `demo_flow.py`. |
| **Model Context Protocol spec (Streamable HTTP)** | Hand-implemented, stateless JSON-response transport in the Cloudflare Worker. |
| **Cloudflare Workers, Static Assets, Durable Objects (SQLite, free plan)** | The free public live demo, with one isolated sandbox per visitor. |
| **Web Speech API** | Voice in (recognition) and voice out (synthesis) in the Alexa+ experience simulator. |
| **GitHub, GitHub Actions** | Public MIT repository; CI runs 16 tests and the end-to-end MCP conformance flow on every push. |
| **Devpost** | Registration, requirements and submission. |

No AWS services are used in this build, so we are not entering the AWS Builder mini challenge.

## What worked well

- **MCP Python SDK:** a small, auditable tool surface takes very little code; structured tool results make the `say` field for voice output natural; the official client made conformance testing easy.
- **Streamable HTTP:** stateless JSON-response mode is simple enough to implement by hand in a Worker, and the official client interoperated without changes.
- **Cloudflare Durable Objects:** "one object per sandbox" gave per-visitor isolation and serialized writes with almost no code, on the free plan.
- **Devpost:** requiring the track technology in code, not just the README, and rewarding friction logs both raise submission quality.

## What needs work

- **Alexa+ onboarding:** the step from "spec-compliant self-hosted MCP server" to "validated in the Alexa+ developer workflow" needs a preflight checklist and a validator (reachability, protocol revision, auth expectations, tool enumeration).
- **Confirmation on consequential actions:** there is no documented Alexa+ pattern for spoken, plan-bound confirmation of risky MCP tool calls; every builder has to invent one (friction #7).
- **Python hosting for judging:** no obvious free, always-on host for a Python MCP server led us to port to JavaScript (friction #5).
- **MCP spec:** a single checklist for a minimal stateless Streamable HTTP server would save trial and error (friction #6).
- **MCP Python SDK docs:** make the `isError=true` result-versus-exception behaviour more prominent (friction #2).

## Onboarding

Getting a local MCP server running was fast. The time went into proving behaviour: client error semantics, CI packaging, and making two runtimes provably equivalent. The Alexa+ track requirement itself (MCP `2025-11-25+` over Streamable HTTP, or an Agent Skill) is clear.

## Would we build with these again?

- **MCP (both SDK and spec): yes.** The protocol boundary is the right place to enforce authorization and verification for agent actions.
- **Cloudflare Workers + Durable Objects: yes,** for free, isolated public demos.
- **Alexa+ self-hosted MCP path: yes,** and a platform-level confirmation pattern for consequential tools would make it much stronger.
