# Changelog

## 0.2.0 — 2026-09-22

Merged the Recall learning coach into ProofGate, making one product:

- risk-tiered effects: routine reviews (`next_review`, `grade_answer`, `progress`) run instantly; `import_deck`, `reset_topic` and `delete_topic` go through plan → approve → execute → verify;
- plan-time prediction of the post-change topic digest, compared at verification;
- hash-chained audit log covering routine effects, approvals, rejections, drift blocks and verifications;
- voice-friendly approval: case- and spacing-insensitive, still bound to one plan;
- deterministic cloze-card extraction, spoken-answer grading and SM-2 scheduling;
- Cloudflare Worker port with one Durable Object per sandbox, deployed as a free public live demo;
- new Alexa+ experience simulator in which the page is itself an MCP client;
- `demo_flow.py` became a 12-check conformance run for any endpoint (`--url`), and CI now runs it end to end;
- Python/JavaScript parity test; 16 tests total;
- removed `demo_web.py`: the simulator talks to `/mcp` directly, so it no longer needs a subprocess bridge.

## 0.1.1 — 2026-09-22

- added a browser-based Alexa+ simulation UI that executes the real MCP E2E flow;
- upgraded the MCP Python SDK to `1.28.1`, the first patched release for the surfaced high-severity advisory;
- re-ran 5/5 tests and the Streamable HTTP plan → block → approve → execute → verify flow successfully.

## 0.1.0 — 2026-09-22

Hackathon-period clean-room implementation: bounded action planning, exact plan-bound approval, pre-execution drift protection, sandbox execution, SHA-256 post-action verification, Streamable HTTP MCP wrapper, unit tests and disclosure boundary documentation.

No proprietary HERMX source was copied into this repository.
