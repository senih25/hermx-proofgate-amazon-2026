import pytest

from proofgate_core import GENESIS, ProofGateStore

SOURCE = (
    "MCP is the Model Context Protocol for agent tools. "
    "Streamable HTTP is the remote transport defined in the 2025-11-25 specification. "
    "Alexa+ can call a self-hosted server through Agent Skills."
)


def imported(tmp_path, topic="mcp"):
    store = ProofGateStore(tmp_path)
    plan = store.plan_change("import_deck", topic, SOURCE, "demo")
    store.approve_change(plan["plan_id"], plan["approval_phrase"])
    store.execute_change(plan["plan_id"])
    return store, plan


def test_unapproved_execution_is_blocked(tmp_path):
    store = ProofGateStore(tmp_path)
    plan = store.plan_change("import_deck", "mcp", SOURCE)
    with pytest.raises(ValueError, match="APPROVAL_REQUIRED"):
        store.execute_change(plan["plan_id"])
    assert store.progress()["total"] == 0


def test_exact_plan_bound_approval_is_required(tmp_path):
    store = ProofGateStore(tmp_path)
    plan = store.plan_change("import_deck", "mcp", SOURCE)
    other = store.plan_change("import_deck", "other", SOURCE)
    count = store.status()["audit_count"]
    for wrong in ("yes", "approve", other["approval_phrase"]):
        with pytest.raises(ValueError, match="APPROVAL_MISMATCH"):
            store.approve_change(plan["plan_id"], wrong)
    assert store.status()["audit_count"] == count + 3  # rejections are evidenced too


def test_spelled_out_voice_approval_matches(tmp_path):
    store = ProofGateStore(tmp_path)
    plan = store.plan_change("import_deck", "mcp", SOURCE)
    code = plan["approval_phrase"].split()[1]
    assert store.approve_change(plan["plan_id"], "approve " + " ".join(code.lower()))["status"] == "APPROVED"


def test_import_execute_and_verify(tmp_path):
    store, plan = imported(tmp_path)
    assert store.progress()["total"] == 3
    v = store.verify_change(plan["plan_id"])
    assert v["verified"] is True
    assert v["expected_topic_sha256"] == v["actual_topic_sha256"] == plan["after_digest"]
    assert len(v["state_sha256"]) == 64


def test_routine_review_is_ungated_but_audited(tmp_path):
    store, _ = imported(tmp_path)
    head_before = store.status()["audit_head"]
    card = store.next_review("mcp")
    assert card["done"] is False and "_____" in card["question"]
    assert "correct_answer" not in card  # the question never leaks the answer
    answer = store._read(store.state_path)["cards"][card["card_id"]]["back"]
    graded = store.grade_answer(card["card_id"], f"I think it's {answer}")
    assert graded["grade"] == 5
    assert graded["audit_head"] != head_before != GENESIS


def test_drift_blocks_stale_approved_plan(tmp_path):
    store, _ = imported(tmp_path)
    plan = store.plan_change("reset_topic", "mcp", reason="start over")
    store.approve_change(plan["plan_id"], plan["approval_phrase"])
    card = store.next_review("mcp")
    store.grade_answer(card["card_id"], "wrong")  # state changes after approval
    with pytest.raises(ValueError, match="STATE_DRIFT"):
        store.execute_change(plan["plan_id"])
    with pytest.raises(ValueError, match="APPROVAL_REQUIRED"):
        store.execute_change(plan["plan_id"])  # a blocked plan can't be retried


def test_delete_topic_is_gated_and_verified(tmp_path):
    store, _ = imported(tmp_path)
    plan = store.plan_change("delete_topic", "mcp")
    assert store.progress()["total"] == 3
    store.approve_change(plan["plan_id"], plan["approval_phrase"])
    store.execute_change(plan["plan_id"])
    assert store.progress()["total"] == 0
    assert store.verify_change(plan["plan_id"])["verified"] is True


def test_later_change_makes_old_plan_unverifiable(tmp_path):
    store, plan = imported(tmp_path)
    store.grade_answer(store.next_review("mcp")["card_id"], "MCP")
    assert store.verify_change(plan["plan_id"])["verified"] is False


@pytest.mark.parametrize(
    "action,topic,source,error",
    [
        ("shell", "mcp", SOURCE, "ACTION_NOT_ALLOWED"),
        ("import_deck", "../etc", SOURCE, "TOPIC_INVALID"),
        ("import_deck", "mcp", "", "SOURCE_INVALID"),
        ("import_deck", "mcp", "x" * 4001, "SOURCE_INVALID"),
        ("import_deck", "mcp", "too short.", "NO_NEW_CARDS"),
        ("reset_topic", "missing", "", "TOPIC_NOT_FOUND"),
    ],
)
def test_effect_surface_is_bounded(tmp_path, action, topic, source, error):
    with pytest.raises(ValueError, match=error):
        ProofGateStore(tmp_path).plan_change(action, topic, source)


def test_reimport_of_same_source_plans_nothing(tmp_path):
    store, _ = imported(tmp_path)
    with pytest.raises(ValueError, match="NO_NEW_CARDS"):
        store.plan_change("import_deck", "mcp", SOURCE)
