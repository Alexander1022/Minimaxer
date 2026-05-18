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
    with gr.Blocks(
            theme=gr.Theme.from_hub("harsh8001/skymist"),
            title="EO"
        ) as app:
        gr.Markdown("# EO")

        saved_solutions = gr.State({})

        with gr.Row():
            problem_name = gr.Textbox(
                label="Име на задача",
                value="Задача",
            )

            direction = gr.Radio(
                label="Optimization direction",
                choices=["maximize", "minimize"],
                value="maximize",
            )

        gr.Markdown("## Променливи")

        open_variable_panel_btn = gr.Button("Добави променлива")

        with Modal(visible=False) as variable_panel:
            gr.Markdown("### Добави променлива")

            with gr.Row():
                variable_name_input = gr.Textbox(label="Име", placeholder="x")
                variable_low_input = gr.Number(label="Долна граница", value=0)
                variable_up_input = gr.Number(label="Горна граница", value=None)

            variable_category_input = gr.Radio(
                label="Категория",
                choices=["Continuous", "Integer", "Binary"],
                value="Continuous",
            )

            with gr.Row():
                add_variable_btn = gr.Button("Добави", variant="primary")
                cancel_variable_btn = gr.Button("Отказ")

        variables_table = gr.Dataframe(
            label="Променливи",
            headers=["име", "долна граница", "горна граница", "категория"],
            value=[
                ["x", 0, None, "Continuous"],
                ["y", 0, None, "Continuous"],
            ],
            row_count=(2, "dynamic"),
            col_count=(4, "fixed"),
            interactive=True,
        )

        gr.Markdown("## Целева функция")

        open_objective_panel_btn = gr.Button("Добави коефициент на целевата функция")

        with Modal(visible=False) as objective_panel:
            gr.Markdown("### Добави коефициент на целевата функция")
            gr.Markdown("Пример: `5x + 3y` означава добавяне на `x = 5` и `y = 3`.")

            with gr.Row():
                objective_variable_input = gr.Textbox(label="Променлива", placeholder="x")
                objective_coefficient_input = gr.Number(label="Коефициент", value=None)

            with gr.Row():
                add_objective_btn = gr.Button("Добави", variant="primary")
                cancel_objective_btn = gr.Button("Отказ")

        objective_table = gr.Dataframe(
            label="Коефициенти на целевата функция",
            headers=["променлива", "коефициент"],
            value=[
                ["x", 5],
                ["y", 3],
            ],
            row_count=(2, "dynamic"),
            col_count=(2, "fixed"),
            interactive=True,
        )

        gr.Markdown("## Ограничения")

        open_constraint_panel_btn = gr.Button("Добави ограничение")

        with Modal(visible=False) as constraint_panel:
            gr.Markdown("### Добави ограничение")
            gr.Markdown("Пример: `2x + y <= 10` става коефициенти `x:2,y:1` <= 10.")

            constraint_name_input = gr.Textbox(label="Име", placeholder="c1")

            constraint_coefficients_input = gr.Textbox(
                label="Коефициенти",
                placeholder="x:2,y:1",
            )

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
            label="Ограничения",
            headers=["име", "коефициенти", "оператор", "дясна страна"],
            value=[
                ["c1", "x:2,y:1", "<=", 10],
                ["c2", "x:1,y:1", "<=", 7],
            ],
            row_count=(2, "dynamic"),
            col_count=(4, "fixed"),
            interactive=True,
        )

        gr.Markdown("## Преглед и решаване")

        with gr.Row():
            preview_btn = gr.Button("Преглед")
            solve_btn = gr.Button("Реши", variant="primary")

        preview_output = gr.Markdown(label="Преглед")

        status_message = gr.Textbox(label="Статус", interactive=False)

        with gr.Row():
            response_output = gr.JSON(label="Отговор от решаването")
            request_output = gr.JSON(label="Генериран JSON за заявка")

        result_table = gr.Dataframe(
            label="Резултати за променливите",
            headers=["име", "стойност"],
            interactive=False,
        )

        gr.Markdown("## Запазени решения")

        saved_dropdown = gr.Dropdown(
            label="Имена на запазени решения",
            choices=[],
            interactive=True,
        )

        load_btn = gr.Button("Зареди запазено решение")

        with gr.Row():
            saved_request_output = gr.JSON(label="Запазена заявка")
            saved_response_output = gr.JSON(label="Запазен отговор")

        open_variable_panel_btn.click(
            fn=show_panel,
            outputs=variable_panel,
        )

        cancel_variable_btn.click(
            fn=hide_panel,
            outputs=variable_panel,
        )

        add_variable_btn.click(
            fn=add_variable,
            inputs=[
                variable_name_input,
                variable_low_input,
                variable_up_input,
                variable_category_input,
                variables_table,
            ],
            outputs=[
                variables_table,
                variable_name_input,
                variable_low_input,
                variable_up_input,
                variable_category_input,
                variable_panel,
            ],
        )

        open_objective_panel_btn.click(
            fn=show_panel,
            outputs=objective_panel,
        )

        cancel_objective_btn.click(
            fn=hide_panel,
            outputs=objective_panel,
        )

        add_objective_btn.click(
            fn=add_objective_coefficient,
            inputs=[
                objective_variable_input,
                objective_coefficient_input,
                objective_table,
            ],
            outputs=[
                objective_table,
                objective_variable_input,
                objective_coefficient_input,
                objective_panel,
            ],
        )

        open_constraint_panel_btn.click(
            fn=show_panel,
            outputs=constraint_panel,
        )

        cancel_constraint_btn.click(
            fn=hide_panel,
            outputs=constraint_panel,
        )

        add_constraint_btn.click(
            fn=add_constraint,
            inputs=[
                constraint_name_input,
                constraint_coefficients_input,
                constraint_operator_input,
                constraint_rhs_input,
                constraints_table,
            ],
            outputs=[
                constraints_table,
                constraint_name_input,
                constraint_coefficients_input,
                constraint_operator_input,
                constraint_rhs_input,
                constraint_panel,
            ],
        )

        preview_btn.click(
            fn=preview_problem,
            inputs=[
                problem_name,
                direction,
                variables_table,
                objective_table,
                constraints_table,
            ],
            outputs=preview_output,
        )

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

    return app