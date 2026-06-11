import gradio as gr
from gradio_modal import Modal

from client.api.solver_api import solve_via_api
from client.core.electre_builders import build_electre_request
from client.core.parsing import normalize_rows, parse_required_float


def initialize_electre_saved_data(state):
    if not state:
        state = {}
    summary = update_electre_history_summary(state)
    return summary, gr.update(choices=list(state.keys()))


def update_electre_history_summary(saved_solutions):
    if not saved_solutions:
        return "Няма запазени ELECTRE решения."

    lines = [""]
    for name, data in saved_solutions.items():
        resp = (data or {}).get("response") or {}
        status = resp.get("status", "Unknown")
        kernel = resp.get("kernel") or []
        if kernel:
            lines.append(f"- **{name}**: {status} (ядро: {', '.join(kernel)})")
        else:
            lines.append(f"- **{name}**: {status}")

    return "\n".join(lines)


def _format_electre_kernel(kernel):
    if not kernel:
        return "Няма елементи в ядрото."
    return "Ядро (недоминирани алтернативи): **" + ", ".join(kernel) + "**"


def _format_outranking_rows(outranking):
    if not outranking:
        return []
    return [
        [p["dominator"], p["dominated"], f"{p['concordance']:.4f}", f"{p['discordance']:.4f}"]
        for p in outranking
    ]


def _format_electre_solver_response(req, response_json, saved_solutions=None, status_prefix="Успешно!"):
    kernel_text = _format_electre_kernel(response_json.get("kernel") or [])
    outranking_rows = _format_outranking_rows(response_json.get("outranking") or [])

    request_json = req.model_dump(mode="json")

    if saved_solutions is not None:
        saved_solutions[req.problem_name] = {"request": request_json, "response": response_json}
        saved_names = list(saved_solutions.keys())
        summary = update_electre_history_summary(saved_solutions)
        list_update = gr.update(choices=saved_names, value=req.problem_name)
        msg = f"{status_prefix} Решението е запазено като: {req.problem_name}"
    else:
        saved_solutions = gr.update()
        list_update = gr.update()
        summary = gr.update()
        msg = f"{status_prefix} (Решението не е запазено)"

    return (
        gr.update(visible=False),
        {},
        response_json,
        kernel_text,
        outranking_rows,
        request_json,
        saved_solutions,
        list_update,
        summary,
        msg,
    )


def _format_electre_solver_error(exc, saved_solutions=None):
    return (
        gr.update(visible=False),
        {},
        {"error": str(exc)},
        f"Грешка: {exc}",
        [],
        None,
        saved_solutions if saved_solutions is not None else gr.update(),
        gr.update(),
        gr.update(),
        f"Грешка: {exc}",
    )


def add_electre_criteria(name, direction, weight, c_type, current_rows, current_alternatives):
    if not name or not str(name).strip():
        raise gr.Error("Името на критерия е задължително.")

    name = str(name).strip()
    try:
        weight_val = parse_required_float(weight, f"Тежест за {name}")
    except ValueError as e:
        raise gr.Error(str(e))

    type_val = c_type if c_type in ["quantitative", "qualitative"] else "quantitative"

    rows = normalize_rows(current_rows)

    updated = False
    for r in rows:
        if str(r[0]).strip() == name:
            r[1] = direction
            r[2] = weight_val
            if len(r) > 3:
                r[3] = type_val
            else:
                r.append(type_val)
            updated = True
            break

    if not updated:
        rows.append([name, direction, weight_val, type_val])

    alt_rows, headers = _update_electre_alternatives_schema(rows, current_alternatives)

    return (
        rows,
        gr.update(value=alt_rows, headers=headers),
        "",
        "maximize",
        "",
        "quantitative",
        gr.update(visible=False),
    )


def _update_electre_alternatives_schema(criteria_rows, alt_rows):
    criteria_names = [str(r[0]).strip() for r in criteria_rows if r and r[0]]
    headers = ["Име на алтернатива"] + criteria_names

    new_alt_rows = []
    alt_rows_normalized = normalize_rows(alt_rows)

    for row in alt_rows_normalized:
        new_row = [row[0]]
        for _ in range(len(criteria_names)):
            new_row.append("")
        new_alt_rows.append(new_row)

    if not new_alt_rows:
        new_row = [""] + [""] * len(criteria_names)
        new_alt_rows.append(new_row)

    return new_alt_rows, headers


def sync_electre_alternatives_columns(criteria_rows, current_alternatives):
    alt_rows, headers = _update_electre_alternatives_schema(
        normalize_rows(criteria_rows), current_alternatives
    )
    return gr.update(value=alt_rows, headers=headers)


def solve_electre_from_ui(
    problem_name,
    criteria_table,
    alternatives_table,
    concordance_threshold,
    discordance_threshold,
    saved_solutions,
):
    try:
        req = build_electre_request(
            problem_name,
            criteria_table,
            alternatives_table,
            concordance_threshold,
            discordance_threshold,
        )

        if saved_solutions and req.problem_name in saved_solutions:
            return (
                gr.update(visible=True),
                req.model_dump(mode="json"),
                gr.update(), gr.update(), gr.update(),
                gr.update(), gr.update(), gr.update(), gr.update(),
                "Забелязан конфликт в имената. Моля, изберете действие в страничния панел.",
            )

        return _perform_electre_solve_and_save(req, saved_solutions)

    except Exception as exc:
        return _format_electre_solver_error(exc, saved_solutions)


