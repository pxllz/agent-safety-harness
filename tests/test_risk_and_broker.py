import pytest

from agent_safety_harness import (
    ApprovalMismatch,
    BasicRiskPolicy,
    FakeBroker,
    NotApproved,
    RiskResult,
    issue_approval,
    semantic_fingerprint,
)

POLICY = BasicRiskPolicy(allowed_kinds={"echo"}, max_magnitude=100)


def test_policy_approves_allowed_action():
    result = POLICY.evaluate({"kind": "echo", "magnitude": 10})
    assert result.approved


def test_policy_rejects_unknown_kind():
    result = POLICY.evaluate({"kind": "launch_missiles"})
    assert not result.approved
    assert any("kind" in reason for reason in result.reasons)


def test_policy_rejects_excessive_magnitude():
    result = POLICY.evaluate({"kind": "echo", "magnitude": 1000})
    assert not result.approved


def test_policy_rejects_non_numeric_magnitude():
    result = POLICY.evaluate({"kind": "echo", "magnitude": "lots"})
    assert not result.approved


def test_approval_is_bound_to_action_fingerprint():
    action = {"kind": "echo", "magnitude": 1}
    approval = issue_approval(POLICY.evaluate(action), action)
    assert approval.action_fingerprint == semantic_fingerprint(action)


def test_rejected_result_cannot_be_approved():
    with pytest.raises(NotApproved):
        issue_approval(RiskResult(approved=False, reasons=("nope",)), {"kind": "echo"})


def test_fake_broker_executes_approved_action():
    broker = FakeBroker()
    action = {"kind": "echo", "magnitude": 1}
    approval = issue_approval(POLICY.evaluate(action), action)
    report = broker.submit(action, approval)
    assert report.status == "FILLED_FAKE"
    assert broker.history == (report,)


def test_fake_broker_refuses_mismatched_approval():
    broker = FakeBroker()
    approved_action = {"kind": "echo", "magnitude": 1}
    other_action = {"kind": "echo", "magnitude": 2}
    approval = issue_approval(POLICY.evaluate(approved_action), approved_action)
    with pytest.raises(ApprovalMismatch):
        broker.submit(other_action, approval)
    assert broker.history == ()
