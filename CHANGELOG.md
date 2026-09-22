# Changelog

## 0.1.1 — 2026-09-22

- added a browser-based Alexa+ simulation UI that executes the real MCP E2E flow;
- added public-safe architecture and live verification output for demo capture;
- upgraded the MCP Python SDK to `1.28.1`, the first patched release for the surfaced high-severity advisory;
- re-ran 5/5 tests and the Streamable HTTP plan → block → approve → execute → verify flow successfully.

## 0.1.0 — 2026-09-22

Hackathon-period clean-room implementation:

- added bounded action planning;
- added exact plan-bound approval;
- added pre-execution drift protection;
- added sandbox execution;
- added SHA-256 post-action verification;
- added Streamable HTTP MCP wrapper;
- added unit tests and disclosure boundary documentation.

No proprietary HERMX source was copied into this repository.
