# agent-safety-harness

A small Python safety harness for experimenting with autonomous agents that
may propose or execute actions in sandboxed environments.

It focuses on deterministic gates, idempotency, dry-run-first workflows,
pause/emergency-stop controls, fake execution, and auditability.

## Why

Autonomous agents are easy to prototype and hard to trust. Before an agent is
allowed to *do* anything, you usually want the same boring guarantees every
time:

- the same trigger, delivered twice, must not act twice (**idempotency**),
- two proposals that *mean* the same thing must not both go through
  (**semantic anti-duplication**),
- every action passes an explicit risk check, and approvals are bound to the
  exact action they were issued for (**no approval reuse**),
- an operator can **pause** (resumable) or **emergency-stop** (latching, no
  reset) the whole pipeline at any moment,
- the default mode is **dry-run**: analyze what the agent *would* do before
  letting it do anything,
- everything that happens is written to an **audit log**.

This library packages those guarantees as small, dependency-free building
blocks. Execution is intentionally fake: the only backend is `FakeBroker`,
which records actions in memory and never touches the outside world.

## Install

```bash
git clone https://github.com/pxllz/agent-safety-harness.git
cd agent-safety-harness
pip install -e ".[dev]"
```

Requires Python 3.10+. No runtime dependencies.

## Quick start

```python
from agent_safety_harness import BasicRiskPolicy, Event, SafetyHarness

policy = BasicRiskPolicy(allowed_kinds={"echo"}, max_magnitude=100)
harness = SafetyHarness(policy=policy)  # dry_run=True by default

result = harness.process(
    Event(source_key="evt-001", kind="proposal",
          payload={"kind": "echo", "text": "hello", "magnitude": 5})
)
print(result.outcome)          # Outcome.DRY_RUN — approved, but nothing executed

# Redelivery of the same event? Dropped.
result = harness.process(
    Event(source_key="evt-001", kind="proposal",
          payload={"kind": "echo", "text": "hello", "magnitude": 5})
)
print(result.outcome)          # Outcome.DUPLICATE_EVENT

# Operator controls.
harness.pause("taking a look")     # resumable
harness.resume()
harness.stop("anomaly detected")   # latching — no reset exists

print(harness.audit.to_jsonl())    # full audit trail
```

A more complete walkthrough lives in
[`examples/basic_dry_run.py`](examples/basic_dry_run.py):

```bash
python examples/basic_dry_run.py
```

## Concepts

| Building block | What it guarantees |
|---|---|
| `Event` / `EventStore` | Each event carries a `source_key`; redeliveries of the same key are dropped. |
| `Run` | One processing attempt per event: `STARTED → COMPLETED \| FAILED`, terminal states are final. |
| `RiskPolicy` / `RiskResult` | Every proposed action is explicitly approved or rejected, with reasons. |
| `RiskApproval` | Bound to the action's semantic fingerprint — it cannot authorize a different action. |
| `semantic_fingerprint` | Stable hash of an action's *meaning* (key order, `1` vs `1.0`, stray whitespace are ignored) used to block duplicates. |
| `PauseGate` | Resumable operator gate checked before any processing. |
| `EmergencyStopGate` | Latching gate: once triggered, it stays closed for the process lifetime. |
| `FakeBroker` | The only execution backend. Records actions in memory; refuses approvals that don't match the action. |
| `AuditLog` | Append-only trail of every decision, exportable as JSONL. |

The pipeline order inside `SafetyHarness.process` is fixed and deterministic:

```
emergency stop → pause → idempotency → run start → risk policy
    → semantic anti-duplicate → dry-run record  (or fake execution)
```

## Non-goals

- **No real-world integrations.** There is no broker, exchange, or external
  execution system here, and none is planned in the core. `FakeBroker` is the
  point, not a placeholder.
- **No network, no credentials, no configuration files.** The library is
  plain in-memory Python.
- **Not financial software and not financial advice.** The building blocks
  are generic; the examples act on made-up actions like `echo`.
- **Not a policy engine.** `BasicRiskPolicy` exists for tests and demos; real
  use cases should implement the `RiskPolicy` protocol.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

[MIT](LICENSE)
