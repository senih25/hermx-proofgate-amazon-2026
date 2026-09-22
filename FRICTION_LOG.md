# Friction Log — HERMX ProofGate

This log documents concrete development friction encountered while preparing the public clean-room MCP submission. It intentionally excludes private HERMX internals, credentials, customer data, and production infrastructure.

## 1. Python package discovery blocked CI

**Task attempted:** Install the project in GitHub Actions with `pip install -e ".[dev]"`.

**Steps taken:**
1. Added `proofgate_core.py`, `server.py`, tests, and `pyproject.toml`.
2. Ran the same editable install locally and in GitHub Actions.
3. CI rejected automatic package discovery because the repository contained multiple top-level Python modules.

**Expected:** Editable installation should discover the two intended modules and proceed to tests.

**Actual:** Setuptools stopped the build during automatic discovery.

**Severity:** Medium — CI could not reach the test stage.

**Workaround:** Declared the module surface explicitly:
```toml
[tool.setuptools]
py-modules = ["server", "proofgate_core"]
```

**Actionable suggestion:** For small MCP reference projects, document an explicit `py-modules` / package-layout example in starter guidance so a two-file server can be copied into CI without package-discovery ambiguity.

---

## 2. MCP tool errors are result-level errors, not Python exceptions

**Task attempted:** Prove that `execute_change` fails closed before approval through a real MCP client.

**Steps taken:**
1. Initialized a real Streamable HTTP MCP client session.
2. Called `plan_change`.
3. Called `execute_change` before approval.
4. Initially checked only for a raised Python exception.

**Expected:** A rejected tool call would raise in client code.

**Actual:** The SDK returned a tool result with `isError=true`; no Python exception was raised. The server behavior was correct, but the first E2E assertion measured it incorrectly.

**Severity:** Medium — easy to misread a correct fail-closed result as a failed safety check.

**Workaround:** Inspect both `isError` and returned error text. After updating the client-side assertion, the gate verified:
- UNAPPROVED_BLOCK = PASS
- APPROVE = PASS
- EXECUTE = PASS
- VERIFY = PASS

**Actionable suggestion:** Add a prominent client example showing the canonical handling of successful tool results versus `isError=true` tool results for Streamable HTTP.

---

## 3. Protocol compliance was easier to verify than platform handoff

**Task attempted:** Prepare a self-hosted MCP endpoint for the Alexa+ track requirement.

**Steps taken:**
1. Built `/mcp` using the official MCP Python SDK.
2. Initialized through a real MCP client.
3. Verified negotiated protocol version `2025-11-25`.
4. Verified tool discovery and an end-to-end approval flow.

**Expected:** After MCP compliance was proven locally, the next steps for handing a validated self-hosted MCP into the Alexa+ developer workflow would be equally explicit.

**Actual:** The MCP protocol/transport path is clear; the platform-specific handoff/checklist is less obvious from the generic MCP material available during implementation.

**Severity:** Low/Medium — it does not block development, but increases uncertainty near the final integration step.

**Workaround:** Kept the submission honest: the repository and demo distinguish “verified MCP server” from “future Alexa+ connection” instead of claiming an integration that has not been demonstrated.

**Actionable suggestion:** Provide an Alexa+ self-hosted MCP preflight page with:
- accepted endpoint visibility/auth patterns,
- protocol/transport validation,
- a minimal connection checklist,
- common rejection diagnostics,
- a test harness that confirms Alexa+ can enumerate tools.

---

## 4. Reproducibility versus dependency upgrades

**Task attempted:** Keep a reproducible hackathon checkpoint while automated dependency tooling proposed an MCP SDK update.

**Expected:** Security/dependency automation should help without changing the verified compatibility target unexpectedly.

**Actual:** An automated dependency PR proposed moving away from the SDK version already used in the verified checkpoint.

**Severity:** Low.

**Workaround:** Initially kept `mcp==1.27.2` pinned for the reproducible `v0.1.0` checkpoint. When GitHub later surfaced a high-severity advisory with `1.28.1` as the first patched release, we upgraded to `mcp==1.28.1` and re-ran the full test and live Streamable HTTP verification flow before accepting the change.

**Actionable suggestion:** Provide a compatibility table that maps MCP SDK releases to supported protocol revisions and migration notes, making upgrade decisions easier during judged/reproducible builds.

---

## 5. No free, obvious home for a public Python MCP server

**Task attempted:** Give judges a free, always-on live endpoint for the Python MCP server.

**Steps taken:**
1. Looked for a free host that runs the official Python SDK server (Starlette/uvicorn) without sleeping or a credit card.
2. Considered Python on Cloudflare Workers; the SDK's dependency tree (pydantic, starlette, anyio) made that a risky bet for a judged deadline.
3. Ported the tool contract to a Cloudflare Worker in JavaScript instead, with one Durable Object per sandbox.

**Expected:** A documented, free path to host the reference Python server publicly for judging.

**Actual:** Two implementations of one contract, which creates a divergence risk.

**Severity:** Medium: extra work and a real chance of the live demo drifting from the reference.

**Workaround:** Kept the algorithms deterministic and added `tests/test_parity.py`, which runs the JavaScript extractor and grader and compares results with Python. `demo_flow.py --url` runs the same 12 MCP checks against both runtimes.

**Actionable suggestion:** Publish a hackathon hosting recipe (or credits) for self-hosted Streamable HTTP MCP servers in Python, and a conformance harness that any endpoint URL can be run through.

---

## 6. Stateless Streamable HTTP details are easy to get subtly wrong

**Task attempted:** Implement Streamable HTTP by hand in the Worker so the official Python client can connect.

**Steps taken:**
1. Answered `initialize` with JSON (not SSE), negotiated `2025-11-25`, and issued no session id.
2. Returned `202` for notifications and `405` for `GET /mcp`, since the server never pushes messages.
3. Validated `MCP-Protocol-Version` on later requests.

**Expected:** A short checklist of exactly what a stateless, JSON-only server must implement.

**Actual:** The rules are spread across the transport, lifecycle and versioning pages; working out which parts are optional for a JSON-only stateless server took trial runs with the official client.

**Severity:** Low: resolved in under an hour, with conformance checks to prove it.

**Workaround:** Ran the official MCP Python client's full flow against the Worker, locally (`wrangler dev`) and live, before trusting it.

**Actionable suggestion:** A "minimal stateless Streamable HTTP server" checklist in the spec, with the exact status codes and headers expected.

---

## 7. Voice approval versus exact approval

**Task attempted:** Keep approval exact (plan-bound) while making it speakable.

**Actual:** Speech recognition returns "approve 7 f 3 a 9 c", "Approve 7F3A9C" or "approve 7 F 3A 9C" for the same intent. A strict string match would reject genuine approvals.

**Severity:** Medium for voice UX.

**Workaround:** Approval phrases are compared after removing whitespace and case, but they stay bound to one plan id: a phrase for another plan, or "yes, go ahead", is still rejected and logged. Covered by `test_spelled_out_voice_approval_matches` and `test_exact_plan_bound_approval_is_required`.

**Actionable suggestion:** Alexa+ guidance for confirmation patterns on consequential MCP tool calls (for example, a platform-level spoken confirmation with a plan-bound code) would let skills stop reinventing this.
