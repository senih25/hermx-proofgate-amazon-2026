# Demo video script (target 2:30, hard limit 3:00)

The video is recorded from the live demo at
https://hermx-proofgate-recall.senih-bayankulu25.workers.dev using its **Play guided demo** button,
with narration added in editing. Every on-screen result comes from real MCP calls.

1. **Problem (0:00–0:15).** Voice assistants now take actions. Asking before every small action is unusable; treating "yeah, go ahead" as permission for a big one is unsafe.
2. **Product (0:15–0:30).** Recall: a hands-free study coach for Alexa+, served by a self-hosted MCP server over Streamable HTTP, protocol 2025-11-25. Routine reviews run instantly; deck changes go through ProofGate.
3. **Plan (0:30–0:50).** "Learn this as mcp" produces a plan card: five cards to import, the topic digest now and the digest predicted afterwards, and a one-off approval phrase. Nothing has changed.
4. **Fail closed (0:50–1:00).** "Yes, go ahead" is rejected and logged.
5. **Approve, execute, verify (1:00–1:20).** The exact phrase approves; Recall re-checks the topic, imports, verifies against the predicted digest, and stamps the card.
6. **Routine reviews (1:20–1:40).** Quiz and spoken answers are graded with SM-2, with no prompts, and each still extends the audit chain.
7. **Drift (1:40–2:00).** Plan a reset, review a card, then approve the reset: the stale approval is blocked with `STATE_DRIFT` and nothing changes.
8. **Proof (2:00–2:25).** The official MCP Python client runs the 12-check conformance flow against the live endpoint; CI runs the same flow plus 16 tests on every push.
9. **Close (2:25–2:35).** Live demo URL, MIT-licensed repository, Alexa+ track.
