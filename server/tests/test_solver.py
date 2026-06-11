import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

EXAMPLE_PAYLOAD = {
  "name": "ProductionPlanning",
  "direction": "maximize",
  "variables": [
    {
      "name": "x",
      "low_bound": 0,
      "category": "Continuous"
    },
    {
      "name": "y",
      "low_bound": 0,
      "category": "Continuous"
    }
  ],
  "objective": {
    "coefficients": {
      "x": 5,
      "y": 3
    }
  },
  "constraints": [
    {
      "name": "MachineTime",
      "coefficients": {
        "x": 2,
        "y": 1
      },
      "operator": "<=",
      "rhs": 10
    },
    {
      "name": "MaterialLimit",
      "coefficients": {
        "x": 1,
        "y": 1
      },
      "operator": "<=",
      "rhs": 7
    }
  ]
}

# TODO: Fix the tests because the path is no longer `/api/solve`

def test_max_example():
    resp = client.post("/api/solvers/linear", json=EXAMPLE_PAYLOAD)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "Optimal"
    assert data["objective_value"] == pytest.approx(27, rel=1e-6)
    var_dict = {v["name"]: v["value"] for v in data["variables"]}
    assert var_dict["x"] == pytest.approx(3, rel=1e-6)
    assert var_dict["y"] == pytest.approx(4, abs=1e-6)


def test_min_example():
    payload = {**EXAMPLE_PAYLOAD, "direction": "minimize"}
    resp = client.post("/api/solvers/linear", json=payload)
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
    resp = client.post("/api/solvers/linear", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "Infeasible"
    assert data["objective_value"] is None
    assert data["variables"] is None


def test_unknown_variable_in_objective():
    payload = {**EXAMPLE_PAYLOAD, "objective": {"coefficients": {"a": 1100, "b": 1200, "d": 1450}}}
    resp = client.post("/api/solvers/linear", json=payload)
    assert resp.status_code == 422


def test_unknown_variable_in_constraint():
    bad_constraints = EXAMPLE_PAYLOAD["constraints"].copy()
    bad_constraints[0] = {"coefficients": {"a": 8, "z": 8, "c": 9}, "operator": "<=", "rhs": 10120}
    payload = {**EXAMPLE_PAYLOAD, "constraints": bad_constraints}
    resp = client.post("/api/solvers/linear", json=payload)
    assert resp.status_code == 422


def test_integer_mode():
    payload = {**EXAMPLE_PAYLOAD}
    payload["variables"] = [
        {"name": "x", "low_bound": 0, "up_bound": None, "category": "Integer"},
        {"name": "y", "low_bound": 0, "up_bound": None, "category": "Integer"},
    ]
    resp = client.post("/api/solvers/linear", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "Optimal"
    var_values = [v["value"] for v in data["variables"]]
    for val in var_values:
        assert val == pytest.approx(round(val), abs=1e-6)