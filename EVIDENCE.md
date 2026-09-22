# Verification Evidence

Verified on 2026-09-22 against the public clean-room repository.

## Repository gates

- Repository visibility: PUBLIC
- Commercial HERMX source copied: NO
- Current-tree secret pattern scan: PASS (0 matches)
- Core tests: PASS (5/5)
- GitHub Actions CI: PASS

## MCP transport gate

A real MCP client connected to the local Streamable HTTP endpoint and completed initialization.

- Endpoint shape: `/mcp`
- Negotiated protocol version: `2025-11-25`
- Public tools:
  - `proofgate_status`
  - `plan_change`
  - `approve_change`
  - `execute_change`
  - `verify_change`

## End-to-end safety gate

The MCP client executed the public demo workflow:

- PLAN: PASS
- UNAPPROVED_BLOCK: PASS
- APPROVE: PASS
- EXECUTE: PASS
- VERIFY: PASS
- Verification digest: `8885871e70a434e945468b0a5284809813e986e3b63dacf479954a1c8ed94df8`

The digest is generated from the resulting sandbox state. It is demonstration evidence, not a credential or secret.

## Disclosure boundary

This evidence intentionally excludes private provider mappings, production tokens, customer data, gateway/tunnel identifiers, commercial routing logic, protected file paths, and proprietary HERMX implementation details.
