# HERMX ProofGate

**Approval-gated actions for Alexa+ over Streamable HTTP MCP.**

ProofGate is a clean-room hackathon demo built for the **Build, Ship, Shape: Amazon Developer Hackathon**. It demonstrates a safety-first agentic workflow without publishing HERMX commercial internals.

## What it demonstrates

An assistant cannot jump directly from intent to effect. Every change follows:

`plan → explicit approval → drift-safe execution → cryptographic verification`

The public demo exposes five MCP tools:

- `proofgate_status`
- `plan_change`
- `approve_change`
- `execute_change`
- `verify_change`

The effect surface is intentionally bounded to two sandbox settings. No shell, customer data, credential path, production API, provider registry, routing logic, tunnel configuration, or proprietary adapter is included.

## Why this matters for Alexa+

Voice and conversational agents become more useful when they can take actions, but higher agency also increases the cost of an incorrect action. ProofGate turns approval and verification into protocol-visible steps rather than hidden application behavior.

A typical interaction is:

1. Alexa+ asks ProofGate to plan a bounded change.
2. ProofGate returns the before/after state and an exact approval phrase.
3. The user explicitly approves that exact plan.
4. ProofGate re-checks preconditions before execution.
5. ProofGate verifies the result and returns a SHA-256 evidence digest.

## Run locally

Requirements: Python 3.11+.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -e .
python server.py
```

The Streamable HTTP endpoint is:

`http://127.0.0.1:8767/mcp`

The project pins `mcp==1.27.2` and uses Streamable HTTP with JSON responses and stateless HTTP sessions.

## Test

```bash
pip install -e ".[dev]"
pytest -q
```

The tests prove that execution is blocked without approval, approval phrases must match exactly, state drift blocks stale plans, allowlists constrain the effect surface, and successful execution produces verifiable evidence.

## Commercial boundary

This repository is intentionally standalone. It reimplements only the public safety pattern needed for the hackathon demo. It does **not** contain or depend on the proprietary HERMX control plane.

See [SECURITY.md](SECURITY.md) for the disclosure boundary and [DEVPOST_SUBMISSION.md](DEVPOST_SUBMISSION.md) for the submission copy.
