import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

EXAMPLE_PAYLOAD = {
    "name": "OptimizationProblem",
    "direction": "maximize",
    "variables": [
        {"name": "a", "low_bound": None, "up_bound": None, "category": "Continuous"},
        {"name": "b", "low_bound": None, "up_bound": None, "category": "Continuous"},
        {"name": "c", "low_bound": None, "up_bound": None, "category": "Continuous"},
    ],
    "objective": {"coefficients": {"a": 1100, "b": 1200, "c": 1450}},
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
    var_dict = {v["name"]: v["value"] for v in data["variables"]}
    assert var_dict["a"] == pytest.approx(770, rel=1e-6)
    assert var_dict["b"] == pytest.approx(0, abs=1e-6)
    assert var_dict["c"] == pytest.approx(440, rel=1e-6)


def test_min_example():
    payload = {**EXAMPLE_PAYLOAD, "direction": "minimize"}
    resp = client.post("/solve", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "Optimal"
    assert data["objective_value"] == pytest.approx(0, abs=1e-6)
    var_values = [v["value"] for v in data["variables"]]
    assert all(v == pytest.approx(0, abs=1e-6) for v in var_values)


def test_infeasible():
    payload = {
        "name": "InfeasibleProblem",
        "direction": "maximize",
        "variables": [
            {"name": "a", "low_bound": None, "up_bound": None, "category": "Continuous"},
            {"name": "b", "low_bound": None, "up_bound": None, "category": "Continuous"},
        ],
        "objective": {"coefficients": {"a": 1, "b": 1}},
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
    payload = {**EXAMPLE_PAYLOAD, "objective": {"coefficients": {"a": 1100, "b": 1200, "d": 1450}}}
    resp = client.post("/solve", json=payload)
    assert resp.status_code == 422


def test_unknown_variable_in_constraint():
    bad_constraints = EXAMPLE_PAYLOAD["constraints"].copy()
    bad_constraints[0] = {"coefficients": {"a": 8, "z": 8, "c": 9}, "operator": "<=", "rhs": 10120}
    payload = {**EXAMPLE_PAYLOAD, "constraints": bad_constraints}
    resp = client.post("/solve", json=payload)
    assert resp.status_code == 422


def test_integer_mode():
    payload = {**EXAMPLE_PAYLOAD}
    payload["variables"] = [
        {"name": "a", "low_bound": None, "up_bound": None, "category": "Integer"},
        {"name": "b", "low_bound": None, "up_bound": None, "category": "Integer"},
        {"name": "c", "low_bound": None, "up_bound": None, "category": "Integer"},
    ]
    resp = client.post("/solve", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "Optimal"
    var_values = [v["value"] for v in data["variables"]]
    for val in var_values:
        assert val == pytest.approx(round(val), abs=1e-6)