import pytest

from agent_safety_harness import semantic_fingerprint


def test_key_order_is_irrelevant():
    a = {"kind": "echo", "text": "hello", "n": 3}
    b = {"n": 3, "text": "hello", "kind": "echo"}
    assert semantic_fingerprint(a) == semantic_fingerprint(b)


def test_integral_floats_collapse_to_ints():
    assert semantic_fingerprint({"n": 1}) == semantic_fingerprint({"n": 1.0})
    assert semantic_fingerprint({"n": 1}) != semantic_fingerprint({"n": 1.5})


def test_string_whitespace_is_stripped():
    assert semantic_fingerprint({"t": " hello "}) == semantic_fingerprint({"t": "hello"})


def test_nested_structures():
    a = {"steps": [{"b": 2, "a": 1}, {"c": 3}]}
    b = {"steps": [{"a": 1, "b": 2}, {"c": 3}]}
    assert semantic_fingerprint(a) == semantic_fingerprint(b)


def test_list_order_matters():
    assert semantic_fingerprint({"xs": [1, 2]}) != semantic_fingerprint({"xs": [2, 1]})


def test_different_actions_differ():
    assert semantic_fingerprint({"kind": "echo"}) != semantic_fingerprint({"kind": "write"})


def test_bool_and_int_do_not_collide():
    assert semantic_fingerprint({"v": True}) != semantic_fingerprint({"v": 1})


def test_unsupported_types_raise():
    with pytest.raises(TypeError):
        semantic_fingerprint({"f": object()})
