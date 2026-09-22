# Security and disclosure boundary

## Public by design

This repository contains only a bounded competition demo:

- a small Streamable HTTP MCP server;
- a sandbox state machine;
- explicit approval enforcement;
- drift protection;
- SHA-256 verification evidence;
- tests and public documentation.

## Explicitly excluded

The repository does not contain HERMX commercial source code, provider implementations, private capability maps, customer data, credentials, tokens, gateway configuration, production endpoints, tunnel identifiers, secret-registry material, private prompts, internal pricing logic, or deployment runbooks.

## Effect boundary

User-controlled file paths and shell commands are not accepted by any tool. Effects are limited to two allowlisted keys stored under this repository's own `runtime/` directory. Runtime JSON files are excluded from Git.

## Reporting

Do not include secrets or private HERMX implementation details in public issues. Security reports should describe the ProofGate demo behavior only.
