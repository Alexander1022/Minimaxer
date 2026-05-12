import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

EXAMPLE_PAYLOAD = {
    "variables": ["a", "b", "c"],
    "objective": {"a": 1100, "b": 1200, "c": 1450},
    "goal": "max",
    "constraints": [
        {"coefficients": {"a": 8, "b": 8, "c": 9}, "operator": "<=", "rhs": 10120},
        {"coefficients": {"a": 8, "b": 9, "c": 11}, "operator": "<=", "rhs": 11000},
        {"coefficients": {"a": 1}, "operator": ">=", "rhs": 0},
        {"coefficients": {"b": 1}, "operator": ">=", "rhs": 0},
        {"coefficients": {"c": 1}, "operator": ">=", "rhs": 0},
    ],
}


def test_max_example():
    resp = client.post("/solve", json=EXAMPLE_PAYLOAD)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "Optimal"
    assert data["objective_value"] == pytest.approx(1_485_000, rel=1e-6)
    assert data["variables"]["a"] == pytest.approx(770, rel=1e-6)
    assert data["variables"]["b"] == pytest.approx(0, abs=1e-6)
    assert data["variables"]["c"] == pytest.approx(440, rel=1e-6)


def test_min_example():
    payload = {**EXAMPLE_PAYLOAD, "goal": "min"}
    resp = client.post("/solve", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "Optimal"
    assert data["objective_value"] == pytest.approx(0, abs=1e-6)
    assert all(v == pytest.approx(0, abs=1e-6) for v in data["variables"].values())


def test_infeasible():
    payload = {
        "variables": ["a", "b"],
        "objective": {"a": 1, "b": 1},
        "goal": "max",
        "constraints": [
            {"coefficients": {"a": 1, "b": 1}, "operator": "<=", "rhs": 5},
            {"coefficients": {"a": 1, "b": 1}, "operator": ">=", "rhs": 10},
            {"coefficients": {"a": 1}, "operator": ">=", "rhs": 0},
            {"coefficients": {"b": 1}, "operator": ">=", "rhs": 0},
        ],
    }
    resp = client.post("/solve", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "Infeasible"
    assert data["objective_value"] is None
    assert data["variables"] is None


def test_unknown_variable_in_objective():
    payload = {**EXAMPLE_PAYLOAD, "objective": {"a": 1100, "b": 1200, "d": 1450}}
    resp = client.post("/solve", json=payload)
    assert resp.status_code == 422


def test_unknown_variable_in_constraint():
    bad_constraints = EXAMPLE_PAYLOAD["constraints"].copy()
    bad_constraints[0] = {"coefficients": {"a": 8, "z": 8, "c": 9}, "operator": "<=", "rhs": 10120}
    payload = {**EXAMPLE_PAYLOAD, "constraints": bad_constraints}
    resp = client.post("/solve", json=payload)
    assert resp.status_code == 422


def test_integer_mode():
    payload = {**EXAMPLE_PAYLOAD, "var_type": "integer"}
    resp = client.post("/solve", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "Optimal"
    for val in data["variables"].values():
        assert val == pytest.approx(round(val), abs=1e-6)
