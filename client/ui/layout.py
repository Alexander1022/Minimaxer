import gradio as gr
from gradio_modal import Modal

from ui.actions import (
    add_constraint,
    add_objective_coefficient,
    add_variable,
    arm_delete,
    cancel_delete,
    handle_overwrite,
    handle_rename,
    hide_panel,
    load_selected_solution,
    show_panel,
    solve_from_ui,
    solve_only,
    toggle_preview,
    update_history_summary,
    initialize_saved_data,
)

def create_app():
    with gr.Blocks(theme=gr.Theme.from_hub("harsh8001/skymist"), title="Еднокритериална Оптимизация") as app:
        gr.Markdown("# Minimaxer")

        saved_solutions = gr.BrowserState(
            storage_key="minimaxer_history",
            secret="minimaxer-history-secret-v1",
            default_value={},
        )
        pending_request = gr.State({})
        delete_armed = gr.State(False)

        with gr.Sidebar():
            gr.Markdown("## Управление на задачи")

            with gr.Group(visible=False) as conflict_ui:
                gr.Markdown("### ⚠️ Име вече съществува")
                gr.Markdown("Задача с това име вече е запазена. Изберете действие:")
                with gr.Row():
                    overwrite_btn = gr.Button("Презапиши", variant="primary")
                gr.Markdown("--- или запишете с ново име ---")
                new_name_input = gr.Textbox(label="Ново име", placeholder="Въведете ново име...")
                rename_save_btn = gr.Button("Запази с ново име", variant="secondary")

            gr.Markdown("### Запазени решения")

            saved_list = gr.Radio(
                label="Изберете задача",
                choices=[],
                interactive=True,
                container=True,
            )

            with gr.Row():
                delete_btn = gr.Button("Изтрий избраната", variant="stop", scale=2)
                delete_cancel_btn = gr.Button("Отказ", variant="secondary", scale=1, visible=False)

            delete_hint = gr.Markdown("", visible=False)

            gr.Markdown("### Обобщение на историята")
            history_summary = gr.Markdown("Няма запазени решения.")

        with gr.Tabs():
            with gr.Tab("1. Модел и Променливи"):
                with gr.Row():
                    problem_name = gr.Textbox(
                        label="Име на задача",
                        value="Примерна задача",
                        scale=2,
                    )
                    direction = gr.Radio(
                        label="Посока на оптимизация",
                        choices=[("Максимизиране", "maximize"), ("Минимизиране", "minimize")],
                        value="maximize",
                        scale=1,
                    )

                gr.Markdown("### Дефиниране на променливи")
                open_variable_panel_btn = gr.Button("Добави променлива", variant="secondary")

                with Modal(visible=False) as variable_panel:
                    gr.Markdown("### Нова променлива")
                    with gr.Row():
                        variable_name_input = gr.Textbox(label="Име", placeholder="x1")
                        # Оставяме ги като текст, за да позволяват празни стойности
                        variable_low_input = gr.Textbox(label="Долна граница", placeholder="напр. 0 (или оставете празно)")
                        variable_up_input = gr.Textbox(label="Горна граница", placeholder="напр. 100 (или оставете празно)")

                    variable_category_input = gr.Dropdown(
                        label="Категория",
                        choices=[("Непрекъсната", "Continuous"),
                                 ("Целочислена", "Integer"),
                                 ("Булева", "Binary")],
                        value="Continuous",
                    )
                    with gr.Row():
                        add_variable_btn = gr.Button("Добави", variant="primary")
                        cancel_variable_btn = gr.Button("Отказ")

                # Променяме datatype изцяло на текст ("str"), за да може да има празни клетки (""),
                # които бекендът ви превръща в None.
                variables_table = gr.Dataframe(
                    label="Списък с променливи",
                    headers=["име", "долна граница", "горна граница", "категория"],
                    datatype=["str", "str", "str", "str"],
                    value=[
                        ["x", "", "", "Continuous"],
                        ["y", "", "", "Continuous"],
                    ],
                    row_count=(2, "dynamic"),
                    col_count=(4, "fixed"),
                    interactive=True,
                )

            with gr.Tab("2. Целева функция и Ограничения"):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### Целева функция")
                        open_objective_panel_btn = gr.Button("Добави коефициент", variant="secondary")

                        with Modal(visible=False) as objective_panel:
                            gr.Markdown("### Добавяне към целевата функция")
                            gr.Markdown("Пример: За 5x изберете променлива x и въведете коефициент 5.")
                            with gr.Row():
                                objective_variable_input = gr.Dropdown(label="Променлива", choices=["x", "y"])
                                objective_coefficient_input = gr.Textbox(label="Коефициент", placeholder="Напр. 5")
                            with gr.Row():
                                add_objective_btn = gr.Button("Добави", variant="primary")
                                cancel_objective_btn = gr.Button("Отказ")

                        objective_table = gr.Dataframe(
                            label="Коефициенти",
                            headers=["променлива", "коефициент"],
                            datatype=["str", "str"],
                            value=[["x", 0], ["y", 0]],
                            row_count=(2, "dynamic"),
                            col_count=(2, "fixed"),
                            interactive=True,
                        )

                    with gr.Column():
                        gr.Markdown("### Ограничения")
                        open_constraint_panel_btn = gr.Button("Добави ограничение", variant="secondary")

                        with Modal(visible=False) as constraint_panel:
                            gr.Markdown("### Ново ограничение")
                            gr.Markdown("Пример: За 2x + y <= 10 въведете коефициенти x:2,y:1")

                            constraint_name_input = gr.Textbox(label="Име", placeholder="c1")
                            constraint_coefficients_input = gr.Textbox(label="Коефициенти", placeholder="x:2,y:1")

                            with gr.Row():
                                constraint_operator_input = gr.Radio(
                                    label="Оператор",
                                    choices=["<=", ">=", "=="],
                                    value="<=",
                                )
                                constraint_rhs_input = gr.Textbox(label="Дясна страна", placeholder="Напр. 10")

                            with gr.Row():
                                add_constraint_btn = gr.Button("Добави", variant="primary")
                                cancel_constraint_btn = gr.Button("Отказ")

                        constraints_table = gr.Dataframe(
                            label="Списък с ограничения",
                            headers=["име", "коефициенти", "оператор", "дясна страна"],
                            datatype=["str", "str", "str", "str"],
                            value=[
                                ["c1", "x:2,y:1", "<=", 10],
                                ["c2", "x:1,y:1", "<=", 7],
                            ],
                            row_count=(2, "dynamic"),
                            col_count=(4, "fixed"),
                            interactive=True,
                        )

            with gr.Tab("3. Преглед и Решаване"):
                with gr.Row():
                    preview_btn = gr.Button("Преглед на модела")
                    solve_btn = gr.Button("Реши и Запази", variant="primary")
                    solve_only_btn = gr.Button("Реши", variant="primary")

                preview_output = gr.Markdown(label="Математически преглед", visible=False)
                status_message = gr.Textbox(label="Статус", interactive=False)

                gr.Markdown("### Резултати")
                objective_value_output = gr.Textbox(label="Оптимална стойност на целевата функция", interactive=False)
                result_table = gr.Dataframe(
                    label="Стойности на променливите",
                    headers=["име", "стойност"],
                    interactive=False,
                )

                with gr.Accordion("Детайли от заявката (JSON)", open=False):
                    with gr.Row():
                        request_output = gr.JSON(label="Изпратена заявка")
                        response_output = gr.JSON(label="Отговор от решаващия модул")

            with gr.Tab("4. Запазени решения (Детайли)"):
                gr.Markdown("### Преглед на запазени данни")
                with gr.Row():
                    saved_request_output = gr.JSON(label="Запазена заявка")
                    saved_response_output = gr.JSON(label="Запазен отговор")

        solve_outputs = [
            conflict_ui, pending_request, response_output,
            objective_value_output, result_table,
            request_output, saved_solutions, saved_list, history_summary, status_message,
        ]

        saved_solutions.change(
            fn=update_history_summary,
            inputs=saved_solutions,
            outputs=history_summary,
        )
        saved_solutions.change(
            fn=lambda s: gr.update(choices=list(s.keys()) if s else []),
            inputs=saved_solutions,
            outputs=saved_list,
        )

        app.load(
            fn=initialize_saved_data,
            inputs=[saved_solutions],
            outputs=[history_summary, saved_list],
        )

        open_variable_panel_btn.click(fn=show_panel, outputs=variable_panel)
        cancel_variable_btn.click(fn=hide_panel, outputs=variable_panel)
        add_variable_btn.click(
            fn=add_variable,
            inputs=[
                variable_name_input,
                variable_low_input,
                variable_up_input,
                variable_category_input,
                variables_table,
                objective_table,
            ],
            outputs=[
                variables_table,
                objective_table,
                objective_variable_input,
                variable_name_input,
                variable_low_input,
                variable_up_input,
                variable_category_input,
                variable_panel,
            ],
        )

        open_objective_panel_btn.click(fn=show_panel, outputs=objective_panel)
        cancel_objective_btn.click(fn=hide_panel, outputs=objective_panel)
        add_objective_btn.click(
            fn=add_objective_coefficient,
            inputs=[objective_variable_input, objective_coefficient_input, objective_table],
            outputs=[objective_table, objective_variable_input, objective_coefficient_input, objective_panel],
        )

        open_constraint_panel_btn.click(fn=show_panel, outputs=constraint_panel)
        cancel_constraint_btn.click(fn=hide_panel, outputs=constraint_panel)
        add_constraint_btn.click(
            fn=add_constraint,
            inputs=[constraint_name_input, constraint_coefficients_input, constraint_operator_input, constraint_rhs_input, constraints_table],
            outputs=[constraints_table, constraint_name_input, constraint_coefficients_input, constraint_operator_input, constraint_rhs_input, constraint_panel],
        )

        preview_btn.click(
            fn=toggle_preview,
            inputs=[preview_btn, problem_name, direction, variables_table, objective_table, constraints_table],
            outputs=[preview_output, preview_btn],
        )

        solve_btn.click(
            fn=solve_from_ui,
            inputs=[problem_name, direction, variables_table, objective_table, constraints_table, saved_solutions],
            outputs=solve_outputs,
        )

        solve_only_btn.click(
            fn=solve_only,
            inputs=[problem_name, direction, variables_table, objective_table, constraints_table],
            outputs=solve_outputs,
        )

        overwrite_btn.click(
            fn=handle_overwrite,
            inputs=[pending_request, saved_solutions],
            outputs=solve_outputs,
        )

        rename_save_btn.click(
            fn=handle_rename,
            inputs=[new_name_input, pending_request, saved_solutions],
            outputs=solve_outputs,
        )

        saved_list.change(
            fn=load_selected_solution,
            inputs=[saved_list, saved_solutions],
            outputs=[
                problem_name, direction, variables_table, objective_table, constraints_table,
                response_output, saved_request_output, saved_response_output,
                objective_value_output, result_table, request_output, status_message,
            ],
        ).then(
            fn=cancel_delete,
            outputs=[delete_armed, delete_btn, delete_cancel_btn, delete_hint],
        )

        delete_btn.click(
            fn=arm_delete,
            inputs=[saved_list, delete_armed, saved_solutions],
            outputs=[
                delete_armed, delete_btn, delete_cancel_btn, delete_hint,
                saved_solutions, saved_list, history_summary, status_message,
            ],
        )

        delete_cancel_btn.click(
            fn=cancel_delete,
            outputs=[delete_armed, delete_btn, delete_cancel_btn, delete_hint],
        )

    return app
