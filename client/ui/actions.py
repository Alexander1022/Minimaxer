import re
import gradio as gr
from gradio_modal import Modal
import pandas as pd

from client.api.solver_api import solve_via_api
from client.core.builders import build_request
from client.core.parsing import normalize_rows, parse_float, parse_required_float

def initialize_saved_data(state):
    if not state:
        state = {}
        
    choices = list(state.keys())
    summary = update_history_summary(state)
    
    return summary, gr.update(choices=choices)

def _format_solver_response(req, response_json, saved_solutions=None, status_prefix="Успешно!"):
    variables_result = []
    if response_json.get("variables"):
        variables_result = [[v["name"], v["value"]] for v in response_json["variables"]]
    obj_val = response_json.get("objective_value", "Няма стойност")
    request_json = req.model_dump(mode="json")
    
    if saved_solutions is not None:
        saved_solutions[req.name] = {"request": request_json, "response": response_json}
        saved_names = list(saved_solutions.keys())
        summary = update_history_summary(saved_solutions)
        dropdown_update = gr.update(choices=saved_names, value=req.name)
        msg = f"{status_prefix} Решението е запазено като: {req.name}"
    else:
        saved_solutions = gr.update()
        dropdown_update = gr.update()
        summary = gr.update()
        msg = f"{status_prefix} (Решението не е запазено)"

    return (
        gr.update(visible=False),
        {},                      
        response_json,
        str(obj_val),
        variables_result,
        request_json,
        saved_solutions,
        dropdown_update,
        summary,
        msg,
    )

def _format_solver_error(exc, saved_solutions=None):
    return (
        gr.update(visible=False),
        {},
        {"error": str(exc)},      
        "",
        [],
        None,          
        saved_solutions if saved_solutions is not None else gr.update(),
        gr.update(),
        gr.update(),
        f"Грешка: {exc}",
    )

def show_panel():
    return Modal(visible=True)

def hide_panel():
    return Modal(visible=False)

def add_variable(name, low_bound, up_bound, category, current_rows, obj_rows):
    if not name or not str(name).strip():
        raise gr.Error("Името на променливата е задължително.")

    name = str(name).strip()
    low_val = parse_float(low_bound, f"Долна граница за {name}") if low_bound not in [None, ""] else None
    up_val = parse_float(up_bound, f"Горна граница за {name}") if up_bound not in [None, ""] else None

    rows = normalize_rows(current_rows)
    rows.append([name, low_val, up_val, category or "Continuous"])

    o_rows = normalize_rows(obj_rows)
    if not any(str(r[0]).strip() == name for r in o_rows):
        o_rows.append([name, 0])

    choices = [str(r[0]).strip() for r in rows]

    return (
        rows,
        o_rows,
        gr.update(choices=choices),
        "",
        None,
        None,
        "Continuous",
        gr.update(visible=False),
    )

def add_objective_coefficient(variable_name, coefficient, current_rows):
    if not variable_name or not str(variable_name).strip():
        raise gr.Error("Името на променливата в целевата функция е задължително.")

    variable_name = str(variable_name).strip()
    coefficient = parse_required_float(
        coefficient,
        f"Коефициент на целевата функция за променлива {variable_name}",
    )

    rows = normalize_rows(current_rows)
    updated = False

    for row in rows:
        if str(row[0]).strip() == variable_name:
            row[1] = coefficient
            updated = True
            break

    if not updated:
        rows.append([variable_name, coefficient])

    return (
        rows,
        gr.update(value=None),
        None,
        gr.update(visible=False),
    )

def add_constraint(name, coefficients_raw, operator, rhs, current_rows):
    if not coefficients_raw or not str(coefficients_raw).strip():
        raise gr.Error("Коефициентите на ограничението са задължителни. Пример: x:2,y:1")

    if not operator:
        raise gr.Error("Операторът на ограничението е задължителен.")

    rhs = parse_required_float(rhs, f"Дясна страна за ограничение {name or 'без_име'}")
    coefficients_raw = str(coefficients_raw).strip()

    for part in coefficients_raw.split(","):
        if ":" not in part:
            raise gr.Error(f"Невалиден формат за коефициент: {part}. Използвайте формат x:2,y:1")

        var_name, coef = part.split(":", 1)
        if not var_name.strip():
            raise gr.Error("Името на променливата в ограничението не може да бъде празно.")

        parse_required_float(
            coef.strip(),
            f"Коефициент за променлива {var_name.strip()} в ограничение {name or 'без_име'}",
        )

    rows = normalize_rows(current_rows)
    rows.append([
        None if name in [None, ""] else str(name).strip(),
        coefficients_raw,
        operator,
        rhs,
    ])

    return (
        rows,
        "",
        "",
        "<=",
        None,
        gr.update(visible=False),
    )

