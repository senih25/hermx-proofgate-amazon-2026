import json

import pytest

from proofgate_core import ProofGateStore


def test_unapproved_execution_is_blocked(tmp_path):
    store = ProofGateStore(tmp_path)
    plan = store.plan_change("release_channel", "canary", "demo")
    with pytest.raises(ValueError, match="APPROVAL_REQUIRED"):
        store.execute_change(plan["plan_id"])


def test_exact_approval_phrase_is_required(tmp_path):
    store = ProofGateStore(tmp_path)
    plan = store.plan_change("feature_mode", "demo", "voice workflow")
    with pytest.raises(ValueError, match="APPROVAL_MISMATCH"):
        store.approve_change(plan["plan_id"], "yes")


def test_execute_and_verify(tmp_path):
    store = ProofGateStore(tmp_path)
    plan = store.plan_change("feature_mode", "demo", "voice workflow")
    store.approve_change(plan["plan_id"], plan["approval_phrase"])
    result = store.execute_change(plan["plan_id"])
    assert result["status"] == "EXECUTED"
    verification = store.verify_change(plan["plan_id"])
    assert verification["verified"] is True
    assert len(verification["state_sha256"]) == 64


def test_drift_blocks_execution(tmp_path):
    store = ProofGateStore(tmp_path)
    plan = store.plan_change("release_channel", "canary", "demo")
    store.approve_change(plan["plan_id"], plan["approval_phrase"])
    state = json.loads(store.state_path.read_text(encoding="utf-8"))
    state["release_channel"] = "canary"
    store.state_path.write_text(json.dumps(state), encoding="utf-8")
    with pytest.raises(ValueError, match="STATE_DRIFT"):
        store.execute_change(plan["plan_id"])


def test_setting_allowlist(tmp_path):
    store = ProofGateStore(tmp_path)
    with pytest.raises(ValueError, match="SETTING_NOT_ALLOWED"):
        store.plan_change("arbitrary_path", "anything", "not allowed")
