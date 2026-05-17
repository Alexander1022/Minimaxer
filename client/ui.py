import gradio as gr
import requests
from pydantic import ValidationError

# Dumb way to import the server-side schema without creating a separate shared package
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "server"))


from schemas.optimization import (
    ConstraintDefinition,
    ConstraintOperator,
    LinearExpression,
    OptimizationDirection,
    SolveRequest,
    VariableDefinition,
)

API_BASE_URL = "http://127.0.0.1:8000/api"

def parse_float(value, field_name):
    if value in [None, ""]:
        return None

    try:
        return float(value)
    except ValueError:
        print(f"PARSE FLOAT ERROR: {field_name} must be a number, got: {value!r}")
        raise ValueError(f"{field_name} must be a number, got: {value!r}")
    
def parse_required_float(value, field_name):
    if value in [None, ""]:
        raise ValueError(f"{field_name} is required")

    try:
        return float(value)
    except ValueError:
        print(f"PARSE REQUIRED FLOAT ERROR: {field_name} must be a number, got: {value!r}")
        raise ValueError(f"{field_name} must be a number, got: {value!r}")
    
def rows_to_variables(rows):
    variables = []
    
    print(rows)

    if rows is None:
        return variables
    
    if hasattr(rows, 'values'):
        rows = rows.values.tolist()

    for row in rows:
        if not row or not row[0]:
            continue

        name = str(row[0]).strip()
        print(f"Variable: {name}, Row: {row}")
        low_bound = parse_float(row[1], f"Low bound for variable {name}")
        up_bound = parse_float(row[2], f"Upper bound for variable {name}")
        category = str(row[3] or "Continuous").strip()

        variables.append(
            VariableDefinition(
                name=name,
                low_bound=low_bound,
                up_bound=up_bound,
                category=category,
            )
        )

    return variables


def rows_to_coefficients(rows):
    coefficients = {}
    
    # Handle Gradio dataframe format - convert to list of lists if needed
    if rows is None:
        return coefficients
    
    if hasattr(rows, 'values'):  # pandas DataFrame
        rows = rows.values.tolist()

    for row in rows:
        if not row or not row[0]:
            continue

        name = str(row[0]).strip()
        value = float(row[1])
        coefficients[name] = value

    return coefficients


def rows_to_constraints(rows):
    constraints = []
    
    # Handle Gradio dataframe format - convert to list of lists if needed
    if rows is None:
        return constraints
    
    if hasattr(rows, 'values'):  # pandas DataFrame
        rows = rows.values.tolist()

    for row in rows:
        if not row or not row[1]:
            continue

        name = None if row[0] in [None, ""] else str(row[0]).strip()
        coefficients_raw = str(row[1]).strip()
        operator = str(row[2]).strip()
        rhs = parse_required_float(row[3], f"RHS for constraint {name or 'unnamed'}")

        coefficients = {}
        for part in coefficients_raw.split(","):
            var_name, coef = part.split(":")
            coefficients[var_name.strip()] = parse_required_float(
                coef.strip(),
                f"Coefficient for variable {var_name.strip()} in constraint {name or 'unnamed'}"
            )

        constraints.append(
            ConstraintDefinition(
                name=name,
                coefficients=coefficients,
                operator=ConstraintOperator(operator),
                rhs=rhs,
            )
        )

    return constraints


def build_request(problem_name, direction, variables_table, objective_table, constraints_table):
    variables = rows_to_variables(variables_table)
    objective_coefficients = rows_to_coefficients(objective_table)
    constraints = rows_to_constraints(constraints_table)

    return SolveRequest(
        name=problem_name or "OptimizationProblem",
        direction=OptimizationDirection(direction),
        variables=variables,
        objective=LinearExpression(coefficients=objective_coefficients),
        constraints=constraints,
    )

def solve_via_api(req: SolveRequest) -> dict:
    response = requests.post(
        f"{API_BASE_URL}/solve",
        json=req.model_dump(mode="json"),
        timeout=10,
    )

    if response.status_code != 200:
        try:
            detail = response.json().get("detail")
        except Exception:
            detail = response.text

        raise ValueError(detail)

    return response.json()


