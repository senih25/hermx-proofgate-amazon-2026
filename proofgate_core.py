from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ALLOWED_VALUES = {
    "release_channel": {"stable", "canary"},
    "feature_mode": {"safe", "demo"},
}
DEFAULT_STATE = {
    "release_channel": "stable",
    "feature_mode": "safe",
    "last_change": None,
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


class ProofGateStore:
    def __init__(self, runtime_dir: str | Path):
        self.runtime_dir = Path(runtime_dir).resolve()
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.runtime_dir / "state.json"
        self.plans_path = self.runtime_dir / "plans.json"
        if not self.state_path.exists():
            self._write_json(self.state_path, DEFAULT_STATE)
        if not self.plans_path.exists():
            self._write_json(self.plans_path, {})

    def _write_json(self, path: Path, value: Any) -> None:
        if path.parent.resolve() != self.runtime_dir:
            raise ValueError("BOUNDARY_VIOLATION")
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")
        os.replace(temp, path)

    @staticmethod
    def _read_json(path: Path) -> Any:
        return json.loads(path.read_text(encoding="utf-8"))

    def status(self) -> dict[str, Any]:
        plans = self._read_json(self.plans_path)
        return {
            "service": "HERMX ProofGate",
            "mode": "CLEAN_ROOM_DEMO",
            "approval_required": True,
            "runtime_boundary": str(self.runtime_dir),
            "plan_count": len(plans),
        }

    def plan_change(self, key: str, value: str, reason: str) -> dict[str, Any]:
        if key not in ALLOWED_VALUES or value not in ALLOWED_VALUES[key]:
            raise ValueError("SETTING_NOT_ALLOWED")
        state = self._read_json(self.state_path)
        plan_id = f"pg_{uuid.uuid4().hex[:12]}"
        plan = {
            "plan_id": plan_id,
            "key": key,
            "before": state[key],
            "after": value,
            "reason": reason.strip()[:240],
            "status": "PLANNED",
            "requires_approval": True,
            "created_at": _now(),
            "audit": ["plan.created"],
        }
        plans = self._read_json(self.plans_path)
        plans[plan_id] = plan
        self._write_json(self.plans_path, plans)
        return {**plan, "approval_phrase": f"APPROVE {plan_id}"}

    def approve_change(self, plan_id: str, approval_phrase: str) -> dict[str, Any]:
        plans = self._read_json(self.plans_path)
        plan = plans.get(plan_id)
        if not plan:
            raise ValueError("PLAN_NOT_FOUND")
        if plan["status"] != "PLANNED":
            raise ValueError("PLAN_NOT_APPROVABLE")
        if approval_phrase != f"APPROVE {plan_id}":
            raise ValueError("APPROVAL_MISMATCH")
        plan["status"] = "APPROVED"
        plan["approved_at"] = _now()
        plan["audit"].append("approval.accepted")
        plans[plan_id] = plan
        self._write_json(self.plans_path, plans)
        return plan

    def execute_change(self, plan_id: str) -> dict[str, Any]:
        plans = self._read_json(self.plans_path)
        plan = plans.get(plan_id)
        if not plan:
            raise ValueError("PLAN_NOT_FOUND")
        if plan["status"] != "APPROVED":
            raise ValueError("APPROVAL_REQUIRED")
        state = self._read_json(self.state_path)
        if state[plan["key"]] != plan["before"]:
            plan["status"] = "BLOCKED_DRIFT"
            plan["audit"].append("execution.blocked_drift")
            plans[plan_id] = plan
            self._write_json(self.plans_path, plans)
            raise ValueError("STATE_DRIFT")
        state[plan["key"]] = plan["after"]
        state["last_change"] = plan_id
        self._write_json(self.state_path, state)
        plan["status"] = "EXECUTED"
        plan["executed_at"] = _now()
        plan["audit"].append("execution.completed")
        plans[plan_id] = plan
        self._write_json(self.plans_path, plans)
        return {"plan_id": plan_id, "status": plan["status"], "state": state}

    def verify_change(self, plan_id: str) -> dict[str, Any]:
        plans = self._read_json(self.plans_path)
        plan = plans.get(plan_id)
        if not plan:
            raise ValueError("PLAN_NOT_FOUND")
        state = self._read_json(self.state_path)
        matches = state.get(plan["key"]) == plan["after"] and state.get("last_change") == plan_id
        digest = hashlib.sha256(_canonical(state)).hexdigest()
        verification = {
            "plan_id": plan_id,
            "verified": bool(matches),
            "state_sha256": digest,
            "checked_at": _now(),
            "status": "VERIFIED" if matches else "DRIFT",
        }
        plan["audit"].append("verification.passed" if matches else "verification.failed")
        plans[plan_id] = plan
        self._write_json(self.plans_path, plans)
        return verification
