import pytest

from agent_safety_harness import Event, EventStore


def test_event_requires_source_key():
    with pytest.raises(ValueError):
        Event(source_key="", kind="tick")


def test_event_requires_kind():
    with pytest.raises(ValueError):
        Event(source_key="k1", kind="")


def test_event_payload_is_frozen():
    event = Event(source_key="k1", kind="tick", payload={"a": 1})
    with pytest.raises(TypeError):
        event.payload["a"] = 2  # type: ignore[index]


def test_store_ingests_new_events():
    store = EventStore()
    assert store.ingest(Event(source_key="k1", kind="tick")) is True
    assert "k1" in store
    assert len(store) == 1


def test_store_drops_duplicate_source_key():
    store = EventStore()
    first = Event(source_key="k1", kind="tick", payload={"n": 1})
    redelivery = Event(source_key="k1", kind="tick", payload={"n": 2})
    assert store.ingest(first) is True
    assert store.ingest(redelivery) is False
    stored = store.get("k1")
    assert stored is not None
    assert stored.payload["n"] == 1  # first delivery wins
