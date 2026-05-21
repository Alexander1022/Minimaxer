import gradio as gr
from gradio_modal import Modal

from ui.actions import (
    add_constraint,
    add_objective_coefficient,
    add_variable,
    hide_panel,
    load_saved_solution,
    show_panel,
    solve_from_ui,
)
from ui.preview import preview_problem

def create_app():
    with gr.Blocks(theme=gr.Theme.from_hub("harsh8001/skymist"), title="Еднокритериална Оптимизация") as app:
        gr.Markdown("# Minimaxer")
        
        saved_solutions = gr.State({})

        with gr.Tabs():
            with gr.Tab("1. Модел и Променливи"):
                with gr.Row():
                    problem_name = gr.Textbox(
                        label="Име на задача",
                        value="Примерна задача",
                        scale=2
                    )
                    direction = gr.Radio(
                        label="Посока на оптимизация",
                        choices=[("Максимизиране", "maximize"), ("Минимизиране", "minimize")],
                        value="maximize",
                        scale=1
                    )

                gr.Markdown("### Дефиниране на променливи")
                open_variable_panel_btn = gr.Button("Добави променлива", variant="secondary")

                with Modal(visible=False) as variable_panel:
                    gr.Markdown("### Нова променлива")
                    with gr.Row():
                        variable_name_input = gr.Textbox(label="Име", placeholder="x1")
                        variable_low_input = gr.Number(label="Долна граница", value=None)
                        variable_up_input = gr.Number(label="Горна граница", value=None)

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

                variables_table = gr.Dataframe(
                    label="Списък с променливи",
                    headers=["име", "долна граница", "горна граница", "категория"],
                    value=[
                        ["x", None, None, "Continuous"],
                        ["y", None, None, "Continuous"],
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
                                objective_coefficient_input = gr.Number(label="Коефициент", value=None)
                            with gr.Row():
                                add_objective_btn = gr.Button("Добави", variant="primary")
                                cancel_objective_btn = gr.Button("Отказ")

                        objective_table = gr.Dataframe(
                            label="Коефициенти",
                            headers=["променлива", "коефициент"],
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
                                constraint_rhs_input = gr.Number(label="Дясна страна", value=None)
                                
                            with gr.Row():
                                add_constraint_btn = gr.Button("Добави", variant="primary")
                                cancel_constraint_btn = gr.Button("Отказ")

                        constraints_table = gr.Dataframe(
                            label="Списък с ограничения",
                            headers=["име", "коефициенти", "оператор", "дясна страна"],
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
                    solve_btn = gr.Button("Реши задачата", variant="primary")

                preview_output = gr.Markdown(label="Математически преглед")
                status_message = gr.Textbox(label="Статус", interactive=False)

                gr.Markdown("### Резултати")
                result_table = gr.Dataframe(
                    label="Стойности на променливите",
                    headers=["име", "стойност"],
                    interactive=False,
                )

                with gr.Accordion("Детайли от заявката (JSON)", open=False):
                    with gr.Row():
                        request_output = gr.JSON(label="Изпратена заявка")
                        response_output = gr.JSON(label="Отговор от решаващия модул")

            with gr.Tab("4. Запазени решения"):
                gr.Markdown("### Зареждане на предишни решения")
                with gr.Row():
                    saved_dropdown = gr.Dropdown(
                        label="Изберете запазено решение",
                        choices=[],
                        interactive=True,
                        scale=3
                    )
                    load_btn = gr.Button("Зареди", scale=1)

                with gr.Row():
                    saved_request_output = gr.JSON(label="Запазена заявка")
                    saved_response_output = gr.JSON(label="Запазен отговор")

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
                objective_table
            ],
            outputs=[
                variables_table, 
                objective_table, 
                objective_variable_input, 
                variable_name_input, 
                variable_low_input, 
                variable_up_input, 
                variable_category_input, 
                variable_panel
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
            fn=preview_problem,
            inputs=[problem_name, direction, variables_table, objective_table, constraints_table],
            outputs=preview_output,
        )

        solve_btn.click(
            fn=solve_from_ui,
            inputs=[problem_name, direction, variables_table, objective_table, constraints_table, saved_solutions],
            outputs=[response_output, result_table, request_output, saved_solutions, saved_dropdown, status_message],
        )

        load_btn.click(
            fn=load_saved_solution,
            inputs=[saved_dropdown, saved_solutions],
            outputs=[saved_request_output, saved_response_output],
        )

    return app