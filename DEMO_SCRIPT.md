# 3-minute demo script

## 0:00–0:25 — Problem
"Alexa+ can understand an action request, but understanding is not the same as authorization. ProofGate adds a visible safety contract between intent and effect."

## 0:25–1:05 — Plan
Ask Alexa+ to switch the demo release channel from `stable` to `canary` for a controlled rollout. Show `plan_change` returning the exact before/after state and a unique approval phrase. No effect has happened yet.

## 1:05–1:35 — Fail closed
Try `execute_change` before approval. Show `APPROVAL_REQUIRED`. Then provide an intentionally wrong approval phrase and show `APPROVAL_MISMATCH`.

## 1:35–2:15 — Approve and execute
Provide the exact approval phrase. Execute the plan. Explain that ProofGate re-checks the original state before the write, so a stale plan cannot silently overwrite a newer change.

## 2:15–2:45 — Verify
Call `verify_change`. Show `VERIFIED` plus the SHA-256 digest of the resulting state.

## 2:45–3:00 — Boundary
Show the public repository: five tools, bounded sandbox state, no shell, no credentials, and no proprietary HERMX control-plane source.
