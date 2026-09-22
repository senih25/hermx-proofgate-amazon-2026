"""ProofGate engine for the Recall learning coach.

Risk-tiered effects:
- Routine, single-card effects (grading a review) run immediately but are
  written to a hash-chained audit log, so they stay evidenced.
- Consequential effects (import a deck, reset a topic, delete a topic) must go
  plan -> exact approval -> drift-checked execution -> verification.

`worker/src/core.js` is a port of this module for the free live demo.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import threading
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from learning import grade, make_cards
from srs import review

GATED_ACTIONS = ("import_deck", "reset_topic", "delete_topic")
ROUTINE_TOOLS = ("next_review", "grade_answer", "progress")
TOPIC_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,31}$")
MAX_SOURCE_CHARS = 4000
MAX_CARDS_PER_IMPORT = 8
MAX_TOTAL_CARDS = 200
MAX_PLANS = 100
GENESIS = "0" * 64
DEFAULT_STATE: dict[str, Any] = {"cards": {}, "last_change": None}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def topic_slice(state: dict, topic: str) -> dict:
    return {cid: c for cid, c in state["cards"].items() if c["topic"] == topic}


def apply_plan(state: dict, plan: dict) -> dict:
    """Pure: return the state that executing `plan` produces."""
    new = copy.deepcopy(state)
    cards, topic, day = new["cards"], plan["topic"], plan["effective_date"]
    fresh = {"repetitions": 0, "interval_days": 0, "easiness": 2.5, "due": day}
    if plan["action"] == "import_deck":
        for c in plan["payload"]["cards"]:
            cards[c["id"]] = {"id": c["id"], "topic": topic, "front": c["front"], "back": c["back"], **fresh}
    elif plan["action"] == "reset_topic":
        for cid in topic_slice(new, topic):
            cards[cid].update(fresh)
    elif plan["action"] == "delete_topic":
        for cid in list(topic_slice(new, topic)):
            del cards[cid]
    return new


class ProofGateStore:
    def __init__(self, runtime_dir: str | Path):
        self.runtime_dir = Path(runtime_dir).resolve()
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.runtime_dir / "state.json"
        self.plans_path = self.runtime_dir / "plans.json"
        self.audit_path = self.runtime_dir / "audit.json"
        self._lock = threading.RLock()
        for path, default in (
            (self.state_path, DEFAULT_STATE),
            (self.plans_path, {}),
            (self.audit_path, {"head": GENESIS, "count": 0}),
        ):
            if not path.exists():
                self._write(path, default)

    # -- persistence -------------------------------------------------------
    def _write(self, path: Path, value: Any) -> None:
        if path.parent.resolve() != self.runtime_dir:
            raise ValueError("BOUNDARY_VIOLATION")
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")
        os.replace(temp, path)

    @staticmethod
    def _read(path: Path) -> Any:
        return json.loads(path.read_text(encoding="utf-8"))

    def _event(self, kind: str, **data: Any) -> str:
        audit = self._read(self.audit_path)
        audit["head"] = hashlib.sha256(
            (audit["head"] + canonical({"kind": kind, **data}).decode()).encode()
        ).hexdigest()
        audit["count"] += 1
        self._write(self.audit_path, audit)
        return audit["head"]

    def _plan(self, plans: dict, plan_id: str) -> dict:
        plan = plans.get(plan_id)
        if not plan:
            raise ValueError("PLAN_NOT_FOUND")
        return plan

    # -- read-only ---------------------------------------------------------
    def status(self) -> dict:
        with self._lock:
            state, plans, audit = (self._read(p) for p in (self.state_path, self.plans_path, self.audit_path))
            return {
                "service": "HERMX ProofGate · Recall",
                "mode": "CLEAN_ROOM_DEMO",
                "approval_required_for": list(GATED_ACTIONS),
                "routine_tools": list(ROUTINE_TOOLS),
                "card_count": len(state["cards"]),
                "plan_count": len(plans),
                "audit_count": audit["count"],
                "audit_head": audit["head"],
                "state_sha256": sha256(state),
            }

    def progress(self) -> dict:
        with self._lock:
            state = self._read(self.state_path)
            today = date.today().isoformat()
            topics: dict[str, dict] = {}
            for c in state["cards"].values():
                t = topics.setdefault(c["topic"], {"cards": 0, "learned": 0, "due": 0})
                t["cards"] += 1
                t["learned"] += c["repetitions"] >= 3
                t["due"] += c["due"] <= today
            total = sum(t["cards"] for t in topics.values())
            learned = sum(t["learned"] for t in topics.values())
            due = sum(t["due"] for t in topics.values())
            n = len(topics)
            return {
                "total": total, "learned": learned, "due": due, "topics": topics,
                "say": f"You have {total} cards across {n} topic{'' if n == 1 else 's'}, "
                       f"{learned} well learned and {due} due now.",
            }

    def next_review(self, topic: str = "") -> dict:
        with self._lock:
            state = self._read(self.state_path)
            today = date.today().isoformat()
            due = sorted(
                (c for c in state["cards"].values() if c["due"] <= today and (not topic or c["topic"] == topic)),
                key=lambda c: (c["due"], c["id"]),
            )
            if not due:
                return {"done": True, "say": "Nothing is due right now. Nice work."}
            c = due[0]
            return {"done": False, "card_id": c["id"], "topic": c["topic"], "question": c["front"],
                    "say": f"Fill in the blank. {c['front'].replace('_____', 'blank')}"}

    # -- routine effect (ungated, evidenced) --------------------------------
    def grade_answer(self, card_id: str, answer: str) -> dict:
        with self._lock:
            state = self._read(self.state_path)
            card = state["cards"].get(card_id)
            if not card:
                raise ValueError("CARD_NOT_FOUND")
            score, feedback = grade(card["back"], answer[:200])
            s = review(score, card["repetitions"], card["interval_days"], card["easiness"])
            card.update(repetitions=s.repetitions, interval_days=s.interval_days,
                        easiness=s.easiness, due=s.due.isoformat())
            self._write(self.state_path, state)
            head = self._event("review.graded", card_id=card_id, grade=score)
            when = "tomorrow" if s.interval_days == 1 else f"in {s.interval_days} days"
            return {"card_id": card_id, "grade": score, "correct_answer": card["back"],
                    "next_due": card["due"], "audit_head": head,
                    "say": f"{feedback} The answer is {card['back']}. Next review {when}."}

    # -- gated effects -----------------------------------------------------
    def plan_change(self, action: str, topic: str, source: str = "", reason: str = "") -> dict:
        with self._lock:
            if action not in GATED_ACTIONS:
                raise ValueError("ACTION_NOT_ALLOWED")
            if not TOPIC_RE.match(topic):
                raise ValueError("TOPIC_INVALID")
            state = self._read(self.state_path)
            before = topic_slice(state, topic)
            payload: dict[str, Any] = {}
            if action == "import_deck":
                if not source.strip() or len(source) > MAX_SOURCE_CHARS:
                    raise ValueError("SOURCE_INVALID")
                new_cards = [c for c in make_cards(source, topic, MAX_CARDS_PER_IMPORT) if c["id"] not in before]
                if not new_cards:
                    raise ValueError("NO_NEW_CARDS")
                if len(state["cards"]) + len(new_cards) > MAX_TOTAL_CARDS:
                    raise ValueError("CAPACITY_EXCEEDED")
                payload = {"cards": new_cards}
                summary = f"import {len(new_cards)} new cards into '{topic}'"
            elif not before:
                raise ValueError("TOPIC_NOT_FOUND")
            else:
                verb = "reset the schedule of" if action == "reset_topic" else "permanently delete"
                summary = f"{verb} {len(before)} cards in '{topic}'"

            plan_id = f"pg_{uuid.uuid4().hex[:12]}"
            code = plan_id[3:9].upper()
            plan = {
                "plan_id": plan_id, "action": action, "topic": topic, "reason": reason.strip()[:240],
                "payload": payload, "effect_summary": summary, "effective_date": date.today().isoformat(),
                "before_count": len(before), "before_digest": sha256(before),
                "status": "PLANNED", "requires_approval": True, "approval_code": code,
                "created_at": _now(), "audit": ["plan.created"],
            }
            plan["after_digest"] = sha256(topic_slice(apply_plan(state, plan), topic))
            plans = self._read(self.plans_path)
            plans[plan_id] = plan
            for old in list(plans)[:-MAX_PLANS]:
                del plans[old]
            self._write(self.plans_path, plans)
            self._event("plan.created", plan_id=plan_id, action=action, topic=topic)
            preview = [c["front"] for c in payload.get("cards", [])[:3]]
            return {
                "plan_id": plan_id, "action": action, "topic": topic, "effect_summary": summary,
                "before_count": len(before), "before_digest": plan["before_digest"],
                "after_digest": plan["after_digest"], "preview": preview, "status": "PLANNED",
                "approval_phrase": f"APPROVE {code}",
                "say": f"I planned to {summary}. Nothing has changed yet. To proceed, say: approve {' '.join(code)}.",
            }

    def approve_change(self, plan_id: str, approval_phrase: str) -> dict:
        with self._lock:
            plans = self._read(self.plans_path)
            plan = self._plan(plans, plan_id)
            if plan["status"] != "PLANNED":
                raise ValueError("PLAN_NOT_APPROVABLE")
            # Spacing/case-insensitive so a spelled-out voice code still matches.
            if re.sub(r"\s+", "", approval_phrase.upper()) != "APPROVE" + plan["approval_code"]:
                self._event("approval.rejected", plan_id=plan_id)
                raise ValueError("APPROVAL_MISMATCH")
            plan["status"] = "APPROVED"
            plan["approved_at"] = _now()
            plan["audit"].append("approval.accepted")
            self._write(self.plans_path, plans)
            self._event("plan.approved", plan_id=plan_id)
            return {"plan_id": plan_id, "status": "APPROVED",
                    "say": "Approved. I'll re-check the current state right before making the change."}

    def execute_change(self, plan_id: str) -> dict:
        with self._lock:
            plans = self._read(self.plans_path)
            plan = self._plan(plans, plan_id)
            if plan["status"] != "APPROVED":
                raise ValueError("APPROVAL_REQUIRED")
            state = self._read(self.state_path)
            if sha256(topic_slice(state, plan["topic"])) != plan["before_digest"]:
                plan["status"] = "BLOCKED_DRIFT"
                plan["audit"].append("execution.blocked_drift")
                self._write(self.plans_path, plans)
                self._event("plan.blocked_drift", plan_id=plan_id)
                raise ValueError("STATE_DRIFT")
            new_state = apply_plan(state, plan)
            new_state["last_change"] = plan_id
            self._write(self.state_path, new_state)
            plan["status"] = "EXECUTED"
            plan["executed_at"] = _now()
            plan["audit"].append("execution.completed")
            self._write(self.plans_path, plans)
            head = self._event("plan.executed", plan_id=plan_id)
            return {"plan_id": plan_id, "status": "EXECUTED", "effect_summary": plan["effect_summary"],
                    "card_count": len(new_state["cards"]), "audit_head": head,
                    "say": f"Done. I {plan['effect_summary'].replace('permanently ', '')}."}

    def verify_change(self, plan_id: str) -> dict:
        with self._lock:
            plans = self._read(self.plans_path)
            plan = self._plan(plans, plan_id)
            state = self._read(self.state_path)
            topic_digest = sha256(topic_slice(state, plan["topic"]))
            ok = plan["status"] == "EXECUTED" and topic_digest == plan["after_digest"] and state["last_change"] == plan_id
            plan["audit"].append("verification.passed" if ok else "verification.failed")
            self._write(self.plans_path, plans)
            head = self._event("plan.verified" if ok else "plan.verify_failed", plan_id=plan_id)
            return {
                "plan_id": plan_id, "verified": ok, "status": "VERIFIED" if ok else "NOT_VERIFIED",
                "expected_topic_sha256": plan["after_digest"], "actual_topic_sha256": topic_digest,
                "state_sha256": sha256(state), "audit_head": head, "checked_at": _now(),
                "say": "Verified. The result matches the approved plan." if ok
                else "Verification failed: the current state doesn't match the approved plan.",
            }
