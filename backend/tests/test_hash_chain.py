from datetime import datetime, timezone

from app.services.hash_chain import canonical_json, compute_chain_hash


def test_canonical_json_is_deterministic() -> None:
    a = {"b": 1, "a": {"z": 2, "y": 3}}
    b = {"a": {"y": 3, "z": 2}, "b": 1}

    assert canonical_json(a) == canonical_json(b)


def test_compute_chain_hash_changes_with_prev_hash() -> None:
    base = {
        "id": 1,
        "session_id": "s1",
        "node_id": "n1",
        "gateway_received_at": datetime(2026, 3, 30, tzinfo=timezone.utc),
        "payload_hash": "abc",
        "prev_hash": None,
    }

    hash_one = compute_chain_hash(base)
    base["prev_hash"] = hash_one
    hash_two = compute_chain_hash(base)

    assert hash_one != hash_two
