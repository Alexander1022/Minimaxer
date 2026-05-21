import gradio as gr
from gradio_modal import Modal
import requests
from pydantic import ValidationError

from api.solver_api import solve_via_api
from core.builders import build_request
from core.parsing import normalize_rows, parse_float, parse_required_float

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
            f"Успешно! Решението е запазено като: {req.name}",
        )

    except (ValueError, ValidationError, KeyError, requests.RequestException) as exc:
        return (
            {"error": str(exc)},
            [],
            None,
            saved_solutions or {},
            gr.update(),
            f"Грешка: {exc}",
        )

def load_saved_solution(selected_name, saved_solutions):
    if not selected_name or not saved_solutions or selected_name not in saved_solutions:
        return None, None

    item = saved_solutions[selected_name]
    return item["request"], item["response"]