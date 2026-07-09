import pytest

from agent_safety_harness import (
    BasicRiskPolicy,
    Event,
    FakeBroker,
    Outcome,
    RunState,
    SafetyHarness,
)


def make_harness(**kwargs) -> SafetyHarness:
    policy = BasicRiskPolicy(allowed_kinds={"echo"}, max_magnitude=100)
    return SafetyHarness(policy=policy, **kwargs)


def echo_event(source_key: str, magnitude: int = 1) -> Event:
    return Event(
        source_key=source_key,
        kind="proposal",
        payload={"kind": "echo", "magnitude": magnitude},
    )


def test_dry_run_is_the_default_and_executes_nothing():
    broker = FakeBroker()
    harness = make_harness(broker=broker)
    result = harness.process(echo_event("e1"))
    assert result.outcome is Outcome.DRY_RUN
    assert result.run is not None and result.run.state is RunState.COMPLETED
    assert broker.history == ()


def test_live_mode_executes_via_fake_broker():
    broker = FakeBroker()
    harness = make_harness(broker=broker, dry_run=False)
    result = harness.process(echo_event("e1"))
    assert result.outcome is Outcome.EXECUTED
    assert result.report is not None
    assert len(broker.history) == 1


def test_duplicate_event_is_dropped_without_a_run():
    harness = make_harness()
    harness.process(echo_event("e1"))
    result = harness.process(echo_event("e1", magnitude=2))
    assert result.outcome is Outcome.DUPLICATE_EVENT
    assert result.run is None
    assert len(harness.runs) == 1


def test_semantically_duplicate_action_is_blocked():
    harness = make_harness()
    harness.process(echo_event("e1"))
    # Different source_key, same action content.
    result = harness.process(echo_event("e2"))
    assert result.outcome is Outcome.DUPLICATE_ACTION


def test_rejected_action_completes_the_run():
    harness = make_harness()
    result = harness.process(echo_event("e1", magnitude=10_000))
    assert result.outcome is Outcome.REJECTED
    assert result.run is not None and result.run.state is RunState.COMPLETED
    assert result.risk is not None and not result.risk.approved


def test_pause_blocks_then_resume_allows_redelivery():
    harness = make_harness()
    harness.pause("operator break")
    blocked = harness.process(echo_event("e1"))
    assert blocked.outcome is Outcome.PAUSED
    harness.resume()
    # The event was never ingested, so redelivery is processed normally.
    result = harness.process(echo_event("e1"))
    assert result.outcome is Outcome.DRY_RUN


def test_emergency_stop_blocks_everything_for_good():
    harness = make_harness()
    harness.stop("anomaly")
    assert harness.process(echo_event("e1")).outcome is Outcome.STOPPED
    harness.resume()  # pause controls must not clear an emergency stop
    assert harness.process(echo_event("e2")).outcome is Outcome.STOPPED


def test_failing_policy_marks_run_failed():
    class ExplodingPolicy:
        def evaluate(self, action):
            raise RuntimeError("policy crashed")

    harness = SafetyHarness(policy=ExplodingPolicy())
    with pytest.raises(RuntimeError, match="policy crashed"):
        harness.process(echo_event("e1"))
    assert harness.runs[0].state is RunState.FAILED
    assert harness.runs[0].error == "policy crashed"


def test_every_step_is_audited():
    harness = make_harness()
    harness.process(echo_event("e1"))
    harness.process(echo_event("e1"))  # duplicate
    categories = {record.category for record in harness.audit.records}
    assert {"run", "dry-run", "idempotency"} <= categories
    assert harness.audit.to_jsonl()  # exportable
