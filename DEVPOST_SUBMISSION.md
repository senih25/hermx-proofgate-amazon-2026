# Devpost submission copy

## Project name
HERMX ProofGate

## Tagline
Approval-gated actions for Alexa+: plan, approve, execute, verify.

## Inspiration
Conversational agents are increasingly capable of taking real actions. The hard part is not only making those actions possible, but making them understandable, explicitly authorized, resistant to stale state, and easy to verify afterward.

## What it does
ProofGate is a self-hosted Streamable HTTP MCP server designed for an Alexa+ action workflow. It exposes a deliberately small action surface where every effect must pass four visible stages: plan, exact user approval, drift-safe execution, and verification. Successful verification returns a SHA-256 digest as compact evidence of the resulting sandbox state.

## How we built it
The public competition repository is a clean-room Python implementation using the official MCP Python SDK (`mcp==1.27.2`). The server exposes five tools over `/mcp`. A pure-Python state engine persists only sandbox data under the repository runtime directory, enforces an allowlist, checks preconditions immediately before execution, and records a minimal audit trail.

## Challenges
The main design challenge was increasing agent capability without turning a conversational request into implicit authorization. We separated intent from effect, made approval exact and plan-bound, and added a drift check so approval cannot be reused after the underlying state changes.

## Accomplishments
- Streamable HTTP MCP action server.
- Explicit plan-bound approval gate.
- Fail-closed execution without approval.
- Stale-state protection before effects.
- Post-action SHA-256 verification evidence.
- Standalone public demo with no dependency on proprietary HERMX internals.

## What we learned
Agent safety is easier to reason about when approval and verification are first-class protocol steps. The same pattern can be applied to richer production actions while keeping the conversational interface simple.

## What's next
Connect the public MCP endpoint to the Alexa+ developer workflow, add a richer but still bounded demonstration action, and publish the short demo video. Production HERMX capabilities remain outside this repository by design.

## Track
Alexa+

## Open Source mini challenge
The competition demo is designed as a standalone open-source reference implementation of the approval-gated action pattern. It contains no commercial HERMX control-plane source.

## Verification status
Local core tests: PASS after package build. Public MCP deployment and Alexa+ end-to-end connection must be verified before final judging submission.
