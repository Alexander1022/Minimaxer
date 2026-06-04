# Linear Programming Solver API

A FastAPI service that solves linear programming (LP) and integer linear programming (ILP) problems via a single REST endpoint, powered by the [PuLP](https://coin-or.github.io/pulp/) library and the CBC solver.

## Setup

```bash
pip install -r requirements.txt
```

## Running the server ![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)

```bash
uvicorn main:app --reload
```

## Running in docker continer

```bash
./start.sh        # build + up -d
./logs.sh         # tail
./stop.sh         # down
```
## After starting 

```text
http://localhost:8000/ — root
http://localhost:8000/api/health — healthcheck
http://localhost:8000/api/solve — POST endpoint
http://localhost:8000/docs — Swagger UI
```

Interactive API docs: `http://localhost:8000/docs`

## Running the client ![Gradio](https://img.shields.io/badge/Gradio-F97316?logo=gradio&logoColor=white)

```bash
python3 client/app.py
```

## Endpoint

### `POST /solve`

Accepts a linear programming problem and returns the optimal solution.

**Request body:**

```json
{
  "name": "OptimizationProblem",
  "direction": "maximize",
  "variables": [
    {"name": "a", "low_bound": null, "up_bound": null, "category": "Continuous"},
    {"name": "b", "low_bound": null, "up_bound": null, "category": "Continuous"},
    {"name": "c", "low_bound": null, "up_bound": null, "category": "Continuous"}
  ],
  "objective": {"coefficients": {"a": 1100, "b": 1200, "c": 1450}},
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
| `name` | `str` | Problem name (e.g., `"OptimizationProblem"`) |
| `direction` | `"maximize"` \| `"minimize"` | Optimization direction |
| `variables` | `list[VariableDefinition]` | Each has `name`, `low_bound`, `up_bound`, and `category` (`"Continuous"`, `"Integer"`, `"Binary"`) |
| `objective` | `LinearExpression` | Has `coefficients` dict mapping variable names to coefficients |
| `constraints` | `list[ConstraintDefinition]` | Each has `coefficients`, `operator` (`"<="`, `">="`, `"=="`), and `rhs` |

Any variable name used in `objective` or `constraints` that is absent from `variables` returns HTTP 422.

**Response body:**

```json
{
  "problem_name": "OptimizationProblem",
  "status": "Optimal",
  "objective_value": 1485000.0,
  "variables": [
    {"name": "a", "value": 770.0},
    {"name": "b", "value": 0.0},
    {"name": "c", "value": 440.0}
  ]
}
```

`objective_value` and `variables` are `null` when the status is not `"Optimal"` (e.g. `"Infeasible"`, `"Unbounded"`).

## Running tests ![pytest](https://img.shields.io/badge/pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)

```bash
pytest tests/ -v
```

## Project structure

```
server/
├── main.py           # FastAPI app + /solve endpoint
├── schemas/          # Pydantic request & response schemas
├── services/         # PuLP solving logic
├── core/             # Configuration
├── api/              # Route handlers
├── requirements.txt
└── test/
    └── test_solver.py
```