def solve_from_ui(problem_name, direction, variables_table, objective_table, constraints_table, saved_solutions):
    try:
        req = build_request(problem_name, direction, variables_table, objective_table, constraints_table)
        
        if saved_solutions and problem_name in saved_solutions:
            return (
                gr.update(visible=True),
                req.model_dump(mode="json"),
                gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), 
                gr.update(), gr.update(),
                "Забелязан конфликт в имената. Моля, изберете действие в страничния панел."
            )

        return perform_solve_and_save(req, saved_solutions)

    except Exception as exc:
        return _format_solver_error(exc, saved_solutions)

def perform_solve_and_save(req, saved_solutions):
    try:
        response_json = solve_via_api(req)
        return _format_solver_response(req, response_json, saved_solutions)
    except Exception as exc:
        return _format_solver_error(exc, saved_solutions)

def handle_overwrite(pending_req_json, saved_solutions):
    from shared.schemas.optimization import SolveRequest
    req = SolveRequest.model_validate(pending_req_json)
    return perform_solve_and_save(req, saved_solutions)

def handle_rename(new_name, pending_req_json, saved_solutions):
    if not new_name or not str(new_name).strip():
        raise gr.Error("Моля, въведете валидно ново име.")
    
    from shared.schemas.optimization import SolveRequest
    req_data = pending_req_json.copy()
    req_data["name"] = str(new_name).strip()
    return perform_solve_and_save(SolveRequest.model_validate(req_data), saved_solutions)

def solve_only(problem_name, direction, variables_table, objective_table, constraints_table):
    try:
        req = build_request(problem_name, direction, variables_table, objective_table, constraints_table)
        response_json = solve_via_api(req)
        return _format_solver_response(req, response_json)
    except Exception as exc:
        return _format_solver_error(exc)

def delete_solution(selected_name, saved_solutions):
    if not selected_name or not saved_solutions or selected_name not in saved_solutions:
        return saved_solutions, gr.update(), gr.update(), "Няма избрана задача за изтриване."
    
    del saved_solutions[selected_name]
    saved_names = list(saved_solutions.keys())
    summary = update_history_summary(saved_solutions)
    
    return (
        saved_solutions,
        gr.update(choices=saved_names, value=None),
        summary,
        f"Задачата '{selected_name}' беше изтрита."
    )

def toggle_preview(btn_text, problem_name, direction, variables_table, objective_table, constraints_table):
    from ui.preview import preview_problem
    if btn_text == "Скрий прегледа":
        return gr.update(visible=False), "Покажи преглед"
    else:
        content = preview_problem(problem_name, direction, variables_table, objective_table, constraints_table)
        return gr.update(value=content, visible=True), "Скрий прегледа"

def reconstruct_ui_inputs(selected_name, saved_solutions):
    if not selected_name or not saved_solutions or selected_name not in saved_solutions:
        return [gr.update()] * 6

    req = saved_solutions[selected_name]["request"]
    
    var_rows = [[v["name"], v.get("low_bound"), v.get("up_bound"), v.get("category", "Continuous")] 
                for v in req.get("variables", [])]
    
    obj_rows = [[var_name, coef] for var_name, coef in req.get("objective", {}).get("coefficients", {}).items()]
    
    const_rows = []
    for c in req.get("constraints", []):
        coef_str = ",".join([f"{k}:{v}" for k, v in c.get("coefficients", {}).items()])
        const_rows.append([c.get("name"), coef_str, c.get("operator"), c.get("rhs")])

    return (
        req.get("name"),
        req.get("direction"),
        var_rows,
        obj_rows,
        const_rows,
        saved_solutions[selected_name]["response"]
    )

def update_history_summary(saved_solutions):
    if not saved_solutions:
        return "Няма запазени решения."
    
    lines = [""]
    for name, data in saved_solutions.items():
        resp = data.get("response", {})
        status = resp.get("status", "Unknown")
        obj_val = resp.get("objective_value")
        if obj_val is not None:
            lines.append(f"- **{name}**: {status} (Цел: {obj_val:.2f})")
        else:
            lines.append(f"- **{name}**: {status}")
            
    return "\n".join(lines)

def load_saved_solution(selected_name, saved_solutions):
    if not selected_name or not saved_solutions or selected_name not in saved_solutions:
        return None, None

    item = saved_solutions[selected_name]
    return item["request"], item["response"]
