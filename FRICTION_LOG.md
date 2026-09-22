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
