# Verification evidence

Recorded on 2026-09-22 for release `v0.2.0`.

## Live endpoint (Cloudflare Worker), official MCP Python client

`python demo_flow.py --url "https://hermx-proofgate-recall.senih-bayankulu25.workers.dev/mcp?sandbox=conformance"`

```text
INITIALIZE            = PASS | protocol=2025-11-25 server=HERMX ProofGate · Recall
TOOL_DISCOVERY        = PASS | 8 tools
PLAN_IMPORT           = PASS | import 4 new cards into 'demo-18ffa4'
UNAPPROVED_BLOCK      = PASS
WRONG_PHRASE_REJECT   = PASS
VOICE_APPROVAL        = PASS | "approve d b 8 2 e b"
EXECUTE               = PASS | import 4 new cards into 'demo-18ffa4'
VERIFY                = PASS | topic_sha256=68c486fc89e0ed84…
ROUTINE_REVIEW        = PASS | ungated, audited grade=1
DRIFT_BLOCK           = PASS | state changed after approval
GATED_DELETE          = PASS
AUDIT_CHAIN           = PASS | events=14
EVIDENCE_STATE_SHA256 = ee74cceab8da5f0f6f478c3ccc17eee4f9817cf3395ab3a69c2ceff802645433
EVIDENCE_AUDIT_HEAD   = 49cfcd32e48e8dda1df98bb9e8b25a7c54542ea88676755d716940c844d5afe7
RESULT = ALL CHECKS PASSED
```

Anyone can reproduce this with their own `?sandbox=` value. Digests will differ per run because plan ids and dates differ; the checks will not.

## Python reference server

The same 12 checks pass against `python server.py` (MCP Python SDK `1.28.1`, protocol `2025-11-25`), locally and in GitHub Actions on every push.

## Tests

`pytest -q`: 16 passed.

- unapproved execution blocked; the wrong phrase, "yes", or another plan's phrase is rejected, and every rejection is audited;
- spelled-out voice approval accepted for the right plan only;
- import, then verify against the digest predicted at plan time;
- routine grading is ungated but extends the audit chain, and a question never leaks its answer;
- drift between plan and execution blocks the stale plan, and the plan can't be retried;
- delete is gated and verified; a later change makes an old plan unverifiable;
- effect surface bounded: action allowlist, topic slug, source size, capacity;
- Python/JavaScript parity for card extraction and grading.

## Repository gates

- Visibility: public, MIT
- Commercial HERMX source copied: no
- Secret-pattern scan of the tree: 0 matches
- MCP Python SDK: `1.28.1` (patched release for the earlier high-severity advisory)

## Disclosure boundary

Digests are demonstration evidence about sandbox state, not credentials. This evidence excludes private provider mappings, production tokens, customer data, gateway or tunnel identifiers and proprietary HERMX details.
