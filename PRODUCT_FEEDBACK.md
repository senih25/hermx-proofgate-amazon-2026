# Product Feedback — HERMX ProofGate

## Tools / APIs / SDKs used

### Model Context Protocol Python SDK
Used to implement the self-hosted MCP server, expose five tools, run Streamable HTTP at `/mcp`, negotiate protocol version `2025-11-25`, and execute the E2E tool-call verification flow.

### GitHub + GitHub Actions
Used for the public open-source repository, versioned hackathon checkpoint, CI, reproducibility, and public evidence.

### Devpost
Used for hackathon registration, project metadata, submission requirements, judging criteria, and the final submission workflow.

> Alexa+ note: ProofGate is built specifically for the Alexa+ self-hosted MCP track, but this public checkpoint does **not** claim a completed live Alexa+ connection. The repository demonstrates and verifies the required MCP server behavior; the Alexa+ developer-workflow connection remains the next integration step.

---

## What worked well

### MCP Python SDK
- FastMCP makes a small, auditable tool surface straightforward to implement.
- Streamable HTTP can be configured with a compact server entry point.
- Tool discovery and structured responses make automated E2E verification practical.
- The protocol boundary enabled us to test approval, execution, and verification independently from any conversational UI.

### GitHub / GitHub Actions
- The public repository provides a strong reproducibility boundary for a clean-room hackathon implementation.
- CI made packaging mistakes visible immediately.
- Tags/releases make it easy to freeze a judging checkpoint without exposing commercial source.

### Devpost
- Submission requirements are explicit about what judges need.
- The requirement that the track technology appear in code—not only documentation—is useful and raises submission quality.
- The friction-log bonus creates an incentive to give actionable developer feedback instead of only marketing the project.

---

## What needs work

### MCP Python SDK
- Client-side error semantics deserve more prominent documentation. Tool failures may arrive as `isError=true` results instead of exceptions, which can surprise developers writing validation tests.
- Minimal Python packaging examples should include explicit packaging metadata so a small two-module MCP project works predictably in CI.

### Alexa+ MCP onboarding
- The transition from “spec-compliant local/self-hosted MCP” to “validated in the Alexa+ developer workflow” would benefit from one canonical preflight checklist.
- A validator that checks endpoint reachability, MCP revision, Streamable HTTP behavior, authentication expectations, and tool enumeration would reduce late-stage integration uncertainty.
- The track documentation should keep a sharp distinction between protocol compliance and successful Alexa+ connection.

### Devpost submission workflow
- The form is comprehensive, but the relationship among primary-track fields, mini-challenge fields, and product-feedback fields is lengthy. A track-specific preflight checklist would help builders detect missing evidence earlier.

---

## Onboarding experience

### MCP Python SDK
Getting to a local “hello world” server was fast. The main learning curve was not creating tools; it was correctly validating client error semantics and producing a reproducible CI package. Once those were understood, the server/test loop was predictable.

### Alexa+ track
The track requirement is clear at a high level: MCP `2025-11-25+` over Streamable HTTP or an Agent Skill. The next stage—taking a locally verified self-hosted MCP into the Alexa+ developer workflow—needs more concrete end-to-end examples and diagnostics.

### GitHub Actions
Straightforward after the Python module-discovery issue was resolved.

---

## Would we build with these tools again?

**MCP Python SDK: Yes.** The protocol boundary is a good fit for agentic workflows where tools, authorization, and verification need to stay explicit.

**GitHub / GitHub Actions: Yes.** They provide the reproducibility and evidence trail needed for a safety-oriented project.

**Alexa+ MCP path: Yes, with continued evaluation.** The self-hosted MCP model is attractive because it keeps tool logic behind a standard protocol boundary. A clearer connection preflight and debugging surface would make the experience substantially stronger.