def solve_from_ui(problem_name, direction, variables_table, objective_table, constraints_table, saved_solutions):
    try:
        req = build_request(
            problem_name,
            direction,
            variables_table,
            objective_table,
            constraints_table,
        )

        request_json = req.model_dump(mode="json")
        response_json = solve_via_api(req)

        variables_result = []
        if response_json.get("variables"):
            variables_result = [
                [v["name"], v["value"]]
                for v in response_json["variables"]
            ]

        saved_solutions = saved_solutions or {}
        saved_solutions[req.name] = {
            "request": request_json,
            "response": response_json,
        }

        saved_names = list(saved_solutions.keys())

        return (
            response_json,
            variables_result,
            request_json,
            saved_solutions,
            gr.update(choices=saved_names, value=req.name),
            f"Saved solution as: {req.name}",
        )

    except (ValueError, ValidationError, KeyError, requests.RequestException) as exc:
        return (
            {"error": str(exc)},
            [],
            None,
            saved_solutions or {},
            gr.update(),
            f"Error: {exc}",
        )


def load_saved_solution(selected_name, saved_solutions):
    if not selected_name or not saved_solutions or selected_name not in saved_solutions:
        return None, None

    item = saved_solutions[selected_name]
    return item["request"], item["response"]


with gr.Blocks(title="Linear Optimization Solver") as demo:
    gr.Markdown("# Linear Optimization Solver")
    gr.Markdown("Define variables, objective function, and constraints. Then solve and save named solutions.")

    saved_solutions = gr.State({})

    with gr.Row():
        problem_name = gr.Textbox(
            label="Problem name",
            value="OptimizationProblem",
        )

        direction = gr.Dropdown(
            label="Optimization direction",
            choices=["maximize", "minimize"],
            value="maximize",
        )

    gr.Markdown("## Variables")

    variables_table = gr.Dataframe(
        label="Variables",
        headers=["name", "low_bound", "up_bound", "category"],
        value=[
            ["x", 0, None, "Continuous"],
            ["y", 0, None, "Continuous"],
        ],
        row_count=(2, "dynamic"),
        col_count=(4, "fixed"),
        interactive=True,
    )

    gr.Markdown("## Objective")
    gr.Markdown("Example: `5x + 3y` becomes rows `x | 5` and `y | 3`.")

    objective_table = gr.Dataframe(
        label="Objective coefficients",
        headers=["variable", "coefficient"],
        value=[
            ["x", 5],
            ["y", 3],
        ],
        row_count=(2, "dynamic"),
        col_count=(2, "fixed"),
        interactive=True,
    )

    gr.Markdown("## Constraints")
    gr.Markdown("Write coefficients as `x:2,y:1`. Example: `2x + y <= 10` becomes `x:2,y:1 | <= | 10`.")

    constraints_table = gr.Dataframe(
        label="Constraints",
        headers=["name", "coefficients", "operator", "rhs"],
        value=[
            ["c1", "x:2,y:1", "<=", 10],
            ["c2", "x:1,y:1", "<=", 7],
        ],
        row_count=(2, "dynamic"),
        col_count=(4, "fixed"),
        interactive=True,
    )

    solve_btn = gr.Button("Solve and save", variant="primary")

    status_message = gr.Textbox(label="Status", interactive=False)

    with gr.Row():
        response_output = gr.JSON(label="Solve response")
        request_output = gr.JSON(label="Generated request JSON")

    result_table = gr.Dataframe(
        label="Variable results",
        headers=["name", "value"],
        interactive=False,
    )

    gr.Markdown("## Saved solutions")

    saved_dropdown = gr.Dropdown(
        label="Saved solution names",
        choices=[],
        interactive=True,
    )

    load_btn = gr.Button("Load saved solution")

    with gr.Row():
        saved_request_output = gr.JSON(label="Saved request")
        saved_response_output = gr.JSON(label="Saved response")

    solve_btn.click(
        fn=solve_from_ui,
        inputs=[
            problem_name,
            direction,
            variables_table,
            objective_table,
            constraints_table,
            saved_solutions,
        ],
        outputs=[
            response_output,
            result_table,
            request_output,
            saved_solutions,
            saved_dropdown,
            status_message,
        ],
    )

    load_btn.click(
        fn=load_saved_solution,
        inputs=[saved_dropdown, saved_solutions],
        outputs=[saved_request_output, saved_response_output],
    )


if __name__ == "__main__":
    demo.launch()