def _perform_electre_solve_and_save(req, saved_solutions):
    try:
        response_json = solve_via_api(req)
        return _format_electre_solver_response(req, response_json, saved_solutions)
    except Exception as exc:
        return _format_electre_solver_error(exc, saved_solutions)


def handle_electre_overwrite(pending_req_json, saved_solutions):
    from shared.schemas.electre import SolveRequest
    req = SolveRequest.model_validate(pending_req_json)
    return _perform_electre_solve_and_save(req, saved_solutions)


def handle_electre_rename(new_name, pending_req_json, saved_solutions):
    if not new_name or not str(new_name).strip():
        raise gr.Error("Моля, въведете валидно ново име.")

    from shared.schemas.electre import SolveRequest
    req_data = dict(pending_req_json)
    req_data["problem_name"] = str(new_name).strip()

    new_req = SolveRequest.model_validate(req_data)
    if saved_solutions and new_req.problem_name in saved_solutions:
        return (
            gr.update(visible=True),
            req_data,
            gr.update(), gr.update(), gr.update(),
            gr.update(), gr.update(), gr.update(), gr.update(),
            f"Името '{new_req.problem_name}' също съществува. Изберете действие.",
        )

    return _perform_electre_solve_and_save(new_req, saved_solutions)


def solve_electre_only(
    problem_name,
    criteria_table,
    alternatives_table,
    concordance_threshold,
    discordance_threshold,
):
    try:
        req = build_electre_request(
            problem_name,
            criteria_table,
            alternatives_table,
            concordance_threshold,
            discordance_threshold,
        )
        response_json = solve_via_api(req)
        return _format_electre_solver_response(req, response_json)
    except Exception as exc:
        return _format_electre_solver_error(exc)


def load_selected_electre_solution(selected_name, saved_solutions):
    if not selected_name or not saved_solutions or selected_name not in saved_solutions:
        return tuple([gr.update()] * 12)

    entry = saved_solutions[selected_name]
    req = entry.get("request", {}) or {}
    resp = entry.get("response", {}) or {}

    crit_rows = [
        [c.get("name"), c.get("direction", "maximize"), c.get("weight"), c.get("type", "quantitative")]
        for c in req.get("criterias", [])
    ]

    criteria_names = [c.get("name") for c in req.get("criterias", [])]
    headers = ["Име на алтернатива"] + criteria_names

    alt_rows = []
    for a in req.get("alternatives", []):
        row = [a.get("name")]
        vals = a.get("values", {})
        for cn in criteria_names:
            row.append(vals.get(cn, ""))
        alt_rows.append(row)

    kernel_text = _format_electre_kernel(resp.get("kernel") or [])
    outranking_rows = _format_outranking_rows(resp.get("outranking") or [])

    c_thr = req.get("concordance_threshold", 0.7)
    d_thr = req.get("discordance_threshold", 0.3)

    return (
        req.get("problem_name", selected_name),
        crit_rows,
        gr.update(value=alt_rows, headers=headers),
        c_thr,
        d_thr,
        resp,
        req,
        resp,
        kernel_text,
        outranking_rows,
        req,
        f"Заредена задача: {selected_name}",
    )


def electre_arm_delete(selected_name, armed, saved_solutions):
    if not selected_name:
        return (
            False,
            gr.update(value="Изтрий избраната", variant="stop"),
            gr.update(visible=False),
            gr.update(value="", visible=False),
            gr.update(),
            gr.update(),
            gr.update(),
            "Първо изберете задача от списъка.",
        )

    if not armed:
        return (
            True,
            gr.update(value=f"⚠️ Потвърди изтриване на „{selected_name}“", variant="stop"),
            gr.update(visible=True),
            gr.update(
                value="Натиснете отново за окончателно изтриване, или *Отказ* за прекратяване.",
                visible=True,
            ),
            gr.update(),
            gr.update(),
            gr.update(),
            f"Готов за изтриване: {selected_name}. Потвърдете или откажете.",
        )

    if not saved_solutions or selected_name not in saved_solutions:
        return (
            False,
            gr.update(value="Изтрий избраната", variant="stop"),
            gr.update(visible=False),
            gr.update(value="", visible=False),
            saved_solutions,
            gr.update(),
            gr.update(),
            f"Задачата '{selected_name}' вече не съществува.",
        )

    del saved_solutions[selected_name]
    saved_names = list(saved_solutions.keys())
    summary = update_electre_history_summary(saved_solutions)

    return (
        False,
        gr.update(value="Изтрий избраната", variant="stop"),
        gr.update(visible=False),
        gr.update(value="", visible=False),
        saved_solutions,
        gr.update(choices=saved_names, value=None),
        summary,
        f"Задачата '{selected_name}' беше изтрита.",
    )


def electre_cancel_delete():
    return (
        False,
        gr.update(value="Изтрий избраната", variant="stop"),
        gr.update(visible=False),
        gr.update(value="", visible=False),
    )
