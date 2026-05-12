# Linear Programming Solver API

A FastAPI service that solves linear programming (LP) and integer linear programming (ILP) problems via a single REST endpoint, powered by the [PuLP](https://coin-or.github.io/pulp/) library and the CBC solver.

## Setup

```bash
pip install -r requirements.txt
```

## Running the server

```bash
uvicorn main:app --reload
```

Interactive API docs: `http://localhost:8000/docs`

## Endpoint

### `POST /solve`

Accepts a linear programming problem and returns the optimal solution.

**Request body:**

```json
{
  "variables": ["a", "b", "c"],
  "objective": {"a": 1100, "b": 1200, "c": 1450},
  "goal": "max",
  "var_type": "continuous",
  "constraints": [
    {"coefficients": {"a": 8, "b": 8, "c": 9}, "operator": "<=", "rhs": 10120},
    {"coefficients": {"a": 8, "b": 9, "c": 11}, "operator": "<=", "rhs": 11000},
    {"coefficients": {"a": 1}, "operator": ">=", "rhs": 0},
    {"coefficients": {"b": 1}, "operator": ">=", "rhs": 0},
    {"coefficients": {"c": 1}, "operator": ">=", "rhs": 0}
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `variables` | `list[str]` | All variable names used in the problem |
| `objective` | `dict[str, float]` | Variable → coefficient in the objective function |
| `goal` | `"max"` \| `"min"` | Optimization direction |
| `var_type` | `"continuous"` \| `"integer"` | Variable domain (default: `"continuous"`) |
| `constraints` | `list[Constraint]` | Each has `coefficients`, `operator` (`<=`, `>=`, `=`), and `rhs` |

Any variable name used in `objective` or `constraints` that is absent from `variables` returns HTTP 422.

**Response body:**

```json
{
  "status": "Optimal",
  "objective_value": 1485000.0,
  "variables": {"a": 770.0, "b": 0.0, "c": 440.0}
}
```

`objective_value` and `variables` are `null` when the status is not `"Optimal"` (e.g. `"Infeasible"`, `"Unbounded"`).

## Running tests

```bash
pytest tests/ -v
```

## Project structure

```
linear_solver/
├── main.py           # FastAPI app + /solve endpoint
├── models.py         # Pydantic request & response schemas
├── solver.py         # PuLP solving logic
├── requirements.txt
└── tests/
    └── test_solver.py
```
