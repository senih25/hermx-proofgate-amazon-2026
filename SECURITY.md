# Security and disclosure boundary

## Public by design

This repository contains only the hackathon build:

- a Python reference Streamable HTTP MCP server and a Cloudflare Worker port;
- a risk-tiered effect engine: routine reviews and gated deck changes;
- plan-bound approval, drift protection, SHA-256 verification and a hash-chained audit log;
- deterministic flashcard extraction and SM-2 scheduling;
- a browser simulator, tests and public documentation.

## Explicitly excluded

No HERMX commercial source code, provider implementations, private capability maps, customer data, credentials, tokens, gateway configuration, tunnel identifiers, secret-registry material, private prompts, pricing logic or deployment runbooks.

## Effect boundary

- No tool accepts file paths, shell commands or URLs. The only inputs are a fixed action allowlist, a topic slug (`[a-z0-9-]`, 32 chars), up to 4,000 characters of source text, card ids and short answers.
- Effects touch only flashcard state: `runtime/` in the Python server (JSON files excluded from Git), or one Durable Object per sandbox in the live demo.
- Per sandbox: at most 8 cards per import, 200 cards in total, and the 100 most recent plans are kept; request bodies over 16 KB are rejected.
- Approval phrases are bound to one plan and cannot be replayed on another. Rejected approvals, blocked executions and failed verifications are recorded in the audit chain.

## Live demo

The public endpoint has no authentication because it holds no personal data: each browser visitor gets a random sandbox id, and the default `public` sandbox contains only demo cards. Anyone deploying this pattern for real users should add authentication in front of `/mcp` and map sandboxes to authenticated identities.

## Reporting

Please report issues through GitHub issues without including secrets. Describe ProofGate/Recall behaviour only.
