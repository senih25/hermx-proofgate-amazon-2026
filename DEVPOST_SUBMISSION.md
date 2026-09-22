# Devpost submission copy

## Project name
HERMX ProofGate: Recall

## Tagline
A voice study coach for Alexa+ that reviews instantly and never changes your decks without your exact approval.

## Links
- Live demo: https://hermx-proofgate-recall.senih-bayankulu25.workers.dev
- Live MCP endpoint: https://hermx-proofgate-recall.senih-bayankulu25.workers.dev/mcp
- Repository: https://github.com/senih25/hermx-proofgate-amazon-2026
- Demo video: https://youtu.be/nxf7_ZA5bQo

## About the project (Devpost story, Markdown)

### Inspiration
Voice assistants are becoming agents: they don't only answer, they change things. That creates a design problem nobody can dodge. If the assistant asks "are you sure?" before every action, voice becomes unbearable. If it treats "yeah, go ahead" as permission for everything, one misheard sentence can wipe out weeks of someone's work.

We wanted to show the middle path in a product people would actually use hands-free: studying.

### What it does
**Recall** is a spaced-repetition coach for Alexa+, served by a self-hosted **MCP server over Streamable HTTP (protocol 2025-11-25)**. **HERMX ProofGate** decides which actions need approval.

- **Routine actions run instantly.** "Quiz me", spoken answers and "how am I doing?" never prompt. Answers are graded and rescheduled with SM-2. Each effect still extends a **SHA-256 audit chain**.
- **Consequential actions are gated.** Importing, resetting or deleting a deck follows **plan → approve → execute → verify**:
  - **Plan:** Recall shows exactly what will change, plus the topic's digest now and the digest it will have afterwards. Nothing is written.
  - **Approve:** only the plan's own phrase works, for example "approve 7 F 3 A 9 C". "Yes, go ahead" is rejected and logged.
  - **Execute:** Recall re-checks the topic first. If anything changed since the plan (say, you reviewed a card), the stale approval is refused with `STATE_DRIFT`.
  - **Verify:** the result is compared with the digest predicted at plan time, and the card gets stamped.

The **live demo** is an Alexa+ experience simulator (voice in and out through the Web Speech API). The page is a real MCP client: every bubble on screen is a JSON-RPC call to `/mcp`. **Play guided demo** walks through the whole story in about a minute.

### How we built it
- **Python reference server:** official MCP Python SDK 1.28.1 (FastMCP), eight tools, Streamable HTTP at `/mcp`.
- **Free public live demo:** the same contract ported to a **Cloudflare Worker**, with **one SQLite-backed Durable Object per visitor sandbox**, so judges never see each other's data.
- **Deterministic learning core:** cloze flashcards are extracted from the user's text without an LLM, and answers are graded by edit distance. Because extraction is deterministic, the server can **predict the post-change digest at plan time**, which is what makes verification meaningful.
- **Proof, not claims:** `demo_flow.py` runs **12 conformance checks** through the official MCP Python client against any endpoint. They pass on the local server, in CI on every push, and on the live Worker. **16 tests** cover the gate, the effect boundary and **Python/JavaScript parity**.

### Challenges we ran into
- **Exact vs speakable approval.** Speech recognition returns "approve 7 f 3 a 9 c" or "Approve 7F3A9C". We normalise case and spacing but keep approval bound to one plan.
- **Two runtimes, one contract.** No free host fit a Python MCP server for judging, so we ported to a Worker and built a parity test so the demo can't drift from the reference.
- **Hand-rolling stateless Streamable HTTP:** JSON responses, 202 for notifications, 405 for GET, and protocol-version checks, validated with the official client.

### Accomplishments that we're proud of
- A voice product where safety is **visible**: you can watch a plan, an approval, a drift block and a verification stamp happen.
- **Every** effect is evidenced, including the ones we deliberately don't gate.
- A **free, public, isolated live demo** with the same guarantees as the reference server.

### What we learned
Agent safety isn't "confirm everything". It's deciding which effects are consequential, binding approval to exactly what the user saw, and checking the world didn't change in between.

### What's next
Connect the verified endpoint into the Alexa+ developer workflow, add authenticated per-user sandboxes, and offer the ProofGate tiering as a reusable pattern for other Alexa+ skills.

## Track
Alexa+

## Open Source mini challenge
- **Repository:** https://github.com/senih25/hermx-proofgate-amazon-2026 (MIT, public)
- **GitHub username:** senih25
- **What / how / why:** An open-source reference for risk-tiered, approval-gated MCP actions in a voice product. It includes the Python server, a Cloudflare Worker port, a conformance harness usable against any MCP endpoint, and parity tests. It matters because every Alexa+ builder shipping consequential actions needs this pattern, and none should have to reinvent it.

## AWS Builder mini challenge
Not entered: this build uses no AWS services.

## Built during the submission window
All code in this repository was written during the hackathon window, clean-room. The learning-coach half began as a separate prototype (`senih25/recall-alexa-mcp`) and was merged in v0.2.0.

## Built with
python, mcp-python-sdk, model-context-protocol, streamable-http, cloudflare-workers, durable-objects, javascript, web-speech-api, html, css, sha-256, github-actions
