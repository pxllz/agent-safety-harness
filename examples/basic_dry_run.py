"""Basic dry-run analysis.

Feeds a batch of events through a SafetyHarness in dry-run mode (the
default), then prints what *would* have happened — including duplicates
dropped, rejections, and gate blocks — and the audit trail.

Run it with:  python examples/basic_dry_run.py
"""

from __future__ import annotations

from collections import Counter

from agent_safety_harness import BasicRiskPolicy, Event, Outcome, SafetyHarness


def main() -> None:
    policy = BasicRiskPolicy(allowed_kinds={"echo", "write_file"}, max_magnitude=100)
    harness = SafetyHarness(policy=policy)  # dry_run=True by default

    events = [
        # A normal, approvable action.
        Event("evt-001", "proposal", {"kind": "echo", "text": "hello", "magnitude": 5}),
        # Exact redelivery of evt-001: dropped by source_key idempotency.
        Event("evt-001", "proposal", {"kind": "echo", "text": "hello", "magnitude": 5}),
        # New event, but semantically the same action (note key order and 5.0):
        # blocked by the semantic fingerprint.
        Event("evt-002", "proposal", {"magnitude": 5.0, "text": " hello ", "kind": "echo"}),
        # Over the magnitude limit: rejected by the risk policy.
        Event("evt-003", "proposal", {"kind": "write_file", "path": "out.txt", "magnitude": 9000}),
        # Action kind not in the allowlist: rejected.
        Event("evt-004", "proposal", {"kind": "delete_everything"}),
        # A second legitimate action.
        Event("evt-005", "proposal", {"kind": "write_file", "path": "notes.md", "magnitude": 2}),
    ]

    print("=== processing events (dry-run) ===")
    outcomes: Counter[Outcome] = Counter()
    for event in events:
        result = harness.process(event)
        outcomes[result.outcome] += 1
        print(f"  {event.source_key}: {result.outcome.value}")

    print("\n=== pause gate ===")
    harness.pause("operator taking a look")
    result = harness.process(Event("evt-006", "proposal", {"kind": "echo", "text": "while paused"}))
    outcomes[result.outcome] += 1
    print(f"  evt-006 while paused: {result.outcome.value}")
    harness.resume()
    result = harness.process(Event("evt-006", "proposal", {"kind": "echo", "text": "while paused"}))
    outcomes[result.outcome] += 1
    print(f"  evt-006 redelivered after resume: {result.outcome.value}")

    print("\n=== emergency stop ===")
    harness.stop("demo: anomaly detected")
    result = harness.process(Event("evt-007", "proposal", {"kind": "echo", "text": "too late"}))
    outcomes[result.outcome] += 1
    print(f"  evt-007 after stop: {result.outcome.value} (latched: no reset exists)")

    print("\n=== dry-run analysis ===")
    for outcome, count in sorted(outcomes.items(), key=lambda item: item[0].value):
        print(f"  {outcome.value:<17} {count}")
    print(f"  runs recorded: {len(harness.runs)}, broker executions: 0 (dry-run)")

    print("\n=== audit trail (JSONL) ===")
    print(harness.audit.to_jsonl())


if __name__ == "__main__":
    main()
