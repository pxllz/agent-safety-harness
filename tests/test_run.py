import pytest

from agent_safety_harness import InvalidTransition, Run, RunState


def test_run_starts_in_started():
    run = Run(source_key="k1")
    assert run.state is RunState.STARTED
    assert not run.is_terminal
    assert run.finished_at is None


def test_run_completes():
    run = Run(source_key="k1")
    run.complete()
    assert run.state is RunState.COMPLETED
    assert run.is_terminal
    assert run.finished_at is not None


def test_run_fails_with_error():
    run = Run(source_key="k1")
    run.fail("boom")
    assert run.state is RunState.FAILED
    assert run.error == "boom"


@pytest.mark.parametrize("first", ["complete", "fail"])
@pytest.mark.parametrize("second", ["complete", "fail"])
def test_terminal_states_are_final(first, second):
    run = Run(source_key="k1")
    getattr(run, first)(*(["x"] if first == "fail" else []))
    with pytest.raises(InvalidTransition):
        getattr(run, second)(*(["y"] if second == "fail" else []))


def test_run_ids_are_unique():
    assert Run(source_key="a").run_id != Run(source_key="a").run_id
