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
            if ":" not in part:
                continue
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


def coefficients_to_row_string(coeffs):
    return ",".join([f"{k}:{v}" for k, v in coeffs.items()])


def update_history_summary(saved_solutions):
    if not saved_solutions:
        return "No saved solutions yet."
    
    lines = ["### Saved History"]
    for name, item in saved_solutions.items():
        resp = item.get("response", {})
        status = resp.get("status", "Unknown")
        obj_val = resp.get("objective_value")
        val_str = f"({obj_val})" if obj_val is not None else ""
        lines.append(f"- **{name}**: {status} {val_str}")
    
    return "\n".join(lines)


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


def perform_solve_and_save(req, saved_solutions):
    try:
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
        summary = update_history_summary(saved_solutions)

        return (
            response_json,
            variables_result,
            request_json,
            saved_solutions,
            gr.update(choices=saved_names, value=req.name),
            f"Saved solution as: {req.name}",
            summary,
            gr.update(visible=False), # Hide collision UI
        )

    except (ValueError, ValidationError, KeyError, requests.RequestException) as exc:
        return (
            {"error": str(exc)},
            [],
            None,
            saved_solutions or {},
            gr.update(),
            f"Error: {exc}",
            update_history_summary(saved_solutions),
            gr.update(),
        )


def check_and_solve(problem_name, direction, variables_table, objective_table, constraints_table, saved_solutions):
    try:
        req = build_request(
            problem_name,
            direction,
            variables_table,
            objective_table,
            constraints_table,
        )
        
        if req.name in (saved_solutions or {}):
            return (
                gr.update(), # response_output
                gr.update(), # result_table
                gr.update(), # request_output
                saved_solutions,
                gr.update(), # saved_dropdown
                f"Collision: Name '{req.name}' already exists.",
                gr.update(), # summary
                gr.update(visible=True), # Show collision UI
                req.model_dump(mode="json"), # Store in pending_request
            )
        
        return perform_solve_and_save(req, saved_solutions) + (None,)

    except Exception as exc:
        return (
            {"error": str(exc)},
            [],
            None,
            saved_solutions or {},
            gr.update(),
            f"Error: {exc}",
            update_history_summary(saved_solutions),
            gr.update(visible=False),
            None,
        )


def handle_overwrite(pending_req_json, saved_solutions):
    if not pending_req_json:
        return [gr.update()] * 8
    
    req = SolveRequest.model_validate(pending_req_json)
    return perform_solve_and_save(req, saved_solutions) + (None,)


def handle_rename(new_name, pending_req_json, saved_solutions):
    if not pending_req_json or not new_name:
        return [gr.update()] * 8
    
    req_dict = pending_req_json.copy()
    req_dict["name"] = new_name
    req = SolveRequest.model_validate(req_dict)
    
    # Still check if new name exists
    if new_name in (saved_solutions or {}):
         return (
            gr.update(), gr.update(), gr.update(), saved_solutions, gr.update(),
            f"Error: New name '{new_name}' also exists.",
            gr.update(), gr.update(visible=True), pending_req_json
        )

    return perform_solve_and_save(req, saved_solutions) + (None,)


def reconstruct_ui_inputs(selected_name, saved_solutions):
    if not selected_name or not saved_solutions or selected_name not in saved_solutions:
        return [gr.update()] * 6

    item = saved_solutions[selected_name]
    req = item["request"]
    
    # Variables
    vars_data = []
    for v in req.get("variables", []):
        vars_data.append([v["name"], v["low_bound"], v["up_bound"], v["category"]])
    
    # Objective
    obj_data = []
    coeffs = req.get("objective", {}).get("coefficients", {})
    for var, coef in coeffs.items():
        obj_data.append([var, coef])
    
    # Constraints
    const_data = []
    for c in req.get("constraints", []):
        coeff_str = coefficients_to_row_string(c.get("coefficients", {}))
        const_data.append([c.get("name"), coeff_str, c.get("operator"), c.get("rhs")])

    return (
        req.get("name"),
        req.get("direction"),
        vars_data,
        obj_data,
        const_data,
        item["response"],
    )


def load_saved_solution(selected_name, saved_solutions):
    if not selected_name or not saved_solutions or selected_name not in saved_solutions:
        return None, None

    item = saved_solutions[selected_name]
    return item["request"], item["response"]


with gr.Blocks(title="Linear Optimization Solver") as demo:
    gr.Markdown("# Linear Optimization Solver")
    
    # Persistent history in Local Storage
    saved_solutions = gr.BrowserState(storage_key="minimaxer_history", default_value={})
    # Temporary state for handling naming collisions
    pending_request = gr.State(None)

    with gr.Sidebar():
        gr.Markdown("## History & Management")
        
        saved_dropdown = gr.Dropdown(
            label="Saved solution names",
            choices=[],
            interactive=True,
        )

        load_btn = gr.Button("Load and Edit Problem", variant="secondary")
        
        history_summary = gr.Markdown("No saved solutions yet.")
        
        with gr.Group(visible=False) as collision_ui:
            gr.Markdown("### ⚠️ Name Collision")
            gr.Markdown("A problem with this name already exists. What would you like to do?")
            
            overwrite_btn = gr.Button("Overwrite Existing", variant="stop")
            
            with gr.Row():
                new_name_input = gr.Textbox(label="New Name", placeholder="Enter new name...")
                rename_btn = gr.Button("Save as New")

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

    solve_btn = gr.Button("Solve and Save", variant="primary")

    status_message = gr.Textbox(label="Status", interactive=False)

    with gr.Row():
        response_output = gr.JSON(label="Solve response")
        request_output = gr.JSON(label="Generated request JSON")

    result_table = gr.Dataframe(
        label="Variable results",
        headers=["name", "value"],
        interactive=False,
    )

    # Event: Initial load or refresh - update the dropdown and summary from BrowserState
    demo.load(
        fn=lambda s: (gr.update(choices=list(s.keys())), update_history_summary(s)),
        inputs=[saved_solutions],
        outputs=[saved_dropdown, history_summary]
    )

    # Event: Main Solve button
    solve_btn.click(
        fn=check_and_solve,
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
            history_summary,
            collision_ui,
            pending_request,
        ],
    )

    # Event: Overwrite collision
    overwrite_btn.click(
        fn=handle_overwrite,
        inputs=[pending_request, saved_solutions],
        outputs=[
            response_output,
            result_table,
            request_output,
            saved_solutions,
            saved_dropdown,
            status_message,
            history_summary,
            collision_ui,
            pending_request,
        ],
    )

    # Event: Rename collision
    rename_btn.click(
        fn=handle_rename,
        inputs=[new_name_input, pending_request, saved_solutions],
        outputs=[
            response_output,
            result_table,
            request_output,
            saved_solutions,
            saved_dropdown,
            status_message,
            history_summary,
            collision_ui,
            pending_request,
        ],
    )

    # Event: Load from history
    load_btn.click(
        fn=reconstruct_ui_inputs,
        inputs=[saved_dropdown, saved_solutions],
        outputs=[
            problem_name,
            direction,
            variables_table,
            objective_table,
            constraints_table,
            response_output,
        ],
    )


if __name__ == "__main__":
    demo.launch()