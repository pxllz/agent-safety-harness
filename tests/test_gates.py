import pytest

from agent_safety_harness import EmergencyStopGate, GateBlocked, PauseGate


def test_pause_gate_blocks_and_resumes():
    gate = PauseGate()
    gate.check()  # open: no raise
    gate.pause("maintenance")
    assert gate.is_paused
    assert gate.reason == "maintenance"
    with pytest.raises(GateBlocked):
        gate.check()
    gate.resume()
    assert not gate.is_paused
    gate.check()


def test_emergency_stop_latches():
    gate = EmergencyStopGate()
    gate.check()
    gate.trigger("anomaly detected")
    assert gate.is_stopped
    with pytest.raises(GateBlocked) as excinfo:
        gate.check()
    assert "emergency-stop" in str(excinfo.value)
    # No reset API exists.
    assert not hasattr(gate, "reset")
    assert not hasattr(gate, "resume")


def test_emergency_stop_first_reason_wins():
    gate = EmergencyStopGate()
    gate.trigger("first")
    gate.trigger("second")
    assert gate.reason == "first"


def test_emergency_stop_requires_reason():
    gate = EmergencyStopGate()
    with pytest.raises(ValueError):
        gate.trigger("")
